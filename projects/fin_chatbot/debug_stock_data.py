#!/usr/bin/env python
"""
调试脚本：检查股票数据不一致问题
"""
from tools import parse_stock_symbol, get_stock_price_history, plot_stock_chart
import json

print('='*70)
print('📊 股票数据一致性测试')
print('='*70)

# 测试股票名称
query = '比亚迪'
print(f'\n1️⃣ 测试搜索: "{query}"')
symbol = parse_stock_symbol(query)
print(f'   找到的股票代码: {symbol}')

if not symbol:
    print('   ❌ 未找到股票代码')
    exit(1)

print(f'\n2️⃣ 测试 get_stock_price_history("{symbol}")')
print('-'*70)
price_result = get_stock_price_history(symbol, period='1mo')
price_data = json.loads(price_result)

if 'error' in price_data:
    print(f'   ❌ 错误: {price_data["error"]}')
else:
    summary = price_data['summary']
    print(f'   当前价格: ¥{summary["current_price"]}')
    print(f'   涨跌: {summary["change"]:+.2f} ({summary["change_percent"]:+.2f}%)')
    print(f'   最高: ¥{summary["high"]}')
    print(f'   最低: ¥{summary["low"]}')
    print(f'   平均成交量: {summary["avg_volume"]:,}')

    # 打印最后3个交易日的数据
    data_points = price_data.get('data', [])
    print(f'\n   📅 最近3个交易日的收盘价:')
    for point in data_points[-3:]:
        print(f'      {point["date"]}: ¥{point["close"]}')

print(f'\n3️⃣ 测试 plot_stock_chart("{symbol}")')
print('-'*70)
chart_result = plot_stock_chart(symbol, period='1mo', chart_type='candlestick')
chart_data = json.loads(chart_result)

if 'error' in chart_data:
    print(f'   ❌ 图表错误: {chart_data["error"]}')
else:
    print('   ✅ 图表生成成功')

    # 直接检查原始 chart_data 结构
    print(f'\n   🔍 调试：chart_data 的键: {list(chart_data.keys())}')

    # 尝试从 plotly JSON 中提取数据
    import plotly.io as pio
    fig = pio.from_json(json.dumps(chart_data["data"]))

    print(f'   🔍 调试：fig.data 数量: {len(fig.data)}')

    if fig.data:
        trace = fig.data[0]
        print(f'   🔍 调试：trace 类型: {type(trace)}')
        print(f'   🔍 调试：trace 属性: {dir(trace)}')

        # 检查 close 属性
        if hasattr(trace, 'close'):
            print(f'   🔍 调试：trace.close 类型: {type(trace.close)}')

            # 如果是字典，尝试解码 base64 数据
            if isinstance(trace.close, dict):
                print(f'   🔍 调试：trace.close 字典的键: {list(trace.close.keys())}')

                if 'bdata' in trace.close and 'dtype' in trace.close:
                    import base64
                    import numpy as np

                    # 解码 base64 数据
                    bdata = trace.close['bdata']
                    dtype = trace.close['dtype']

                    try:
                        # Base64 解码
                        binary_data = base64.b64decode(bdata)
                        # 转换为 numpy 数组
                        close_array = np.frombuffer(binary_data, dtype=dtype)

                        print(f'   ✅ 成功解码！数据点数量: {len(close_array)}')
                        print(f'   📊 最近3个收盘价: {close_array[-3:]}')
                        print(f'   💰 图表中最后一个收盘价: ¥{close_array[-1]:.2f}')

                        chart_last_price = float(close_array[-1])
                    except Exception as e:
                        print(f'   ❌ 解码失败: {e}')
                        chart_last_price = None
                else:
                    print(f'   🔍 调试：trace.close 完整内容: {trace.close}')
                    chart_last_price = None
            else:
                # 如果是数组/列表（普通情况）
                print(f'   🔍 调试：trace.close 内容（前5个）: {trace.close[:5] if trace.close else None}')

                # 尝试转换为列表
                if trace.close:
                    try:
                        close_list = list(trace.close)
                        print(f'   🔍 调试：转换为列表后的类型: {type(close_list[0]) if close_list else None}')
                        print(f'   🔍 调试：最后3个元素: {close_list[-3:]}')

                        # 如果是数字，显示价格
                        if close_list and isinstance(close_list[-1], (int, float)):
                            print(f'   ✅ 图表中最后一个收盘价: ¥{close_list[-1]:.2f}')
                            chart_last_price = close_list[-1]
                        else:
                            print(f'   ⚠️ close 数据不是数字类型')
                            chart_last_price = None
                    except Exception as e:
                        print(f'   ❌ 转换失败: {e}')
                        chart_last_price = None
                else:
                    chart_last_price = None
        else:
            print('   ⚠️ trace 没有 close 属性')
            chart_last_price = None

print('\n' + '='*70)
print('🔍 数据一致性检查')
print('='*70)

# 对比两个数据源
if 'error' not in price_data and 'error' not in chart_data:
    summary_price = summary["current_price"]

    if 'chart_last_price' in locals() and chart_last_price is not None:
        print(f'get_stock_price_history 返回的当前价格: ¥{summary_price:.2f}')
        print(f'plot_stock_chart 图表中的当前价格:    ¥{chart_last_price:.2f}')

        if abs(summary_price - chart_last_price) < 0.01:
            print('\n✅ 数据一致！')
        else:
            print(f'\n❌ 数据不一致！差异: ¥{abs(summary_price - chart_last_price):.2f}')
            print('\n可能的原因:')
            print('  1. 两个函数调用了不同的 akshare API')
            print('  2. 数据有缓存问题')
            print('  3. 股票代码搜索匹配到了错误的股票')
    else:
        print('⚠️ 无法从图表中提取价格数据，跳过对比')

print('\n' + '='*70)
