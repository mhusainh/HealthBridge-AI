# Gunakan Python 3.11 sebagai base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy seluruh project ke container
COPY . .

# Expose ports
# 8501 untuk Streamlit
EXPOSE 8501

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV BACKEND_HOST=localhost

# Start backend in background then frontend
CMD python AI/main.py & sleep 3 && streamlit run AI/app.py --server.address 0.0.0.0 --server.port 8501
