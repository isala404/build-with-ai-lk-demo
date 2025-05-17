# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install pip and pip-tools
RUN pip install --upgrade pip

# Copy project files
COPY . .

# Install dependencies
RUN pip install .

# Expose the port FastAPI will run on
EXPOSE 8080

# Command to run the app with uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]