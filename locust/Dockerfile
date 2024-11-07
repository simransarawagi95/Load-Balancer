# # # Start from the official Locust image
# # FROM locustio/locust:latest

# # # Switch to root user to install packages
# # USER root

# # # Install necessary utilities
# # RUN apt-get update && apt-get install -y curl dnsutils && rm -rf /var/lib/apt/lists/*

# # # Switch back to the locust user
# # USER locust

# # # Set the working directory
# # WORKDIR /mnt/locust

# # # Copy the locustfile and any additional requirements file into the image
# # COPY locustfile.py /mnt/locust/
# # COPY requirements.txt /mnt/locust/

# # # Install any required dependencies
# # RUN pip install -r requirements.txt

# # # Set locust as the entrypoint so we can pass custom args in the deployment
# # ENTRYPOINT ["locust"]


# # # locust/Dockerfile
# # # FROM locustio/locust
# # # USER root

# # # RUN apt-get update && apt-get install -y curl dnsutils && rm -rf /var/lib/apt/lists/*
# # # USER locust

# # # WORKDIR /locust

# # # COPY locustfile.py .
# # # COPY requirements.txt .

# # # RUN pip install -r requirements.txt

# # # CMD ["locust", "-f", "locustfile.py", "--host", "http://node-app-primary-service"]


# # Use an official Python image
# FROM python:3.13-slim

# # Set the working directory
# WORKDIR /locust

# # Copy locust file and requirements
# COPY locustfile.py ./
# COPY requirements.txt ./

# # Install dependencies
# RUN pip install -r requirements.txt

# # Expose Locust ports
# EXPOSE 8089 5557 5558

# # Command to start Locust
# CMD ["locust", "-f", "locustfile.py"]

# Use the Python slim image
FROM python:3.13-slim

# Set the working directory
WORKDIR /locust

# Copy requirements
COPY requirements.txt .

# Install necessary build tools
RUN apt-get update && \
    apt-get install -y curl && \
    apt-get install -y gcc build-essential && \
    rm -rf /var/lib/apt/lists/*

# Install dependencies
RUN pip install -r requirements.txt

# Copy the locustfile.py
COPY locustfile.py .

# Expose Locust ports
EXPOSE 8089 5557

ENTRYPOINT ["locust"]

# Set the command to run Locust
CMD ["locust", "-f", "locustfile.py"]
