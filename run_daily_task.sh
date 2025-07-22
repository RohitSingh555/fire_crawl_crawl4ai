#!/bin/bash

# Fire Incident Daily Task Runner
# Simple script to run the complete fire incident pipeline

echo "🔥 Fire Incident Daily Task Runner"
echo "=================================="
echo "Starting at: $(date)"
echo ""

# Navigate to src directory
cd /root/fire_crawl_crawl4ai/src

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Run the main pipeline
echo "🚀 Running Fire Incident Pipeline..."
python fire_incident_pipeline.py

# Deactivate virtual environment
deactivate

echo ""
echo "🏁 Pipeline execution completed at: $(date)"
