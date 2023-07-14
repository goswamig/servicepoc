# Use the official Python base image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file to the working directory
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Clone the GitHub repository
RUN apt-get update && apt-get install -y git
RUN git clone https://github.com/AI-secure/DecodingTrust.git

# Copy the application code to the container
COPY main.py .

# Expose the required port
EXPOSE 8000

# Run the FastAPI application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

