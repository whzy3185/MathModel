# 2026 高教社杯 C 题：微网与外部电网电力调控策略

本目录是分支 `c` 的完整数学建模工作空间。最新一轮已按 `reaslab/MathModelingAgent-CodexBundle` 的 CUMCM、visualizer 与 pre-submission-reviewer 规范重构论文与科研图件：保留 Modeler / Coder / Writer / Reviewer 证据边界，论文按问题拆分，定量图全部由可复现程序生成，并同时输出矢量版本与统计 metadata。

## 当前 Gate

- Problem Understanding: **PASS**
- Data Audit: **PASS**
- Model Specification: **PASS**
- Implementation: **PASS**
- Numerical Experiments: **PASS**
- Result Validation: **PASS**
- Model Refinement: **PASS**
- Scientific Visualization: **PASS**
- Paper Construction: **PASS**
- Independent Review: **PASS**
- Workbook Delivery: **PASS**
- Final Delivery Candidate: **YES**

## 核心模型

1. **问题 1**：10 min 离散确定性线性规划，直接优化外网购电和储能充放电。
2. **问题 2**：逐日递推负载/光伏预测 + 28 d 残差 0.8 分位风险裕度 + 储能 LP。
3. **问题 3**：0:00 日前计划 + 6/12/18 时滚动调整；外部光伏预报与历史预测按滚动 MAE 择优，并用当日已观测负载修正剩余时段。
4. **问题 4**：7 d 同时间隔价格预测满足非前视信息约束；真实当日电价仅用于结算，完全信息模型只作为 oracle 下界。

## 关键结果

- Q1：全天购电量 **59,482.699 kWh**，费用 **35,126.949 元**，较无储能直购方案下降 **26.90%**。
- Q2（2/1–12/31）：总费用 **14,916,093.656 元**，紧急购电 **367,486.925 kWh**。
- Q3：总费用 **14,679,141.979 元**，较 Q2 下降 **1.59%**；紧急购电下降 **28.98%**。
- Q3 保守结算替代解释：总费用 **14,927,429.698 元**，与主口径相差约 **1.69%**。
- Q4-2 causal：**15,774,011.240 元**；Q4-3 causal：**15,507,241.002 元**，后者下降 **1.6912%**。
- Q4 perfect-information oracle：**15,603,450.520 / 15,338,096.770 元**；causal 策略仅高约 **1.09% / 1.10%**。
- 7 d 滞后价格预测：MAE **0.047151 元/kWh**，相关系数 **0.981085**。

## ReasLab 对齐后的论文结构

`writer/` 采用中文 CUMCM 风格的 LaTeX 文件树：

- `main.tex`
- `abstract.tex`
- `01-restatement.tex`
- `02-assumptions.tex`
- `03-q1.tex` ~ `06-q4.tex`
- `07-results.tex`
- `evaluation.tex`
- `appendix.tex`
- `references.bib` / `references_manual.tex`
- `core_solver.py`
- `Paper_Final.md / .docx / .pdf`

题目指定日期的充放电与紧急购电详细结果已从附录提升到**正文第 8 节**，使赛题要求、模型和数值证据处于同一正文链条。最终 PDF 为 A4、28 页，并已逐页渲染检查。

## 科研绘图工具链

- **数据图**：Python + Matplotlib，300 dpi PNG + PDF/SVG 矢量输出；采用色盲友好配色和双重编码。
- **流程/时间线**：Graphviz，输出 PDF/SVG。
- **人工精修建议**：Adobe Illustrator 或开源 Inkscape，仅做字体、对齐、组合与留白调整，不改数据。
- 每幅图强制生成 `.png.metadata`，记录数据血缘、绘图程序和程序计算得到的统计洞察。
- 不使用生成式 AI 替代定量图；不使用 3D、阴影、渐变或截断柱状图夸大差异。

## 目录说明

- `problem/`：赛题与原始附件，保持只读。
- `modeler/`：Modeling Brief、方法检索、模型规格和改进记录。
- `coder/`：求解代码、实验/验证日志、科研图脚本和可视化规范。
- `figures_reaslab/`：ReasLab 对齐图件（PNG/PDF/SVG + metadata）。
- `results/`：`result1.xlsx` ~ `result4-3.xlsx`。
- `writer/`：论文源文件与最终 PDF/DOCX/Markdown。
- `reviewer/`：最终审查记录。

## 仍需明确的三项模型边界

1. 附件时点与结果模板区间标签存在首末边界命名差异，按列序一一映射并在论文中披露。
2. “充放电效率 90%”按充、放电单向效率各 90% 处理；若解释为总往返效率，数值会改变。
3. 题面未给储能退化参数，因此不虚构退化成本，只在模型局限中说明。
