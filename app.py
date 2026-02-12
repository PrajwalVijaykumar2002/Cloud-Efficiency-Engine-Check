# import streamlit as st
# import time
# import os
# from google.cloud import storage
# from google.cloud.sql.connector import Connector
# import sqlalchemy

# # --- CONFIGURATION ---
# os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "keys.json"
# BUCKET_NAME = "group-c-assets"
# INSTANCE_CONNECTION = "cloud-storage-vs-sql-groupc:europe-west9:metadata-db"
# DB_USER = "app-user"
# DB_PASS = ""
# DB_NAME = "app_data"

# st.set_page_config(page_title="Topic B: GCS vs SQL Comparison", layout="wide")
# st.title("📊 Google Cloud Storage vs. Cloud SQL")
# st.subheader("Group C - Comparative Performance Analysis")

# # --- DATABASE CONNECTION ---
# connector = Connector()
# def getconn():
#     return connector.connect(INSTANCE_CONNECTION, "pymysql", user=DB_USER, password=DB_PASS, db=DB_NAME)

# pool = sqlalchemy.create_engine("mysql+pymysql://", creator=getconn)

# # --- APP UI ---
# uploaded_file = st.file_uploader("Upload a file to compare performance", type=['jpg', 'png', 'pdf', 'txt'])

# if uploaded_file:
#     file_bytes = uploaded_file.getvalue()
#     filename = uploaded_file.name

#     col1, col2 = st.columns(2)

#     # --- TEST 1: GOOGLE CLOUD STORAGE ---
#     with col1:
#         st.info("Testing GCS (Object Storage)...")
#         start_time = time.time()
        
#         storage_client = storage.Client()
#         bucket = storage_client.bucket(BUCKET_NAME)
#         blob = bucket.blob(filename)
#         blob.upload_from_string(file_bytes)
        
#         gcs_time = time.time() - start_time
#         st.success(f"GCS Upload Complete!")
#         st.metric("Time Taken", f"{gcs_time:.4f} seconds")

#     # --- TEST 2: CLOUD SQL ---
#     with col2:
#         st.info("Testing Cloud SQL (Relational)...")
#         start_time = time.time()
        
#         with pool.connect() as conn:
#             # We store the actual file bytes in a LONGBLOB to show why SQL is slower for files
#             conn.execute(sqlalchemy.text("CREATE TABLE IF NOT EXISTS file_blobs (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(255), data LONGBLOB)"))
#             conn.execute(sqlalchemy.text("INSERT INTO file_blobs (name, data) VALUES (:name, :data)"), {"name": filename, "data": file_bytes})
#             conn.commit()
            
#         sql_time = time.time() - start_time
#         st.success(f"SQL Upload Complete!")
#         st.metric("Time Taken", f"{sql_time:.4f} seconds")

#     # --- RESULTS ---
#     st.divider()
#     st.header("Comparative Analysis Summary")
    
#     if gcs_time < sql_time:
#         st.write(f"✅ **GCS was {(sql_time/gcs_time):.1f}x faster** than Cloud SQL for this file.")
#     else:
#         st.write("SQL was faster (only common for tiny text fragments).")

import streamlit as st
import time
import os
import pandas as pd
from google.cloud import storage
from google.cloud.sql.connector import Connector
import sqlalchemy

# --- 1. CONFIGURATION ---
# Ensure your keys.json is in the same folder as this script
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "keys.json"

# --- 2. CLOUD SQL SETUP ---
# Replace these with your actual credentials
INSTANCE_CONNECTION = "cloud-storage-vs-sql-groupc:europe-west9:metadata-db"
DB_USER = "app-user"
DB_PASS = ""  # Add your password here
DB_NAME = "app_data"

# Initialize Cloud SQL Connector
connector = Connector()

def getconn():
    conn = connector.connect(
        INSTANCE_CONNECTION,
        "pymysql",
        user=DB_USER,
        password=DB_PASS,
        db=DB_NAME
    )
    return conn

# Create the SQLAlchemy Engine
pool = sqlalchemy.create_engine("mysql+pymysql://", creator=getconn)

# --- 3. UI CONFIGURATION ---
st.set_page_config(page_title="Topic B: Cloud Benchmarking", layout="wide")
st.title("☁️ Google Cloud Storage vs. Cloud SQL")
st.markdown("### Group C - Comparative Analysis Prototype")

# Architecture Info Expander
with st.expander("ℹ️ See System Architecture & Workflow"):
    st.write("""
    **How this works:**
    1. **Unstructured Path:** The file is sent directly to a GCS Bucket as an 'Object'.
    2. **Structured Path:** The file is converted to a binary stream and stored in a MySQL `LONGBLOB` column.
    3. **Comparison:** We measure the total time (latency) for each operation to show why GCS is optimized for files.
    """)

# Sidebar for bucket configuration
st.sidebar.header("Cloud Settings")
bucket_name = st.sidebar.text_input("GCS Bucket Name", "group-c-assets")

# --- 4. EXECUTION LOGIC ---
uploaded_file = st.file_uploader("Upload a file to trigger benchmark", type=['png', 'jpg', 'pdf', 'txt'])

if uploaded_file:
    file_bytes = uploaded_file.getvalue()
    file_name = uploaded_file.name
    file_size_kb = len(file_bytes) / 1024
    
    st.info(f"📂 **File:** {file_name} | **Size:** {file_size_kb:.2f} KB")
    
    # Visual Progress
    progress_bar = st.progress(0)
    status_text = st.empty()

    # --- TEST 1: GOOGLE CLOUD STORAGE ---
    status_text.text("🚀 Uploading to GCS...")
    start_gcs = time.time()
    
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_name)
    blob.upload_from_string(file_bytes)
    
    end_gcs = time.time() - start_gcs
    progress_bar.progress(50)

    # --- TEST 2: CLOUD SQL ---
    status_text.text("💾 Inserting into Cloud SQL...")
    start_sql = time.time()
    
    with pool.connect() as conn:
        # Create table if not exists
        conn.execute(sqlalchemy.text("""
            CREATE TABLE IF NOT EXISTS file_benchmarks 
            (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(255), data LONGBLOB)
        """))
        # Insert file
        conn.execute(
            sqlalchemy.text("INSERT INTO file_benchmarks (name, data) VALUES (:name, :data)"),
            {"name": file_name, "data": file_bytes}
        )
        conn.commit()
        
    end_sql = time.time() - start_sql
    progress_bar.progress(100)
    status_text.text("✅ Benchmark Complete!")

    # --- 5. RESULTS & VISUALS ---
    st.divider()
    col_a, col_b, col_c = st.columns(3)
    
    with col_a:
        st.metric("GCS Latency", f"{end_gcs:.4f}s")
    with col_b:
        st.metric("SQL Latency", f"{end_sql:.4f}s")
    with col_c:
        diff = (end_sql / end_gcs) if end_gcs > 0 else 0
        st.metric("Speed Advantage", f"{diff:.1f}x", delta="GCS is Faster", delta_color="normal")

    # Bar Chart for the Presentation
    chart_data = pd.DataFrame({
        "Service": ["Cloud Storage (GCS)", "Cloud SQL (MySQL)"],
        "Time (Seconds)": [end_gcs, end_sql]
    })
    st.bar_chart(chart_data, x="Service", y="Time (Seconds)")

    # Technical Log Table
    st.subheader("🛠️ Technical Execution Details")
    logs = {
        "Metric": ["Timestamp", "Payload Size", "GCS Operation", "SQL Operation", "Network Overhead"],
        "Value": [time.ctime(), f"{file_size_kb:.2f} KB", "Object.Write", "INSERT BLOB", "High (Auth Proxy)"]
    }
    st.table(pd.DataFrame(logs))