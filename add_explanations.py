#!/usr/bin/env python3
"""为 report.html 添加风险模型和技术指标的通俗解释"""

REPORT_PATH = '/Users/haerangxxi/Desktop/task1/report.html'

with open(REPORT_PATH, 'r') as f:
    html = f.read()

# === 1. 添加 CSS ===
new_css = '''
/* ── 指标解读面板 ── */
.interpret-panel{background:linear-gradient(135deg,#f0f9ff,#e0f2fe);border:1px solid #bae6fd;border-radius:14px;padding:20px 28px;margin:8px 28px 20px}
.interpret-panel h4{font-size:15px;font-weight:700;color:#0c4a6e;margin-bottom:14px}
.interpret-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));gap:12px}
.interpret-item{display:flex;align-items:flex-start;gap:10px;padding:8px 0}
.interpret-icon{width:32px;height:32px;border-radius:8px;display:flex;align-items:center;justify-content:center;flex-shrink:0;font-size:15px}
.interpret-icon.good{background:#dcfce7;color:#16a34a}
.interpret-icon.warn{background:#fef3c7;color:#d97706}
.interpret-icon.info{background:#dbeafe;color:#2563eb}
.interpret-icon.risk{background:#fee2e2;color:#dc2626}
.interpret-body .name{font-size:13px;font-weight:600;color:#334155}
.interpret-body .desc{font-size:12px;color:#64748b;line-height:1.5;margin-top:2px}
/* ── 技术指标解释条 ── */
.tech-explain{padding:8px 20px 14px;font-size:12px;color:#94a3b8;line-height:1.7;border-top:1px dashed #f0f0f0}
.tech-explain strong{color:#64748b}
.tech-explain .good{color:#16a34a;font-weight:600}
.tech-explain .warn{color:#dc2626;font-weight:600}
.tech-explain .info{color:#2563eb;font-weight:600}
'''

# Insert before the first closing </style>
first_style_end = html.index('</style>')
html = html[:first_style_end] + new_css + '\n' + html[first_style_end:]

# === 2. 添加风险指标解读面板 ===
risk_panel = '''
<!-- 指标解读速查 -->
<div class="interpret-panel">
<h4>📖 风险指标速查 — 非专业人士一分钟看懂</h4>
<div class="interpret-grid">
    <div class="interpret-item">
        <div class="interpret-icon risk">📊</div>
        <div class="interpret-body">
            <div class="name">年化波动率</div>
            <div class="desc">衡量股价"上蹿下跳"的幅度。数值越大，每天涨跌越剧烈。50%意味着一年内价格可能在当前价±50%范围内波动，属高波动成长股特征。</div>
        </div>
    </div>
    <div class="interpret-item">
        <div class="interpret-icon risk">⚠️</div>
        <div class="interpret-body">
            <div class="name">VaR（风险价值）</div>
            <div class="desc">"今天最多亏多少"的科学回答。VaR(95%)=-4.23%表示：<strong>有95%的把握，单日亏损不会超过4.23%</strong>。99%更保守，应对极端情况。</div>
        </div>
    </div>
    <div class="interpret-item">
        <div class="interpret-icon risk">📉</div>
        <div class="interpret-body">
            <div class="name">最大回撤</div>
            <div class="desc">过去一年从最高点跌到最低点的最大跌幅。-28.13%意味着<strong>最倒霉的时候账面亏了近三成</strong>。用来评估"最坏情况你能扛住吗"。</div>
        </div>
    </div>
    <div class="interpret-item">
        <div class="interpret-icon good">📈</div>
        <div class="interpret-body">
            <div class="name">夏普比率</div>
            <div class="desc">"每承担1单位风险，能赚多少"。>1算不错，>2算优秀。<strong>1.49意味着冒的风险获得了对等的超额回报</strong>，风险调整后收益良好。</div>
        </div>
    </div>
    <div class="interpret-item">
        <div class="interpret-icon info">🎯</div>
        <div class="interpret-body">
            <div class="name">索提诺比率</div>
            <div class="desc">夏普的"升级版"，只看下跌风险（涨不算风险）。<strong>1.75说明在扣除下跌风险后收益仍然可观</strong>，比夏普更高说明上涨日多于下跌日。</div>
        </div>
    </div>
    <div class="interpret-item">
        <div class="interpret-icon good">💪</div>
        <div class="interpret-body">
            <div class="name">卡玛比率</div>
            <div class="desc">年化收益÷最大回撤。<strong>2.75意味着年均收益约为最大回撤的2.75倍</strong>，"赚到的"覆盖了"亏最多的"，风险补偿充足。</div>
        </div>
    </div>
    <div class="interpret-item">
        <div class="interpret-icon info">🎲</div>
        <div class="interpret-body">
            <div class="name">胜率 & 盈亏比</div>
            <div class="desc"><strong>54%的交易日上涨</strong>，平均涨2.27% vs 跌2.01%。盈亏比1.13说明单次盈利略大于亏损，靠高胜率+正盈亏比双轮驱动。</div>
        </div>
    </div>
    <div class="interpret-item">
        <div class="interpret-icon info">🔗</div>
        <div class="interpret-body">
            <div class="name">Beta（贝塔系数）</div>
            <div class="desc">衡量"大盘涨1%，这股票涨多少"。>1表示比大盘更敏感（涨时多涨、跌时多跌），<1则更稳健。当前数据暂缺，参考行业均值约1.2-1.5。</div>
        </div>
    </div>
</div>
</div>
'''

# Insert before "<!-- 回撤曲线 -->"
html = html.replace('<!-- 回撤曲线 -->', risk_panel + '\n\n<!-- 回撤曲线 -->')

# === 3. 为技术指标添加解释 ===
# RSI explanation
rsi_explain = '''
        <div class="tech-explain">💡 <strong>怎么看：</strong>RSI在0-100之间波动。<span class="warn">高于70=超买</span>（短期涨多了可能回调），<span class="good">低于30=超卖</span>（跌多了可能反弹）。<strong>50是分水岭</strong>，50以上多头占优、50以下空头占优。图中虚线为70/30参考线。</div>
'''
html = html.replace(
    '        <div class="signal-summary">\n            <strong>当前RSI：',
    rsi_explain + '\n        <div class="signal-summary">\n            <strong>当前RSI：',
    1  # only first occurrence (RSI section)
)

# MACD explanation
macd_explain = '''
        <div class="tech-explain">💡 <strong>怎么看：</strong><span class="info">DIF线上穿DEA线=金叉</span>（买入信号），下穿=死叉（卖出信号）。红柱=多头在发力，绿柱=空头在发力。<strong>柱体由绿转红且持续放大=趋势转强</strong>；柱体由红转绿且持续放大=趋势转弱。关注DIF与DEA在零轴上方还是下方。</div>
'''
# Find the MACD signal-summary - it's the one after "MACD" chart-title
html = html.replace(
    '        <div class="signal-summary">\n            <strong>DIF=',
    macd_explain + '\n        <div class="signal-summary">\n            <strong>DIF=',
    1
)

# Bollinger explanation - add after signal-summary in bollinger section
bb_explain = '''
        <div class="tech-explain">💡 <strong>怎么看：</strong>布林带由三条线组成。中轨=20日均线（趋势基准），上轨/下轨=中轨±2倍标准差（统计波动边界）。<span class="info">价格触及上轨=短期偏强但可能超买</span>，<span class="warn">触及下轨=短期偏弱但可能超卖</span>。<strong>带宽收窄=变盘前兆</strong>（波动率压缩到极致后往往跟随大行情），带宽扩张=趋势确认。</div>
'''
html = html.replace(
    '    <div class="signal-summary">\n        <strong>上轨：',
    bb_explain + '\n    <div class="signal-summary">\n        <strong>上轨：',
    1
)

# === 4. 综合信号面板增强 ===
# Add more context to the signal verdict
signal_context = '''        <div class="tech-explain" style="padding-bottom:16px">💡 <strong>综合研判逻辑：</strong>系统自动汇总RSI、MACD、均线排列、布林带四个维度的多空信号。偏多=买入信号多于卖出信号（但并不保证上涨，只是概率更高）。<strong>最终决策需结合基本面、大盘环境和自身风险承受能力。</strong></div>
'''
html = html.replace(
    '        </div>\n    </div>\n</section>\n\n<section class="section" id="forecast">',
    signal_context + '        </div>\n    </div>\n</section>\n\n<section class="section" id="forecast">',
    1
)

with open(REPORT_PATH, 'w') as f:
    f.write(html)

print(f'✅ 指标解释已添加: {REPORT_PATH}')
print(f'   文件大小: {len(html)} 字符')
