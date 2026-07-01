#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成北方华创综合决策报告 HTML
包含：公司简介、核心财务、K线行情、行业趋势、近期新闻动态
"""

import requests, json, pandas as pd
from datetime import datetime, timedelta
import os

TOKEN      = 'aaca426ed7010fd4e2072f0637cf94412dd290ea14c75166d8e51505'
TS_CODE    = '002371.SZ'
OUTPUT_DIR = '/Users/haerangxxi/Desktop/task1'
OUTPUT     = os.path.join(OUTPUT_DIR, 'report.html')
END_DATE   = datetime.now().strftime('%Y%m%d')
START_DATE = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')

def ts_api(api_name, fields, **params):
    r = requests.post('http://api.tushare.pro',
        json={'api_name': api_name, 'token': TOKEN, 'params': params, 'fields': fields},
        timeout=30, proxies={'http': None, 'https': None})
    data = r.json()
    if data.get('code') != 0:
        return None
    return pd.DataFrame(data['data']['items'], columns=data['data']['fields'])

print('获取行情数据...')
df = ts_api('daily', 'ts_code,trade_date,open,high,low,close,vol,amount',
            ts_code=TS_CODE, start_date=START_DATE, end_date=END_DATE)
df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')
df = df.sort_values('trade_date').reset_index(drop=True)
for c in ['open','high','low','close']: df[c] = df[c].astype(float)
df['vol'] = df['vol'].astype(float).astype(int)

dates  = df['trade_date'].dt.strftime('%Y-%m-%d').tolist()
opens  = df['open'].tolist()
closes = df['close'].tolist()
highs  = df['high'].tolist()
lows   = df['low'].tolist()
vols   = df['vol'].tolist()

def ma(data, n):
    return [round(sum(data[i-n+1:i+1])/n,2) if i>=n-1 else None for i in range(len(data))]

ma5=ma(closes,5); ma10=ma(closes,10); ma20=ma(closes,20)
first_c=closes[0]; last_c=closes[-1]
pct_all=round((last_c-first_c)/first_c*100,2)
avg_vol=round(sum(vols)/len(vols)/10000,2)
pct_str=('+' if pct_all>=0 else '')+f'{pct_all:.2f}%'

js_data=(
    'const DATES='+json.dumps(dates)+';\n'
    'const OPN='+json.dumps(opens)+';\n'
    'const CLS='+json.dumps(closes)+';\n'
    'const HI='+json.dumps(highs)+';\n'
    'const LO='+json.dumps(lows)+';\n'
    'const VOL='+json.dumps(vols)+';\n'
    'const MA5='+json.dumps(ma5)+';\n'
    'const MA10='+json.dumps(ma10)+';\n'
    'const MA20='+json.dumps(ma20)+';\n'
)

# 历史财务数据（硬编码，来自公告）
fin_data = {
    'years': ['2022', '2023', '2024', '2025'],
    'revenue': [146.88, 220.05, 300.63, 393.53],      # 亿元
    'net_profit': [23.53, 40.42, 56.21, 55.22],       # 亿元
    'rd_expense': [25.49, 41.88, 49.51, 72.77],       # 亿元
    'gross_margin': [44.98, 43.52, 42.93, 40.10],     # %
    'net_margin': [16.02, 18.37, 18.70, 13.78],       # %
    'rd_ratio': [17.35, 19.03, 16.47, 18.49],         # %
}

print('✅ 数据准备完成，生成HTML...')

html = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>北方华创(002371) 综合分析报告</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;background:#f0f2f5;color:#2c3e50;line-height:1.6}
/* ── 顶部 ── */
.top-header{background:linear-gradient(135deg,#0f2027,#203a43,#2c5364);color:#fff;padding:28px 40px;display:flex;justify-content:space-between;align-items:flex-end;flex-wrap:wrap;gap:16px}
.top-header .left h1{font-size:26px;font-weight:800;letter-spacing:1px}
.top-header .left p{font-size:13px;color:#8fa8b8;margin-top:6px}
.top-header .right{text-align:right}
.price-big{font-size:42px;font-weight:900;color:#ff6b6b}
.price-sub{font-size:14px;color:#8fa8b8;margin-top:4px}
/* ── 导航 ── */
nav{background:#fff;border-bottom:2px solid #e8ecf0;padding:0 40px;display:flex;gap:0;position:sticky;top:0;z-index:100;box-shadow:0 2px 8px rgba(0,0,0,.06)}
nav a{padding:14px 22px;font-size:14px;font-weight:500;color:#666;text-decoration:none;border-bottom:3px solid transparent;transition:.2s;cursor:pointer}
nav a:hover,nav a.active{color:#2c5364;border-bottom-color:#2c5364}
/* ── 布局 ── */
.container{max-width:1300px;margin:0 auto;padding:28px 40px;display:flex;flex-direction:column;gap:24px}
section{background:#fff;border-radius:14px;box-shadow:0 2px 12px rgba(0,0,0,.05);overflow:hidden}
.sec-title{padding:20px 28px 16px;border-bottom:1px solid #f0f0f0;display:flex;align-items:center;gap:10px}
.sec-title h2{font-size:18px;font-weight:700;color:#2c3e50}
.sec-title .icon{font-size:20px}
.sec-body{padding:24px 28px}
/* ── 概况卡片 ── */
.kpi-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:16px}
.kpi{background:#f7f9fc;border-radius:12px;padding:18px 20px;border-left:4px solid #2c5364}
.kpi.red{border-left-color:#e74c3c}
.kpi.green{border-left-color:#27ae60}
.kpi.blue{border-left-color:#3498db}
.kpi.orange{border-left-color:#f39c12}
.kpi .lb{font-size:12px;color:#888;margin-bottom:6px}
.kpi .val{font-size:24px;font-weight:800}
.kpi .sub{font-size:12px;color:#aaa;margin-top:4px}
.up{color:#e74c3c}
.down{color:#27ae60}
/* ── 公司信息 ── */
.company-grid{display:grid;grid-template-columns:1fr 1fr;gap:24px}
@media(max-width:768px){.company-grid{grid-template-columns:1fr}}
.info-table{width:100%;border-collapse:collapse}
.info-table td{padding:10px 12px;font-size:14px;border-bottom:1px solid #f5f5f5}
.info-table td:first-child{font-weight:600;color:#555;width:100px;background:#fafafa}
.biz-card{background:#f7f9fc;border-radius:10px;padding:18px;font-size:14px;color:#555;line-height:1.9}
.biz-card strong{color:#2c3e50}
/* ── 产品矩阵 ── */
.product-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:12px}
.prod-card{background:#f0f5ff;border-radius:10px;padding:14px 16px;border:1px solid #d4e4ff}
.prod-card .pt{font-size:13px;font-weight:700;color:#2c5364;margin-bottom:6px}
.prod-card .pl{font-size:12px;color:#666;line-height:1.8}
/* ── 图表 ── */
#chart-revenue{width:100%;height:320px}
#chart-margin{width:100%;height:280px}
#chart-kline{width:100%;height:500px}
#chart-close{width:100%;height:300px}
#chart-vol{width:100%;height:260px}
/* ── 行业趋势 ── */
.trend-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:16px}
.trend-card{background:#fff;border-radius:12px;padding:20px;border:1px solid #e8ecf0;transition:.2s}
.trend-card:hover{box-shadow:0 4px 16px rgba(0,0,0,.1)}
.trend-card .th{font-size:14px;font-weight:700;color:#2c3e50;display:flex;align-items:center;gap:8px;margin-bottom:10px}
.trend-card p{font-size:13px;color:#666;line-height:1.8}
.tag{display:inline-block;padding:2px 10px;border-radius:20px;font-size:11px;font-weight:600;margin-left:auto}
.tag.pos{background:#fef3f3;color:#e74c3c}
.tag.neg{background:#f3fef5;color:#27ae60}
.tag.neu{background:#f0f5ff;color:#3498db}
/* ── 新闻 ── */
.news-list{display:flex;flex-direction:column;gap:0}
.news-item{display:flex;gap:20px;padding:18px 0;border-bottom:1px solid #f5f5f5;align-items:flex-start}
.news-item:last-child{border-bottom:none}
.news-dot{width:8px;height:8px;border-radius:50%;background:#2c5364;margin-top:6px;flex-shrink:0}
.news-meta{font-size:12px;color:#aaa;margin-top:4px}
.news-title{font-size:14px;font-weight:600;color:#2c3e50;line-height:1.6}
.news-desc{font-size:13px;color:#666;margin-top:4px;line-height:1.7}
/* ── 结论 ── */
.swot{display:grid;grid-template-columns:1fr 1fr;gap:16px}
@media(max-width:600px){.swot{grid-template-columns:1fr}}
.swot-card{border-radius:12px;padding:20px}
.swot-card.s{background:#fff8f8;border:1px solid #ffdede}
.swot-card.w{background:#fffbf0;border:1px solid #ffe0a0}
.swot-card.o{background:#f0fff4;border:1px solid #a8edbd}
.swot-card.t{background:#f0f5ff;border:1px solid #bbd4ff}
.swot-card h3{font-size:14px;font-weight:700;margin-bottom:10px}
.swot-card.s h3{color:#c0392b}
.swot-card.w h3{color:#d68910}
.swot-card.o h3{color:#1a8c3e}
.swot-card.t h3{color:#2471a3}
.swot-card ul{padding-left:16px;font-size:13px;color:#555;line-height:2}
.conclusion-box{background:linear-gradient(135deg,#0f2027,#203a43);color:#fff;border-radius:14px;padding:28px 32px}
.conclusion-box h3{font-size:16px;font-weight:700;margin-bottom:12px;color:#7fc8e8}
.conclusion-box p{font-size:14px;color:#cde;line-height:1.9}
.footer{text-align:center;padding:24px;font-size:12px;color:#aaa;background:#fff;margin-top:8px}
</style>
</head>
<body>

<!-- ── 顶部标题 ── -->
<div class="top-header">
  <div class="left">
    <h1>📊 北方华创科技集团 · 综合分析报告</h1>
    <p>股票代码：002371.SZ &nbsp;|&nbsp; 深圳证券交易所 &nbsp;|&nbsp; 报告日期：__TODAY__</p>
  </div>
  <div class="right">
    <div class="price-big" id="price-display">935.36 元</div>
    <div class="price-sub">最新收盘价（2026-07-01）&nbsp;|&nbsp;全年涨跌幅 <span style="color:#ff6b6b">__PCT__</span></div>
  </div>
</div>

<!-- ── 导航 ── -->
<nav>
  <a href="#overview" class="active">概况</a>
  <a href="#company">公司简介</a>
  <a href="#finance">财务分析</a>
  <a href="#market">行情走势</a>
  <a href="#industry">行业趋势</a>
  <a href="#news">新闻动态</a>
  <a href="#conclusion">投资结论</a>
</nav>

<div class="container">

<!-- ══════════════════════════════════════════════════ -->
<!-- 1. 关键指标速览 -->
<!-- ══════════════════════════════════════════════════ -->
<section id="overview">
  <div class="sec-title"><span class="icon">🔑</span><h2>关键指标速览</h2></div>
  <div class="sec-body">
    <div class="kpi-grid">
      <div class="kpi red">
        <div class="lb">最新收盘价</div>
        <div class="val up">935.36元</div>
        <div class="sub">2026-07-01</div>
      </div>
      <div class="kpi red">
        <div class="lb">过去一年涨跌幅</div>
        <div class="val up">__PCT__</div>
        <div class="sub">2025-07 → 2026-07</div>
      </div>
      <div class="kpi blue">
        <div class="lb">2025年营业收入</div>
        <div class="val">393.53亿</div>
        <div class="sub">同比 +30.85%</div>
      </div>
      <div class="kpi orange">
        <div class="lb">2025年归母净利润</div>
        <div class="val">55.22亿</div>
        <div class="sub">同比 -1.77%（研发重投期）</div>
      </div>
      <div class="kpi green">
        <div class="lb">2026Q1营业收入</div>
        <div class="val">103.23亿</div>
        <div class="sub">同比 +25.80%</div>
      </div>
      <div class="kpi green">
        <div class="lb">2026Q1归母净利润</div>
        <div class="val">16.35亿</div>
        <div class="sub">同比 +3.42%</div>
      </div>
      <div class="kpi blue">
        <div class="lb">2025年研发投入</div>
        <div class="val">72.77亿</div>
        <div class="sub">占营收 18.49%，同比 +46.96%</div>
      </div>
      <div class="kpi">
        <div class="lb">2025年毛利率</div>
        <div class="val">40.10%</div>
        <div class="sub">同比 -2.83pp</div>
      </div>
    </div>
  </div>
</section>

<!-- ══════════════════════════════════════════════════ -->
<!-- 2. 公司简介 -->
<!-- ══════════════════════════════════════════════════ -->
<section id="company">
  <div class="sec-title"><span class="icon">🏢</span><h2>公司简介</h2></div>
  <div class="sec-body">
    <div class="company-grid">
      <div>
        <table class="info-table">
          <tr><td>全称</td><td>北方华创科技集团股份有限公司</td></tr>
          <tr><td>股票代码</td><td>002371.SZ（深圳证券交易所）</td></tr>
          <tr><td>成立时间</td><td>2001年9月28日</td></tr>
          <tr><td>上市时间</td><td>2010年</td></tr>
          <tr><td>注册地址</td><td>北京市朝阳区酒仙桥东路1号</td></tr>
          <tr><td>实际控制人</td><td>北京市国资委（国有控股）</td></tr>
          <tr><td>所属行业</td><td>半导体设备（电子专用设备）</td></tr>
          <tr><td>员工规模</td><td>~2万人（研发人员6511人）</td></tr>
          <tr><td>法定代表人</td><td>赵晋荣</td></tr>
        </table>
      </div>
      <div>
        <div class="biz-card">
          <strong>公司定位：</strong>国内集成电路高端工艺装备领先企业，是半导体设备领域的"国家队"。<br><br>
          <strong>主营业务：</strong><br>
          ① <strong>电子工艺装备</strong>（占营收 93.34%）：刻蚀、薄膜沉积（PVD/CVD）、炉管、清洗、涂胶显影、离子注入等多类半导体前道设备<br>
          ② <strong>精密电子元器件</strong>（占营收 6.55%）：真空仪器、电子元器件<br><br>
          <strong>发展历程：</strong>由北京七星华创与北方微电子战略重组而成，2018年入选国企改革"双百企业"，2021年写入北京市政府工作报告。十年间营收增长45倍，从中低端迈向高端平台化。
        </div>
      </div>
    </div>

    <div style="margin-top:24px">
      <h3 style="font-size:15px;font-weight:700;margin-bottom:14px;color:#2c3e50">🔧 产品矩阵（平台化布局）</h3>
      <div class="product-grid">
        <div class="prod-card">
          <div class="pt">⚡ 干法刻蚀设备</div>
          <div class="pl">CCP/ICP 刻蚀<br>高选择比刻蚀<br>市占率持续提升</div>
        </div>
        <div class="prod-card">
          <div class="pt">🧱 薄膜沉积设备</div>
          <div class="pl">PVD、CVD、ALD<br>多类薄膜工艺<br>覆盖逻辑/存储</div>
        </div>
        <div class="prod-card">
          <div class="pt">🔥 炉管/热处理</div>
          <div class="pl">氧化/退火/RTP<br>扩散炉<br>批量处理优势</div>
        </div>
        <div class="prod-card">
          <div class="pt">💧 湿法清洗</div>
          <div class="pl">单晶圆清洗<br>批量清洗<br>28nm 以上验证</div>
        </div>
        <div class="prod-card">
          <div class="pt">🔬 离子注入机</div>
          <div class="pl">Sirius MC 系列<br>2025年推出新品<br>国产突破方向</div>
        </div>
        <div class="prod-card">
          <div class="pt">🖨️ 涂胶显影</div>
          <div class="pl">Track 设备<br>与光刻机配套<br>新品快速落地</div>
        </div>
        <div class="prod-card">
          <div class="pt">🔗 混合键合</div>
          <div class="pl">先进封装设备<br>2026年新发布<br>面向HBM/AI芯片</div>
        </div>
        <div class="prod-card">
          <div class="pt">⚙️ 真空/新能源</div>
          <div class="pl">真空仪器设备<br>锂电池设备<br>多元化布局</div>
        </div>
      </div>
    </div>
  </div>
</section>

<!-- ══════════════════════════════════════════════════ -->
<!-- 3. 财务分析 -->
<!-- ══════════════════════════════════════════════════ -->
<section id="finance">
  <div class="sec-title"><span class="icon">💰</span><h2>财务分析（2022–2026Q1）</h2></div>
  <div class="sec-body">
    <!-- 财务亮点 -->
    <div class="kpi-grid" style="margin-bottom:24px">
      <div class="kpi blue">
        <div class="lb">营收 CAGR（22→25）</div>
        <div class="val">+38.8%</div>
        <div class="sub">4年复合增长</div>
      </div>
      <div class="kpi orange">
        <div class="lb">资产负债率</div>
        <div class="val">51.08%</div>
        <div class="sub">总体稳健</div>
      </div>
      <div class="kpi green">
        <div class="lb">经营现金流</div>
        <div class="val">21.33亿</div>
        <div class="sub">2025年，同比+37.5%</div>
      </div>
      <div class="kpi red">
        <div class="lb">每股分红</div>
        <div class="val">7.62元</div>
        <div class="sub">2025年，10派7.62元</div>
      </div>
    </div>
    <!-- 营收/利润趋势图 -->
    <div id="chart-revenue"></div>
    <div style="margin-top:20px"><div id="chart-margin"></div></div>

    <!-- 财务说明 -->
    <div style="margin-top:20px;background:#fffbf0;border-left:4px solid #f39c12;border-radius:8px;padding:16px 20px">
      <h4 style="font-weight:700;color:#d68910;margin-bottom:8px">⚠️ 关注点：利润增速放缓原因分析</h4>
      <p style="font-size:13px;color:#666;line-height:1.9">
        2025年净利润同比微降 1.77%，主因：<br>
        ① <strong>研发费用暴增 47%</strong>（72.77亿元），为新产品（离子注入、涂胶显影等）客户端验证投入大量资源；<br>
        ② 新产品验证期零部件迭代成本上升，<strong>毛利率降至 40.1%</strong>；<br>
        ③ 为匹配订单增长新增大量借款，<strong>财务费用激增 264.8%</strong>。<br>
        这是主动加大投入、抢占未来市场份额的战略选择，非经营恶化信号。
      </p>
    </div>
  </div>
</section>

<!-- ══════════════════════════════════════════════════ -->
<!-- 4. 行情走势 -->
<!-- ══════════════════════════════════════════════════ -->
<section id="market">
  <div class="sec-title"><span class="icon">📈</span><h2>股价行情走势（过去一年，前复权）</h2></div>
  <div class="sec-body">
    <div style="margin-bottom:16px;background:#f0f5ff;border-radius:8px;padding:12px 18px;font-size:13px;color:#3a5068">
      <b>📌 近期行情：</b>2026年7月1日收盘 <b style="color:#e74c3c">935.36元</b>，过去一年累计上涨 <b style="color:#e74c3c">__PCT__</b>。
      6月起加速上行，最近10个交易日涨幅超30%，成交量同步放大，量价配合良好。
    </div>
    <div id="chart-kline"></div>
    <div style="margin-top:16px"><div id="chart-close"></div></div>
    <div style="margin-top:16px"><div id="chart-vol"></div></div>
  </div>
</section>

<!-- ══════════════════════════════════════════════════ -->
<!-- 5. 行业趋势 -->
<!-- ══════════════════════════════════════════════════ -->
<section id="industry">
  <div class="sec-title"><span class="icon">🌐</span><h2>行业趋势分析：半导体设备</h2></div>
  <div class="sec-body">
    <div class="trend-grid">
      <div class="trend-card">
        <div class="th">🤖 AI驱动超级扩产周期 <span class="tag pos">核心驱动</span></div>
        <p>AI算力需求爆发推动全球晶圆厂大规模资本开支。TechInsights预测2026年半导体设备支出将较2025年增长超50%，Q4单季设备支出预计达创纪录的605亿美元（约8.3万亿韩元）。北方华创直接受益于国内AI相关晶圆厂扩产订单。</p>
      </div>
      <div class="trend-card">
        <div class="th">🏭 国产替代加速突破 <span class="tag pos">长期利好</span></div>
        <p>中国半导体设备国产化率已从2024年的16%提升至2025年的21%，预计2026年达26%，2028年进一步提升至43%。北方华创在刻蚀、薄膜沉积、炉管等领域市占率稳步提升，离子注入等高难度设备快速落地，国产替代的核心受益标的。</p>
      </div>
      <div class="trend-card">
        <div class="th">🇨🇳 政策与产业集群共振 <span class="tag pos">政策护航</span></div>
        <p>大基金三期（约3440亿元）持续注入，重点支持半导体设备和材料。国内12英寸晶圆厂产能扩张持续（预计2026年底月产能超276万片），为设备供应商提供稳定的国内订单基本盘。</p>
      </div>
      <div class="trend-card">
        <div class="th">🌍 出海与海外订单 <span class="tag neu">新增看点</span></div>
        <p>据2026年5月投资者关系活动记录，公司已开始关注出海前景，观察到海外晶圆厂采购国内设备的趋势苗头。若出海订单成真，将打开第二增长曲线。目前海外营收贡献尚小，但方向明确。</p>
      </div>
      <div class="trend-card">
        <div class="th">⚡ 先进封装新赛道 <span class="tag pos">新增量</span></div>
        <p>HBM高带宽内存和Chiplet封装需求随AI芯片爆发而快速增长。北方华创2026年推出混合键合设备（Hybrid Bonding），切入先进封装新赛道，有望成为未来营收增量的重要来源。</p>
      </div>
      <div class="trend-card">
        <div class="th">⚠️ 出口管制与验证风险 <span class="tag neg">风险关注</span></div>
        <p>美国对华出口管制持续升级，可能影响部分零部件采购，推高成本。国产设备在先进制程（14nm以下）的验证周期较长，叠加客户端验收节奏影响收入确认时点。研发投入持续高企将持续压制近期利润率。</p>
      </div>
    </div>
  </div>
</section>

<!-- ══════════════════════════════════════════════════ -->
<!-- 6. 近期新闻动态 -->
<!-- ══════════════════════════════════════════════════ -->
<section id="news">
  <div class="sec-title"><span class="icon">📰</span><h2>近期新闻动态</h2></div>
  <div class="sec-body">
    <div class="news-list">

      <div class="news-item">
        <div class="news-dot"></div>
        <div>
          <div class="news-title">2026年Q1业绩：营收103.23亿元（+25.8%），净利润16.35亿元（+3.4%）</div>
          <div class="news-desc">2026年一季度营收稳步增长，但净利润增速低于营收，主因研发费用同比增长36.6%至14.02亿元。毛利率40.77%，环比改善3.62pp。经营现金流7.48亿元，同比转正。存货286亿元保持高位，反映在手订单充足。</div>
          <div class="news-meta">📅 2026-04-29 &nbsp;|&nbsp; 来源：公司公告</div>
        </div>
      </div>

      <div class="news-item">
        <div class="news-dot"></div>
        <div>
          <div class="news-title">2025年年报发布：营收393.53亿元（+30.85%），研发费用创历史新高72.77亿元</div>
          <div class="news-desc">2025年业绩报告显示集成电路设备营收同比增长超50%，平台化布局加速落地。研发人员增至6511人，同比增长42%。计划每10股分红7.62元。中部及东南部地区收入占比升至62.41%，持续向长三角/珠三角产业集群聚拢。</div>
          <div class="news-meta">📅 2026-04-17 &nbsp;|&nbsp; 来源：公司年报</div>
        </div>
      </div>

      <div class="news-item">
        <div class="news-dot"></div>
        <div>
          <div class="news-title">东吴证券维持"买入"评级：平台化布局加速，长期受益国产替代</div>
          <div class="news-desc">东吴证券2026Q1点评认为，北方华创作为本土半导体设备平台型公司，将长期受益于AI带动行业扩产及国产替代浪潮。维持2026-2028年盈利预测不变，当前估值对应动态市盈率具备吸引力，维持"买入"评级。</div>
          <div class="news-meta">📅 2026-05-02 &nbsp;|&nbsp; 来源：东吴证券研报</div>
        </div>
      </div>

      <div class="news-item">
        <div class="news-dot"></div>
        <div>
          <div class="news-title">投资者关系活动：公司探讨出海前景，观察到海外晶圆厂采购国内设备趋势</div>
          <div class="news-desc">2026年5月投资者关系活动中，公司表示正关注出海前景，观察到海外晶圆厂出货周期拉长和采购国内设备的新现象。若海外订单落地，将打开增量市场，是重要的边际变化信号。</div>
          <div class="news-meta">📅 2026-05-15 &nbsp;|&nbsp; 来源：投资者关系活动记录</div>
        </div>
      </div>

      <div class="news-item">
        <div class="news-dot"></div>
        <div>
          <div class="news-title">SEMICON 2025：推出离子注入机新品 Sirius MC 3 等多款新设备</div>
          <div class="news-desc">公司在SEMICON展会发布多款新设备，包括新一代离子注入机Sirius MC 3、混合键合设备等，产品线覆盖薄膜沉积、刻蚀、涂胶显影、离子注入、清洗、热处理、混合键合等几乎全套前道工艺，平台化程度达到国内领先水平。</div>
          <div class="news-meta">📅 2025年下半年 &nbsp;|&nbsp; 来源：展会资讯</div>
        </div>
      </div>

    </div>
  </div>
</section>

<!-- ══════════════════════════════════════════════════ -->
<!-- 7. 投资结论 -->
<!-- ══════════════════════════════════════════════════ -->
<section id="conclusion">
  <div class="sec-title"><span class="icon">🎯</span><h2>综合分析结论（SWOT）</h2></div>
  <div class="sec-body">
    <div class="swot" style="margin-bottom:24px">
      <div class="swot-card s">
        <h3>💪 优势（Strengths）</h3>
        <ul>
          <li>国内半导体设备龙头，平台化布局最完整</li>
          <li>营收十年增长45倍，增长持续性强</li>
          <li>国资背景，政策支持确定性高</li>
          <li>研发人员6500+，研发投入行业顶尖</li>
          <li>在手订单充足（存货286亿），业绩可见度高</li>
        </ul>
      </div>
      <div class="swot-card w">
        <h3>⚠️ 劣势（Weaknesses）</h3>
        <ul>
          <li>利润率承压，2025年净利率仅13.78%</li>
          <li>高端制程（7nm以下）设备尚未突破</li>
          <li>光刻机等关键设备缺失，依赖外部配套</li>
          <li>财务费用快速攀升（+265%）</li>
          <li>新产品验证周期长，收入确认存在时间差</li>
        </ul>
      </div>
      <div class="swot-card o">
        <h3>🚀 机会（Opportunities）</h3>
        <ul>
          <li>AI芯片需求拉动全球设备支出超级周期</li>
          <li>国产化率从21%提升至43%的巨大空间</li>
          <li>出海订单落地预期，打开海外市场</li>
          <li>先进封装（HBM/Chiplet）新赛道切入</li>
          <li>大基金三期持续注资，政策红利延续</li>
        </ul>
      </div>
      <div class="swot-card t">
        <h3>🔍 威胁（Threats）</h3>
        <ul>
          <li>美国出口管制升级，零部件成本上升</li>
          <li>ASML、应用材料等国际巨头技术壁垒高</li>
          <li>客户验收节奏不确定，收入有波动风险</li>
          <li>同行（拓荆科技、北华航天等）竞争加剧</li>
          <li>宏观经济下行影响下游客户资本开支</li>
        </ul>
      </div>
    </div>

    <div class="conclusion-box">
      <h3>📋 综合结论与决策建议</h3>
      <p>
        <strong style="color:#7fc8e8">整体判断：</strong>
        北方华创是国内半导体设备领域最具综合实力的平台型龙头，当前处于"以研发换未来"的战略投入期。2025年营收近400亿、同比增长31%，证明国产替代需求旺盛且公司执行力强；净利润的短暂承压源于主动高强度研发投入，而非经营质量下滑。<br><br>
        <strong style="color:#7fc8e8">核心逻辑：</strong>
        AI超级扩产周期 + 国产化率从21%到43%的空间 + 出海订单预期 = 多重增长引擎叠加。2026年在手订单充足（存货286亿），收入增长确定性较高。<br><br>
        <strong style="color:#7fc8e8">风险提示：</strong>
        关注毛利率能否随新产品验证完成后企稳回升（预期2026年H2改善），以及美国出口管制对零部件供应链的影响程度。短期股价已大幅上涨（过去一年+__PCT__），需关注估值水位。<br><br>
        <strong style="color:#f8b400">⚡ 机构观点：</strong>东吴证券维持"买入"，认为当前估值仍具吸引力，长期逻辑不变。
      </p>
    </div>
  </div>
</section>

</div><!-- /container -->

<div class="footer">
  ⚠️ 本报告数据来源：Tushare、AkShare、公司年报、东吴证券研报、同花顺、央广网等公开资料，仅供参考，不构成任何投资建议。&nbsp;|&nbsp;
  报告生成时间：__TODAY__ &nbsp;|&nbsp; 数据截止：2026年7月1日
</div>

<script>
// ══════════════════════════════════════════════════════════
// 数据注入
// ══════════════════════════════════════════════════════════
__JSDATA__

function fmtVol(v){
  v=Number(v);
  if(v>=1e8) return (v/1e8).toFixed(1)+"亿手";
  if(v>=1e4) return (v/1e4).toFixed(1)+"万手";
  return v.toFixed(0)+"手";
}

var UP="#e74c3c", DOWN="#27ae60";
var dzI={type:"inside",start:50,end:100};
var dzS={type:"slider",start:50,end:100,height:22,bottom:6};

// ── 营收利润趋势图 ──
var cr=echarts.init(document.getElementById("chart-revenue"));
cr.setOption({
  title:{text:"营业收入 & 归母净利润趋势（亿元）",left:0,textStyle:{fontSize:14}},
  tooltip:{trigger:"axis"},
  legend:{top:0,right:0},
  grid:{left:60,right:20,top:50,bottom:30},
  xAxis:{type:"category",data:["2022","2023","2024","2025"]},
  yAxis:{type:"value",axisLabel:{formatter:"{value}亿"}},
  series:[
    {name:"营业收入",type:"bar",data:[146.88,220.05,300.63,393.53],
     itemStyle:{color:"#3498db"},barMaxWidth:60,
     label:{show:true,position:"top",formatter:"{c}亿",fontSize:12}},
    {name:"归母净利润",type:"bar",data:[23.53,40.42,56.21,55.22],
     itemStyle:{color:"#e74c3c"},barMaxWidth:60,
     label:{show:true,position:"top",formatter:"{c}亿",fontSize:12}},
    {name:"研发费用",type:"line",data:[25.49,41.88,49.51,72.77],
     lineStyle:{color:"#f39c12",width:2.5},symbol:"circle",symbolSize:7,
     label:{show:true,position:"top",formatter:"{c}亿",fontSize:11,color:"#f39c12"}}
  ]
});

// ── 毛利率/净利率/研发占比趋势 ──
var cm=echarts.init(document.getElementById("chart-margin"));
cm.setOption({
  title:{text:"盈利能力与研发投入比率（%）",left:0,textStyle:{fontSize:14}},
  tooltip:{trigger:"axis",formatter:function(p){
    return p.map(function(i){return i.seriesName+": "+i.value+"%";}).join("<br>");
  }},
  legend:{top:0,right:0},
  grid:{left:60,right:20,top:50,bottom:30},
  xAxis:{type:"category",data:["2022","2023","2024","2025"]},
  yAxis:{type:"value",min:0,max:55,axisLabel:{formatter:"{value}%"}},
  series:[
    {name:"毛利率",type:"line",data:[44.98,43.52,42.93,40.10],
     lineStyle:{color:"#3498db",width:2.5},symbol:"circle",symbolSize:7},
    {name:"净利率",type:"line",data:[16.02,18.37,18.70,13.78],
     lineStyle:{color:"#e74c3c",width:2.5},symbol:"circle",symbolSize:7},
    {name:"研发费用率",type:"line",data:[17.35,19.03,16.47,18.49],
     lineStyle:{color:"#f39c12",width:2.5,type:"dashed"},symbol:"circle",symbolSize:7}
  ]
});

// ── K线图 ──
var ck=echarts.init(document.getElementById("chart-kline"));
ck.setOption({
  title:{text:"K线图（前复权）",left:0,textStyle:{fontSize:14}},
  tooltip:{trigger:"axis",axisPointer:{type:"cross"},
    formatter:function(p){
      var i=p[0].dataIndex;
      return "<b>"+DATES[i]+"</b><br>开:"+OPN[i].toFixed(2)+" 收:"+CLS[i].toFixed(2)
        +"<br>高:"+HI[i].toFixed(2)+" 低:"+LO[i].toFixed(2)+"<br>量:"+fmtVol(VOL[i]);
    }},
  legend:{data:["K线","MA5","MA10","MA20"],top:0,right:0},
  grid:{left:80,right:20,top:46,bottom:30},
  xAxis:{type:"category",data:DATES,axisLabel:{show:false},splitLine:{show:false}},
  yAxis:{type:"value",scale:true,splitLine:{lineStyle:{color:"#f0f0f0"}}},
  dataZoom:[dzI,dzS],
  series:[
    {name:"K线",type:"candlestick",
     data:DATES.map(function(d,i){return [OPN[i],CLS[i],LO[i],HI[i]];}),
     itemStyle:{color:UP,color0:DOWN,borderColor:UP,borderColor0:DOWN}},
    {name:"MA5", type:"line",data:MA5, lineStyle:{width:1.5},symbol:"none",smooth:true},
    {name:"MA10",type:"line",data:MA10,lineStyle:{width:1.5},symbol:"none",smooth:true},
    {name:"MA20",type:"line",data:MA20,lineStyle:{width:1.5},symbol:"none",smooth:true}
  ]
});

// ── 收盘价 ──
var cc=echarts.init(document.getElementById("chart-close"));
cc.setOption({
  title:{text:"收盘价走势",left:0,textStyle:{fontSize:14}},
  tooltip:{trigger:"axis",formatter:function(p){return "<b>"+p[0].axisValue+"</b><br>收盘: "+p[0].value.toFixed(2);}},
  grid:{left:80,right:20,top:46,bottom:30},
  xAxis:{type:"category",data:DATES,axisLabel:{show:false},splitLine:{show:false}},
  yAxis:{type:"value",scale:true,splitLine:{lineStyle:{color:"#f0f0f0"}}},
  dataZoom:[dzI,dzS],
  series:[{name:"收盘价",type:"line",data:CLS,smooth:true,
    lineStyle:{color:"#3498db",width:2.5},
    areaStyle:{color:new echarts.graphic.LinearGradient(0,0,0,1,
      [{offset:0,color:"rgba(52,152,219,0.2)"},{offset:1,color:"rgba(52,152,219,0.02)"}])},
    symbol:"none"}]
});

// ── 成交量 ──
var cv=echarts.init(document.getElementById("chart-vol"));
cv.setOption({
  title:{text:"成交量（手）",left:0,textStyle:{fontSize:14}},
  tooltip:{trigger:"axis",
    formatter:function(p){return "<b>"+DATES[p[0].dataIndex]+"</b><br>"+fmtVol(VOL[p[0].dataIndex]);}},
  grid:{left:80,right:20,top:46,bottom:30},
  xAxis:{type:"category",data:DATES,axisLabel:{show:false},splitLine:{show:false}},
  yAxis:{type:"value",axisLabel:{formatter:function(v){return fmtVol(v);}},
    splitLine:{lineStyle:{color:"#f0f0f0"}}},
  dataZoom:[dzI,dzS],
  series:[{name:"成交量",type:"bar",data:VOL,
    itemStyle:{color:function(p){return CLS[p.dataIndex]>=OPN[p.dataIndex]?UP:DOWN;}},
    barWidth:"60%"}]
});

// 三图联动
function link(s,t){
  s.on("dataZoom",function(){
    var o=s.getOption().dataZoom;
    t.forEach(function(x){x.dispatchAction({type:"dataZoom",start:o[0].start,end:o[0].end});});
  });
}
link(ck,[cc,cv]); link(cc,[ck,cv]); link(cv,[ck,cc]);
window.addEventListener("resize",function(){cr.resize();cm.resize();ck.resize();cc.resize();cv.resize();});

// 导航高亮
var sections=document.querySelectorAll("section[id]");
var navLinks=document.querySelectorAll("nav a");
window.addEventListener("scroll",function(){
  var y=window.scrollY+90;
  sections.forEach(function(s){
    var top=s.offsetTop, bot=top+s.offsetHeight;
    if(y>=top&&y<bot){
      navLinks.forEach(function(a){a.classList.remove("active");});
      var link=document.querySelector("nav a[href='#"+s.id+"']");
      if(link) link.classList.add("active");
    }
  });
});
</script>
</body>
</html>
'''

# 替换占位符
today = datetime.now().strftime('%Y年%m月%d日')
html = html.replace('__JSDATA__', js_data)
html = html.replace('__PCT__', pct_str)
html = html.replace('__TODAY__', today)

with open(OUTPUT, 'w', encoding='utf-8') as f:
    f.write(html)

print(f'✅ 综合报告已生成: {OUTPUT}')
