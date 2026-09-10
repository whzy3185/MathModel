# Candidate Model Pool — v0.2 Decision Record

| ID | 问题 | 方法 | 地位 | 主要优点 | 主要风险 | 当前决定 |
|---|---|---|---|---|---|---|
| Q1-M1 | Q1 | 有界误差半平面交 + MEC | Primary | 完全匹配±1°集合不确定性；清除触发严格 | 需处理退化/量化 | ACCEPT |
| Q1-M2 | Q1 | 标准HPI + rotating calipers | Alternative | 渐近复杂度更好 | 本题规模小，复杂度收益低 | KEEP |
| Q1-B0 | Q1 | 精确测向线LS交点 | Baseline | 简单 | 忽略有界误差 | BASELINE ONLY |
| Q2-M1 | Q2 | 保守扇环四角点 + 1000m交圆候选区 | Primary | 分布无关；给二测可见保证 | 较保守，移动接近1km | ACCEPT |
| Q2-M2 | Q2 | detectability + sin²交会角 + travel期望评分 | Alternative | 平均效率可能更好 | 依赖设计先验 | KEEP AS ALTERNATIVE |
| Q3-M1 | Q3 | 7点覆盖 + opportunistic定位 + nearest clear | Primary | 当前离线样本100%清除且时间最低 | 官方分布未验证 | ACCEPT FOR REHEARSAL |
| Q3-M0 | Q3 | 发现即绕路event-driven | Rejected candidate | 测量次数少 | 大量移动绕路，当前慢约25% | REJECT v0.2 |
| Q3-B0 | Q3 | 7点全频道扫完再定位清除 | Baseline | 确定性强、结构简单 | measure较多 | BASELINE |
| Q4-M1 | Q4 | 1000m三角网格 + 多点交会 + directional fallback | Primary-safe | 任意方向首次发现有解析保证 | 31点扫描较慢 | ACCEPT FOR SAFETY |
| Q4-M2 | Q4 | 安全网格裁剪/动态跳扫 | Refinement | 有望显著提速 | 必须重新证明覆盖 | EXPLORE |
| Q4-B0 | Q4 | 直接复用Q3七点圆盘覆盖 | Baseline | 简单 | 定向盲区可完全漏检 | REJECT AS GUARANTEE |
