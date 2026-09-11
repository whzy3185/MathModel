import json
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import font_manager

ROOT = Path('/mnt/data/C_microgrid_project')
OUT = ROOT / 'figures_reaslab'
OUT.mkdir(parents=True, exist_ok=True)
DATA = json.loads(Path('/mnt/data/plot_data.json').read_text(encoding='utf-8'))

# Publication-oriented Chinese typography; no decorative style preset.
font_path = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
font = font_manager.FontProperties(fname=font_path).get_name()
plt.rcParams['font.family'] = font
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['font.size'] = 10
plt.rcParams['axes.titlesize'] = 12
plt.rcParams['axes.labelsize'] = 10
plt.rcParams['legend.fontsize'] = 9
plt.rcParams['xtick.labelsize'] = 9
plt.rcParams['ytick.labelsize'] = 9
plt.rcParams['axes.spines.top'] = False
plt.rcParams['axes.spines.right'] = False
plt.rcParams['axes.linewidth'] = 0.8
plt.rcParams['xtick.direction'] = 'out'
plt.rcParams['ytick.direction'] = 'out'
plt.rcParams['pdf.fonttype'] = 42
plt.rcParams['ps.fonttype'] = 42
plt.rcParams['svg.fonttype'] = 'none'

# Okabe-Ito color-blind-safe palette.
BLUE = '#0072B2'
ORANGE = '#E69F00'
GREEN = '#009E73'
VERMILLION = '#D55E00'
SKY = '#56B4E9'
PURPLE = '#CC79A7'
BLACK = '#222222'
GRAY = '#777777'


def save(fig, stem, description, predecessors, insights):
    for ext in ['png','svg','pdf']:
        path = OUT / f'{stem}.{ext}'
        if ext == 'png':
            fig.savefig(path, dpi=300, bbox_inches='tight', facecolor='white')
        else:
            fig.savefig(path, bbox_inches='tight', facecolor='white')
    meta = OUT / f'{stem}.png.metadata'
    text = [f'### Visual Metadata for {stem}.png',
            f'- **Description**: {description}',
            f'- **Program**: `coder/scripts/make_reaslab_figures.py`',
            '- **Predecessors**:']
    text += [f'  - {p}' for p in predecessors]
    text += ['- **Autonomous Insights**:']
    text += [f'  - {k}: {v}' for k,v in insights.items()]
    meta.write_text('\n'.join(text)+'\n', encoding='utf-8')
    plt.close(fig)

load = np.array(DATA['attachment1']['load'], float)
pv = np.array(DATA['attachment1']['pv'], float)
price = np.array(DATA['attachment1']['price'], float)
x = np.arange(1,145)/6

fig, ax = plt.subplots(figsize=(7.2,4.2))
ax.plot(x, load, linewidth=1.8, color=BLUE, label='小区负载')
ax.plot(x, pv, linewidth=1.8, color=ORANGE, label='光伏预测功率')
ax.set_xlabel('时间 / h'); ax.set_ylabel('功率 / kW')
ax.set_title('典型日负载与光伏功率剖面')
ax.set_xlim(0,24); ax.set_xticks(np.arange(0,25,4)); ax.legend(frameon=False)
save(fig,'fig02_load_pv','展示典型日负载与光伏功率的日内错峰关系。',['附件1.xlsx'],{
    '负载峰值': f'{load.max():.1f} kW，出现在约 {x[load.argmax()]:.2f} h',
    '光伏峰值': f'{pv.max():.1f} kW，出现在约 {x[pv.argmax()]:.2f} h',
    '光伏高于负载的时段数': f'{int(np.sum(pv>load))} 个10 min时段',
    '日均负载': f'{load.mean():.1f} kW', '日均光伏': f'{pv.mean():.1f} kW'})

fig, ax = plt.subplots(figsize=(7.2,3.9))
ax.plot(x, price, linewidth=1.8, color=BLUE)
ax.set_xlabel('时间 / h'); ax.set_ylabel('电价 / (元·kWh$^{-1}$)')
ax.set_title('典型日外网电价曲线'); ax.set_xlim(0,24); ax.set_xticks(np.arange(0,25,4))
save(fig,'fig03_price_profile','展示典型日电价的峰谷结构，为储能套利解释提供依据。',['附件1.xlsx'],{
    '最低电价':f'{price.min():.4f} 元/kWh','最高电价':f'{price.max():.4f} 元/kWh',
    '峰谷价差':f'{price.max()-price.min():.4f} 元/kWh','最高价时刻':f'约 {x[price.argmax()]:.2f} h'})

net = np.maximum(load-pv,0)/6
q1g = np.array(DATA['q1']['grid_kwh'],float)
fig, ax = plt.subplots(figsize=(7.2,4.2))
ax.plot(x, net, linewidth=1.6, color=GRAY, linestyle='--', label='无储能净负荷购电需求')
ax.plot(x, q1g, linewidth=1.8, color=BLUE, label='优化后外网购电量')
ax.set_xlabel('时间 / h'); ax.set_ylabel('10 min 电量 / kWh')
ax.set_title('问题一：储能调度对外网购电曲线的重塑')
ax.set_xlim(0,24); ax.set_xticks(np.arange(0,25,4)); ax.legend(frameon=False)
save(fig,'fig04_q1_dispatch','比较无储能净负荷需求与优化后的外网购电时序。',['附件1.xlsx','results/result1.xlsx'],{
    '优化购电总量':f'{q1g.sum():.3f} kWh','无储能净负荷总量':f'{net.sum():.3f} kWh',
    '最大单时段购电量':f'{q1g.max():.3f} kWh','零购电时段数':str(int(np.sum(q1g<1e-9)))})

q=np.array(DATA['risk_sensitivity']['q'],float)
q2=np.array(DATA['risk_sensitivity']['q2_cost'],float)/1e6
q3=np.array(DATA['risk_sensitivity']['q3_cost'],float)/1e6
fig, ax=plt.subplots(figsize=(6.8,4.1))
ax.plot(q,q2,marker='o',linewidth=1.7,color=BLUE,label='Q2')
ax.plot(q,q3,marker='s',linewidth=1.7,color=ORANGE,label='Q3')
ax.set_xlabel('风险分位数 $q$'); ax.set_ylabel('2–12月总费用 / 百万元')
ax.set_title('风险分位数敏感性'); ax.set_xticks(q); ax.legend(frameon=False)
save(fig,'fig05_quantile_sensitivity','比较Q2/Q3在不同风险分位数下的全年费用。',['writer/Paper_Final.md'],{
    'Q2最低费用分位':f'q={q[q2.argmin()]:.1f}','Q3最低费用分位':f'q={q[q3.argmin()]:.1f}',
    'Q2_q0.8费用':f'{q2[1]:.3f} 百万元','Q3_q0.8费用':f'{q3[1]:.3f} 百万元'})

hour=np.array(DATA['forecast_mae']['hour'],float)
mae=np.array(DATA['forecast_mae']['net_load_mae'],float)
fig,ax=plt.subplots(figsize=(6.8,4.1))
ax.plot(hour,mae,marker='o',linewidth=1.8,color=BLUE)
ax.set_xlabel('预报发布时刻'); ax.set_ylabel('剩余净负荷 MAE / kW')
ax.set_title('日内滚动更新后的净负荷预测误差'); ax.set_xticks(hour,[f'{int(h)}:00' for h in hour])
save(fig,'fig06_forecast_mae','展示日内信息更新后剩余净负荷预测误差的变化。',['writer/Paper_Final.md'],{
    '0:00 MAE':f'{mae[0]:.2f} kW','18:00 MAE':f'{mae[-1]:.2f} kW',
    '相对降幅':f'{(1-mae[-1]/mae[0])*100:.2f}%','单调下降':str(bool(np.all(np.diff(mae)<0)))})

sel=np.array(DATA['forecast_mae']['external_selection_rate'],float)
fig,ax=plt.subplots(figsize=(6.8,4.1))
ax.bar(np.arange(len(hour)),sel,width=0.58,color=BLUE,edgecolor='black',linewidth=0.45)
ax.set_xlabel('预报发布时刻'); ax.set_ylabel('外部光伏预报选择率 / %')
ax.set_title('滚动择优中外部光伏预报的采用比例')
ax.set_xticks(np.arange(len(hour)),[f'{int(h)}:00' for h in hour]); ax.set_ylim(0,110)
for i,v in enumerate(sel): ax.text(i,v+3,f'{v:.1f}%',ha='center',va='bottom',fontsize=8)
save(fig,'fig07_forecast_selection','展示四个发布时刻外部光伏预报被滚动择优机制采用的比例。',['writer/Paper_Final.md'],{
    '6:00选择率':f'{sel[1]:.1f}%','12:00选择率':f'{sel[2]:.1f}%',
    '0:00选择率':f'{sel[0]:.2f}%','18:00选择率':f'{sel[3]:.2f}%'})

m=DATA['main_metrics']
fig,ax=plt.subplots(figsize=(5.8,4.0))
vals=np.array([m['q2_emergency'],m['q3_emergency']])/1000
bars=ax.bar(['Q2','Q3'],vals,width=0.52,color=[GRAY,BLUE],edgecolor='black',linewidth=0.45)
ax.set_ylabel('2–12月紧急购电量 / MWh'); ax.set_title('滚动调整降低紧急购电暴露')
for b,v in zip(bars,vals): ax.text(b.get_x()+b.get_width()/2,v+3,f'{v:.1f}',ha='center',fontsize=9)
save(fig,'fig08_emergency_reduction','比较Q2和Q3的紧急购电总量。',['results/result2.xlsx','results/result3.xlsx'],{
    'Q2紧急购电':f'{vals[0]:.3f} MWh','Q3紧急购电':f'{vals[1]:.3f} MWh','降幅':f'{(1-vals[1]/vals[0])*100:.2f}%'})

# Paired dot plot: avoids a truncated bar-chart baseline.
q42_pair=np.array([m['q42_oracle'],m['q42_cost']])/1e6
q43_pair=np.array([m['q43_oracle'],m['q43_cost']])/1e6
fig,ax=plt.subplots(figsize=(6.8,4.1))
for xpos, pair in [(0,q42_pair),(1,q43_pair)]:
    ax.plot([xpos,xpos], pair, color=GRAY, linewidth=1.2, zorder=1)
    ax.scatter([xpos-0.04],[pair[0]],s=42,color=ORANGE,marker='o',label='完全信息下界' if xpos==0 else None,zorder=3)
    ax.scatter([xpos+0.04],[pair[1]],s=46,color=BLUE,marker='s',label='因果价格策略' if xpos==0 else None,zorder=3)
    ax.text(xpos-0.06,pair[0]-0.025,f'{pair[0]:.3f}',ha='right',va='top',fontsize=8)
    ax.text(xpos+0.06,pair[1]+0.020,f'{pair[1]:.3f}',ha='left',va='bottom',fontsize=8)
ax.set_xticks([0,1],['Q4-2','Q4-3']); ax.set_ylabel('2–12月总费用 / 百万元')
ax.set_title('因果价格策略与完全信息下界'); ax.set_xlim(-0.45,1.45); ax.legend(frameon=False,loc='upper right')
save(fig,'fig09_causal_oracle','以成对点图比较严格因果价格预测调度与完全预知价格Oracle的费用，避免截断柱状图夸大差异。',['coder/logs/refinement_round2.json'],{
    'Q4-2因果溢价':f'{(m["q42_cost"]/m["q42_oracle"]-1)*100:.3f}%',
    'Q4-3因果溢价':f'{(m["q43_cost"]/m["q43_oracle"]-1)*100:.3f}%',
    'Q4-3相对Q4-2节省':f'{(1-m["q43_cost"]/m["q42_cost"])*100:.3f}%'})

# Paired points for a small relative settlement difference.
vals=np.array([m['q3_cost'],m['q3_alt_cost']])/1e6
fig,ax=plt.subplots(figsize=(6.2,4.0))
ax.plot([0,1],vals,color=GRAY,linewidth=1.2,zorder=1)
ax.scatter([0],[vals[0]],s=52,color=BLUE,marker='o',zorder=3)
ax.scatter([1],[vals[1]],s=52,color=ORANGE,marker='s',zorder=3)
ax.set_xticks([0,1],['主结算口径','保守替代口径']); ax.set_ylabel('2–12月总费用 / 百万元')
ax.set_title('问题三结算规则解释的敏感性')
for i,v in enumerate(vals): ax.text(i,v+0.025,f'{v:.3f}',ha='center',fontsize=8)
ax.text(0.5,vals.mean()-0.035,f'相对差异 +{(vals[1]/vals[0]-1)*100:.2f}%',ha='center',fontsize=9)
save(fig,'fig10_settlement_sensitivity','以成对点图比较问题三两种结算规则解释下的总费用。',['coder/logs/refinement_round2.json'],{
    '主口径费用':f'{m["q3_cost"]:.3f} 元','替代口径费用':f'{m["q3_alt_cost"]:.3f} 元',
    '相对差异':f'{(m["q3_alt_cost"]/m["q3_cost"]-1)*100:.2f}%'})

print('created', len(list(OUT.glob('*.png'))), 'PNG figures in', OUT)
