#!/bin/bash
# Start the Streamlit Dashboard

echo "🚀 Starting Phone Usage Analytics Dashboard..."
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "Please create .env file with your Snowflake credentials."
    echo "You can copy .env.example and fill in your details:"
    echo ""
    echo "  cp .env.example .env"
    echo ""
    exit 1
fi

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
fi

# Check if streamlit is installed
if ! command -v streamlit &> /dev/null; then
    echo "📥 Installing Streamlit..."
    pip install streamlit plotly
fi

# Start the dashboard
echo "✅ Starting dashboard..."
echo ""
echo "Dashboard will open in your browser at: http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop the dashboard"
echo ""

streamlit run streamlit_app.py
