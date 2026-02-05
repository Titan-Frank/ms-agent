#!/usr/bin/env python
"""
测试实际的工具调用流程 - 模拟 LLM 调用
"""
import sys
sys.path.insert(0, '/Users/titan-frank/Documents/hsd/research/MY/ms-agent/projects/fin_chatbot')

from chatbot.tools_handler import get_stock_data
import json

print('='*70)
print('🔧 模拟 LLM 调用工具')
print('='*70)

# 模拟 LLM 调用 get_stock_data 工具
symbol = '300476.SZ'
period = '1mo'
chart_type = 'line'

print(f'\n调用: get_stock_data("{symbol}", period="{period}", chart_type="{chart_type}")')
print('-'*70)

result_json, plotly_fig = get_stock_data(symbol, period, chart_type)

print('\n📊 返回给 LLM 的 JSON 数据:')
print(result_json)

print('\n🔍 解析数据:')
data = json.loads(result_json)
for key, value in data.items():
    print(f'  {key}: {value}')

print('\n📈 Plotly 图表:', '✅ 已生成' if plotly_fig else '❌ 未生成')

print('\n' + '='*70)
print('🎯 结论')
print('='*70)

if 'error' in data:
    print(f'❌ 工具返回错误: {data["error"]}')
elif data.get('current_price'):
    print(f'✅ 工具返回的价格: ¥{data["current_price"]}')
    print(f'   (这就是 LLM 看到的数据)')
else:
    print(f'⚠️ 返回数据中没有 current_price')

print('='*70)
