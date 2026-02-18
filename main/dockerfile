FROM python:3.9-slim

WORKDIR /app

# Copy all files (including the requirements.txt)
COPY . .

# Install libraries
RUN pip install --no-cache-dir -r requirements.txt

# Streamlit-specific config
EXPOSE 8080

# Run the app on the port Cloud Run expects ($PORT)
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"]

