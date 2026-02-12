# 🛠️ Project Setup Guide: GCS vs. Cloud SQL
This guide will help you set up your Google Cloud environment from scratch to run the benchmarking prototype.

---

## ☁️ Phase 1: Google Cloud Console Setup
1.  **Create a Project**: 
    * Go to [Google Cloud Console](https://console.cloud.google.com/).
    * Click the project dropdown (top left) > **New Project**.
    * Name it something like `cloud-benchmark-group-c`.
2.  **Enable Billing**: Ensure your free trial or student credits are active under the **Billing** tab.
3.  **Enable APIs**: Search for and **Enable** these three:
    * ✅ `Cloud Storage API`
    * ✅ `Cloud SQL Admin API`
    * ✅ `IAM Service Account Credentials API`

---

## 🗄️ Phase 2: Create Storage & Database
### 1. Google Cloud Storage (GCS) 📦
* Go to **Cloud Storage > Buckets**.
* Click **Create**.
* **Name**: Must be unique (e.g., `assets-yourname-123`).
* **Location**: Choose `europe-west9` (Paris) or your preferred region.
* Keep other settings as **Standard**.

### 2. Cloud SQL (MySQL) 🛢️
* Go to **SQL > Create Instance**.
* Choose **MySQL**.
* **Instance ID**: `metadata-db`.
* **Password**: *Set a password and SAVE IT!*
* **Edition**: Choose **Enterprise (Sandbox/Lightweight)** to save credits.
* **Connections**: Ensure **Public IP** is checked for this prototype.

---

## 🔑 Phase 3: Security & Keys (Crucial!)
To allow the Python app to talk to Google, you need a "Service Account."

1.  **Create Service Account**:
    * Go to **IAM & Admin > Service Accounts**.
    * Click **Create Service Account**. Name it `app-runner`.
2.  **Assign Roles**: Add these 3 specific roles:
    * 👤 `Storage Object Admin` (To upload files)
    * 👤 `Cloud SQL Client` (To connect to DB)
    * 👤 `Cloud SQL Editor` (To create tables/insert data)
3.  **Generate JSON Key**:
    * Click on your new service account > **Keys** tab.
    * **Add Key > Create New Key > JSON**.
    * A file will download. **Rename it to `keys.json`** and move it into your project folder.

---

## 💻 Phase 4: Local Environment Setup
1. **Clone the Repo**: 
   ```bash
   git clone <your-repo-link>
   cd <repo-folder>

## Install Dependencies:

pip install streamlit google-cloud-storage google-cloud-sql-connector sqlalchemy pymysql pandas

## Configure app.py:

    Open app.py.

    Update INSTANCE_CONNECTION with your Connection Name (found on the SQL Overview page).

    Update DB_PASS and BUCKET_NAME.

## Run the App:

    streamlit run app.py