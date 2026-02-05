#!/usr/bin/env python
"""
专门调试胜宏科技的数据不一致问题
"""
from tools import get_stock_price_history, plot_stock_chart, parse_stock_symbol
import json
import base64
import numpy as np

print('='*70)
print('🔍 胜宏科技 (300476.SZ) 数据诊断')
print('='*70)

symbol = '300476.SZ'

# 1. 测试 get_stock_price_history
print('\n1️⃣ 测试 get_stock_price_history')
print('-'*70)
price_result = get_stock_price_history(symbol, period='1mo')
price_data = json.loads(price_result)

if 'error' in price_data:
    print(f'❌ 错误: {price_data["error"]}')
    exit(1)

summary = price_data['summary']
data_points = price_data.get('data', [])

print(f'📊 Summary 数据:')
print(f'   当前价格: ¥{summary["current_price"]}')
print(f'   涨跌: {summary["change"]:+.2f} ({summary["change_percent"]:+.2f}%)')
print(f'   最高: ¥{summary["high"]}')
print(f'   最低: ¥{summary["low"]}')
print(f'   数据点数量: {len(data_points)}')

print(f'\n📅 原始数据的最后5个数据点:')
for point in data_points[-5:]:
    print(f'   {point["date"]}: 开={point["open"]:.2f}, 高={point["high"]:.2f}, 低={point["low"]:.2f}, 收={point["close"]:.2f}')

print(f'\n🔍 Summary 是如何计算的:')
print(f'   current_price = data[-1]["close"] = {data_points[-1]["close"]}')
print(f'   prev_close = data[0]["close"] = {data_points[0]["close"]}')
print(f'   change = current - prev = {data_points[-1]["close"]} - {data_points[0]["close"]} = {data_points[-1]["close"] - data_points[0]["close"]:.2f}')

# 2. 测试 plot_stock_chart
print('\n' + '='*70)
print('2️⃣ 测试 plot_stock_chart')
print('-'*70)
chart_result = plot_stock_chart(symbol, period='1mo', chart_type='line')
chart_data = json.loads(chart_result)

if 'error' in chart_data:
    print(f'❌ 图表错误: {chart_data["error"]}')
    exit(1)

import plotly.io as pio
fig = pio.from_json(json.dumps(chart_data["data"]))

print(f'✅ 图表生成成功')
print(f'Trace 数量: {len(fig.data)}')

# 提取第一个 trace（价格线）
trace = fig.data[0]
print(f'Trace 类型: {type(trace).__name__}')

# 提取收盘价数据
if hasattr(trace, 'y') and trace.y:
    if isinstance(trace.y, dict) and 'bdata' in trace.y:
        # Base64 编码数据
        binary_data = base64.b64decode(trace.y['bdata'])
        y_array = np.frombuffer(binary_data, dtype=trace.y['dtype'])
        print(f'\n📊 图表中的收盘价数据（解码后）:')
        print(f'   数据点数量: {len(y_array)}')
        print(f'   最后5个收盘价: {y_array[-5:]}')
        print(f'   最后一个收盘价: ¥{y_array[-1]:.2f}')
        chart_last_price = y_array[-1]
    else:
        # 普通数组
        y_list = list(trace.y) if hasattr(trace.y, '__iter__') else [trace.y]
        print(f'\n📊 图表中的收盘价数据:')
        print(f'   最后5个收盘价: {y_list[-5:]}')
        print(f'   最后一个收盘价: ¥{y_list[-1]:.2f}')
        chart_last_price = y_list[-1]

# 3. 对比分析
print('\n' + '='*70)
print('3️⃣ 数据一致性对比')
print('-'*70)

summary_current = summary['current_price']
data_last_close = data_points[-1]['close']

print(f'📊 三个数据源对比:')
print(f'   1. summary["current_price"]    = ¥{summary_current:.2f}')
print(f'   2. data[-1]["close"]           = ¥{data_last_close:.2f}')
print(f'   3. 图表中的最后收盘价           = ¥{chart_last_price:.2f}')

if abs(summary_current - data_last_close) > 0.01:
    print(f'\n❌ 问题1: summary 和 data 不一致！差异 {abs(summary_current - data_last_close):.2f}元')
else:
    print(f'\n✅ summary 和 data 一致')

if abs(data_last_close - chart_last_price) > 0.01:
    print(f'❌ 问题2: data 和图表不一致！差异 {abs(data_last_close - chart_last_price):.2f}元')
else:
    print(f'✅ data 和图表一致')

print('\n' + '='*70)
print('🔍 结论')
print('='*70)

if abs(summary_current - chart_last_price) > 0.01:
    print(f'❌ 存在数据不一致！')
    print(f'   工具返回给 LLM 的价格: ¥{summary_current:.2f}')
    print(f'   图表显示的真实价格:   ¥{chart_last_price:.2f}')
    print(f'   差异: ¥{abs(summary_current - chart_last_price):.2f}')
    print(f'\n可能的原因:')
    print(f'   1. get_stock_price_history 和 plot_stock_chart 获取了不同时间范围的数据')
    print(f'   2. summary 计算逻辑有错误')
    print(f'   3. akshare API 返回数据不一致')
else:
    print(f'✅ 所有数据源一致！价格: ¥{summary_current:.2f}')

print('='*70)
