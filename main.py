import os
from google.cloud import storage
from google.cloud.sql.connector import Connector
import sqlalchemy

# 1. SETTINGS - FILL THESE IN
KEY_PATH = "keys.json"
BUCKET_NAME = "group-c-assets"
INSTANCE_CONNECTION = "cloud-storage-vs-sql-groupc:europe-west9:metadata-db" # From Overview page
DB_USER = "app-user"
DB_PASS = ""
DB_NAME = "app_data"

# Authenticate GCS
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = KEY_PATH

def test_cloud_services():
    # --- PART A: GOOGLE CLOUD STORAGE (Unstructured) ---
    print("Testing GCS...")
    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob("test-upload.txt")
    blob.upload_from_string("This is a test file stored in GCS!")
    print(f"Success! File uploaded to {BUCKET_NAME}")

    # --- PART B: GOOGLE CLOUD SQL (Structured) ---
    print("\nTesting Cloud SQL...")
    connector = Connector()
    
    def getconn():
        return connector.connect(
            INSTANCE_CONNECTION, "pymysql", user=DB_USER, password=DB_PASS, db=DB_NAME
        )

    pool = sqlalchemy.create_engine("mysql+pymysql://", creator=getconn)
    
    with pool.connect() as db_conn:
        # Create a simple table
        db_conn.execute(sqlalchemy.text("CREATE TABLE IF NOT EXISTS uploads (id INT AUTO_INCREMENT PRIMARY KEY, filename VARCHAR(255))"))
        # Insert a record
        db_conn.execute(sqlalchemy.text("INSERT INTO uploads (filename) VALUES ('test-upload.txt')"))
        db_conn.commit()
        print("Success! Record inserted into Cloud SQL.")

if __name__ == "__main__":
    test_cloud_services()