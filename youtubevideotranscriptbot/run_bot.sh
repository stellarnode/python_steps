#!/bin/bash

# Define the image tag and container name
IMAGE_TAG="youtubevideotranscriptbot"
CONTAINER_NAME="youtubevideotranscriptbot-container"

# Check if a container with the name exists
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
  echo "Stopping and removing existing container: ${CONTAINER_NAME}"
  docker stop ${CONTAINER_NAME} > /dev/null  # Stop the container
  docker rm ${CONTAINER_NAME} > /dev/null    # Remove the container
fi

# Build the Docker image
echo "Building the Docker image..."
docker build -t ${IMAGE_TAG} .

# Run the container with the volume and auto-restart
echo "Starting the container..."
docker run -d --name ${CONTAINER_NAME} \
  -v $(pwd)/transcripts:/app/transcripts \
  --restart unless-stopped \
  ${IMAGE_TAG}

echo "Container started successfully!"