# Use a lightweight Python image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app.py .
COPY translation_mappings.json .
COPY templates/ templates/
COPY static/ static/

# Expose the Flask port (optional for HF Spaces)
EXPOSE 5000

# Start the Flask app
CMD ["python", "app.py"]
