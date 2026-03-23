# Use an official Python runtime as a parent image (slim variants are smaller)
FROM python:3.12-slim

# Set the working directory to /app inside the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt ./

# Install any needed Python packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application source code into the container
COPY . .

# Define the command to run the application when the container starts
CMD ["python", "main.py"]

