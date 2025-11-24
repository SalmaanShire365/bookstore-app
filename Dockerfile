# Use an official Python runtime as a parent image
FROM python:3.8

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Render uses port 10000 by default, but we'll use the PORT env variable
EXPOSE 10000

# Define environment variable for Flask to run in production mode
ENV FLASK_ENV=production

# Use gunicorn instead of Flask dev server for production
CMD gunicorn --bind 0.0.0.0:$PORT app:app
