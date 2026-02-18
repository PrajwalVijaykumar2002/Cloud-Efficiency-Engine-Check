import streamlit as st
import time
import os
import pandas as pd
from google.cloud import storage
from google.cloud.sql.connector import Connector
import sqlalchemy

# --- 1. CONFIGURATION ---
current_dir = os.path.dirname(os.path.abspath(__file__))
key_path = os.path.join(current_dir, "keys.json")

if not os.path.exists(key_path):
    st.error(f"❌ Critical Error: '{key_path}' not found!")
    st.stop()

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = key_path

# --- 2. CLOUD SQL SETUP ---
INSTANCE_CONNECTION = "cloud-storage-vs-sql-groupc:europe-west9:metadata-db"
DB_USER = "app-user"
DB_PASS = ""  # ENTER YOUR PASSWORD HERE
DB_NAME = "app_data"

connector = Connector()

def getconn():
    return connector.connect(INSTANCE_CONNECTION, "pymysql", user=DB_USER, password=DB_PASS, db=DB_NAME)

pool = sqlalchemy.create_engine(
    "mysql+pymysql://", 
    creator=getconn,
    pool_pre_ping=True,    # Fixes 'Remote end closed connection' errors
    pool_recycle=1800      # Refreshes connections every 30 mins
)

# --- 3. UI CONFIGURATION ---
st.set_page_config(page_title="Topic B: Cloud Benchmarking", layout="wide")
st.title("☁️ Google Cloud Storage vs. Cloud SQL")
st.markdown("### Group C - Comparative Analysis Prototype")

with st.expander("ℹ️ See System Architecture & Workflow"):
    st.write("""
    1. **Unstructured Path:** Object sent to GCS Bucket.
    2. **Structured Path:** Binary stream stored in MySQL `LONGBLOB`.
    3. **Benchmark:** Real-time latency measurement for Upload vs Download.
    """)

st.sidebar.header("Cloud Settings")
bucket_name_input = st.sidebar.text_input("GCS Bucket Name", "group-c-assets")

# --- 4. UPLOAD & BENCHMARK LOGIC ---
st.header("📤 Upload Benchmark")
uploaded_file = st.file_uploader("Upload a file (Image or Video)", type=['png', 'jpg', 'pdf', 'txt', 'mp4', 'mov'])

if uploaded_file:
    file_bytes = uploaded_file.getvalue()
    file_name = uploaded_file.name
    file_size_mb = len(file_bytes) / (1024 * 1024)
    
    st.info(f"📂 **Processing:** {file_name} ({file_size_mb:.2f} MB)")
    
    progress_bar = st.progress(0)
    status_text = st.empty()

    # --- GCS UPLOAD ---
    status_text.text("🚀 Uploading to GCS...")
    start_gcs = time.time()
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name_input)
    blob = bucket.blob(file_name)
    blob.upload_from_string(file_bytes, content_type=uploaded_file.type)
    end_gcs = time.time() - start_gcs
    progress_bar.progress(50)

    # --- SQL UPLOAD ---
    status_text.text("💾 Inserting into Cloud SQL...")
    start_sql = time.time()
    sql_success = False 
    
    try:
        with pool.connect() as conn:
            conn.execute(sqlalchemy.text("INSERT INTO file_benchmarks (name, data) VALUES (:name, :data)"), 
                         {"name": file_name, "data": file_bytes})
            conn.commit()
        end_sql = time.time() - start_sql
        sql_success = True
    except Exception as e:
        end_sql = 0
        st.error(f"❌ SQL Upload Failed: File ({file_size_mb:.2f}MB) exceeds 'max_allowed_packet' or timeout limits.")
        st.warning("Note: This is a known limitation of storing Large Blobs in Relational Databases.")
    
    progress_bar.progress(100)
    status_text.text("✅ Benchmark Attempt Complete")

    # --- RESULTS ---
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("GCS Upload", f"{end_gcs:.4f}s")
    
    if sql_success:
        col_b.metric("SQL Upload", f"{end_sql:.4f}s")
        if end_gcs < end_sql:
            diff = (end_sql / end_gcs)
            col_c.metric("Winner", "GCS", delta=f"{diff:.1f}x Faster")
        else:
            diff = (end_gcs / end_sql)
            col_c.metric("Winner", "SQL", delta=f"{diff:.1f}x Faster")
            
        # --- BAR CHART ---
        st.subheader("📊 Latency Comparison (Upload)")
        chart_data = pd.DataFrame({
            "Service": ["GCS", "SQL"],
            "Time (Seconds)": [end_gcs, end_sql]
        })
        st.bar_chart(chart_data, x="Service", y="Time (Seconds)")
    else:
        col_b.metric("SQL Upload", "FAILED")
        col_c.metric("Winner", "GCS", delta="SQL crashed")

# --- 5. DATA MANAGEMENT & EXPLORER ---
st.divider()
tab_benchmark, tab_search, tab_preview = st.tabs(["🚀 Benchmark Retrieval", "🔍 Search Files", "📋 Database Preview"])

with tab_benchmark:
    st.header("📂 Retrieval Comparison")
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name_input)
        gcs_files = [blob.name for blob in bucket.list_blobs()]

        with pool.connect() as conn:
            result = conn.execute(sqlalchemy.text("SELECT name FROM file_benchmarks"))
            sql_files = [row[0] for row in result.fetchall()]

        available_files = list(set(gcs_files + sql_files))

        if available_files:
            selected_file = st.selectbox("Choose a file to retrieve:", available_files)
            
            if st.button("🚀 Run Download Benchmark"):
                dl_status = st.empty()
                dl_status.text("⏳ Retrieving from both services...")
                
                dl_col1, dl_col2 = st.columns(2)

                # GCS Download
                with dl_col1:
                    start_dl_gcs = time.time()
                    blob = bucket.blob(selected_file)
                    gcs_data = blob.download_as_bytes()
                    end_dl_gcs = time.time() - start_dl_gcs
                    st.metric("GCS Retrieval", f"{end_dl_gcs:.4f}s")
                    st.download_button("Save from GCS", data=gcs_data, file_name=f"gcs_{selected_file}")

                # SQL Download
                with dl_col2:
                    start_dl_sql = time.time()
                    with pool.connect() as conn:
                        row = conn.execute(
                            sqlalchemy.text("SELECT data FROM file_benchmarks WHERE name = :name LIMIT 1"),
                            {"name": selected_file}
                        ).fetchone()
                        sql_data = row[0] if row else None
                    end_dl_sql = time.time() - start_dl_sql
                    
                    if sql_data:
                        st.metric("SQL Retrieval", f"{end_dl_sql:.4f}s")
                        st.download_button("Save from SQL", data=sql_data, file_name=f"sql_{selected_file}")
                    else:
                        st.warning("File not found in SQL database.")

                dl_status.empty()

                st.divider()
                if end_dl_gcs < end_dl_sql:
                    speed_diff = end_dl_sql / end_dl_gcs
                    st.success(f"🏆 **Benchmark Result:** GCS was **{speed_diff:.1f}x faster** than Cloud SQL.")
                    st.balloons()
                else:
                    speed_diff = end_dl_gcs / end_dl_sql
                    st.success(f"🏆 **Benchmark Result:** Cloud SQL was **{speed_diff:.1f}x faster** than GCS.")
                    st.snow()
                    
                st.subheader("📊 Latency Comparison (Retrieval)")
                dl_chart_data = pd.DataFrame({
                    "Service": ["GCS", "SQL"],
                    "Time (Seconds)": [end_dl_gcs, end_dl_sql]
                })
                st.bar_chart(dl_chart_data, x="Service", y="Time (Seconds)")
        else:
            st.info("No files found. Please upload a file above first.")
    except Exception as e:
        st.error(f"Explorer Error: {e}")

with tab_search:
    st.subheader("🔍 Metadata Search")
    search_query = st.text_input("Enter filename to search in SQL database...")
    
    if search_query:
        try:
            with pool.connect() as conn:
                query = sqlalchemy.text("SELECT id, name FROM file_benchmarks WHERE name LIKE :name")
                search_results = conn.execute(query, {"name": f"%{search_query}%"}).fetchall()
                
                if search_results:
                    st.write(f"Found {len(search_results)} result(s):")
                    st.dataframe(pd.DataFrame(search_results, columns=["ID", "Filename"]), use_container_width=True)
                else:
                    st.warning("No matches found in the SQL database.")
        except Exception as e:
            st.error(f"Search Error: {e}")

with tab_preview:
    st.subheader("📋 SQL Table Statistics & Management")
    
    # 1. Fetch data for the table and the selection dropdown
    try:
        with pool.connect() as conn:
            query = sqlalchemy.text("SELECT id, name, LENGTH(data) as size_bytes FROM file_benchmarks")
            all_data = conn.execute(query).fetchall()
            
            if all_data:
                df = pd.DataFrame(all_data, columns=["ID", "Filename", "Size_Bytes"])
                df["Size (MB)"] = (df["Size_Bytes"] / (1024 * 1024)).round(4)
                
                # Display the current table
                st.table(df[["ID", "Filename", "Size (MB)"]])
                
                st.divider()
                st.subheader("🗑️ Delete Data")
                col_del1, col_del2 = st.columns([2, 1])
                target_file = col_del1.selectbox("Select a file to remove:", df["Filename"].tolist())
                # 2. UI for Deletion
                col_del1, col_del2 = st.columns([2, 1])
                file_to_delete = col_del1.selectbox("Select a file to remove from Cloud:", df["Filename"].tolist(), key="del_select")
                
                if col_del2.button("⚠️ Delete Permanently", type="primary"):
                    # A. Delete from Cloud SQL
                    with pool.connect() as conn:
                        conn.execute(
                            sqlalchemy.text("DELETE FROM file_benchmarks WHERE name = :name"),
                            {"name": target_file}
                        )
                        conn.commit()
                    
                    # B. Delete from GCS
                    try:
                        storage_client = storage.Client()
                        bucket = storage_client.bucket(bucket_name_input)
                        blob = bucket.blob(target_file)
                        blob.delete()
                        gcs_msg = "and GCS Bucket"
                    except Exception as gcs_err:
                        gcs_msg = "(GCS file already gone or error)"

                    st.success(f"Successfully deleted '{target_file}' from SQL {gcs_msg}!")
                    time.sleep(1) # Short pause so the user sees the success
                    st.rerun() # Refresh the page to update the table
                    
            else:
                st.info("The SQL database is currently empty.")
                if st.button("🔄 Refresh View"):
                    st.rerun()

    except Exception as e:
        st.error(f"Management Error: {e}")