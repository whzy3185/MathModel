# Experiment Plan v0.2

所有实验必须区分 `Exploratory` 与 `Confirmatory`；离线开发模拟器仅用于前两者中的算法筛选、边界验证与回归测试。官方演练/正式日志才可支撑最终竞赛性能结论。

## E1 — Q1 Geometry Correctness [Confirmatory-offline]

**Hypothesis**：半平面交算法在题面 bounded-error 条件下包含真实源，并正确处理 BOUNDED / UNBOUNDED / EMPTY；MEC可作为20m清除的严格触发。

- 变量：检测站数量、交会角、误差在区间内部/端点、近共线边界。
- 指标：true-source containment、区域状态、直径、MEC、直径圆判定。
- 随机种子：固定记录。
- 成功条件：所有约束一致随机例包含真实源；解析退化例分类正确；等边三角形反例判定正确。

## E2 — Q2 Robust Second Point [Confirmatory-offline]

**Hypothesis**：保守扇环四角点构造可给出不依赖源位置分布的二次可检测保证。

- Primary：`robust_symmetric_second_points`。
- Alternative：带设计先验的 `E[I(d<=1000) sin^2(alpha)] - lambda*travel`。
- Baseline：固定垂直偏移。
- 指标：对扩大保守扇环的最大距离、移动距离、交会角分位数、二测后定位直径。
- 成功条件：Primary最大距离<=1000m；不同先验只影响二级排序，不影响保证性结论。

## E3 — Q3 Strategy Selection [Exploratory-offline]

**Hypothesis**：直接“发现即清除”会因频繁绕路劣于沿覆盖路线机会式定位、最后集中清除。

- Paired hidden cases：同一批隐藏环境对不同策略复用。
- Strategies：event_driven、scan_then_clear、discover_once_then_clear、opportunistic_then_clear。
- 指标：full-clear ratio、total virtual time、average clear time、measure/clear calls、移动距离、anomaly count。
- 初筛规模：100 paired cases。
- 选择规则：首先100%全清除，其次最小平均/中位总时间；不因测量次数更少而忽略移动代价。

## E4 — Q3 Bounded-error Stress [Confirmatory-offline]

**Hypothesis**：冻结后的 Q3 Primary 在最小接收半径、边界源、聚集源、环形源以及误差端点场景仍保持全清除。

- 场景：uniform/mixed-R、boundary/R=1000/endpoint、clustered/R=1000/+1°、ring/R=1000/-1°。
- 每组至少50例。
- 指标：full-clear、P95 virtual time、measure calls、anomaly count。
- 失败条件：任何漏清、假EMPTY、死循环或异常退出；必须进入 `reviewer/anomaly_log.csv` 并重建受影响结果。

## E5 — Q4 Directional Robustness [Confirmatory-offline]

**Hypothesis**：边长<=1000m三角网格保证任意方向定向源至少有一个可见扫描点；定向 fallback 能从一个已知可见点持续获得可见进展直到MEC<=20或near/clear。

- Directed proportion：0/50/100%。
- R：重点 R=1000。
- Error：endpoint_hash、+1°、-1°。
- 指标：full-clear、virtual time、measure calls、fallback steps、anomaly count。
- 额外证明检验：密集枚举目标位置和半平面方向，确认至少一个1000m内网格顶点位于可见半平面。

## E6 — Q4 Efficiency Refinement [Exploratory-offline]

**Hypothesis**：在不改变“首次发现保证”的前提下，可通过网格节点裁剪、频道分组、已见频道跳扫、局部信息增益调度减少总虚拟时间和fallback次数。

- Baseline：31点全频道安全扫描。
- Candidate：边界三角形精确裁剪 / 访问次序优化 / 动态频道集合。
- Gate：任意候选先通过方向保证测试，再比较性能；若保证破坏则拒绝。

## E7 — Official Simulator Rehearsal [Required]

- 在参赛电脑运行 `simulator_client.py` 接入 localhost。
- 先问题3演练，再问题4演练。
- 保存本地 JSONL 动作日志和模拟器导出日志；失败运行不删除。
- 用真实演练估计策略时间、请求数、正式日志大小、程序现实耗时。
- 若官方演练暴露与离线规则不一致的行为，建立 `Evidence Conflict`，从 Modeler/Coder 上游修复。

## E8 — Formal Tests [Final evidence]

- 参数、代码和停止规则在正式测试前冻结。
- Q3三次 + Q4三次，不用正式机会做探索。
- 每次记录案例编码、清除个数、平均定位清除时间、程序运行时间。
- 保留模拟器原名加密行为日志并放入支撑材料。
- 表1必须由日志解析生成，禁止手工修改数字。
