# Reviewer Round 2 — Evidence-first Review

## Verdict

**PASS FOR PAPER CONSTRUCTION; FINAL DELIVERY HAS ONE TECHNICAL BLOCKER.**

Critical = 0；Major modeling defects = 0；Technical blocker = 1。

## Attack matrix updates

### Q3 settlement ambiguity — RESOLVED TO REVIEW STANDARD
Responsible Role: Modeler.  
Rework Mode: local-repair + sensitivity experiment.

主结算公式已写成显式分段等价式，并增加“计划费之外再加 50% 罚金”的保守替代实验。两种解释均完成全年数值求解与约束验证。费用差约 1.69%，但滚动调整的可靠性价值没有消失。因此论文可保留主解释，但必须把替代口径列为敏感性/局限性，不能把口径当成唯一事实。

### Q4 price leakage — RESOLVED
Responsible Role: Modeler + Coder.  
Rework Mode: upstream-rebuild from Q4 specification.

第一轮“当天真实价格全知”已降级为 oracle 下界。正式 Q4 使用 d-7 同时段价格预测，决策仅见历史价格，结算见实际价格。预测 MAE=0.04715 元/kWh，Q4-2/4-3 因果策略距 oracle 约 1.09%/1.10%，且 Q4-3 仍比 Q4-2 低 1.6912%。PASS。

### Time-boundary convention — ACCEPT WITH DISCLOSURE
附件时点与模板区间标签存在边界命名差异。按列位置一一映射与官方模板保持完整 144 列，不进行人工循环平移。论文需在数据预处理中说明。若赛事官方后续给出解释，应立即按官方口径重导出而不改变模型主体。

### Constraint / reproducibility audit — PASS
Round-2 `validation_round2.json` 表明 causal Q4 与 Q3 alternative 均满足 SOC、功率、跨日连续、供需平衡与充放电互斥的数值检查。

## Technical blocker

`result4-3.xlsx` 因果版写回模板时当前 artifact_tool RPC 在大表导出阶段超时。`state/q4_3_causal.npz`、数值汇总与验证均已经存在，因此这是交付工件问题，不是数学/计算结论缺失。最终交付前必须完成该 Excel 写回并重新做抽样核对。

## Gate
- Mathematical correctness: PASS
- Causal information structure: PASS
- Evidence chain: PASS
- Paper construction: PASS
- Final delivery: BLOCKED ONLY BY causal `result4-3.xlsx` export
