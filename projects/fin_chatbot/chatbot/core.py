"""
Core FinancialChatbot class with LLM integration.
"""
import os
import json
from typing import List, Optional, Tuple

from .prompts import (
    FUNCTION_CALLING_SYSTEM_PROMPT,
    ANALYSIS_SYSTEM_PROMPT,
    GENERAL_CHAT_SYSTEM_PROMPT
)
from .tools_handler import TOOL_SCHEMAS, TOOL_FUNCTIONS


class FinancialChatbot:
    """Professional financial chatbot with LLM-powered function calling."""

    def __init__(self):
        """Initialize chatbot with LLM and tools."""
        self.enable_llm = os.getenv('ENABLE_LLM', 'true').lower() in ('true', '1', 'yes')

        if self.enable_llm:
            try:
                from ms_agent.llm.llm import LLM
                from omegaconf import DictConfig

                llm_provider = os.getenv('LLM_PROVIDER', 'dashscope').lower()

                if llm_provider == 'dashscope':
                    llm_config = {
                        'service': 'dashscope',
                        'model': os.getenv('DASHSCOPE_MODEL', 'qwen-max'),
                        'dashscope_api_key': os.getenv('DASHSCOPE_API_KEY'),
                        'modelscope_base_url': None,
                    }
                else:
                    llm_config = {
                        'service': 'openai',
                        'model': os.getenv('OPENAI_MODEL', 'gpt-4'),
                        'openai_api_key': os.getenv('OPENAI_API_KEY'),
                        'openai_base_url': os.getenv('OPENAI_API_BASE', 'https://api.openai.com/v1'),
                    }

                config = DictConfig({'llm': llm_config})
                self.llm = LLM.from_config(config)
                print("✓ LLM initialized successfully with Function Calling")
                print(f"→ Using {llm_provider} - {llm_config['model']}")
            except Exception as e:
                print(f"⚠ LLM initialization failed: {e}")
                self.llm = None
        else:
            self.llm = None
            print("ℹ️ LLM mode disabled")

        self.tools = TOOL_SCHEMAS

    def chat(self, message: str, history: List):
        """
        Process chat message (non-streaming for stability).

        Yields:
            Tuple of (updated_history, plotly_figure)
        """
        if not message.strip():
            yield history, None
            return

        try:
            # Add user message
            history.append({"role": "user", "content": message})

            # Process query (non-streaming)
            text_response, plotly_fig = self._process_query(message, history[:-1])

            # Add assistant response
            history.append({"role": "assistant", "content": text_response})

            # Single yield with complete response
            yield history, plotly_fig

        except Exception as e:
            import traceback
            traceback.print_exc()
            error_msg = f"❌ Error: {str(e)}"
            history.append({"role": "assistant", "content": error_msg})
            yield history, None

    def _process_query(self, message: str, history: List = None) -> Tuple[str, Optional[object]]:
        """Process query using LLM with function calling and conversation context."""
        if not self.llm:
            return self._fallback_response(), None

        try:
            from ms_agent.llm.utils import Message

            # Build messages with conversation history
            messages = [Message(role='system', content=FUNCTION_CALLING_SYSTEM_PROMPT)]

            # Add conversation history for context (last 10 messages)
            if history:
                for msg in history[-10:]:
                    messages.append(Message(
                        role=msg['role'],
                        content=msg['content']
                    ))

            # Add current message
            messages.append(Message(role='user', content=message))

            # Call LLM with tools
            response = self.llm.generate(messages=messages, tools=self.tools)

            # Check if LLM wants to call functions
            if hasattr(response, 'tool_calls') and response.tool_calls:
                return self._handle_tool_calls(response, message, history)
            else:
                # No tool call, just return text response
                text = response.content if hasattr(response, 'content') else str(response)
                return text, None

        except Exception as e:
            print(f"Function calling error: {e}")
            import traceback
            traceback.print_exc()
            return self._fallback_response(), None

    def _handle_tool_calls(self, response, original_message: str, history: List = None) -> Tuple[str, Optional[object]]:
        """Execute tool calls and generate final response with chart."""
        from ms_agent.llm.utils import Message

        tool_results = []
        chart_data = None
        stock_data_summary = None  # 用于强制嵌入数据

        # Execute each tool call
        for tool_call in response.tool_calls:
            # ms_agent format: tool_call is a dict with 'tool_name' and 'arguments'
            func_name = tool_call['tool_name']
            func_args = json.loads(tool_call['arguments'])

            print(f"🔧 Tool call: {func_name}({func_args})")

            # Get the tool function
            tool_func = TOOL_FUNCTIONS.get(func_name)
            if not tool_func:
                print(f"⚠️ Unknown tool: {func_name}")
                continue

            # Execute the tool
            if func_name == "search_stock":
                result = tool_func(func_args.get('query', ''))
                tool_results.append({
                    "tool_call_id": tool_call['id'],
                    "role": "tool",
                    "name": func_name,
                    "content": result
                })
                print(f"📊 search_stock result: {result[:100]}...")

            elif func_name == "get_stock_data":
                symbol = func_args.get('symbol', '')
                period = func_args.get('period', '1mo')
                chart_type = func_args.get('chart_type', 'line')

                result, fig = tool_func(symbol, period, chart_type)
                tool_results.append({
                    "tool_call_id": tool_call['id'],
                    "role": "tool",
                    "name": func_name,
                    "content": result
                })
                chart_data = fig

                # 解析数据用于强制嵌入
                try:
                    stock_data_summary = json.loads(result)
                    print(f"📊 get_stock_data result:")
                    print(f"   {result}")
                except:
                    pass

            elif func_name == "compare_stocks":
                symbols = func_args.get('symbols', [])
                period = func_args.get('period', '1mo')

                result, fig = tool_func(symbols, period)
                tool_results.append({
                    "tool_call_id": tool_call['id'],
                    "role": "tool",
                    "name": func_name,
                    "content": result
                })
                chart_data = fig

        # 🔥 关键修复：在 user message 中强制嵌入真实数据
        enhanced_message = original_message
        if stock_data_summary:
            enhanced_message = f"""{original_message}

【系统提供的真实股票数据 - 必须严格使用以下数据】
股票代码: {stock_data_summary.get('symbol', 'N/A')}
当前价格: ¥{stock_data_summary.get('current_price', 0):.2f}
涨跌金额: {stock_data_summary.get('change', 0):+.2f}元
涨跌幅度: {stock_data_summary.get('change_percent', 0):+.2f}%
期间最高: ¥{stock_data_summary.get('high', 0):.2f}
期间最低: ¥{stock_data_summary.get('low', 0):.2f}
平均成交量: {stock_data_summary.get('avg_volume', 0):,}手

⚠️ 警告：以上数字来自真实数据源，禁止修改或编造！必须原样使用！
"""

        # Build second LLM call with tool results
        messages = [Message(role='system', content=ANALYSIS_SYSTEM_PROMPT)]

        # Add conversation history for context
        if history:
            for msg in history[-8:]:
                messages.append(Message(role=msg['role'], content=msg['content']))

        # 使用强化后的 message
        messages.append(Message(role='user', content=enhanced_message))
        messages.append(Message(role='assistant', content=response.content, tool_calls=response.tool_calls))

        # Add tool results
        for tool_result in tool_results:
            messages.append(Message(
                role='tool',
                content=tool_result['content'],
                tool_call_id=tool_result['tool_call_id']
            ))
            # 🔍 调试：打印传递给 LLM 的 tool message
            print(f"🔧 Adding tool result to LLM context:")
            print(f"   role: tool")
            print(f"   name: {tool_result['name']}")
            print(f"   content: {tool_result['content'][:150]}...")

        # 🔍 调试：打印最终发送给 LLM 的 messages
        print(f"\n📤 Sending to LLM (second call):")
        print(f"   Total messages: {len(messages)}")
        for i, msg in enumerate(messages):
            print(f"   [{i}] role={msg.role}, content_length={len(str(msg.content))}")

        # Get final response from LLM
        final_response = self.llm.generate(messages=messages)
        final_text = final_response.content if hasattr(final_response, 'content') else str(final_response)

        print(f"\n💬 LLM final response preview:")
        print(f"   {final_text[:200]}...")

        return final_text, chart_data

    def _fallback_response(self) -> str:
        """Fallback response when LLM is not available."""
        return """📊 **欢迎使用金融聊天机器人！**

我可以帮您查询股票信息并生成交互式图表。

**示例查询:**
- "胜宏科技最近一个月的走势分析"
- "画一个特斯拉的K线图"
- "比较一下比亚迪和宁德时代"

**支持的股票:**
- 🇺🇸 美股: AAPL, TSLA, MSFT, NVDA
- 🇨🇳 A股: 任何中文股票名称或代码

**图表交互提示:**
- 🖱️ 鼠标拖动可缩放
- 📌 双击重置视图
- 💡 悬停查看详细数据

⚠️ LLM 功能未启用，请配置 API 密钥以获得完整功能。
"""
