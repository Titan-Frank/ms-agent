#!/usr/bin/env python3
"""
Financial Chatbot Launcher
An intelligent chatbot for stock queries powered by LLM and AKShare.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import chatbot from ms_agent.app
from ms_agent.app.fin_chatbot import launch_chatbot

if __name__ == "__main__":
    print("=" * 60)
    print("💰 Starting Financial Chatbot...")
    print("=" * 60)
    print("\nFeatures:")
    print("  ✓ Natural language understanding (中英文)")
    print("  ✓ Stock price queries (股票查询)")
    print("  ✓ Interactive charts (交互式图表)")
    print("  ✓ AI-powered analysis (智能分析)")
    print("  ✓ Multi-market support (US & A-shares)")
    print("\n" + "=" * 60)
    print("\nServer will start at: http://0.0.0.0:7860")
    print("Press Ctrl+C to stop the server\n")

    # Load config from project directory
    config_file = Path(__file__).parent / 'config.env'
    if config_file.exists():
        from dotenv import load_dotenv
        load_dotenv(config_file)
        print(f"✓ Loaded configuration from: {config_file}\n")

    launch_chatbot(
        server_name=os.getenv('SERVER_HOST', '0.0.0.0'),
        server_port=int(os.getenv('SERVER_PORT', 7860)),
        share=os.getenv('SHARE', 'false').lower() == 'true'
    )
