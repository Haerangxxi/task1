#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
风险模型 + 未来1个月预测分析
输出：risk_forecast_block.html（嵌入report.html的新模块）
"""

import numpy as np
import pandas as pd
import json, math, requests
from datetime import datetime, timedelta

TOKEN      = 'aaca426ed7010fd4e2072f0637cf94412dd290ea14c75166d8e51505'
TS_CODE    = '002371.SZ'
BENCHMARK  = '000300.SH'
OUTPUT_DIR = '/Users/haerangxxi/Desktop/task1'
CSV_PATH   = f'{OUTPUT_DIR}/beifang_huachuang.csv'
OUT_BLOCK  = f'{OUTPUT_DIR}/risk_forecast_block.html'

# ---------------- read data ----------------
def ts_api(api_name, fields, **params):
    r = requests.post('http://api.tushare.pro',
        json={'api_name': api_name, 'token': TOKEN, 'params': params, 'fields': fields},
        timeout=30, proxies={'http': None, 'https': None})
    data = r.json()
    if data.get('code') != 0:
        print(f'  [Tushare] {api_name} err: code={data["code"]} msg={data["msg"]}')
        return None
    return pd.DataFrame(data['data']['items'], columns=data['data']['fields'])

df = pd.read_csv(CSV_PATH)
df['日期'] = pd.to_datetime(df['日期'])
df = df.sort_values('日期').reset_index(drop=True)

closes = df['收盘'].values
dates  = df['日期'].dt.strftime('%Y-%m-%d').tolist()
daily_ret = np.diff(closes) / closes[:-1]  # 日收益率
n = len(closes)

# ---------------- 1. Risk Metrics ----------------
print('计算风险指标...')

# VaR — historical simulation
var_95 = np.percentile(daily_ret, 5) * 100
var_99 = np.percentile(daily_ret, 1) * 100

# Max Drawdown
peak  = closes[0]
mdd   = 0.0
mdd_start_idx = mdd_end_idx = mdd_peak_idx = 0
for i in range(n):
    if closes[i] > peak:
        peak = closes[i]
        mdd_peak_idx = i
    dd = (peak - closes[i]) / peak
    if dd > mdd:
        mdd = dd
        mdd_start_idx = mdd_peak_idx
        mdd_end_idx = i
mdd_pct = round(mdd * 100, 2)
mdd_start_date = dates[mdd_start_idx]
mdd_end_date   = dates[mdd_end_idx]
mdd_peak_price = round(closes[mdd_start_idx], 2)

# Annualized Volatility
ann_vol = round(np.std(daily_ret) * np.sqrt(252) * 100, 2)
daily_vol = round(np.std(daily_ret) * 100, 2)

# Sharpe Ratio (risk-free 2%)
rf_daily = 0.02 / 252
sharpe = round((np.mean(daily_ret) - rf_daily) / np.std(daily_ret) * np.sqrt(252), 2)

# Sortino Ratio (downside deviation only)
neg_rets = daily_ret[daily_ret < 0]
downside_std = np.std(neg_rets) if len(neg_rets) > 0 else np.std(daily_ret)
sortino = round((np.mean(daily_ret) - rf_daily) / downside_std * np.sqrt(252), 2) if downside_std > 0 else 0

# Calmar Ratio
calmar = round((np.mean(daily_ret) * 252) / mdd, 2) if mdd > 0 else 0

# Win Rate
win_rate = round(np.sum(daily_ret > 0) / len(daily_ret) * 100, 2)

# Average gain/loss
avg_gain = round(np.mean(daily_ret[daily_ret > 0]) * 100, 2) if np.sum(daily_ret > 0) > 0 else 0
avg_loss = round(np.mean(daily_ret[daily_ret < 0]) * 100, 2) if np.sum(daily_ret < 0) > 0 else 0

# Profit/Loss Ratio
pl_ratio = round(abs(avg_gain / avg_loss), 2) if avg_loss != 0 else 0

# ---------------- 2. Fetch Benchmark (CSI 300) for Beta ----------------
print('获取沪深300基准数据...')
try:
    df_bm = ts_api('daily', 'ts_code,trade_date,close',
                   ts_code=BENCHMARK,
                   start_date=dates[0].replace('-',''), end_date=dates[-1].replace('-',''))
    if df_bm is not None:
        df_bm['trade_date'] = pd.to_datetime(df_bm['trade_date'], format='%Y%m%d')
        df_bm = df_bm.sort_values('trade_date').reset_index(drop=True)
        df_bm['close'] = df_bm['close'].astype(float)
        bm_rets = np.diff(df_bm['close'].values) / df_bm['close'].values[:-1]
        # align lengths
        min_len = min(len(daily_ret), len(bm_rets))
        aligned_ret = daily_ret[-min_len:]
        aligned_bm   = bm_rets[-min_len:]
        cov_matrix = np.cov(aligned_ret, aligned_bm)
        beta = round(cov_matrix[0][1] / cov_matrix[1][1], 2)
        corr = round(np.corrcoef(aligned_ret, aligned_bm)[0][1], 2)
    else:
        beta = None; corr = None
except Exception as e:
    print(f'基准数据获取失败: {e}')
    beta = None; corr = None

# ---------------- 3. Technical Indicators + Prediction ----------------
print('计算技术指标与预测模型...')

# MA
def rolling_ma(data, window):
    return np.array([np.nan if i < window-1 else np.mean(data[i-window+1:i+1]) for i in range(len(data))])

ma5_arr  = rolling_ma(closes, 5)
ma10_arr = rolling_ma(closes, 10)
ma20_arr = rolling_ma(closes, 20)
ma60_arr = rolling_ma(closes, 60)

# RSI (14)
def calc_rsi(prices, period=14):
    deltas = np.diff(prices)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    avg_gain = np.convolve(gains, np.ones(period)/period, mode='full')[:len(gains)]
    avg_loss = np.convolve(losses, np.ones(period)/period, mode='full')[:len(gains)]
    # Use Wilder smoothing for subsequent values
    for i in range(period, len(gains)):
        avg_gain[i] = (avg_gain[i-1] * (period-1) + gains[i]) / period
        avg_loss[i] = (avg_loss[i-1] * (period-1) + losses[i]) / period
    rs = np.where(avg_loss == 0, 100, avg_gain / avg_loss)
    rsi = 100 - (100 / (1 + rs))
    return np.concatenate([[np.nan], rsi])

rsi_arr = calc_rsi(closes, 14)

# MACD
def calc_macd(prices, fast=12, slow=26, signal=9):
    def ema(data, period):
        result = np.zeros_like(data)
        result[:period] = np.nan
        result[period-1] = np.mean(data[:period])
        multiplier = 2 / (period + 1)
        for i in range(period, len(data)):
            result[i] = (data[i] - result[i-1]) * multiplier + result[i-1]
        return result
    
    ema_fast = ema(prices, fast)
    ema_slow = ema(prices, slow)
    dif = ema_fast - ema_slow
    dea = ema(dif, signal)
    macd_bar = 2 * (dif - dea)
    return dif, dea, macd_bar

dif_arr, dea_arr, macd_bar_arr = calc_macd(closes)

# Bollinger Bands (20)
bb_ma = rolling_ma(closes, 20)
bb_std = np.array([np.nan if i < 19 else np.std(closes[i-19:i+1], ddof=1) for i in range(len(closes))])
bb_upper = bb_ma + 2 * bb_std
bb_lower = bb_ma - 2 * bb_std

# Current technical signals
last_close = closes[-1]
rsi_now    = rsi_arr[-1]
dif_now    = dif_arr[-1]
dea_now    = dea_arr[-1]
macd_now   = macd_bar_arr[-1]
ma5_now    = ma5_arr[-1]
ma10_now   = ma10_arr[-1]
ma20_now   = ma20_arr[-1]
ma60_now   = ma60_arr[-1] if not np.isnan(ma60_arr[-1]) else None
bb_upper_n = bb_upper[-1]
bb_lower_n = bb_lower[-1]
bb_ma_n    = bb_ma[-1]

# Signal synthesis
signals = []
# RSI
if rsi_now > 70:    signals.append(('RSI超买', 'bearish'))
elif rsi_now < 30:  signals.append(('RSI超卖', 'bullish'))
elif rsi_now > 50:  signals.append(('RSI偏强', 'neutral_bull'))
else:               signals.append(('RSI偏弱', 'neutral_bear'))

# MACD
if dif_now > dea_now and macd_now > 0:         signals.append(('MACD金叉上零轴', 'bullish'))
elif dif_now > dea_now and macd_now < 0:        signals.append(('MACD金叉', 'neutral_bull'))
elif dif_now < dea_now and macd_now < 0:        signals.append(('MACD死叉下零轴', 'bearish'))
elif dif_now < dea_now and macd_now > 0:        signals.append(('MACD死叉', 'neutral_bear'))
else:                                           signals.append(('MACD平盘', 'neutral'))

# MA
if ma5_now > ma10_now > ma20_now:              signals.append(('均线多头排列', 'bullish'))
elif ma5_now < ma10_now < ma20_now:            signals.append(('均线空头排列', 'bearish'))
elif last_close > ma20_now:                    signals.append(('站上MA20', 'neutral_bull'))
else:                                          signals.append(('跌破MA20', 'neutral_bear'))

# Bollinger
if last_close > bb_upper_n:                    signals.append(('突破布林上轨(强势)', 'bullish'))
elif last_close < bb_lower_n:                  signals.append(('跌破布林下轨(超跌)', 'neutral_bull'))
elif last_close > bb_ma_n:                     signals.append(('布林中轨之上', 'neutral_bull'))
else:                                          signals.append(('布林中轨之下', 'neutral_bear'))

# Overall bias
bullish_cnt = sum(1 for _, d in signals if d == 'bullish')
bearish_cnt = sum(1 for _, d in signals if d == 'bearish')
if bullish_cnt > bearish_cnt:  overall_bias = '偏多'
elif bearish_cnt > bullish_cnt: overall_bias = '偏空'
else:                           overall_bias = '中性震荡'

# ---------------- 4. Linear Regression Trend Extrapolation ----------------
# Last 60 trading days for trend fitting
lookback = min(60, n)
x = np.arange(lookback)
y = closes[-lookback:]
coeff = np.polyfit(x, y, 1)
trend_slope = coeff[0] * lookback / closes[-1] * 100  # slope as % of price over period
trend_daily = coeff[0]  # per-day price change

# ---------------- 5. Monte Carlo Simulation ----------------
print('运行蒙特卡洛模拟 (10000次)...')
mc_days = 20  # 1 month ~ 20 trading days
mc_sims = 10000
mu  = np.mean(daily_ret)
sigma = np.std(daily_ret)
np.random.seed(42)
mc_paths = np.zeros((mc_sims, mc_days))
mc_paths[:, 0] = last_close

for i in range(1, mc_days):
    mc_paths[:, i] = mc_paths[:, i-1] * np.exp(
        (mu - 0.5 * sigma**2) + sigma * np.random.randn(mc_sims)
    )

mc_final = mc_paths[:, -1]
mc_mean = np.mean(mc_final)
mc_p10  = np.percentile(mc_final, 10)
mc_p25  = np.percentile(mc_final, 25)
mc_p50  = np.percentile(mc_final, 50)
mc_p75  = np.percentile(mc_final, 75)
mc_p90  = np.percentile(mc_final, 90)

# Probability of being above current price
prob_up = round(np.mean(mc_final > last_close) * 100, 1)

# Confidence intervals for chart — use percentiles of all paths at each day
mc_p10_series = np.percentile(mc_paths, 10, axis=0).tolist()
mc_p25_series = np.percentile(mc_paths, 25, axis=0).tolist()
mc_p50_series = np.percentile(mc_paths, 50, axis=0).tolist()
mc_p75_series = np.percentile(mc_paths, 75, axis=0).tolist()
mc_p90_series = np.percentile(mc_paths, 90, axis=0).tolist()

# Linear trend prediction
trend_series = [last_close + trend_daily * i for i in range(mc_days)]
trend_series = [round(v, 2) for v in trend_series]

# ---------------- 6. Low-risk / High-risk scenario ----------------
# Low: mu - sigma*1.28 (80th percentile worst case)
low_scenario = [round(last_close * np.exp((mu - 0.5*sigma**2) * i - 1.28*sigma*np.sqrt(i)), 2) for i in range(mc_days)]
high_scenario = [round(last_close * np.exp((mu - 0.5*sigma**2) * i + 1.28*sigma*np.sqrt(i)), 2) for i in range(mc_days)]

# Today's last date
last_date_str = dates[-1]

# ---------------- 7. Compute daily return data for chart ----------------
ret_pct  = (np.diff(closes) / closes[:-1] * 100).tolist()
ret_dates = dates[1:]

# ---------------- 8. Export everything as JSON + HTML ----------------
print('生成风险/预测HTML模块...')

# Prepare JS data
data_js = {
    'dates': dates,
    'closes': [round(c, 2) for c in closes.tolist()],
    'ret_pct': [round(r, 4) for r in ret_pct],
    'ret_dates': ret_dates,
    'ma5': [round(v, 2) if not np.isnan(v) else None for v in ma5_arr.tolist()],
    'ma10': [round(v, 2) if not np.isnan(v) else None for v in ma10_arr.tolist()],
    'ma20': [round(v, 2) if not np.isnan(v) else None for v in ma20_arr.tolist()],
    'ma60': [round(v, 2) if not np.isnan(v) else None for v in ma60_arr.tolist()],
    'rsi': [round(v, 2) if not np.isnan(v) else None for v in rsi_arr.tolist()],
    'dif': [round(v, 4) if not np.isnan(v) else None for v in dif_arr.tolist()],
    'dea': [round(v, 4) if not np.isnan(v) else None for v in dea_arr.tolist()],
    'macd_bar': [round(v, 4) if not np.isnan(v) else None for v in macd_bar_arr.tolist()],
    'bb_upper': [round(v, 2) if not np.isnan(v) else None for v in bb_upper.tolist()],
    'bb_lower': [round(v, 2) if not np.isnan(v) else None for v in bb_lower.tolist()],
    'bb_ma': [round(v, 2) if not np.isnan(v) else None for v in bb_ma.tolist()],
    'mc_p10': [round(v, 2) for v in mc_p10_series],
    'mc_p25': [round(v, 2) for v in mc_p25_series],
    'mc_p50': [round(v, 2) for v in mc_p50_series],
    'mc_p75': [round(v, 2) for v in mc_p75_series],
    'mc_p90': [round(v, 2) for v in mc_p90_series],
    'trend_series': trend_series,
    'low_scenario': low_scenario,
    'high_scenario': high_scenario,
    'last_date_str': last_date_str,
    'forecast_days': mc_days,
}

# Compute probability buckets for MC distribution chart
buckets = np.linspace(mc_p10, mc_p90, 16)
hist_counts, hist_edges = np.histogram(mc_final, bins=15)
hist_data = {
    'edges': [round(e, 2) for e in hist_edges.tolist()],
    'counts': hist_counts.tolist(),
}

# Compute DD series for chart
dd_series = []
peak_val = closes[0]
for i in range(n):
    if closes[i] > peak_val:
        peak_val = closes[i]
    dd_series.append(round((peak_val - closes[i]) / peak_val * 100, 2))

hist_data['drawdown_series'] = dd_series

html = f'''<!-- ====== 风险模型 & 股价预测 ====== -->
<section class="section" id="risk">
<div class="section-header"><span class="section-icon">🛡️</span> 风险模型</div>
<div class="risk-grid">
    <div class="risk-card">
        <div class="risk-label">日波动率</div>
        <div class="risk-value">{daily_vol}%</div>
        <div class="risk-sub">年化 {ann_vol}%</div>
    </div>
    <div class="risk-card">
        <div class="risk-label">VaR (95%)</div>
        <div class="risk-value var-neg">{var_95:.2f}%</div>
        <div class="risk-sub">单日最大损失置信</div>
    </div>
    <div class="risk-card">
        <div class="risk-label">VaR (99%)</div>
        <div class="risk-value var-neg">{var_99:.2f}%</div>
        <div class="risk-sub">极端单日损失置信</div>
    </div>
    <div class="risk-card">
        <div class="risk-label">最大回撤</div>
        <div class="risk-value var-neg">-{mdd_pct}%</div>
        <div class="risk-sub">{mdd_start_date} → {mdd_end_date}</div>
    </div>
    <div class="risk-card">
        <div class="risk-label">夏普比率</div>
        <div class="risk-value">{sharpe}</div>
        <div class="risk-sub">（无风险利率2%）</div>
    </div>
    <div class="risk-card">
        <div class="risk-label">索提诺比率</div>
        <div class="risk-value">{sortino}</div>
        <div class="risk-sub">只计下行波动</div>
    </div>
    <div class="risk-card">
        <div class="risk-label">卡玛比率</div>
        <div class="risk-value">{calmar}</div>
        <div class="risk-sub">收益/最大回撤</div>
    </div>
    <div class="risk-card">
        <div class="risk-label">胜率</div>
        <div class="risk-value">{win_rate}%</div>
        <div class="risk-sub">日均涨{avg_gain}% 跌{avg_loss}%</div>
    </div>
</div>
<div class="risk-sub-grid">
    <div class="risk-card risk-card-sm">
        <div class="risk-label">盈亏比</div>
        <div class="risk-value">{pl_ratio}</div>
    </div>
    <div class="risk-card risk-card-sm">
        <div class="risk-label">Beta (vs 沪深300)</div>
        <div class="risk-value">{"{:.2f}".format(beta) if beta is not None else '-'}</div>
    </div>
    <div class="risk-card risk-card-sm">
        <div class="risk-label">相关系数</div>
        <div class="risk-value">{"{:.2f}".format(corr) if corr is not None else '-'}</div>
    </div>
    <div class="risk-card risk-card-sm">
        <div class="risk-label">盈亏比</div>
        <div class="risk-value">{pl_ratio}</div>
    </div>
</div>

<!-- 回撤曲线 -->
<div class="chart-card wide">
    <h3 class="chart-title">📉 历史回撤曲线</h3>
    <div class="chart-wrap" id="chart_drawdown" style="height:240px"></div>
</div>

</section>

<section class="section" id="technicals">
<div class="section-header"><span class="section-icon">📊</span> 技术指标</div>
<div class="charts-row">
    <div class="chart-card half">
        <h3 class="chart-title">RSI（14日）</h3>
        <div class="chart-wrap" id="chart_rsi" style="height:200px"></div>
        <div class="signal-summary">
            <strong>当前RSI：{rsi_now:.1f}</strong>
            <span class="tag tag-{'bearish' if rsi_now>70 else 'bullish' if rsi_now<30 else 'neutral'}">
                {'超买' if rsi_now>70 else '超卖' if rsi_now<30 else '中性' if 40<=rsi_now<=60 else ('偏强' if rsi_now>50 else '偏弱')}
            </span>
        </div>
    </div>
    <div class="chart-card half">
        <h3 class="chart-title">MACD</h3>
        <div class="chart-wrap" id="chart_macd" style="height:200px"></div>
        <div class="signal-summary">
            <strong>DIF={dif_now:.2f} DEA={dea_now:.2f} BAR={macd_now:.2f}</strong>
            <span class="tag tag-{'bullish' if dif_now>dea_now else 'bearish'}">
                {'金叉' if dif_now>dea_now else '死叉'}
            </span>
        </div>
    </div>
</div>

<!-- 布林带 -->
<div class="chart-card wide">
    <h3 class="chart-title">📐 布林带（20日，2σ）</h3>
    <div class="chart-wrap" id="chart_bollinger" style="height:360px"></div>
    <div class="signal-summary">
        <strong>上轨：{bb_upper_n:.2f} | 中轨：{bb_ma_n:.2f} | 下轨：{bb_lower_n:.2f} | 收盘：{last_close:.2f}</strong>
        <span class="tag tag-{'bullish' if last_close>bb_upper_n else 'neutral_bear' if last_close<bb_lower_n else 'neutral'}">
            {'突破上轨' if last_close>bb_upper_n else '跌破下轨' if last_close<bb_lower_n else '轨内运行'}
        </span>
    </div>
</div>

<!-- 综合信号 -->
<div class="chart-card wide">
    <h3 class="chart-title">🔔 综合技术信号研判</h3>
    <div class="signal-panel">
        <div class="signal-list">
            {''.join(f'<span class="signal-item signal-{direction}">{name}</span>' for name, direction in signals)}
        </div>
        <div class="signal-verdict">
            综合研判：<strong>{overall_bias}</strong>
            <span style="margin-left:8px">（多头信号{bullish_cnt} vs 空头信号{bearish_cnt}）</span>
        </div>
    </div>
</div>
</section>

<section class="section" id="forecast">
<div class="section-header"><span class="section-icon">🔮</span> 未来1个月股价预测</div>

<!-- 预测总览卡片 -->
<div class="forecast-grid">
    <div class="forecast-card forecast-up">
        <div class="forecast-label">上涨概率（MC模拟）</div>
        <div class="forecast-value">{prob_up}%</div>
        <div class="forecast-sub">10000次蒙特卡洛</div>
    </div>
    <div class="forecast-card">
        <div class="forecast-label">预测中位数（20天后）</div>
        <div class="forecast-value">{mc_p50:.2f}</div>
        <div class="forecast-sub">较当前{'+' if mc_p50>last_close else ''}{((mc_p50-last_close)/last_close*100):.2f}%</div>
    </div>
    <div class="forecast-card">
        <div class="forecast-label">80%置信区间</div>
        <div class="forecast-value">{mc_p10:.2f} ~ {mc_p90:.2f}</div>
        <div class="forecast-sub">P10-P90范围</div>
    </div>
    <div class="forecast-card">
        <div class="forecast-label">趋势外推目标价</div>
        <div class="forecast-value">{trend_series[-1]:.2f}</div>
        <div class="forecast-sub">近60日线性拟合</div>
    </div>
</div>

<!-- 蒙特卡洛模拟曲线 -->
<div class="chart-card wide">
    <h3 class="chart-title">🎲 蒙特卡洛模拟（20个交易日，10000次）</h3>
    <div class="chart-wrap" id="chart_montecarlo" style="height:380px"></div>
</div>

<!-- 分布直方图 -->
<div class="charts-row">
    <div class="chart-card half">
        <h3 class="chart-title">📊 终值概率分布（20日后）</h3>
        <div class="chart-wrap" id="chart_histogram" style="height:240px"></div>
    </div>
    <div class="chart-card half">
        <h3 class="chart-title">📋 情景分析</h3>
        <table class="scenario-table">
            <tr><th>情景</th><th>概率</th><th>20日后价格</th><th>涨跌幅</th></tr>
            <tr class="scenario-bull"><td>📈 乐观</td><td>25%</td><td>{mc_p75:.2f}</td><td class="up">+{((mc_p75-last_close)/last_close*100):.2f}%</td></tr>
            <tr class="scenario-neutral"><td>📊 基准</td><td>50%</td><td>{mc_p50:.2f}</td><td class="{'up' if mc_p50>last_close else 'down'}">{'+' if mc_p50>last_close else ''}{((mc_p50-last_close)/last_close*100):.2f}%</td></tr>
            <tr class="scenario-bear"><td>📉 悲观</td><td>25%</td><td>{mc_p25:.2f}</td><td class="down">{((mc_p25-last_close)/last_close*100):.2f}%</td></tr>
            <tr class="scenario-extreme"><td>⚠️ 极端</td><td>10%</td><td>{mc_p10:.2f}</td><td class="down">{((mc_p10-last_close)/last_close*100):.2f}%</td></tr>
        </table>
    </div>
</div>

<!-- ⚠️ 免责声明 -->
<div class="disclaimer-block">
    <p>⚠️ <strong>免责声明：</strong>以上预测基于历史数据的统计模型（蒙特卡洛模拟、线性回归、技术指标），仅供研究参考，不构成任何投资建议。股市有风险，投资需谨慎。实际走势可能因政策变化、市场情绪、公司基本面变化等因素与预测结果存在重大差异。</p>
</div>
</section>

<script>
(function() {{
    // Build prediction dates
    var lastDate = new Date('{last_date_str}');
    var predDates = [];
    var d = new Date(lastDate);
    for (var i = 0; i < {mc_days}; i++) {{
        d.setDate(d.getDate() + 1);
        while (d.getDay() === 0 || d.getDay() === 6) d.setDate(d.getDate() + 1);
        predDates.push(d.toISOString().slice(0,10));
    }}

    // ---- Drawdown Chart ----
    (function() {{
        var chart = echarts.init(document.getElementById('chart_drawdown'));
        var ddData = {json.dumps(dd_series)};
        var ddDates = {json.dumps(dates)};
        chart.setOption({{
            tooltip: {{ trigger: 'axis', formatter: function(p) {{ return p[0].axisValue + '<br/>回撤: ' + (-p[0].value).toFixed(2) + '%'; }} }},
            grid: {{ left: 60, right: 20, top: 15, bottom: 30 }},
            xAxis: {{ type: 'category', data: ddDates, axisLabel: {{ formatter: function(v) {{ return v.slice(5); }} }} }},
            yAxis: {{ type: 'value', axisLabel: {{ formatter: function(v) {{ return -v.toFixed(0) + '%'; }} }}, max: 0, inverse: true }},
            series: [{{
                type: 'line', data: ddData, smooth: true, lineStyle: {{ color: '#ef4444', width: 2 }},
                areaStyle: {{ color: new echarts.graphic.LinearGradient(0,0,0,1,[{{offset:0,color:'rgba(239,68,68,0.3)'}},{{offset:1,color:'rgba(239,68,68,0.02)'}}]) }},
                itemStyle: {{ color: '#ef4444' }}
            }}]
        }});
    }})();

    // ---- RSI Chart ----
    (function() {{
        var chart = echarts.init(document.getElementById('chart_rsi'));
        var rsiData  = {json.dumps([round(v, 2) if v and not np.isnan(v) else None for v in rsi_arr.tolist()])};
        var allDates = {json.dumps(dates)};
        chart.setOption({{
            tooltip: {{ trigger: 'axis', formatter: function(p) {{ return p[0].axisValue + '<br/>RSI: ' + p[0].value.toFixed(2); }} }},
            grid: {{ left: 60, right: 20, top: 15, bottom: 30 }},
            xAxis: {{ type: 'category', data: allDates.slice(-120), axisLabel: {{ formatter: function(v) {{ return v.slice(5); }} }} }},
            yAxis: {{ type: 'value', min: 0, max: 100 }},
            series: [{{
                type: 'line', data: rsiData.slice(-120), smooth: true, lineStyle: {{ color: '#6366f1', width: 2 }},
                areaStyle: {{ color: new echarts.graphic.LinearGradient(0,0,0,1,[{{offset:0,color:'rgba(99,102,241,0.2)'}},{{offset:1,color:'rgba(99,102,241,0)'}}]) }},
                markLine: {{ silent: true, data: [{{ yAxis: 70, lineStyle: {{ color: '#ef4444', type: 'dashed' }} }}, {{ yAxis: 30, lineStyle: {{ color: '#22c55e', type: 'dashed' }} }}] }}
            }}]
        }});
    }})();

    // ---- MACD Chart ----
    (function() {{
        var chart = echarts.init(document.getElementById('chart_macd'));
        var difData = {json.dumps([round(v, 4) if v and not np.isnan(float(v)) else None for v in dif_arr[-120:].tolist()])};
        var deaData = {json.dumps([round(v, 4) if v and not np.isnan(float(v)) else None for v in dea_arr[-120:].tolist()])};
        var macdData = {json.dumps([round(v, 4) if v and not np.isnan(float(v)) else None for v in macd_bar_arr[-120:].tolist()])};
        var allDates = {json.dumps(dates)};
        chart.setOption({{
            tooltip: {{ trigger: 'axis' }},
            grid: {{ left: 60, right: 20, top: 15, bottom: 30 }},
            xAxis: {{ type: 'category', data: allDates.slice(-120), axisLabel: {{ formatter: function(v) {{ return v.slice(5); }} }} }},
            yAxis: {{ type: 'value' }},
            series: [
                {{ type: 'bar', data: macdData, name: 'MACD柱',
                    itemStyle: {{ color: function(p) {{ return p.value >= 0 ? '#ef4444' : '#22c55e'; }} }} }},
                {{ type: 'line', data: difData, name: 'DIF', lineStyle: {{ color: '#6366f1', width: 1.5 }}, symbol: 'none' }},
                {{ type: 'line', data: deaData, name: 'DEA', lineStyle: {{ color: '#f59e0b', width: 1.5 }}, symbol: 'none' }}
            ]
        }});
    }})();

    // ---- Bollinger Chart ----
    (function() {{
        var chart = echarts.init(document.getElementById('chart_bollinger'));
        var dates = {json.dumps(dates)};
        var closes = {json.dumps([round(c, 2) for c in closes.tolist()])};
        var bbU = {json.dumps([round(v, 2) if v and not np.isnan(float(v)) else None for v in bb_upper[-120:].tolist()])};
        var bbL = {json.dumps([round(v, 2) if v and not np.isnan(float(v)) else None for v in bb_lower[-120:].tolist()])};
        var bbM = {json.dumps([round(v, 2) if v and not np.isnan(float(v)) else None for v in bb_ma[-120:].tolist()])};
        chart.setOption({{
            tooltip: {{ trigger: 'axis' }},
            grid: {{ left: 70, right: 20, top: 15, bottom: 30 }},
            xAxis: {{ type: 'category', data: dates.slice(-120), axisLabel: {{ formatter: function(v) {{ return v.slice(5); }} }} }},
            yAxis: {{ type: 'value', axisLabel: {{ formatter: '¥{{value}}' }} }},
            series: [
                {{ type: 'line', data: closes.slice(-120), name: '收盘价', lineStyle: {{ color: '#6366f1', width: 2 }}, symbol: 'none' }},
                {{ type: 'line', data: bbU, name: '上轨', lineStyle: {{ color: '#ef4444', width: 1, type: 'dashed' }}, symbol: 'none', itemStyle: {{ color: '#ef4444' }} }},
                {{ type: 'line', data: bbM, name: '中轨(MA20)', lineStyle: {{ color: '#f59e0b', width: 1, type: 'dashed' }}, symbol: 'none' }},
                {{ type: 'line', data: bbL, name: '下轨', lineStyle: {{ color: '#22c55e', width: 1, type: 'dashed' }}, symbol: 'none' }}
            ]
        }});
    }})();

    // ---- Monte Carlo Chart ----
    (function() {{
        var chart = echarts.init(document.getElementById('chart_montecarlo'));
        var p10 = {json.dumps([round(v, 2) for v in mc_p10_series])};
        var p25 = {json.dumps([round(v, 2) for v in mc_p25_series])};
        var p50 = {json.dumps([round(v, 2) for v in mc_p50_series])};
        var p75 = {json.dumps([round(v, 2) for v in mc_p75_series])};
        var p90 = {json.dumps([round(v, 2) for v in mc_p90_series])};
        var trend = {json.dumps(trend_series)};
        var low = {json.dumps(low_scenario)};
        var high = {json.dumps(high_scenario)};
        var curPrice = {last_close};
        chart.setOption({{
            tooltip: {{ trigger: 'axis' }},
            legend: {{ data: ['P10-P90区间','P25-P75区间','P50中位数','线性趋势','当前价'], bottom: 0 }},
            grid: {{ left: 70, right: 50, top: 20, bottom: 40 }},
            xAxis: {{ type: 'category', data: predDates, axisLabel: {{ formatter: function(v) {{ return v.slice(5); }} }} }},
            yAxis: {{ type: 'value', axisLabel: {{ formatter: '¥{{value}}' }} }},
            series: [
                {{ name: 'P10-P90区间', type: 'line', data: p90, lineStyle: {{ color: 'rgba(99,102,241,0.05)', width: 0.5 }},
                    areaStyle: {{ color: 'rgba(99,102,241,0.05)' }}, stack: 'a', symbol: 'none',
                    tooltip: {{ show: false }} }},
                {{ name: 'P10', type: 'line', data: p10, lineStyle: {{ color: 'rgba(99,102,241,0.15)', width: 1, type: 'dashed' }},
                    areaStyle: {{ color: 'rgba(99,102,241,0.05)' }}, stack: 'b', symbol: 'none' }},
                {{ name: 'P25-P75区间', type: 'line', data: p75, lineStyle: {{ color: 'rgba(99,102,241,0.08)', width: 0.5 }},
                    areaStyle: {{ color: 'rgba(99,102,241,0.1)' }}, stack: 'c', symbol: 'none',
                    tooltip: {{ show: false }} }},
                {{ name: 'P25', type: 'line', data: p25, lineStyle: {{ color: 'rgba(99,102,241,0.2)', width: 1, type: 'dashed' }},
                    areaStyle: {{ color: 'rgba(99,102,241,0.1)' }}, stack: 'd', symbol: 'none' }},
                {{ name: 'P50中位数', type: 'line', data: p50, lineStyle: {{ color: '#6366f1', width: 2.5 }}, symbol: 'none' }},
                {{ name: '线性趋势', type: 'line', data: trend, lineStyle: {{ color: '#f59e0b', width: 2, type: 'dashed' }}, symbol: 'none' }},
                {{ name: '当前价', type: 'line', data: Array(predDates.length).fill(curPrice), lineStyle: {{ color: '#94a3b8', width: 1, type: 'dotted' }}, symbol: 'none' }}
            ]
        }});
    }})();

    // ---- Histogram ----
    (function() {{
        var chart = echarts.init(document.getElementById('chart_histogram'));
        var edges = {json.dumps(hist_data['edges'])};
        var counts = {json.dumps(hist_data['counts'])};
        var curPrice = {last_close};
        // build x-axis bins
        var bins = [];
        for (var i = 0; i < edges.length - 1; i++) {{
            bins.push(edges[i].toFixed(0) + '-' + edges[i+1].toFixed(0));
        }}
        chart.setOption({{
            tooltip: {{ trigger: 'axis' }},
            grid: {{ left: 60, right: 20, top: 15, bottom: 40 }},
            xAxis: {{ type: 'category', data: bins, axisLabel: {{ rotate: 45, fontSize: 10 }} }},
            yAxis: {{ type: 'value', name: '频次' }},
            series: [{{
                type: 'bar', data: counts,
                itemStyle: {{ color: function(p) {{
                    var binMid = (edges[p.dataIndex] + edges[p.dataIndex+1]) / 2;
                    return binMid > curPrice ? '#ef4444' : '#22c55e';
                }} }},
                markLine: {{ silent: true, data: [{{ xAxis: bins.length/2, name: '当前价', lineStyle: {{ color: '#6366f1', type: 'dashed', width: 2 }} }}] }}
            }}]
        }});
    }})();
}})();
</script>
'''

with open(OUT_BLOCK, 'w', encoding='utf-8') as f:
    f.write(html)

print(f'\n✅ 风险模型 & 预测 HTML block 已生成: {OUT_BLOCK}')
print(f'   生成大小: {len(html)} 字符')
