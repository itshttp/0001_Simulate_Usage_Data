#!/bin/bash
# Launcher for Account Usage Analytics Dashboard

echo "🚀 Starting Account Usage Analytics Dashboard..."
echo ""

# Activate virtual environment and run dashboard
./venv/bin/streamlit run account_usage_dashboard.py --server.headless=true

echo ""
echo "Dashboard stopped."
