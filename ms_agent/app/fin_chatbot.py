"""
Simplified Financial Chatbot
A lightweight chatbot for basic financial queries like stock price history and charts.
"""

import os
import json
import re
import tempfile
from datetime import datetime, timedelta
from typing import Optional, List, Tuple, Dict
from pathlib import Path
import gradio as gr

# Try to load .env file if it exists
try:
    from dotenv import load_dotenv
    # Look for config.env in the project directory
    config_file = Path(__file__).parent.parent.parent / 'projects' / 'fin_research' / 'config.env'
    if config_file.exists():
        load_dotenv(config_file)
        print(f"✓ Loaded configuration from: {config_file}")
except ImportError:
    pass  # python-dotenv not installed, will use system env vars

# Initialize akshare
try:
    import akshare as ak
    print("✓ AKShare loaded successfully")
except ImportError:
    print("⚠ AKShare not installed. Please run: pip install akshare")
    ak = None


# ============================================================================
# Stock Symbol Mapping (Chinese to English)
# ============================================================================

STOCK_NAME_MAPPING = {
    # US Stocks - Chinese names
    '特斯拉': 'TSLA',
    '苹果': 'AAPL',
    '微软': 'MSFT',
    '英伟达': 'NVDA',
    '谷歌': 'GOOGL',
    '亚马逊': 'AMZN',
    '脸书': 'META',
    'Meta': 'META',
    '奈飞': 'NFLX',

    # A-share stocks - Chinese names to codes
    '宁德时代': '300750',
    '贵州茅台': '600519',
    '比亚迪': '002594',
    '中国平安': '601318',
    '招商银行': '600036',
    '工商银行': '601398',
    '建设银行': '601939',
    '农业银行': '601288',
    '中国银行': '601988',
    '五粮液': '000858',
}


# ============================================================================
# Stock Query Tools
# ============================================================================

def parse_stock_symbol(message: str) -> Optional[str]:
    """
    Parse stock symbol from user message.
    Supports:
    - US stocks: AAPL, TSLA, etc.
    - A-shares: 300750.SZ, 000001.SZ, 600519.SS
    - Chinese stock names: 特斯拉, 宁德时代
    - 6-digit A-share codes: 300750, 000001, 600519

    Returns:
        Stock symbol or None
    """
    # First check for Chinese stock names
    for cn_name, symbol in STOCK_NAME_MAPPING.items():
        if cn_name in message:
            # Determine if it's a US stock or A-share
            if symbol.isalpha():
                return symbol  # US stock
            else:
                # A-share: determine exchange
                return normalize_a_share_code(symbol)

    # Check for symbols with exchange suffix (.SZ, .SS)
    pattern_with_suffix = r'\b(\d{6}\.(SZ|SS|sz|ss))\b'
    matches = re.findall(pattern_with_suffix, message.upper())
    if matches:
        return matches[0][0].upper()

    # Check for 6-digit A-share codes (without suffix)
    pattern_a_share = r'\b([036]\d{5})\b'
    matches = re.findall(pattern_a_share, message)
    if matches:
        code = matches[0]
        return normalize_a_share_code(code)

    # Check for US stock symbols (uppercase letters)
    pattern_us = r'\b([A-Z]{1,5})\b'
    matches = re.findall(pattern_us, message.upper())
    if matches:
        return matches[0]

    return None


def normalize_a_share_code(code: str) -> str:
    """
    Normalize A-share code with proper exchange suffix.

    Args:
        code: 6-digit code or code with suffix

    Returns:
        Code with proper suffix (.SZ or .SS)
    """
    # Remove existing suffix
    code = code.upper().replace('.SZ', '').replace('.SS', '')

    # Determine exchange based on first digit
    if code.startswith('6'):
        return f"{code}.SS"  # Shanghai
    else:
        return f"{code}.SZ"  # Shenzhen (000xxx, 002xxx, 300xxx)


def get_stock_price_history(
    symbol: str,
    period: str = "1mo",
    interval: str = "1d"
) -> str:
    """
    Get stock price history data using AKShare.

    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL', 'TSLA', '300750.SZ' for A-shares)
        period: Time period - 1d, 5d, 1mo, 3mo, 6mo, 1y
        interval: Data interval (daily only for now)

    Returns:
        str: JSON string of stock data including prices, volumes, and metadata
    """
    if ak is None:
        return json.dumps({
            "error": "AKShare not installed. Please run: pip install akshare",
            "symbol": symbol
        })

    try:
        # Convert period to days
        period_days_map = {
            "1d": 1,
            "5d": 5,
            "1mo": 30,
            "3mo": 90,
            "6mo": 180,
            "1y": 365,
        }
        days = period_days_map.get(period, 30)

        # Calculate date range
        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")

        # Fetch data based on market
        if symbol.endswith('.SZ') or symbol.endswith('.SS'):
            # A-share market
            clean_symbol = symbol.replace('.SZ', '').replace('.SS', '')
            df = ak.stock_zh_a_hist(symbol=clean_symbol, period='daily',
                                   start_date=start_date, end_date=end_date, adjust="")
        else:
            # US market
            df = ak.stock_us_hist(symbol=symbol, period='daily',
                                 start_date=start_date, end_date=end_date, adjust="")

        if df.empty:
            return json.dumps({
                "error": f"No data found for symbol: {symbol}",
                "symbol": symbol
            })

        # Standardize column names
        column_map = {
            '日期': 'date',
            '开盘': 'open',
            '收盘': 'close',
            '最高': 'high',
            '最低': 'low',
            '成交量': 'volume',
            '成交额': 'amount',
        }
        df = df.rename(columns=column_map)

        # Convert to JSON-serializable format
        data = {
            "symbol": symbol,
            "period": period,
            "interval": interval,
            "data": []
        }

        for _, row in df.iterrows():
            data["data"].append({
                "date": str(row.get("date", "")),
                "open": float(row.get("open", 0)),
                "high": float(row.get("high", 0)),
                "low": float(row.get("low", 0)),
                "close": float(row.get("close", 0)),
                "volume": int(row.get("volume", 0))
            })

        # Add summary statistics
        if len(df) > 0:
            data["summary"] = {
                "current_price": float(df["close"].iloc[-1]),
                "prev_close": float(df["close"].iloc[-2]) if len(df) > 1 else None,
                "change": float(df["close"].iloc[-1] - df["close"].iloc[-2]) if len(df) > 1 else None,
                "change_percent": float((df["close"].iloc[-1] / df["close"].iloc[-2] - 1) * 100) if len(df) > 1 else None,
                "high": float(df["high"].max()),
                "low": float(df["low"].min()),
                "avg_volume": int(df["volume"].mean())
            }

        return json.dumps(data, indent=2, ensure_ascii=False)

    except Exception as e:
        return json.dumps({
            "error": f"Error fetching data: {str(e)}",
            "symbol": symbol
        }, ensure_ascii=False)


def plot_stock_chart(
    symbol: str,
    period: str = "1mo",
    chart_type: str = "line"
) -> str:
    """
    Generate a professional stock price chart using Plotly.

    Args:
        symbol: Stock ticker symbol
        period: Time period for the chart
        chart_type: Type of chart - 'line', 'candlestick', or 'area'

    Returns:
        str: Path to the generated chart image, or error message
    """
    if ak is None:
        return "Error: AKShare not installed. Please run: pip install akshare"

    try:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
        import pandas as pd

        # Convert period to days
        period_days_map = {
            "1d": 1,
            "5d": 5,
            "1mo": 30,
            "3mo": 90,
            "6mo": 180,
            "1y": 365,
        }
        days = period_days_map.get(period, 30)

        # Calculate date range
        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")

        # Fetch data based on market
        if symbol.endswith('.SZ') or symbol.endswith('.SS'):
            # A-share market
            clean_symbol = symbol.replace('.SZ', '').replace('.SS', '')
            df = ak.stock_zh_a_hist(symbol=clean_symbol, period='daily',
                                   start_date=start_date, end_date=end_date, adjust="")
        else:
            # US market
            df = ak.stock_us_hist(symbol=symbol, period='daily',
                                 start_date=start_date, end_date=end_date, adjust="")

        if df.empty:
            return f"Error: No data found for symbol {symbol}"

        # Standardize column names
        column_map = {
            '日期': 'Date',
            '开盘': 'Open',
            '收盘': 'Close',
            '最高': 'High',
            '最低': 'Low',
            '成交量': 'Volume',
            '成交额': 'Amount',
            '涨跌幅': 'Change',
        }
        df = df.rename(columns=column_map)
        df['Date'] = pd.to_datetime(df['Date'])

        # Calculate price change
        current_price = df['Close'].iloc[-1]
        prev_price = df['Close'].iloc[0]
        price_change = current_price - prev_price
        price_change_pct = (price_change / prev_price) * 100

        # Determine color based on change
        if price_change >= 0:
            line_color = '#00C805'  # Green
            fill_color = 'rgba(0, 200, 5, 0.1)'
        else:
            line_color = '#FF5252'  # Red
            fill_color = 'rgba(255, 82, 82, 0.1)'

        # Create figure with secondary y-axis for volume
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=[0.7, 0.3],
            subplot_titles=None
        )

        # Add price chart
        if chart_type == 'candlestick':
            # Candlestick chart
            fig.add_trace(
                go.Candlestick(
                    x=df['Date'],
                    open=df['Open'],
                    high=df['High'],
                    low=df['Low'],
                    close=df['Close'],
                    name='K线',
                    increasing_line_color='#00C805',
                    decreasing_line_color='#FF5252',
                ),
                row=1, col=1
            )
        else:
            # Line/Area chart
            fig.add_trace(
                go.Scatter(
                    x=df['Date'],
                    y=df['Close'],
                    mode='lines',
                    name='收盘价',
                    line=dict(color=line_color, width=2),
                    fill='tozeroy' if chart_type == 'area' else None,
                    fillcolor=fill_color,
                    hovertemplate='<b>%{x|%Y-%m-%d}</b><br>' +
                                  '收盘: ¥%{y:.2f}<br>' +
                                  '<extra></extra>'
                ),
                row=1, col=1
            )

        # Add volume bars
        colors = ['#00C805' if df['Close'].iloc[i] >= df['Open'].iloc[i] else '#FF5252'
                  for i in range(len(df))]
        fig.add_trace(
            go.Bar(
                x=df['Date'],
                y=df['Volume'],
                name='成交量',
                marker_color=colors,
                opacity=0.7,
                hovertemplate='<b>%{x|%Y-%m-%d}</b><br>' +
                              '成交量: %{y:,.0f}<br>' +
                              '<extra></extra>'
            ),
            row=2, col=1
        )

        # Format change display
        change_sign = "+" if price_change >= 0 else ""
        change_arrow = "↗" if price_change >= 0 else "↘"

        # Update layout with dark theme
        fig.update_layout(
            title=dict(
                text=f'<b>{symbol}</b><br>' +
                     f'<span style="font-size:24px">¥{current_price:.2f}</span> ' +
                     f'<span style="color:{line_color}">{change_sign}{price_change:.2f} {change_arrow} {change_sign}{price_change_pct:.2f}%</span>',
                x=0.02,
                y=0.98,
                font=dict(size=16)
            ),
            template='plotly_dark',
            paper_bgcolor='#0D1117',
            plot_bgcolor='#0D1117',
            font=dict(family='Arial', color='#C9D1D9'),
            showlegend=False,
            height=600,
            width=900,
            margin=dict(l=60, r=40, t=100, b=40),
            xaxis_rangeslider_visible=False,
            hovermode='x unified'
        )

        # Update axes
        fig.update_xaxes(
            gridcolor='#21262D',
            showgrid=True,
            zeroline=False,
            showline=True,
            linecolor='#30363D',
            tickformat='%m/%d',
            row=1, col=1
        )
        fig.update_xaxes(
            gridcolor='#21262D',
            showgrid=True,
            zeroline=False,
            showline=True,
            linecolor='#30363D',
            tickformat='%m/%d',
            row=2, col=1
        )
        fig.update_yaxes(
            gridcolor='#21262D',
            showgrid=True,
            zeroline=False,
            showline=True,
            linecolor='#30363D',
            tickprefix='¥',
            row=1, col=1
        )
        fig.update_yaxes(
            gridcolor='#21262D',
            showgrid=True,
            zeroline=False,
            showline=True,
            linecolor='#30363D',
            title='成交量',
            row=2, col=1
        )

        # Save to temp file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
        fig.write_image(temp_file.name, scale=2)

        return temp_file.name

    except ImportError as e:
        return f"Error: Missing library - {e}. Please install: pip install plotly kaleido akshare pandas"
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"Error generating chart: {str(e)}"


def get_stock_info(symbol: str) -> str:
    """
    Get basic stock information.

    Args:
        symbol: Stock ticker symbol

    Returns:
        str: JSON string of stock information
    """
    if ak is None:
        return json.dumps({
            "error": "AKShare not installed. Please run: pip install akshare",
            "symbol": symbol
        })

    try:
        data = {"symbol": symbol}

        # A-share market
        if symbol.endswith('.SZ') or symbol.endswith('.SS'):
            clean_symbol = symbol.replace('.SZ', '').replace('.SS', '')

            # Get basic info
            try:
                df_info = ak.stock_individual_info_em(symbol=clean_symbol)
                if not df_info.empty:
                    info_dict = dict(zip(df_info['item'], df_info['value']))
                    data["name"] = info_dict.get("股票简称", "N/A")
                    data["industry"] = info_dict.get("行业", "N/A")
                    data["listing_date"] = info_dict.get("上市时间", "N/A")
                    data["total_shares"] = info_dict.get("总股本", "N/A")
                    data["market_value"] = info_dict.get("总市值", "N/A")
            except:
                pass

            # Get realtime data
            try:
                df_spot = ak.stock_zh_a_spot_em()
                stock_data = df_spot[df_spot['代码'] == clean_symbol]
                if not stock_data.empty:
                    row = stock_data.iloc[0]
                    data["current_price"] = row.get("最新价", "N/A")
                    data["change_percent"] = row.get("涨跌幅", "N/A")
                    data["pe_ratio"] = row.get("市盈率-动态", "N/A")
                    data["market_cap"] = row.get("总市值", "N/A")
            except:
                pass

        # US market
        else:
            try:
                df_spot = ak.stock_us_spot_em()
                stock_data = df_spot[df_spot['代码'] == symbol.upper()]
                if not stock_data.empty:
                    row = stock_data.iloc[0]
                    data["name"] = row.get("名称", "N/A")
                    data["current_price"] = row.get("最新价", "N/A")
                    data["change_percent"] = row.get("涨跌幅", "N/A")
                    data["market_cap"] = row.get("市值", "N/A")
            except:
                pass

        return json.dumps(data, indent=2, ensure_ascii=False)
    except Exception as e:
        return json.dumps({
            "error": f"Error fetching info: {str(e)}",
            "symbol": symbol
        }, ensure_ascii=False)


# ============================================================================
# Financial Chatbot Agent
# ============================================================================

class FinancialChatbot:
    """Simple financial chatbot for stock queries."""

    def __init__(self, enable_llm: bool = False):
        """
        Initialize the chatbot.

        Args:
            enable_llm: Whether to enable LLM-powered responses
        """
        self.llm = None
        self.enable_llm = enable_llm

        if enable_llm:
            try:
                from ms_agent.llm.llm import LLM
                from omegaconf import DictConfig

                # Get LLM configuration from environment
                llm_provider = os.getenv('LLM_PROVIDER', 'dashscope').lower()

                # Build LLM config based on provider
                if llm_provider == 'dashscope':
                    llm_config = {
                        'service': 'dashscope',
                        'model': os.getenv('DASHSCOPE_MODEL', 'qwen-max'),
                        'dashscope_api_key': os.getenv('DASHSCOPE_API_KEY'),
                        'modelscope_base_url': None,
                    }
                elif llm_provider == 'openai':
                    llm_config = {
                        'service': 'openai',
                        'model': os.getenv('OPENAI_MODEL', 'gpt-4'),
                        'openai_api_key': os.getenv('OPENAI_API_KEY'),
                        'openai_base_url': os.getenv('OPENAI_API_BASE', 'https://api.openai.com/v1'),
                    }
                elif llm_provider == 'deepseek':
                    llm_config = {
                        'service': 'openai',
                        'model': os.getenv('DEEPSEEK_MODEL', 'deepseek-chat'),
                        'openai_api_key': os.getenv('DEEPSEEK_API_KEY'),
                        'openai_base_url': os.getenv('DEEPSEEK_API_BASE', 'https://api.deepseek.com/v1'),
                    }
                else:
                    llm_config = {
                        'service': 'dashscope',
                        'model': 'qwen-max',
                        'dashscope_api_key': os.getenv('DASHSCOPE_API_KEY'),
                        'modelscope_base_url': None,
                    }

                api_key = llm_config.get('dashscope_api_key') or llm_config.get('openai_api_key')
                if not api_key:
                    raise ValueError(f"API key not found for provider: {llm_provider}")

                print(f"✓ Using LLM provider: {llm_provider}, model: {llm_config['model']}")

                # Create LLM instance directly
                config = DictConfig({'llm': llm_config})
                self.llm = LLM.from_config(config)

                print("✓ LLM initialized successfully")
                print("→ Using intelligent LLM mode")
            except Exception as e:
                print(f"⚠ LLM initialization failed: {e}")
                print("→ Will use direct tool call mode")
                self.llm = None
        else:
            print("ℹ️ LLM mode disabled (default)")
            print("→ Using direct tool call mode")

    def chat(self, message: str, history: List[Dict[str, str]]) -> Tuple[List[Dict[str, str]], Optional[str]]:
        """
        Process a chat message and return updated history with optional image.

        Args:
            message: User message
            history: Chat history as list of message dicts with 'role' and 'content'

        Returns:
            Tuple of (updated_history, image_path)
        """
        if not message.strip():
            return history, None

        try:
            # Use LLM if enabled and available
            if self.enable_llm and self.llm is not None:
                text_response, image_path = self._process_with_llm(message, history)
            else:
                # Fallback to direct tool call mode
                text_response, image_path = self._process_query(message)

            # Update history in Gradio 6.0 format
            history.append({"role": "user", "content": message})

            # If there's an image, add it as a separate message or embed in content
            if image_path:
                # Gradio 6.0 format: use dict with files
                history.append({
                    "role": "assistant",
                    "content": {"path": image_path}
                })
                if text_response:
                    history.append({"role": "assistant", "content": text_response})
            else:
                history.append({"role": "assistant", "content": text_response})

            return history, None

        except Exception as e:
            error_msg = f"❌ Error: {str(e)}"
            history.append({"role": "user", "content": message})
            history.append({"role": "assistant", "content": error_msg})
            return history, None

    def _process_with_llm(self, message: str, history: List[Dict[str, str]]) -> Tuple[str, Optional[str]]:
        """Process query using LLM with tool calling capability.

        Returns:
            Tuple of (text_response, image_path)
        """
        from ms_agent.llm.utils import Message, Tool

        # System prompt
        system_prompt = """你是一个金融助手聊天机器人。You are a helpful financial assistant chatbot.

你可以帮助用户：
1. 查询股票历史价格和趋势
2. 生成股票图表（折线图、K线图、面积图）
3. 获取股票基本信息

股票代码格式：
- 美股: AAPL, TSLA, MSFT, NVDA
- A股: 6位数字加后缀，如 300750.SZ (深圳), 600519.SS (上海)
- 常见中文名称: 特斯拉=TSLA, 苹果=AAPL, 宁德时代=300750.SZ, 比亚迪=002594.SZ

如果用户只是打招呼或问一般问题，请友好地回应。
当用户询问股票时，请使用工具获取数据。"""

        # Build messages
        messages = [Message(role='system', content=system_prompt)]
        for msg in history:
            messages.append(Message(role=msg.get('role', 'user'), content=msg.get('content', '')))
        messages.append(Message(role='user', content=message))

        # Define tools
        tools = [
            Tool(
                tool_name='get_stock_price_history',
                description='获取股票历史价格数据。参数: symbol(股票代码如AAPL,300750.SZ), period(时间周期:1mo,3mo,6mo,1y)',
                parameters={
                    'type': 'object',
                    'properties': {
                        'symbol': {'type': 'string', 'description': '股票代码'},
                        'period': {'type': 'string', 'description': '时间周期', 'default': '1mo'}
                    },
                    'required': ['symbol']
                }
            ),
            Tool(
                tool_name='plot_stock_chart',
                description='生成股票价格图表。参数: symbol(股票代码), period(时间周期), chart_type(图表类型:line,candlestick,area)',
                parameters={
                    'type': 'object',
                    'properties': {
                        'symbol': {'type': 'string', 'description': '股票代码'},
                        'period': {'type': 'string', 'description': '时间周期', 'default': '1mo'},
                        'chart_type': {'type': 'string', 'description': '图表类型', 'default': 'line'}
                    },
                    'required': ['symbol']
                }
            ),
            Tool(
                tool_name='get_stock_info',
                description='获取股票基本信息。参数: symbol(股票代码)',
                parameters={
                    'type': 'object',
                    'properties': {
                        'symbol': {'type': 'string', 'description': '股票代码'}
                    },
                    'required': ['symbol']
                }
            )
        ]

        # Tool function mapping
        tool_functions = {
            'get_stock_price_history': get_stock_price_history,
            'plot_stock_chart': plot_stock_chart,
            'get_stock_info': get_stock_info,
        }

        try:
            # Call LLM with tools
            response = self.llm.generate(messages=messages, tools=tools)

            # Check if LLM wants to call a tool
            if hasattr(response, 'tool_calls') and response.tool_calls:
                tool_results = []
                image_path = None

                for tool_call in response.tool_calls:
                    # Handle different tool_call formats
                    if isinstance(tool_call, dict):
                        tool_name = tool_call.get('tool_name') or tool_call.get('name', '')
                        tool_args = tool_call.get('arguments', {})
                        tool_call_id = tool_call.get('id', '')
                    elif hasattr(tool_call, 'function'):
                        tool_name = tool_call.function.name
                        tool_args = tool_call.function.arguments
                        tool_call_id = getattr(tool_call, 'id', '')
                    else:
                        tool_name = getattr(tool_call, 'tool_name', '') or getattr(tool_call, 'name', '')
                        tool_args = getattr(tool_call, 'arguments', {})
                        tool_call_id = getattr(tool_call, 'id', '')

                    if isinstance(tool_args, str):
                        import json as json_module
                        tool_args = json_module.loads(tool_args)

                    print(f"✓ Calling tool: {tool_name} with args: {tool_args}")

                    if tool_name in tool_functions:
                        result = tool_functions[tool_name](**tool_args)

                        # For chart tool, also fetch price data for analysis
                        if tool_name == 'plot_stock_chart' and result and not result.startswith('Error'):
                            image_path = result
                            # Fetch price data and extract key metrics
                            price_data_json = get_stock_price_history(
                                symbol=tool_args.get('symbol'),
                                period=tool_args.get('period', '1mo')
                            )

                            # Parse JSON and extract summary
                            try:
                                import json as json_module
                                data = json_module.loads(price_data_json)
                                if 'summary' in data and 'data' in data:
                                    summary = data['summary']
                                    historical_data = data['data']

                                    # Format concise summary for LLM
                                    price_summary = f"""股票代码: {tool_args.get('symbol')}
时间周期: {tool_args.get('period', '1mo')}

关键指标:
- 当前价格: ¥{summary.get('current_price', 0):.2f}
- 前收盘价: ¥{summary.get('prev_close', 0):.2f}
- 涨跌额: ¥{summary.get('change', 0):.2f}
- 涨跌幅: {summary.get('change_percent', 0):.2f}%
- 期间最高: ¥{summary.get('high', 0):.2f}
- 期间最低: ¥{summary.get('low', 0):.2f}
- 平均成交量: {summary.get('avg_volume', 0):,}手

近期数据点 (最近5个交易日):
"""
                                    # Add last 5 data points
                                    for item in historical_data[-5:]:
                                        price_summary += f"- {item['date']}: 开盘¥{item['open']:.2f}, 收盘¥{item['close']:.2f}, 最高¥{item['high']:.2f}, 最低¥{item['low']:.2f}\n"

                                    tool_results.append(f"[工具 plot_stock_chart] 已生成图表\n\n{price_summary}")
                                else:
                                    tool_results.append(f"[工具 plot_stock_chart] 已生成图表\n{price_data_json}")
                            except:
                                tool_results.append(f"[工具 plot_stock_chart] 已生成图表")
                        else:
                            # For other tools, parse and format the result
                            if isinstance(result, str) and result.startswith('{'):
                                try:
                                    import json as json_module
                                    data = json_module.loads(result)
                                    if 'summary' in data:
                                        # Format price history result
                                        summary = data['summary']
                                        formatted_result = f"""关键指标:
- 当前价格: ¥{summary.get('current_price', 0):.2f}
- 涨跌幅: {summary.get('change_percent', 0):.2f}%
- 期间最高: ¥{summary.get('high', 0):.2f}
- 期间最低: ¥{summary.get('low', 0):.2f}"""
                                        tool_results.append(f"[工具 {tool_name}]\n{formatted_result}")
                                    else:
                                        tool_results.append(f"[工具 {tool_name}]\n{result}")
                                except:
                                    tool_results.append(f"[工具 {tool_name}]\n{result}")
                            else:
                                tool_results.append(f"[工具 {tool_name}]\n{result}")

                # Now send tool results back to LLM for analysis
                if tool_results:
                    # Add assistant message with tool calls
                    messages.append(Message(role='assistant', content='', tool_calls=response.tool_calls))

                    # Add tool results as tool response
                    tool_result_content = "\n\n".join(tool_results)
                    messages.append(Message(role='tool', content=tool_result_content, tool_call_id=tool_call_id))

                    # Ask LLM to analyze the results
                    analysis_prompt = Message(role='user', content="""请根据上面获取的数据，为用户提供详细的分析和解读：
1. 总结关键数据指标
2. 分析近期走势趋势
3. 给出简要的市场观点
请用清晰易懂的中文回答。""")
                    messages.append(analysis_prompt)

                    # Get LLM analysis
                    analysis_response = self.llm.generate(messages=messages)

                    if hasattr(analysis_response, 'content') and analysis_response.content:
                        return analysis_response.content, image_path
                    else:
                        return tool_result_content, image_path

            # Return text response (no tool calls)
            if hasattr(response, 'content') and response.content:
                return response.content, None
            elif isinstance(response, str):
                return response, None
            else:
                return str(response), None

        except Exception as e:
            print(f"⚠ LLM error: {e}, falling back to direct mode")
            import traceback
            traceback.print_exc()
            return self._process_query(message)

    def _process_query(self, message: str) -> Tuple[str, Optional[str]]:
        """Process query using direct tool calls."""
        message_lower = message.lower()

        # Try to extract symbol using improved parser
        symbol = parse_stock_symbol(message)

        if not symbol:
            return """📊 **欢迎使用金融聊天机器人！/ Welcome to Financial Chatbot!**

我可以帮您查询股票信息，请指定股票代码或名称。

**示例 / Examples:**
- "给我看看苹果公司的股价" / "Show me AAPL stock price"
- "画一个特斯拉的K线图" / "Plot TSLA candlestick chart"
- "查询宁德时代的信息" / "Get info about 300750.SZ"
- "比亚迪最近一个月的价格" / "BYD price last month"

**股票代码格式 / Stock Symbol Format:**
- 美股 / US stocks: AAPL, MSFT, TSLA, NVDA
- A股 / A-shares:
  - 可以直接输入6位数字: 300750, 600519, 000001
  - 或带交易所后缀: 300750.SZ, 600519.SS
- 中文名称 / Chinese names: 特斯拉, 宁德时代, 比亚迪
""", None

        print(f"✓ Detected symbol: {symbol} from message: {message}")

        # Determine action
        if 'chart' in message_lower or 'plot' in message_lower or '图' in message_lower:
            chart_type = 'candlestick' if 'candle' in message_lower or 'k线' in message_lower or 'k-line' in message_lower else 'line'
            period = '3mo' if '3' in message and ('month' in message_lower or '月' in message_lower) else '1mo'

            result = plot_stock_chart(symbol, period=period, chart_type=chart_type)

            if result.startswith('Error'):
                return f"❌ {result}", None
            else:
                return f"📈 已生成 {symbol} 的{chart_type}图表 (周期: {period})", result

        elif 'info' in message_lower or 'about' in message_lower or 'detail' in message_lower or '信息' in message_lower:
            result = get_stock_info(symbol)
            try:
                data = json.loads(result)
                if 'error' in data:
                    return f"❌ {data['error']}", None

                info_text = f"""📊 **{symbol} 股票信息**

**基本信息:**
- 🏢 名称: {data.get('name', 'N/A')}
- 🔧 行业: {data.get('industry', 'N/A')}

**市场数据:**
- 💰 当前价格: {data.get('current_price', 'N/A')}
- 📊 涨跌幅: {data.get('change_percent', 'N/A')}%
- 📈 市值: {data.get('market_cap', 'N/A')}
- 📊 市盈率: {data.get('pe_ratio', 'N/A')}
"""
                return info_text, None
            except:
                return result, None
        else:
            # Default: show price history
            period = '3mo' if '3' in message and ('month' in message_lower or '月' in message_lower) else '1mo'
            result = get_stock_price_history(symbol, period=period)

            try:
                data = json.loads(result)
                if 'error' in data:
                    return f"❌ {data['error']}", None

                summary = data.get('summary', {})
                current = summary.get('current_price') or 0
                change = summary.get('change') or 0
                change_pct = summary.get('change_percent') or 0

                change_emoji = "📈" if change >= 0 else "📉"
                change_sign = "+" if change >= 0 else ""

                high_val = summary.get('high') or 0
                low_val = summary.get('low') or 0
                avg_vol = summary.get('avg_volume') or 0

                price_text = f"""📊 **{symbol} 股价摘要**

**当前价格:** ¥{current:.2f}
**涨跌:** {change_emoji} {change_sign}¥{change:.2f} ({change_sign}{change_pct:.2f}%)

**{period} 统计:**
- 📈 最高: ¥{high_val:.2f}
- 📉 最低: ¥{low_val:.2f}
- 📊 平均成交量: {avg_vol:,}

💡 输入 "画 {symbol} 图" 查看走势图！
"""
                return price_text, None
            except:
                return result, None


# ============================================================================
# Gradio Interface
# ============================================================================

def create_chatbot_interface():
    """Create the Gradio chatbot interface."""

    # Check if LLM mode should be enabled from environment variable
    enable_llm = os.getenv('ENABLE_LLM', 'false').lower() in ('true', '1', 'yes')

    # Initialize chatbot
    chatbot_instance = FinancialChatbot(enable_llm=enable_llm)

    _theme = gr.themes.Soft(
        primary_hue="blue",
        secondary_hue="slate"
    )

    _css = """
    .gradio-container {
        max-width: 1200px !important;
        margin: 0 auto !important;
    }
    .header {
        text-align: center;
        padding: 2rem 1rem;
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
        border-radius: 1rem;
        color: white;
        margin-bottom: 2rem;
    }
    .header h1 {
        font-size: 2rem;
        margin-bottom: 0.5rem;
    }
    .header p {
        font-size: 1.1rem;
        opacity: 0.95;
    }
    .examples-box {
        margin-top: 1rem;
        padding: 1rem;
        background: #f8fafc;
        border-radius: 0.5rem;
    }
    """

    with gr.Blocks(title="Financial Chatbot") as demo:
        mode_text = "🤖 LLM Mode - Intelligent Agent" if enable_llm else "🚀 Direct Mode - No API Key Required"
        gr.HTML(f"""
        <div class="header">
            <h1>💰 Financial Chatbot</h1>
            <p>Your AI assistant for stock queries and market insights</p>
            <p style="font-size: 0.9rem; opacity: 0.8;">{mode_text}</p>
        </div>
        """)

        with gr.Row():
            with gr.Column(scale=2):
                chatbot_ui = gr.Chatbot(
                    label="Chat",
                    height=500,
                    show_label=False
                )

                with gr.Row():
                    msg_input = gr.Textbox(
                        label="Message",
                        placeholder="Ask me about stocks... (e.g., 'Show me AAPL stock price for the last month')",
                        scale=4,
                        show_label=False
                    )
                    send_btn = gr.Button("Send", variant="primary", scale=1)

                with gr.Row():
                    clear_btn = gr.Button("Clear Chat", size="sm")

            with gr.Column(scale=1):
                gr.HTML("""
                <div class="examples-box">
                    <h3 style="margin-top: 0;">💡 Example Queries:</h3>
                    <ul style="line-height: 1.8;">
                        <li>Show me AAPL stock price for the last 3 months</li>
                        <li>Plot a candlestick chart for TSLA in the past month</li>
                        <li>What's the current price of Microsoft?</li>
                        <li>Get info about NVDA stock</li>
                        <li>Show me 宁德时代 (300750.SZ) trend</li>
                    </ul>

                    <h3>📊 Supported Features:</h3>
                    <ul style="line-height: 1.8;">
                        <li>Stock price history</li>
                        <li>Price charts (line, candlestick, area)</li>
                        <li>Company information</li>
                        <li>Market statistics</li>
                        <li>US stocks & Chinese A-shares</li>
                    </ul>

                    <h3>📝 Stock Symbols:</h3>
                    <ul style="line-height: 1.8;">
                        <li><strong>US:</strong> AAPL, MSFT, TSLA, NVDA</li>
                        <li><strong>A-shares:</strong> Add .SZ or .SS suffix<br>
                        (e.g., 000001.SZ, 600000.SS)</li>
                    </ul>
                </div>
                """)

        def respond(message, chat_history):
            """Handle user message and update chat."""
            if not message.strip():
                return chat_history, ""

            # Ensure chat_history is a list (handle None case)
            if chat_history is None:
                chat_history = []

            # Get bot response
            updated_history, _ = chatbot_instance.chat(message, chat_history)

            return updated_history, ""

        def clear():
            """Clear chat history."""
            return [], ""

        # Event handlers
        send_btn.click(
            respond,
            inputs=[msg_input, chatbot_ui],
            outputs=[chatbot_ui, msg_input]
        )

        msg_input.submit(
            respond,
            inputs=[msg_input, chatbot_ui],
            outputs=[chatbot_ui, msg_input]
        )

        clear_btn.click(
            clear,
            outputs=[chatbot_ui, msg_input]
        )

    return demo, _theme, _css


# ============================================================================
# Launch Server
# ============================================================================

def launch_chatbot(
    server_name: str = "0.0.0.0",
    server_port: int = 7860,
    share: bool = False
):
    """Launch the chatbot server."""
    demo, theme, css = create_chatbot_interface()
    demo.launch(
        server_name=server_name,
        server_port=server_port,
        share=share,
        theme=theme,
        css=css
    )


if __name__ == "__main__":
    launch_chatbot(server_name="0.0.0.0", server_port=7860, share=False)
