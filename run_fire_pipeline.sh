#!/bin/bash

# Fire Incident Pipeline Runner
# This script runs the complete fire incident monitoring pipeline

echo "🔥 Fire Incident Pipeline Runner"
echo "=================================="

# Check if we're in the right directory
if [ ! -f "src/fire_incident_pipeline.py" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    echo "   Current directory: $(pwd)"
    echo "   Expected files: src/fire_incident_pipeline.py"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "src/venv" ]; then
    echo "📦 Creating virtual environment..."
    cd src
    python3 -m venv venv
    cd ..
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source src/venv/bin/activate

# Install/update requirements
echo "📥 Installing/updating requirements..."
pip install -r src/requirements.txt

# Check for OpenAI API key
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  Warning: OPENAI_API_KEY not set in environment"
    echo "   You can set it with: export OPENAI_API_KEY='your-key-here'"
    echo "   Or create a .env file in the src/ directory"
fi

# Run the pipeline
echo "🚀 Starting Fire Incident Pipeline..."
cd src
python fire_incident_pipeline.py

# Deactivate virtual environment
deactivate

echo "🏁 Pipeline execution completed!" 