# 金融聊天机器人 (Financial Chatbot)

一个基于 LLM 的智能金融聊天机器人，支持股票查询、图表生成和数据分析。

## 功能特性

- ✅ **智能对话** - 自然语言理解，支持中英文
- ✅ **股票查询** - 实时价格、历史数据、公司信息
- ✅ **图表生成** - 专业的 Plotly 交互式图表（折线图、K线图、面积图）
- ✅ **数据分析** - LLM 自动分析股价走势并给出市场观点
- ✅ **多市场支持** - 美股、A股
- ✅ **中文股票名称识别** - 支持"特斯拉"、"宁德时代"等中文名称

## 快速开始

### 1. 安装依赖

```bash
pip install akshare plotly kaleido pandas python-dotenv
```

### 2. 配置环境

复制配置文件模板：

```bash
cp config.env.example config.env
```

编辑 `config.env` 填入你的 API Key：

```bash
# LLM Provider
LLM_PROVIDER=dashscope

# Dashscope (通义千问)
DASHSCOPE_API_KEY=your-api-key-here
DASHSCOPE_MODEL=qwen-max

# 启用 LLM 模式
ENABLE_LLM=true
```

### 3. 启动聊天机器人

```bash
python fin_chatbot.py
```

访问 http://localhost:7860

## 使用示例

### 中文查询

```
用户: 帮我画出中公教育近3个月的股价图
助手: [生成专业图表 + 详细分析]

用户: 宁德时代最近怎么样？
助手: [查询价格 + 市场分析]

用户: 给我看看特斯拉的K线图
助手: [生成K线图 + 走势分析]
```

### 英文查询

```
用户: Show me AAPL stock price
助手: [显示苹果股价数据]

用户: Plot TSLA candlestick chart
助手: [生成特斯拉K线图]
```

## 股票代码格式

### 美股
直接使用股票代码：
- `AAPL` - 苹果
- `TSLA` - 特斯拉
- `MSFT` - 微软
- `NVDA` - 英伟达

### A股
使用6位数字 + 交易所后缀：
- `300750.SZ` - 宁德时代（深圳）
- `600519.SS` - 贵州茅台（上海）
- `002594.SZ` - 比亚迪

也可以直接使用6位数字，系统会自动添加后缀：
- `300750` → `300750.SZ`
- `600519` → `600519.SS`

### 中文名称
支持常见股票的中文名称：
- `特斯拉` → `TSLA`
- `苹果` → `AAPL`
- `宁德时代` → `300750.SZ`
- `比亚迪` → `002594.SZ`

## 配置说明

### LLM 模式

**启用 LLM 模式** (需要 API Key):
- 智能理解自然语言查询
- 自动调用合适的工具
- 对数据进行深度分析

**直接模式** (无需 API Key):
- 基于正则表达式匹配
- 直接返回数据
- 适合简单查询

### 支持的 LLM 提供商

1. **Dashscope (通义千问)** - 推荐
   ```env
   LLM_PROVIDER=dashscope
   DASHSCOPE_API_KEY=sk-xxx
   DASHSCOPE_MODEL=qwen-max
   ```

2. **OpenAI**
   ```env
   LLM_PROVIDER=openai
   OPENAI_API_KEY=sk-xxx
   OPENAI_MODEL=gpt-4
   ```

3. **DeepSeek**
   ```env
   LLM_PROVIDER=deepseek
   DEEPSEEK_API_KEY=sk-xxx
   DEEPSEEK_MODEL=deepseek-chat
   ```

## 项目结构

```
fin_chatbot/
├── README_zh.md           # 中文文档
├── README.md              # 英文文档
├── config.env.example     # 配置模板
├── config.env             # 实际配置（需自行创建）
├── fin_chatbot.py         # 启动脚本
├── chatbot_agent.yaml     # Agent 配置
├── tools/                 # 工具模块
│   ├── __init__.py
│   ├── stock_tools.py     # 股票查询工具
│   └── chart_tools.py     # 图表生成工具
└── examples/              # 示例代码
```

## 技术栈

- **数据源**: AKShare - 免费、无需 API Key
- **图表**: Plotly - 专业交互式金融图表
- **LLM**: 支持 Dashscope、OpenAI、DeepSeek
- **UI**: Gradio - 简洁易用的 Web 界面

## 常见问题

### Q: 启动时提示 "API key not found"
A: 请确保已创建 `config.env` 文件并填入正确的 API Key

### Q: 中文股票查不到数据
A: 确保股票代码格式正确，A股需要加 `.SZ` 或 `.SS` 后缀

### Q: 图表中文显示乱码
A: 已配置中文字体支持，如仍有问题请安装中文字体

### Q: 可以不用 LLM 吗？
A: 可以，设置 `ENABLE_LLM=false` 即可使用直接模式

## 许可证

与 ms-agent 项目保持一致
