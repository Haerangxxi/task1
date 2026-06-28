import tushare as ts
import pandas as pd
from datetime import datetime, timedelta
import os

# 直接传token，不调用set_token避免写文件
TOKEN = 'aaca426ed7010fd4e2072f0637cf94412dd290ea14c75166d8e51505'
pro = ts.pro_api(TOKEN)

# 北方华创 ts_code
TS_CODE = '002371.SZ'
END_DATE = datetime.now().strftime('%Y%m%d')
START_DATE = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')

print(f"正在获取 {TS_CODE} 从 {START_DATE} 到 {END_DATE} 的数据...")

try:
    # 获取日线行情
    df = pro.daily(ts_code=TS_CODE, start_date=START_DATE, end_date=END_DATE)
    if df is not None and not df.empty:
        print(f"获取到 {len(df)} 条记录")
        print(df.head())
        # 按日期排序（tushare返回是倒序）
        df = df.sort_values('trade_date')
        # 保存到csv
        csv_path = '/Users/haerangxxi/Desktop/task1/beifang_huachuang.csv'
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        print(f"数据已保存到 {csv_path}")
    else:
        print("未获取到数据，可能权限不足")
except Exception as e:
    print(f"获取失败: {e}")
    import traceback
    traceback.print_exc()
