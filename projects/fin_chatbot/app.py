#!/usr/bin/env python
"""
Financial Chatbot - Gradio Web Interface
A professional financial assistant powered by LLM and AKShare data.
"""
import os
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT.parent.parent))

import gradio as gr
from dotenv import load_dotenv
from chatbot import FinancialChatbot

# Load environment variables
env_file = PROJECT_ROOT / 'config.env'
if env_file.exists():
    load_dotenv(env_file)
    print(f"✓ Loaded configuration from: {env_file}")
else:
    print(f"⚠ Config file not found: {env_file}")


def create_interface():
    """Create Gradio interface with interactive Plotly support."""
    chatbot_instance = FinancialChatbot()

    with gr.Blocks(title="💰 Financial Chatbot") as demo:
        mode_text = "🤖 LLM Mode - Chat Enabled" if chatbot_instance.enable_llm else "🚀 Direct Mode"

        gr.HTML(f"""
        <div style="text-align: center; padding: 30px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
             color: white; border-radius: 15px; margin-bottom: 20px;">
            <h1 style="margin: 0; font-size: 2.5em; font-weight: bold;">💰 Financial Chatbot</h1>
            <p style="font-size: 1.2em; margin: 10px 0 0 0;">Your AI-powered stock analysis assistant with interactive charts</p>
            <p style="font-size: 0.9em; margin-top: 5px; opacity: 0.9;">{mode_text} | Powered by AKShare & Plotly</p>
        </div>
        """)

        with gr.Row():
            with gr.Column(scale=1):
                chatbot = gr.Chatbot(
                    height=500,
                    label="💬 Chat History",
                    elem_id="chatbot"
                )

                with gr.Row():
                    msg = gr.Textbox(
                        placeholder="💬 输入您的查询... (例如: 胜宏科技怎么样？或 比较比亚迪和宁德时代)",
                        show_label=False,
                        container=False,
                        scale=9,
                        lines=1
                    )
                    send_btn = gr.Button("发送 📤", scale=1, variant="primary")

                gr.Examples(
                    examples=[
                        "你好，你能做什么？",
                        "胜宏科技最近表现怎么样？",
                        "画一个特斯拉最近一个月的K线图",
                        "比较一下比亚迪和宁德时代",
                        "宁德时代近3个月的走势分析",
                    ],
                    inputs=msg,
                    label="💡 示例查询"
                )

            with gr.Column(scale=1):
                plotly_chart = gr.Plot(
                    label="📈 Interactive Stock Chart",
                    elem_id="plotly-chart"
                )

                gr.Markdown("""
                ### 📊 图表交互说明

                - **🖱️ 拖动** - 框选区域进行缩放
                - **📌 双击** - 重置视图到原始状态
                - **💡 悬停** - 查看每日详细数据
                - **🔍 工具栏** - 右上角有缩放、平移等工具

                #### 💬 聊天功能
                - 支持自然语言对话
                - 智能理解上下文（如"它"、"再看看"）
                - 可以对比多只股票
                - 支持所有A股和美股查询

                #### 📈 图表类型
                - 折线图 (默认)
                - K线图 (说"K线图")
                - 面积图 (说"area")
                - 对比图 (多股票对比)
                """)

        def respond(message, history):
            for new_history, plotly_fig in chatbot_instance.chat(message, history):
                yield "", new_history, plotly_fig

        msg.submit(respond, [msg, chatbot], [msg, chatbot, plotly_chart])
        send_btn.click(respond, [msg, chatbot], [msg, chatbot, plotly_chart])

    return demo


if __name__ == "__main__":
    print("\n" + "="*70)
    print("🚀 Starting Financial Chatbot with AI-Powered Function Calling")
    print("="*70)
    print("\n✨ Features:")
    print("  ✓ AI-powered function calling (智能工具调用)")
    print("  ✓ Context-aware conversation (理解上下文)")
    print("  ✓ Multi-stock comparison (多股票对比)")
    print("  ✓ Interactive Plotly charts (交互式图表)")
    print("  ✓ Real-time stock data from AKShare")
    print("  ✓ Support for all A-shares and US stocks")
    print("  ✓ Intelligent trend analysis (智能趋势分析)")
    print("\n💬 Chat Examples:")
    print("  • 胜宏科技最近表现怎么样？")
    print("  • 再看看它的K线图 (上下文理解)")
    print("  • 比较一下比亚迪和宁德时代")
    print("\n📊 Stock Query Examples:")
    print("  • 画一个特斯拉的K线图")
    print("  • 宁德时代股价")
    print("  • 对比腾讯、阿里和美团")
    print("\n" + "="*70)
    print("\n🌐 Server starting at: http://0.0.0.0:7860")
    print("Press Ctrl+C to stop the server\n")

    demo = create_interface()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )
