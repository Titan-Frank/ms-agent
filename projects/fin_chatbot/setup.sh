#!/bin/bash
# Financial Chatbot Setup Script

echo "=================================================="
echo "  Financial Chatbot - Setup"
echo "=================================================="
echo ""

# Check Python version
echo "1. Checking Python version..."
python3 --version

# Install dependencies
echo ""
echo "2. Installing dependencies..."
pip install akshare plotly kaleido pandas python-dotenv gradio

# Create config file if not exists
echo ""
echo "3. Setting up configuration..."
if [ ! -f "config.env" ]; then
    echo "   Creating config.env from template..."
    cp config.env.example config.env
    echo "   ⚠️  Please edit config.env and fill in your API key"
else
    echo "   ✓ config.env already exists"
fi

echo ""
echo "=================================================="
echo "  Setup Complete!"
echo "=================================================="
echo ""
echo "Next steps:"
echo "  1. Edit config.env and add your API key"
echo "  2. Run: python fin_chatbot.py"
echo ""
