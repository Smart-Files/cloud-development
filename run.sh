#!/bin/bash

echo "Entering Directory"
cd /app

echo "Listing contents"
ls -la

echo "Running the application"
uvicorn main:app --host 0.0.0.0 --port 8080