#!/usr/bin/env python3
"""
Simple Financial Chatbot Launcher
Run this script to start the simplified financial chatbot.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from ms_agent.app.fin_chatbot import launch_chatbot

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Starting Financial Chatbot...")
    print("=" * 60)
    print("\nFeatures:")
    print("  ✓ Stock price history queries")
    print("  ✓ Interactive price charts (line, candlestick, area)")
    print("  ✓ Company information and statistics")
    print("  ✓ Support for US stocks and Chinese A-shares")
    print("\n" + "=" * 60)
    print("\nServer will start at: http://0.0.0.0:7860")
    print("Press Ctrl+C to stop the server\n")

    launch_chatbot(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )
