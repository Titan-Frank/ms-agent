#!/usr/bin/env python
"""
诊断股票对比图表的数据问题
"""
import sys
sys.path.insert(0, '/Users/titan-frank/Documents/hsd/research/MY/ms-agent/projects/fin_chatbot')

from tools import get_stock_price_history
import json

print('='*70)
print('📊 诊断股票对比数据')
print('='*70)

symbols = ['002594.SZ', '300750.SZ']  # 比亚迪、宁德时代
period = '1y'  # 使用1年数据来查看问题

for symbol in symbols:
    print(f'\n{"="*70}')
    print(f'股票: {symbol}')
    print('='*70)

    result = get_stock_price_history(symbol, period=period)
    data = json.loads(result)

    if 'error' in data:
        print(f'❌ 错误: {data["error"]}')
        continue

    data_points = data['data']
    print(f'数据点数量: {len(data_points)}')
    print(f'起始日期: {data_points[0]["date"]}')
    print(f'结束日期: {data_points[-1]["date"]}')
    print(f'起始收盘价: {data_points[0]["close"]:.2f}')
    print(f'结束收盘价: {data_points[-1]["close"]:.2f}')

    # 检查是否有异常的跳跃
    print(f'\n检查价格跳跃:')
    for i in range(1, len(data_points)):
        prev_close = data_points[i-1]['close']
        curr_close = data_points[i]['close']
        change_pct = ((curr_close - prev_close) / prev_close) * 100

        if abs(change_pct) > 15:  # 单日涨跌超过15%
            print(f'  ⚠️ {data_points[i]["date"]}: {prev_close:.2f} → {curr_close:.2f} ({change_pct:+.2f}%)')

    # 显示归一化后的涨跌幅
    print(f'\n归一化涨跌幅计算:')
    start_price = data_points[0]['close']
    print(f'  基准价格（第一天收盘价）: {start_price:.2f}')

    # 显示最后5个交易日的归一化涨跌幅
    print(f'  最后5个交易日的归一化涨跌:')
    for point in data_points[-5:]:
        pct_change = ((point['close'] - start_price) / start_price) * 100
        print(f'    {point["date"]}: {point["close"]:.2f} → {pct_change:+.2f}%')

print('\n' + '='*70)
print('🔍 总结')
print('='*70)
print('如果两只股票的起始日期不同，归一化对比会有问题！')
print('='*70)
