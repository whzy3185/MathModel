# ReasLab Visual Final Audit

## Verdict

**PASS — READY FOR FINAL DELIVERY CANDIDATE**

Critical = 0；Major = 0；Minor = 3。三项 Minor 均已在论文中显式说明，不改变核心结论。

## ReasLab / CUMCM structure audit

- 中文国赛结构采用 `ctexart`，问题一至问题四分别拆分成独立 LaTeX 文件。
- 摘要报告四问关键数值；正文按问题分析、模型建立、模型求解、结果分析组织。
- 题目指定日期的充放电与紧急购电详细结果已经从附录提升到正文第 8 节，避免重要赛题结果只藏在附录。
- 显式高教社杯任务保留核心求解代码附录。
- 正文未出现本地路径、result 文件名、agent 交接语、Critical/Major 等内部制作术语。

## Scientific figure audit

- 共 11 幅主图；数据图由 Python/Matplotlib 可复现生成，流程/时序图由 Graphviz 生成。
- 每幅图均提供 300 dpi PNG、PDF、SVG 与 `.png.metadata`；论文正文优先嵌入 PDF 矢量版。
- 采用色盲友好配色和双重编码，不使用 3D、阴影、渐变背景或装饰性图标。
- Q4 causal-vs-oracle 与 Q3 结算敏感性由截断柱状图改为成对点图，避免视觉夸大差异。
- 机制图删除了内部项目管理/审稿措辞，改为成本、风险和稳健性的研究表达。
- 图中文字、坐标轴单位与图例完整；渲染中未发现缺字和重叠。

## Mathematical / computational checks

1. 时间离散 `Δt=1/6 h`，最大单步充放电量 833.333 kWh。
2. SOC 递推 `E_t=E_(t-1)+0.9c_t-d_t/0.9`；确认实验 SOC 位于 1200–10800 kWh，仅有约 1e-11 浮点误差。
3. 跨日连续性误差 = 0；同时充放电次数 = 0。
4. 加入紧急购电后的实际供需平衡最小 slack 约 -1e-13，属于数值容差。
5. Q2/Q3 风险残差均采用 walk-forward，决策日不使用未来真实残差。
6. Q4 正式策略只使用历史价格构造因果预测；真实当日电价只用于结算；完全信息模型只作为 oracle 下界。
7. Q3 下调结算替代解释已完整重算并披露。

## Key evidence

- Q1 费用 **35,126.949 元**，较无储能直购下降 **26.90%**。
- Q2 Feb–Dec 费用 **14,916,093.656 元**；紧急购电 **367,486.925 kWh**。
- Q3 费用 **14,679,141.979 元**，较 Q2 下降 **1.59%**；紧急购电下降 **28.98%**。
- Q3 保守替代结算费用 **14,927,429.698 元**。
- Q4-2 causal **15,774,011.240 元**；Q4-3 causal **15,507,241.002 元**。
- 7 d 滞后价格预测 MAE **0.047151 元/kWh**，corr **0.981085**。
- causal 策略距 perfect-information oracle 约 **1.09% / 1.10%**。

## Paper render audit

- 最新 LaTeX PDF：A4，**28 页**。
- 已渲染全部页面进行 contact-sheet 检查，未发现裁切、覆盖、表格越界、缺失字形或不可读图例。
- 指定日期详细结果位于正文中部，题设输出与模型论证处于同一主证据链。
- LaTeX 日志仍有一个浮动体 `Overfull vbox` 与一个约 2.27 pt 的轻微 `Overfull hbox`；对应页面视觉渲染无裁切或重叠，判定为非阻塞排版警告。
- DOCX 同步版已经重新生成并逐页渲染检查。

## Remaining Minor Issues

1. 附件时点与结果模板区间标签的边界命名存在歧义，按列序一一映射并披露。
2. 题面 90% 效率按充、放电单向效率均为 90% 解释；若按往返效率解释，结果会变化。
3. 题面未给储能退化参数，因此不虚构退化成本，只在模型局限中说明。

## Final Gate

Scientific Visualization: **PASS**  
Paper Construction: **PASS**  
Independent Review: **PASS**  
Workbook Delivery: **PASS**  
Final Delivery Candidate: **YES**
