from pathlib import Path
import subprocess

ROOT=Path('/mnt/data/C_microgrid_project')
OUT=ROOT/'figures_reaslab'
OUT.mkdir(exist_ok=True)

figs={
'fig01_framework': r'''
digraph G {
  graph [rankdir=LR, bgcolor="white", margin=0.05, pad=0.15, nodesep=0.28, ranksep=0.42];
  node [shape=box, style="rounded", fontname="Noto Sans CJK SC", fontsize=11, margin="0.12,0.08", color="black"];
  edge [fontname="Noto Sans CJK SC", fontsize=9, arrowsize=0.7, color="black"];
  data [label="原始数据\n负载 / 光伏 / 电价 / 预报"];
  audit [label="数据审计\n时间对齐·量纲·缺失·边界"];
  q1 [label="Q1 确定性 LP\n典型日储能调度"];
  q2 [label="Q2 风险修正日前计划\n0.8 分位安全裕度"];
  q3 [label="Q3 滚动时域调整\n0/6/12/18 时更新"];
  q4 [label="Q4 因果价格预测\n7 d 同时刻滞后"];
  valid [label="验证与稳健性\nSOC·功率·供需·敏感性"];
  out [label="综合决策结论\n成本·风险·稳健性"];
  data -> audit -> q1 -> q2 -> q3 -> q4 -> valid -> out;
}
''',
'fig11_q3_rolling_timeline': r'''
digraph G {
  graph [rankdir=LR, bgcolor="white", margin=0.05, pad=0.15, nodesep=0.24, ranksep=0.38];
  node [shape=box, style="rounded", fontname="Noto Sans CJK SC", fontsize=10, margin="0.11,0.07", color="black"];
  edge [fontname="Noto Sans CJK SC", fontsize=8.5, arrowsize=0.7, color="black"];
  n0 [label="0:00\n生成全天计划\n执行 0–6 h"];
  n6 [label="6:00\n读取新 PV 预报\n修正负载\n重优化 6–12 h"];
  n12 [label="12:00\n读取新 PV 预报\n更新当前 SOC\n重优化 12–18 h"];
  n18 [label="18:00\n读取新 PV 预报\n更新夜间负载\n重优化 18–24 h"];
  settle [label="24:00\n按计划、调整与紧急购电\n统一结算"];
  n0 -> n6 -> n12 -> n18 -> settle;
}
'''
}
for stem,dot in figs.items():
    dotfile=OUT/f'{stem}.dot'
    dotfile.write_text(dot,encoding='utf-8')
    for fmt in ['svg','pdf','png']:
        cmd=['dot',f'-T{fmt}',str(dotfile),'-o',str(OUT/f'{stem}.{fmt}')]
        if fmt=='png': cmd.insert(1,'-Gdpi=300')
        subprocess.run(cmd,check=True)
    desc = '统一建模证据链与四问递进关系。' if stem=='fig01_framework' else '问题三从0:00计划到6/12/18时滚动调整的执行时间线。'
    insights = ['四问按照“确定性→不确定性→滚动预报→波动电价”递进。','最终结论同时报告经济性、供电风险与稳健性。'] if stem=='fig01_framework' else ['滚动优化只使用发布时刻之前可获得的信息。','每次重优化仅执行到下一次预报更新，避免未来信息泄露。']
    meta=OUT/f'{stem}.png.metadata'
    meta.write_text('### Visual Metadata for '+stem+'.png\n- **Description**: '+desc+'\n- **Program**: `coder/scripts/make_schematic_figures.py`\n- **Predecessors**:\n  - 赛题原文\n  - modeler/Refinement_Round2.md\n- **Autonomous Insights**:\n'+''.join('  - '+x+'\n' for x in insights),encoding='utf-8')
print('created schematics')
