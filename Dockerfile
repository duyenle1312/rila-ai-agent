# Use official Python image as base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements file if you have one (optional)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the app folder into the container
COPY ./app /app/app

# Expose port
EXPOSE 8000

# Command to run the app with Uvicorn
CMD ["uvicorn", "app.app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
