# Financial Chatbot

An intelligent LLM-powered chatbot for stock market queries, chart generation, and data analysis.

[中文文档](README_zh.md)

## Features

- ✅ **Intelligent Dialogue** - Natural language understanding (English & Chinese)
- ✅ **Stock Queries** - Real-time prices, historical data, company information
- ✅ **Chart Generation** - Professional Plotly interactive charts (line, candlestick, area)
- ✅ **Data Analysis** - AI-powered trend analysis and market insights
- ✅ **Multi-Market** - US stocks and Chinese A-shares
- ✅ **Chinese Stock Names** - Supports "特斯拉", "宁德时代" etc.

## Quick Start

### 1. Install Dependencies

```bash
pip install akshare plotly kaleido pandas python-dotenv gradio
# Or run the setup script
./setup.sh
```

### 2. Configure

```bash
cp config.env.example config.env
# Edit config.env and add your API key
```

### 3. Launch

```bash
python fin_chatbot.py
```

Visit http://localhost:7860

## Usage Examples

### English Queries
```
User: Show me AAPL stock price
Bot: [Displays Apple stock data + analysis]

User: Plot TSLA candlestick chart
Bot: [Generates Tesla K-line chart + trend analysis]
```

### Chinese Queries
```
用户: 帮我画出中公教育近3个月的股价图
Bot: [生成专业图表 + 详细分析]

用户: 宁德时代最近怎么样？
Bot: [查询价格 + 市场分析]
```

## Stock Symbol Format

### US Stocks
Use ticker directly: `AAPL`, `TSLA`, `MSFT`, `NVDA`

### Chinese A-Shares
Use 6-digit code + exchange suffix:
- `300750.SZ` - CATL (Shenzhen)
- `600519.SS` - Moutai (Shanghai)
- `002594.SZ` - BYD

Or just use 6 digits (auto-adds suffix):
- `300750` → `300750.SZ`

### Chinese Names
Supports common stock names:
- `特斯拉` → `TSLA`
- `宁德时代` → `300750.SZ`

## Tech Stack

- **Data Source**: AKShare (free, no API key needed)
- **Charts**: Plotly (professional interactive charts)
- **LLM**: Dashscope / OpenAI / DeepSeek
- **UI**: Gradio (clean web interface)

## License

Same as ms-agent project
