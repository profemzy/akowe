#!/bin/bash

# Setup virtual environment if not already done
if [ ! -d "venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Initialize the database if not already done
if [ ! -f "instance/akowe.db" ]; then
  echo "Setting up database..."
  python setup.py
fi

# Run the application
echo "Starting Akowe Financial Tracker..."
flask run --host=0.0.0.0