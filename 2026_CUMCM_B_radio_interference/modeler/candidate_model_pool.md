# Candidate Model Pool

见 `modeling_brief.md` 第五节。本文件用于后续版本比较记录。

| ID | 问题 | 方法 | 地位 | 主要优点 | 主要风险 | 当前决定 |
|---|---|---|---|---|---|---|
| Q1-M1 | Q1 | 半平面交集合定位 | Primary | 与±1°有界误差完全一致，可验证 | 需处理空/无界/退化 | ACCEPT |
| Q1-M2 | Q1 | 标准HPI | Alternative | O(n log n)成熟 | 实现复杂、n很小时收益小 | KEEP |
| Q1-B0 | Q1 | 精确直线LS | Baseline | 简单 | 忽略有界误差 | BASELINE ONLY |
| Q2-M1 | Q2 | detectability+angle+travel主动设计 | Primary | 直接针对题意 | 权重需敏感性 | ACCEPT |
| Q2-M2 | Q2 | minimax低分位 | Alternative | 分布无关更稳健 | 可能过保守 | KEEP |
| Q3-M1 | Q3 | 覆盖+事件驱动 | Primary | 兼顾找全和尽快清 | 调度较复杂 | ACCEPT |
| Q3-B0 | Q3 | 固定哨点全扫后清 | Baseline | 可给保证、易复现 | 时间较长 | BASELINE |
| Q4-M1 | Q4 | 三角网格+对称侧探 | Primary | 任意方向可见性证明 | 扫描节点较多 | ACCEPT |
| Q4-B0 | Q4 | 复用Q3圆覆盖 | Baseline | 简单 | 对定向源无保证 | REJECT AS PRIMARY |
