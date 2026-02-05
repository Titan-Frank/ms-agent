"""
Tool calling handlers for the financial chatbot.
"""
import json
from typing import List, Tuple, Optional

import plotly.graph_objects as go
from plotly.subplots import make_subplots


# Tool schemas definition (ms_agent format)
TOOL_SCHEMAS = [
    {
        "tool_name": "search_stock",
        "description": "搜索股票代码。当用户提到任何公司名称、股票名称时使用此工具。支持中文名称（如'胜宏科技'）、美股符号（如'AAPL'）或股票代码（如'300476'）。",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "股票名称或代码，例如：'胜宏科技'、'TSLA'、'300476'"
                }
            },
            "required": ["query"]
        }
    },
    {
        "tool_name": "get_stock_data",
        "description": "获取股票的历史价格数据和走势分析。用于回答关于股价、涨跌、走势等问题。",
        "parameters": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "股票代码，如 'TSLA'、'300476.SZ'、'600519.SS'"
                },
                "period": {
                    "type": "string",
                    "description": "时间周期",
                    "enum": ["1d", "5d", "1mo", "3mo", "6mo", "1y"],
                    "default": "1mo"
                },
                "chart_type": {
                    "type": "string",
                    "description": "图表类型：line(折线图)、candlestick(K线图)、area(面积图)",
                    "enum": ["line", "candlestick", "area"],
                    "default": "line"
                }
            },
            "required": ["symbol"]
        }
    },
    {
        "tool_name": "compare_stocks",
        "description": "对比多只股票的表现。当用户想要比较、对比多只股票时使用。",
        "parameters": {
            "type": "object",
            "properties": {
                "symbols": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "要对比的股票代码列表，如 ['TSLA', 'AAPL'] 或 ['300750.SZ', '002594.SZ']",
                    "minItems": 2,
                    "maxItems": 5
                },
                "period": {
                    "type": "string",
                    "description": "时间周期",
                    "enum": ["1d", "5d", "1mo", "3mo", "6mo", "1y"],
                    "default": "1mo"
                }
            },
            "required": ["symbols"]
        }
    }
]


def search_stock(query: str) -> str:
    """Tool implementation: Search for stock symbol."""
    from tools import parse_stock_symbol

    symbol = parse_stock_symbol(query)
    if symbol:
        return json.dumps({
            "success": True,
            "symbol": symbol,
            "query": query,
            "message": f"找到股票代码: {symbol}"
        }, ensure_ascii=False)
    else:
        return json.dumps({
            "success": False,
            "query": query,
            "message": f"未找到股票: {query}"
        }, ensure_ascii=False)


def get_stock_data(symbol: str, period: str = "1mo", chart_type: str = "line") -> Tuple[str, Optional[object]]:
    """Tool implementation: Get stock data and chart."""
    from tools import get_stock_price_history, plot_stock_chart

    # Get price history
    price_result = get_stock_price_history(symbol, period=period)
    price_data = json.loads(price_result)

    if "error" in price_data:
        return json.dumps({"error": price_data["error"]}, ensure_ascii=False), None

    # Generate chart
    chart_result = plot_stock_chart(symbol, period=period, chart_type=chart_type)
    chart_data = json.loads(chart_result)

    # Create plotly figure
    plotly_fig = None
    if chart_data.get("type") == "plotly":
        import plotly.io as pio
        plotly_fig = pio.from_json(json.dumps(chart_data["data"]))

    # Return data summary for LLM
    summary = price_data.get('summary', {})
    result = {
        "symbol": symbol,
        "period": period,
        "current_price": summary.get('current_price'),
        "change": summary.get('change'),
        "change_percent": summary.get('change_percent'),
        "high": summary.get('high'),
        "low": summary.get('low'),
        "avg_volume": summary.get('avg_volume'),
        "chart_generated": plotly_fig is not None
    }

    return json.dumps(result, ensure_ascii=False, indent=2), plotly_fig


def compare_stocks(symbols: List[str], period: str = "1mo") -> Tuple[str, Optional[object]]:
    """Tool implementation: Compare multiple stocks."""
    from tools import get_stock_price_history

    try:
        comparison_data = []
        fig_data = []

        # Fetch data for each stock
        for symbol in symbols:
            price_result = get_stock_price_history(symbol, period=period)
            price_data = json.loads(price_result)

            if "error" not in price_data:
                summary = price_data.get('summary', {})
                comparison_data.append({
                    "symbol": symbol,
                    "current_price": summary.get('current_price'),
                    "change": summary.get('change'),
                    "change_percent": summary.get('change_percent'),
                    "high": summary.get('high'),
                    "low": summary.get('low'),
                })

                # Add line to chart (normalized to percentage change)
                data_points = price_data.get('data', [])
                if data_points:
                    dates = [d['date'] for d in data_points]
                    closes = [d['close'] for d in data_points]

                    # Normalize to percentage change from start
                    start_price = closes[0]
                    pct_changes = [(c / start_price - 1) * 100 for c in closes]

                    fig_data.append(go.Scatter(
                        x=dates,
                        y=pct_changes,
                        mode='lines',
                        name=symbol,
                        line=dict(width=2),
                        hovertemplate=f'<b>{symbol}</b><br>%{{x}}<br>涨跌: %{{y:.2f}}%<extra></extra>'
                    ))

        # Create comparison chart
        if fig_data:
            fig = go.Figure(data=fig_data)
            fig.update_layout(
                title="股票对比 - 归一化涨跌幅 (%)",
                template='plotly_dark',
                paper_bgcolor='#0D1117',
                plot_bgcolor='#0D1117',
                font=dict(family='Arial, sans-serif', color='#C9D1D9'),
                height=500,
                xaxis_title="日期",
                yaxis_title="涨跌幅 (%)",
                hovermode='x unified',
                legend=dict(
                    yanchor="top",
                    y=0.99,
                    xanchor="left",
                    x=0.01
                )
            )
            fig.update_xaxes(gridcolor='#21262D', showgrid=True)
            fig.update_yaxes(gridcolor='#21262D', showgrid=True, zeroline=True, zerolinecolor='#30363D')
        else:
            fig = None

        # Return comparison data for LLM
        result = {
            "period": period,
            "stocks": comparison_data,
            "chart_generated": fig is not None
        }

        return json.dumps(result, ensure_ascii=False, indent=2), fig

    except Exception as e:
        import traceback
        traceback.print_exc()
        return json.dumps({"error": str(e)}, ensure_ascii=False), None


# Tool registry
TOOL_FUNCTIONS = {
    "search_stock": search_stock,
    "get_stock_data": get_stock_data,
    "compare_stocks": compare_stocks,
}
