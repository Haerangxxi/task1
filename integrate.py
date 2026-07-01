#!/usr/bin/env python3
"""Integrate risk_forecast_block.html into report.html"""

REPORT_PATH = '/Users/haerangxxi/Desktop/task1/report.html'
BLOCK_PATH  = '/Users/haerangxxi/Desktop/task1/risk_forecast_block.html'

with open(REPORT_PATH, 'r') as f:
    report = f.read()

with open(BLOCK_PATH, 'r') as f:
    block = f.read()

# 1. Add new CSS rules before </style>
new_css = '''
/* ── 风险模型 ── */
.section-header{display:flex;align-items:center;gap:12px;padding:20px 28px 16px;border-bottom:1px solid #f0f0f0;font-size:18px;font-weight:700;color:#2c3e50}
.section-icon{font-size:22px}
.risk-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:16px;padding:24px 28px}
.risk-sub-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:16px;padding:0 28px 24px}
.risk-card{background:#f7f9fc;border-radius:12px;padding:18px 20px;text-align:center;transition:.2s}
.risk-card:hover{transform:translateY(-2px);box-shadow:0 4px 12px rgba(0,0,0,.08)}
.risk-card-sm{padding:14px 16px}
.risk-label{font-size:13px;color:#888;margin-bottom:8px}
.risk-value{font-size:28px;font-weight:800;color:#2c5364}
.risk-value.var-neg{color:#e74c3c}
.risk-sub{font-size:12px;color:#aaa;margin-top:6px}
/* ── 图表卡片 ── */
.chart-card{margin:0 28px 24px;background:#fff;border-radius:12px;border:1px solid #f0f0f0;overflow:hidden}
.chart-card.wide{margin-bottom:8px}
.chart-title{font-size:15px;font-weight:600;color:#555;padding:16px 20px 0;margin-bottom:4px}
.chart-wrap{width:100%}
.charts-row{display:flex;gap:16px;padding:0 28px 24px;flex-wrap:wrap}
.charts-row .chart-card{flex:1;min-width:340px;margin:0}
.chart-card.half{flex:1;min-width:400px}
/* ── 信号面板 ── */
.signal-summary{padding:8px 20px 16px;font-size:14px;color:#555;display:flex;align-items:center;gap:12px}
.signal-summary .tag{padding:4px 12px;border-radius:20px;font-size:12px;font-weight:600}
.tag-bullish{color:#fff;background:#27ae60}
.tag-bearish{color:#fff;background:#e74c3c}
.tag-neutral{color:#666;background:#f0f0f0}
.tag-neutral_bull{color:#27ae60;background:#e8f8ef}
.tag-neutral_bear{color:#e74c3c;background:#fde8e8}
.signal-panel{padding:16px 20px}
.signal-list{display:flex;flex-wrap:wrap;gap:10px;margin-bottom:16px}
.signal-item{padding:6px 14px;border-radius:20px;font-size:13px;font-weight:500}
.signal-bullish{color:#fff;background:#27ae60}
.signal-bearish{color:#fff;background:#e74c3c}
.signal-neutral_bull{color:#27ae60;background:#e8f8ef;border:1px solid #a3e4c1}
.signal-neutral_bear{color:#e74c3c;background:#fde8e8;border:1px solid #f5b7b7}
.signal-neutral{color:#888;background:#f0f0f0}
.signal-verdict{padding:12px 16px;background:linear-gradient(135deg,#0f2027,#203a43);color:#fff;border-radius:10px;font-size:15px}
/* ── 预测卡片 ── */
.forecast-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:16px;padding:24px 28px}
.forecast-card{background:#f7f9fc;border-radius:14px;padding:20px;text-align:center;transition:.2s}
.forecast-card:hover{transform:translateY(-2px);box-shadow:0 4px 14px rgba(0,0,0,.08)}
.forecast-card.forecast-up{background:linear-gradient(135deg,#e8f8ef,#d4edda)}
.forecast-label{font-size:13px;color:#888;margin-bottom:10px}
.forecast-value{font-size:32px;font-weight:900;color:#2c5364}
.forecast-sub{font-size:12px;color:#aaa;margin-top:8px}
/* ── 情景表格 ── */
.scenario-table{width:100%;border-collapse:collapse;margin:12px 0;font-size:14px}
.scenario-table th{background:#f7f9fc;padding:10px 14px;text-align:left;font-weight:600;color:#555;border-bottom:2px solid #e8ecf0}
.scenario-table td{padding:10px 14px;border-bottom:1px solid #f0f0f0;color:#2c3e50}
.scenario-table .scenario-bull td{background:#f0fdf4}
.scenario-table .scenario-bear td{background:#fef2f2}
.scenario-table .scenario-extreme td{background:#fff7ed}
.scenario-table .up{color:#e74c3c;font-weight:600}
.scenario-table .down{color:#27ae60;font-weight:600}
/* ── 免责声明 ── */
.disclaimer-block{padding:16px 28px 24px}
.disclaimer-block p{font-size:12px;color:#aaa;line-height:1.7}
'''

report = report.replace('</style>', new_css + '\n</style>')

# 2. Add new navigation links
old_nav_items = '<a href="#conclusion">投资结论</a>'
new_nav_items = '<a href="#risk">风险模型</a>\n  <a href="#technicals">技术指标</a>\n  <a href="#forecast">股价预测</a>\n  <a href="#conclusion">投资结论</a>'
report = report.replace(old_nav_items, new_nav_items)

# 3. Insert HTML sections before </div><!-- /container -->
insert_point = '</div><!-- /container -->'
# Extract HTML part only (everything before <script>)
block_html, block_script = block.split('<script>', 1)
block_script = '<script>' + block_script

report = report.replace(insert_point, block_html + '\n' + insert_point)

# 4. Insert JS before </body>
# Find the last <script> closing tag and insert before it
last_script_close = report.rfind('</script>')
body_close = report.rfind('</body>')

# The new JS should go before </script> that's before </body>
# Let's find the second-to-last </script>... actually, just insert before </body>
report_without_body = report[:body_close]
report_after_body   = report[body_close:]

# Insert the new JS script right before </body>
# Extract just the JS content (between <script> and </script>)
block_js_content = block_script.replace('<script>', '').replace('</script>', '').strip()
# Wrap in a new script tag
new_js_block = f'\n<script>\n{block_js_content}\n</script>\n'

report = report_without_body + new_js_block + report_after_body

# Write the new report
with open(REPORT_PATH, 'w') as f:
    f.write(report)

print(f'✅ 报告已整合完成: {REPORT_PATH}')
print(f'   文件大小: {len(report)} 字符')
