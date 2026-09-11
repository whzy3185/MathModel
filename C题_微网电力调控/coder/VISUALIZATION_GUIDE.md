# C题科研绘图工具链与版式规范（ReasLab 对齐版）

## 1. 工具选型

本项目不使用生成式图片替代定量图。数据图优先采用 **Python + Matplotlib**，因为能够从原始数据和计算结果直接复现，并可同时导出 PNG（300 dpi）与 PDF/SVG 矢量图。流程图和滚动控制时间线采用 **Graphviz**。若需要人工精修，可使用 **Inkscape / Adobe Illustrator** 对 SVG/PDF 做字体、对齐、组合和留白微调，但不得修改数据点和数值含义。

科研常用工具链分三层：

1. **数据驱动图**：Python/Matplotlib、Origin/OriginPro。数模项目首选 Python；Origin 更适合交互式拟合和实验曲线快速调整。
2. **结构/机制/流程图**：Graphviz、draw.io、PowerPoint；生命科学机制图可使用 BioRender。数模中的算法框架与时间线优先 Graphviz/draw.io。
3. **出版级矢量精修**：Adobe Illustrator 或开源 Inkscape，只进行排版精修。

ReasLab `visualizer` 的要求是：每张图有可复现绘图程序，输出 300 dpi 图像，并配套 `.png.metadata`，记录图意、数据源和程序计算的统计洞察。本项目按此规则输出 PNG/PDF/SVG 与 metadata。

## 2. 科研图版式

- 中文图题、坐标轴、图例；坐标轴必须带单位；
- 单图约 6.8--7.2 in 宽；正文优先使用 PDF 矢量版本；
- PNG 仅用于预览，统一 300 dpi；
- 不使用 3D 柱状图、阴影、渐变背景、装饰性图标；
- 不画无意义背景网格，减少视觉噪声；
- 多序列同时依靠颜色 + 线型/标记/位置区别，不只依赖红绿颜色；
- 数字标注只保留支持比较的关键值；
- 图注说明“该图回答什么问题”，正文解释机制和现实含义。

这一方向与 Nature Research Figure Guide 一致：保证文字可读、轴标签完整、避免背景网格和多余装饰、避免色盲不友好的配色。

## 3. 关于“小红书科研绘图”参考

公开搜索引擎对小红书具体科研笔记的索引并不稳定，因此不把社交平台内容当作技术规范。科研社区常见路线是“**Origin/Python 出数据图 → Illustrator/Inkscape 做矢量精修**”。本项目吸收这一工作流，但最终标准仍以可复现性、竞赛论文规范和科研出版规范为准。

## 4. 本项目实际采用

- `fig01_framework`：Graphviz，统一建模框架；
- `fig02_load_pv`：Matplotlib，负载与光伏典型日剖面；
- `fig03_price_profile`：Matplotlib，典型日电价；
- `fig04_q1_dispatch`：Matplotlib，无储能净负荷与优化购电曲线；
- `fig05_quantile_sensitivity`：Matplotlib，风险分位敏感性；
- `fig06_forecast_mae`：Matplotlib，滚动预测误差；
- `fig07_forecast_selection`：Matplotlib，各发布时刻外部预报选择率；
- `fig08_emergency_reduction`：Matplotlib，Q2/Q3 紧急购电对比；
- `fig09_causal_oracle`：Matplotlib，因果策略与完全信息下界；
- `fig10_settlement_sensitivity`：Matplotlib，结算解释敏感性；
- `fig11_q3_rolling_timeline`：Graphviz，问题三滚动优化时间线。

每幅图同时提供 `.png`、`.pdf`、`.svg` 和 `.png.metadata`。

## 5. 第三轮图形优化

结合 ReasLab `visualizer` 和科研出版图规范，本轮进一步统一：

- 数据图采用 Okabe–Ito 色盲友好配色，并同时使用线型、点型或位置进行双重编码；
- PDF/SVG 保留可编辑文字；
- 不使用截断纵轴的柱状图夸大小差异。Q4 causal-vs-oracle、Q3 两种结算口径均改为**成对点图**；
- 定量柱状图从 0 基线开始；时间序列图不添加无必要背景网格；
- 机制图只表达研究逻辑与因果信息约束，不出现项目管理或内部审稿术语；
- 论文正文使用 PDF 矢量图，PNG 只用于快速预览与 QA。

## 6. 公开参考

- ReasLab MathModelingAgent-CodexBundle visualizer skill
- ReasLab CUMCM writing skill
- Nature Research Figure Guide
- Fujii, R. *How to design effective scientific figures*. Nature Human Behaviour, 2026.
