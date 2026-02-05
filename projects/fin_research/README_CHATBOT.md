# 💰 Financial Chatbot - 简化版金融聊天机器人

一个轻量级的金融聊天机器人，专注于股票查询和图表展示等基础功能。

## 🌟 功能特性

- **📊 股票历史数据查询**: 获取任意时间段的股票价格数据
- **📈 多种图表类型**: 支持折线图、K线图(蜡烛图)、面积图
- **ℹ️ 公司信息查询**: 获取公司基本信息、市值、PE比率等
- **🌐 多市场支持**: 支持美股和A股市场
- **💬 对话式交互**: 自然语言查询，无需记忆复杂命令

## 🚀 快速开始

### 1. 安装依赖

```bash
# 安装所需的Python包
pip install -r ../../requirements/research.txt
```

### 2. 配置LLM

设置你的API密钥（支持OpenAI、Azure OpenAI、通义千问等）:

```bash
# OpenAI
export OPENAI_API_KEY="your-api-key"

# 或者 Azure OpenAI
export AZURE_OPENAI_API_KEY="your-api-key"
export AZURE_OPENAI_ENDPOINT="your-endpoint"

# 或者 通义千问
export DASHSCOPE_API_KEY="your-api-key"
```

### 3. 启动聊天机器人

```bash
python fin_chatbot.py
```

然后在浏览器中访问: http://localhost:7860

## 💡 使用示例

### 查询股票价格

**中文示例:**
- "查询苹果公司最近一个月的股价"
- "显示特斯拉最近三个月的价格走势"
- "宁德时代的当前股价是多少？"

**English Examples:**
- "Show me AAPL stock price for the last month"
- "What's the current price of Tesla?"
- "Get Microsoft stock info"

### 生成图表

**K线图:**
- "给我画一个特斯拉最近一个月的K线图"
- "Plot a candlestick chart for NVDA"

**折线图和面积图:**
- "Show me a line chart for AAPL in the past 3 months"
- "Plot an area chart for MSFT"

### 查询公司信息

- "告诉我关于英伟达的信息"
- "Get info about Apple stock"
- "What's the market cap of Tesla?"

## 📝 股票代码格式

### 美股
直接使用股票代码:
- Apple: `AAPL`
- Microsoft: `MSFT`
- Tesla: `TSLA`
- NVIDIA: `NVDA`

### A股
需要添加交易所后缀:
- 深圳证券交易所: 添加 `.SZ` (如: `000001.SZ`, `300750.SZ`)
- 上海证券交易所: 添加 `.SS` (如: `600000.SS`, `601398.SS`)

**常见A股示例:**
- 平安银行: `000001.SZ`
- 宁德时代: `300750.SZ`
- 贵州茅台: `600519.SS`
- 中国平安: `601318.SS`

## 🛠️ 技术架构

```
Financial Chatbot
├── MS-Agent Framework: 核心Agent引擎
├── yfinance: 股票数据获取
├── matplotlib: 图表生成
└── Gradio: Web界面
```

## 📊 支持的时间周期

- `1d`, `5d`: 1天、5天
- `1mo`, `3mo`, `6mo`: 1个月、3个月、6个月
- `1y`, `2y`, `5y`, `10y`: 1年、2年、5年、10年
- `ytd`: 年初至今
- `max`: 最大可用历史数据

## 🔧 高级配置

### 修改服务器端口

编辑 `fin_chatbot.py`:

```python
launch_chatbot(
    server_name="0.0.0.0",
    server_port=8080,  # 修改为你想要的端口
    share=False
)
```

### 启用公网分享

```python
launch_chatbot(
    server_name="0.0.0.0",
    server_port=7860,
    share=True  # 生成公网访问链接
)
```

## 🆚 与原版fin_research的区别

| 特性 | 原版fin_research | 简化版chatbot |
|------|-----------------|---------------|
| 复杂度 | 高 (多Agent工作流) | 低 (单Agent对话) |
| 功能 | 深度研究报告生成 | 基础数据查询和图表 |
| 响应速度 | 较慢 (需要多轮推理) | 快速 |
| 适用场景 | 专业金融研究 | 日常股票查询 |
| 资源消耗 | 高 | 低 |

## 📚 API文档

### 内置工具函数

#### `get_stock_price_history(symbol, period, interval)`
获取股票历史价格数据

#### `plot_stock_chart(symbol, period, chart_type)`
生成股票价格图表

#### `get_stock_info(symbol)`
获取股票基本信息

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

与MS-Agent主项目保持一致

---

**Enjoy trading! 📈💰**
