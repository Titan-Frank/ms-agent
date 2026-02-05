"""
Stock data tools for financial chatbot.
Provides functions to fetch stock prices, generate charts, and get company info.
"""
import json
import tempfile
from datetime import datetime, timedelta
from typing import Optional

try:
    import akshare as ak
    import pandas as pd
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
except ImportError as e:
    raise ImportError(
        f"Missing required library: {e}. "
        "Please install: pip install akshare pandas plotly kaleido"
    )


# Chinese stock name to code mapping
STOCK_NAME_MAP = {
    # US stocks
    '特斯拉': 'TSLA',
    '苹果': 'AAPL',
    '微软': 'MSFT',
    '英伟达': 'NVDA',
    '谷歌': 'GOOGL',
    '亚马逊': 'AMZN',
    '脸书': 'META',

    # Chinese A-shares
    '宁德时代': '300750',
    '贵州茅台': '600519',
    '比亚迪': '002594',
    '中公教育': '002607',
    '五粮液': '000858',
    '美的集团': '000333',
    '格力电器': '000651',
    '中际旭创': '300308',
    '胜宏科技': '300476',
}


def search_stock_by_name(name: str) -> Optional[str]:
    """
    Search for stock code by Chinese name using akshare.

    Args:
        name: Chinese stock name (e.g., "胜宏科技", "宁德时代")

    Returns:
        Stock code with exchange suffix (e.g., "300476.SZ") or None
    """
    import time

    # Try multiple times with backoff
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Get all A-share stocks
            df = ak.stock_zh_a_spot_em()

            # Search by name (exact match or contains)
            # Columns: 代码, 名称, ...
            matched = df[df['名称'].str.contains(name, na=False)]

            if not matched.empty:
                code = matched.iloc[0]['代码']
                # Add exchange suffix
                if code.startswith('6'):
                    return f"{code}.SS"  # Shanghai
                else:
                    return f"{code}.SZ"  # Shenzhen

            return None

        except Exception as e:
            print(f"Stock search error (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff: 1s, 2s, 4s
            else:
                # Final fallback: try to use cached mapping
                print(f"⚠️ akshare API failed, trying fallback...")
                return None

    return None


def parse_stock_symbol(message: str) -> Optional[str]:
    """
    Intelligently parse stock symbol from user message.
    Supports: US symbols (AAPL), A-share codes (300750.SZ), Chinese names (特斯拉).

    Strategy:
    1. Check hardcoded mapping (fast path for common stocks)
    2. Check for explicit stock codes in message
    3. Search Chinese stock names via akshare (intelligent search)
    4. Check for US stock symbols
    """
    import re

    # Strategy 1: Check hardcoded mapping first (fast path)
    for name, code in STOCK_NAME_MAP.items():
        if name in message:
            # Add exchange suffix for A-shares
            if code.isdigit() and len(code) == 6:
                if code.startswith('6'):
                    return f"{code}.SS"  # Shanghai
                else:
                    return f"{code}.SZ"  # Shenzhen
            return code

    # Strategy 2: Check for explicit A-share codes (6 digits with optional .SZ/.SS suffix)
    a_share_pattern = r'\b(\d{6})(?:\.(SZ|SS))?\b'
    match = re.search(a_share_pattern, message)
    if match:
        code = match.group(1)
        suffix = match.group(2)
        if not suffix:
            # Auto-detect exchange
            if code.startswith('6'):
                suffix = 'SS'  # Shanghai
            else:
                suffix = 'SZ'  # Shenzhen
        return f"{code}.{suffix}"

    # Strategy 3: Intelligent search for Chinese stock names
    # Extract potential Chinese stock names (2-6 Chinese characters)
    chinese_pattern = r'[\u4e00-\u9fa5]{2,6}'
    matches = re.findall(chinese_pattern, message)

    for potential_name in matches:
        # Try to search this name via akshare
        result = search_stock_by_name(potential_name)
        if result:
            print(f"✓ Found stock: {potential_name} -> {result}")
            return result

    # Strategy 4: Check for US stock symbols (1-5 uppercase letters)
    us_pattern = r'\b([A-Z]{1,5})\b'
    match = re.search(us_pattern, message.upper())
    if match:
        symbol = match.group(1)
        # Filter out common English words
        if symbol not in ['A', 'I', 'K', 'THE', 'AND', 'OR', 'NOT', 'FOR', 'TO', 'IN', 'ON', 'AT']:
            return symbol

    return None


def get_stock_price_history(symbol: str, period: str = "1mo", interval: str = "1d") -> str:
    """
    Get historical stock price data.

    Args:
        symbol: Stock ticker symbol (e.g., AAPL, 300750.SZ)
        period: Time period (1d, 5d, 1mo, 3mo, 6mo, 1y)
        interval: Data interval (1d)

    Returns:
        JSON string with price data and summary
    """
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

        # Fetch data with forward adjustment (前复权)
        # adjust="qfq" 表示前复权，可以消除拆股、分红的影响
        if symbol.endswith('.SZ') or symbol.endswith('.SS'):
            clean_symbol = symbol.replace('.SZ', '').replace('.SS', '')
            df = ak.stock_zh_a_hist(symbol=clean_symbol, period='daily',
                                   start_date=start_date, end_date=end_date, adjust="qfq")
        else:
            df = ak.stock_us_hist(symbol=symbol, period='daily',
                                 start_date=start_date, end_date=end_date, adjust="")

        if df.empty:
            return json.dumps({"error": f"No data found for {symbol}"}, ensure_ascii=False)

        # Standardize columns
        column_map = {
            '日期': 'date', '开盘': 'open', '收盘': 'close',
            '最高': 'high', '最低': 'low', '成交量': 'volume',
        }
        df = df.rename(columns=column_map)

        # Calculate summary
        current_price = float(df['close'].iloc[-1])
        prev_close = float(df['close'].iloc[0])
        price_change = current_price - prev_close
        price_change_pct = (price_change / prev_close) * 100

        summary = {
            "current_price": round(current_price, 2),
            "prev_close": round(prev_close, 2),
            "change": round(price_change, 2),
            "change_percent": round(price_change_pct, 2),
            "high": round(float(df['high'].max()), 2),
            "low": round(float(df['low'].min()), 2),
            "avg_volume": int(df['volume'].mean()),
        }

        # Prepare historical data
        data_points = []
        for _, row in df.iterrows():
            data_points.append({
                "date": str(row['date']),
                "open": round(float(row['open']), 2),
                "close": round(float(row['close']), 2),
                "high": round(float(row['high']), 2),
                "low": round(float(row['low']), 2),
                "volume": int(row['volume']),
            })

        return json.dumps({
            "symbol": symbol,
            "period": period,
            "summary": summary,
            "data": data_points
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


def plot_stock_chart(symbol: str, period: str = "1mo", chart_type: str = "line") -> str:
    """
    Generate professional stock price chart using Plotly.

    Args:
        symbol: Stock ticker symbol
        period: Time period (1mo, 3mo, 6mo, 1y)
        chart_type: Chart type (line, candlestick, area)

    Returns:
        JSON string containing Plotly figure data for interactive rendering
    """
    try:
        # Convert period to days
        period_days_map = {"1d": 1, "5d": 5, "1mo": 30, "3mo": 90, "6mo": 180, "1y": 365}
        days = period_days_map.get(period, 30)

        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")

        # Fetch data
        if symbol.endswith('.SZ') or symbol.endswith('.SS'):
            clean_symbol = symbol.replace('.SZ', '').replace('.SS', '')
            df = ak.stock_zh_a_hist(symbol=clean_symbol, period='daily',
                                   start_date=start_date, end_date=end_date, adjust="")
        else:
            df = ak.stock_us_hist(symbol=symbol, period='daily',
                                 start_date=start_date, end_date=end_date, adjust="")

        if df.empty:
            return json.dumps({"error": f"No data for {symbol}"}, ensure_ascii=False)

        # Standardize columns
        column_map = {'日期': 'Date', '开盘': 'Open', '收盘': 'Close',
                     '最高': 'High', '最低': 'Low', '成交量': 'Volume'}
        df = df.rename(columns=column_map)
        df['Date'] = pd.to_datetime(df['Date'])

        # Calculate metrics
        current_price = df['Close'].iloc[-1]
        prev_price = df['Close'].iloc[0]
        price_change = current_price - prev_price
        price_change_pct = (price_change / prev_price) * 100

        # Determine colors
        line_color = '#00C805' if price_change >= 0 else '#FF5252'
        fill_color = 'rgba(0, 200, 5, 0.1)' if price_change >= 0 else 'rgba(255, 82, 82, 0.1)'

        # Create figure
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03,
                           row_heights=[0.7, 0.3])

        # Add price chart
        if chart_type == 'candlestick':
            fig.add_trace(go.Candlestick(
                x=df['Date'],
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close'],
                name='K线',
                increasing_line_color='#00C805',
                decreasing_line_color='#FF5252',
                increasing_fillcolor='#00C805',
                decreasing_fillcolor='#FF5252',
            ), row=1, col=1)
        else:
            fig.add_trace(go.Scatter(
                x=df['Date'],
                y=df['Close'],
                mode='lines',
                name='收盘价',
                line=dict(color=line_color, width=2),
                fill='tozeroy' if chart_type == 'area' else None,
                fillcolor=fill_color,
                hovertemplate='<b>%{x|%Y-%m-%d}</b><br>收盘: ¥%{y:.2f}<extra></extra>'
            ), row=1, col=1)

        # Add volume bars
        colors = ['#00C805' if df['Close'].iloc[i] >= df['Open'].iloc[i] else '#FF5252'
                  for i in range(len(df))]
        fig.add_trace(go.Bar(
            x=df['Date'],
            y=df['Volume'],
            name='成交量',
            marker_color=colors,
            opacity=0.7,
            hovertemplate='<b>%{x|%Y-%m-%d}</b><br>成交量: %{y:,.0f}<extra></extra>'
        ), row=2, col=1)

        # Update layout
        change_sign = "+" if price_change >= 0 else ""
        change_arrow = "↗" if price_change >= 0 else "↘"

        fig.update_layout(
            title=dict(
                text=f'<b>{symbol}</b><br>' +
                     f'<span style="font-size:24px">¥{current_price:.2f}</span> ' +
                     f'<span style="color:{line_color}">{change_sign}{price_change:.2f} {change_arrow} {change_sign}{price_change_pct:.2f}%</span>',
                x=0.02, y=0.98, font=dict(size=16, color='#E1E4E8')
            ),
            template='plotly_dark',
            paper_bgcolor='#0D1117',
            plot_bgcolor='#0D1117',
            font=dict(family='Arial, sans-serif', color='#C9D1D9'),
            showlegend=False,
            height=600,
            margin=dict(l=60, r=40, t=100, b=40),
            xaxis_rangeslider_visible=False,
            hovermode='x unified',
            dragmode='zoom',  # Enable zoom by dragging
        )

        # Update axes
        for row in [1, 2]:
            fig.update_xaxes(
                gridcolor='#21262D',
                showgrid=True,
                zeroline=False,
                showline=True,
                linecolor='#30363D',
                tickformat='%m/%d',
                row=row, col=1
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

        # Return Plotly figure as JSON for interactive rendering
        import plotly.io as pio

        return json.dumps({
            "type": "plotly",
            "data": json.loads(pio.to_json(fig))
        }, ensure_ascii=False)

    except ImportError:
        return json.dumps({"error": "Missing library. Install: pip install plotly"}, ensure_ascii=False)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return json.dumps({"error": str(e)}, ensure_ascii=False)


def get_stock_info(symbol: str) -> str:
    """
    Get basic stock information.

    Args:
        symbol: Stock ticker symbol

    Returns:
        JSON string with stock info
    """
    try:
        # For now, return basic info (can be extended with more data sources)
        price_data = get_stock_price_history(symbol, period="1mo")
        data = json.loads(price_data)

        if "error" in data:
            return price_data

        info = {
            "symbol": symbol,
            "name": symbol,  # Can be enhanced with company name lookup
            "current_price": data["summary"]["current_price"],
            "change_percent": data["summary"]["change_percent"],
            "high": data["summary"]["high"],
            "low": data["summary"]["low"],
        }

        return json.dumps(info, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)
