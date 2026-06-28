#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取北方华创(002371)过去一年日交易数据，
生成 CSV + HTML 分析面板（含K线、收盘价曲线、成交量）
- 使用 Tushare HTTP API（绕过代理）
- 成交量单位：手，Y轴智能格式化
- 修复：CSS bottom 拼写、JS fmtVol 函数位置
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
import os, json

# ── 参数 ────────────────────────────────────────────────────────
TOKEN      = 'aaca426ed7010fd4e2072f0637cf94412dd290ea14c75166d8e51505'
STOCK_CODE = "002371"
TS_CODE    = "002371.SZ"
STOCK_NAME = "北方华创"
OUTPUT_DIR = "/Users/haerangxxi/Desktop/task1"
CSV_PATH   = os.path.join(OUTPUT_DIR, "beifang_huachuang.csv")
HTML_PATH  = os.path.join(OUTPUT_DIR, "kline_dashboard.html")

END_DATE   = datetime.now().strftime("%Y%m%d")
START_DATE = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")

print(f"正在获取 {STOCK_NAME}({STOCK_CODE}) 日线数据...")
print(f"时间范围: {START_DATE} ~ {END_DATE}")

# ── 调用 Tushare HTTP API（绕过系统代理）────────────────────────
def tushare_query(api_name, fields, **params):
    url = "http://api.tushare.pro"
    payload = {"api_name": api_name, "token": TOKEN, "params": params, "fields": fields}
    r = requests.post(url, json=payload, timeout=30, proxies={'http': None, 'https': None})
    r.raise_for_status()
    data = r.json()
    if data.get("code") != 0:
        raise Exception(f"Tushare 错误 [{data.get('code')}]: {data.get('msg')}")
    return pd.DataFrame(data["data"]["items"], columns=data["data"]["fields"])

try:
    # 只调用 daily 接口（避免 daily_basic 频率限制）
    df = tushare_query(
        "daily",
        "ts_code,trade_date,open,high,low,close,vol,amount",
        ts_code=TS_CODE, start_date=START_DATE, end_date=END_DATE
    )
    # 类型转换
    df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')
    for col in ['open','close','high','low']:
        df[col] = df[col].astype(float)
    df['vol']   = df['vol'].astype(int)      # 手
    df['amount'] = df['amount'].astype(float)  # 千元
    df['pct_chg'] = df['close'].pct_change() * 100
    # 排序 + 格式化
    df = df.sort_values('trade_date').reset_index(drop=True)
    df_out = pd.DataFrame({
        '日期':     df['trade_date'].dt.strftime('%Y-%m-%d'),
        '股票代码':  TS_CODE,
        '开盘':     df['open'],
        '收盘':     df['close'],
        '最高':     df['high'],
        '最低':     df['low'],
        '成交量':   df['vol'],
        '成交额':   df['amount'] * 1000,   # 千元 -> 元
        '涨跌幅':   df['pct_chg'],
        '换手率':   ''   # daily_basic 有频率限制，暂不获取
    })
    source = "Tushare"
    print(f"✅ Tushare 获取数据成功，共 {len(df_out)} 条")
except Exception as e:
    print(f"❌ Tushare 失败: {e}")
    raise

# ── 保存 CSV ────────────────────────────────────────────────────
df_out.to_csv(CSV_PATH, index=False, encoding='utf-8-sig')
print(f"✅ CSV 已保存: {CSV_PATH}")

# ── 准备 JS 数据 ────────────────────────────────────────────────
dates   = df_out['日期'].tolist()
opens   = [float(x) for x in df_out['开盘'].tolist()]
closes  = [float(x) for x in df_out['收盘'].tolist()]
highs    = [float(x) for x in df_out['最高'].tolist()]
lows     = [float(x) for x in df_out['最低'].tolist()]
vols     = [int(x)   for x in df_out['成交量'].tolist()]

first_c = closes[0]
last_c  = closes[-1]
pct     = round((last_c - first_c) / first_c * 100, 2)
avg_vol = round(sum(vols) / len(vols) / 10000, 2)  # 万手

def ma(data, n):
    return [round(sum(data[i-n+1:i+1])/n, 2) if i >= n-1 else None
            for i in range(len(data))]

# ── 生成 HTML（Here-document 风格，避免 f-string 大括号问题）───
js_vars = (
    "const DATES="  + json.dumps(dates, ensure_ascii=False) + ";\n"
    "const OPN="    + json.dumps(opens, ensure_ascii=False) + ";\n"
    "const CLS="    + json.dumps(closes, ensure_ascii=False) + ";\n"
    "const HI="     + json.dumps(highs, ensure_ascii=False) + ";\n"
    "const LO="     + json.dumps(lows, ensure_ascii=False) + ";\n"
    "const VOL="    + json.dumps(vols, ensure_ascii=False) + ";\n"
    "const MA5="    + json.dumps(ma(closes,5),  ensure_ascii=False) + ";\n"
    "const MA10="   + json.dumps(ma(closes,10), ensure_ascii=False) + ";\n"
    "const MA20="   + json.dumps(ma(closes,20), ensure_ascii=False) + ";\n"
)

UP   = '#e74c3c'
DOWN = '#27ae60'
PCT_STR = (('+' if pct >= 0 else '') + f"{pct:.2f}%")
C0 = 'up' if last_c >= first_c else 'down'
C1 = 'up' if pct >= 0 else 'down'

html = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>北方华创(002371) 行情分析</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;background:#f0f2f5;color:#333}
.header{background:linear-gradient(135deg,#1a1a2e,#16213e);color:#fff;padding:18px 32px;display:flex;align-items:center;gap:20px;flex-wrap:wrap}
.header h1{font-size:22px;font-weight:700}
.badge{background:rgba(255,255,255,.12);border-radius:20px;padding:4px 14px;font-size:12px;color:#b0b8c8}
.stats{display:flex;gap:16px;padding:16px 32px;background:#fff;border-bottom:1px solid #e8e8e8;flex-wrap:wrap}
.sc{background:#f7f9fc;border-radius:10px;padding:14px 22px;min-width:140px}
.sc .lb{font-size:12px;color:#888;margin-bottom:4px}
.sc .val{font-size:22px;font-weight:700}
.up{color:#e74c3c}
.down{color:#27ae60}
.charts{padding:20px 32px;display:flex;flex-direction:column;gap:16px}
.cb{background:#fff;border-radius:12px;box-shadow:0 2px 12px rgba(0,0,0,.06);padding:8px}
#kline{width:100%;height:520px}
#close{width:100%;height:320px}
#vol{width:100%;height:280px}
.disclaimer{padding:14px 32px 28px;font-size:12px;color:#aaa;line-height:1.7}
</style>
</head>
<body>

<div class="header">
  <h1>📈 北方华创 (002371.SZ) 行情分析</h1>
  <span class="badge">数据来源: Tushare</span>
  <span class="badge">前复权 · 过去一年</span>
  <span class="badge">__N__ 个交易日</span>
</div>

<div class="stats" id="stats"></div>

<div class="charts">
  <div class="cb"><div id="kline"></div></div>
  <div class="cb"><div id="close"></div></div>
  <div class="cb"><div id="vol"></div></div>
</div>

<div class="disclaimer">
  ⚠️ 本页面仅供学习参考，不构成任何投资建议。数据以交易所公告为准。<br>
  成交量单位：手（1手=100股）。红色K线/柱表示当日上涨，绿色表示下跌。
</div>

<script>
// ══════════════════════════════════════════════════════════════
// 数据区（由 Python 自动注入）
// ══════════════════════════════════════════════════════════════
__JSVARS__

// 成交量格式化（单位：手）
function fmtVol(v){
  v=Number(v);
  if(v>=1e8) return (v/1e8).toFixed(1)+"亿手";
  if(v>=1e4) return (v/1e4).toFixed(1)+"万手";
  return v.toFixed(0)+"手";
}

// ══════════════════════════════════════════════════════════════
// 统计卡片
// ══════════════════════════════════════════════════════════════
document.getElementById("stats").innerHTML=
  '<div class="sc"><div class="lb">最新收盘</div><div class="val __C0__">'+CLS[CLS.length-1].toFixed(2)+'</div></div>'
+'<div class="sc"><div class="lb">全年涨跌幅</div><div class="val __C1__">__PCTSTR__</div></div>'
+'<div class="sc"><div class="lb">全年最高</div><div class="val">'+Math.max.apply(null,HI).toFixed(2)+'</div></div>'
+'<div class="sc"><div class="lb">全年最低</div><div class="val">'+Math.min.apply(null,LO).toFixed(2)+'</div></div>'
+'<div class="sc"><div class="lb">均成交量</div><div class="val">__AVGVOL__万手</div></div>';

var UP="#e74c3c", DOWN="#27ae60";

// ══════════════════════════════════════════════════════════════
// 公共 dataZoom 配置
// ══════════════════════════════════════════════════════════════
var dzI={type:"inside",start:50,end:100};
var dzS={type:"slider",start:50,end:100,height:22,bottom:6};

// ══════════════════════════════════════════════════════════════
// K线图
// ══════════════════════════════════════════════════════════════
var ck=echarts.init(document.getElementById("kline"));
ck.setOption({
  title:{text:"K线图（前复权）",left:20,top:10,textStyle:{fontSize:15}},
  tooltip:{
    trigger:"axis",axisPointer:{type:"cross"},
    formatter:function(p){
      var i=p[0].dataIndex;
      return "<b>"+DATES[i]+"</b><br>开:"+OPN[i].toFixed(2)+" 收:"+CLS[i].toFixed(2)
        +"<br>高:"+HI[i].toFixed(2)+" 低:"+LO[i].toFixed(2)
        +"<br>成交量:"+fmtVol(VOL[i]);
    }
  },
  legend:{data:["K线","MA5","MA10","MA20"],top:10,right:20},
  grid:{left:80,right:30,top:52,bottom:32},
  xAxis:{type:"category",data:DATES,axisLabel:{show:false},splitLine:{show:false}},
  yAxis:{type:"value",scale:true,splitLine:{lineStyle:{color:"#f0f0f0"}}},
  dataZoom:[dzI,dzS],
  series:[
    {name:"K线",type:"candlestick",
     data:DATES.map(function(d,i){return [OPN[i],CLS[i],LO[i],HI[i]];}),
     itemStyle:{color:UP,color0:DOWN,borderColor:UP,borderColor0:DOWN}},
    {name:"MA5",  type:"line",data:MA5,  lineStyle:{width:1.5},symbol:"none",smooth:true},
    {name:"MA10", type:"line",data:MA10, lineStyle:{width:1.5},symbol:"none",smooth:true},
    {name:"MA20", type:"line",data:MA20, lineStyle:{width:1.5},symbol:"none",smooth:true}
  ]
});

// ══════════════════════════════════════════════════════════════
// 收盘价曲线
// ══════════════════════════════════════════════════════════════
var cc=echarts.init(document.getElementById("close"));
cc.setOption({
  title:{text:"收盘价走势",left:20,top:10,textStyle:{fontSize:15}},
  tooltip:{trigger:"axis",formatter:function(p){return "<b>"+p[0].axisValue+"</b><br>收盘: "+p[0].value.toFixed(2);}},
  grid:{left:80,right:30,top:52,bottom:32},
  xAxis:{type:"category",data:DATES,axisLabel:{show:false},splitLine:{show:false}},
  yAxis:{type:"value",scale:true,splitLine:{lineStyle:{color:"#f0f0f0"}}},
  dataZoom:[dzI,dzS],
  series:[{
    name:"收盘价",type:"line",data:CLS,smooth:true,
    lineStyle:{color:"#3498db",width:2.5},
    areaStyle:{color:new echarts.graphic.LinearGradient(0,0,0,1,
      [{offset:0,color:"rgba(52,152,219,0.25)"},{offset:1,color:"rgba(52,152,219,0.02)"}])},
    symbol:"none"
  }]
});

// ══════════════════════════════════════════════════════════════
// 成交量图
// ══════════════════════════════════════════════════════════════
var cv=echarts.init(document.getElementById("vol"));
cv.setOption({
  title:{text:"成交量（单位：手）",left:20,top:10,textStyle:{fontSize:15}},
  tooltip:{
    trigger:"axis",
    formatter:function(p){return "<b>"+DATES[p[0].dataIndex]+"</b><br>成交量: "+fmtVol(VOL[p[0].dataIndex]);}
  },
  grid:{left:80,right:30,top:50,bottom:32},
  xAxis:{type:"category",data:DATES,axisLabel:{show:false},splitLine:{show:false}},
  yAxis:{
    type:"value",name:"成交量",
    axisLabel:{formatter:function(v){return fmtVol(v);}},
    splitLine:{lineStyle:{color:"#f0f0f0"}}
  },
  dataZoom:[dzI,dzS],
  series:[{
    name:"成交量",type:"bar",data:VOL,
    itemStyle:{color:function(p){return CLS[p.dataIndex]>=OPN[p.dataIndex]?UP:DOWN;}},
    barWidth:"60%"
  }]
});

// ══════════════════════════════════════════════════════════════
// 三图联动缩放
// ══════════════════════════════════════════════════════════════
function link(s,t){
  s.on("dataZoom",function(){
    var o=s.getOption().dataZoom;
    t.forEach(function(x){x.dispatchAction({type:"dataZoom",start:o[0].start,end:o[0].end});});
  });
}
link(ck,[cc,cv]); link(cc,[ck,cv]); link(cv,[ck,cc]);
window.addEventListener("resize",function(){ck.resize();cc.resize();cv.resize();});
</script>
</body>
</html>
'''

# 替换占位符
html = html.replace("__JSVARS__", js_vars)
html = html.replace("__N__",     str(len(dates)))
html = html.replace("__C0__",    C0)
html = html.replace("__C1__",    C1)
html = html.replace("__PCTSTR__", PCT_STR)
html = html.replace("__AVGVOL__", str(avg_vol))

with open(HTML_PATH, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"\n🎉 全部完成！")
print(f"   数据来源 : {source}")
print(f"   CSV 数据 : {CSV_PATH}")
print(f"   HTML 面板: {HTML_PATH}")
