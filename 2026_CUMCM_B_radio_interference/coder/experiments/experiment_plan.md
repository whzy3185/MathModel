# Experiment Plan v0.1

## E1-Q1 Geometry Correctness
Hypothesis: 半平面交算法能在 bounded-error 模型下始终包含真实源，并正确识别 EMPTY/UNBOUNDED/BOUNDED。

- Variables: 站点数2-8、交会角5°-175°、误差端点/内部。
- Metrics: true-source containment、状态分类、diameter数值误差、coverage-circle判定。
- Seeds: 20260910 + [0..49]。
- Success: 100%约束一致样本包含真实源；退化样本状态与解析预期一致。

## E2-Q2 Active Second Point
Hypothesis: 主动评分策略在相同或更低移动预算下，比固定垂直偏移得到更高的二次保证检测率和更小定位直径。

- Baselines: perpendicular_offset_300, forward_lateral_fixed。
- Metrics: guaranteed-detection rate under R=1000, median/q10 sin(angle), resulting diameter, move time。
- Strong-assumption check: Uniform / edge-heavy / adversarial source samples。

## E3-Q3 Offline Monte Carlo
Hypothesis: 事件驱动策略相对“7哨点全扫完再逐源清除”减少总虚拟时间，同时保持100%清除率。

- N: 10..16。
- Spatial scenarios: uniform disk, boundary-heavy, clustered, adversarial ring。
- R: 1000, Uniform[1000,1500], 1500。
- Bearing errors: uniform, clipped Gaussian, endpoint adversarial。
- Confirmatory runs: >=100 cases/strategy with frozen parameters。

## E4-Q4 Directional Robustness
Hypothesis: s<=1000三角网格能对任意源方向提供至少一次可见扫描点，而Q3圆盘覆盖baseline存在方向性漏检案例。

- Directed proportion: 0,25,50,75,100%。
- Orientation: random + boundary aligned + adversarial half-plane。
- Metrics: first-detection guarantee, total scans, clear rate, total virtual time。

## E5 Official Simulator
- 先演练，保存本地动作日志 + 模拟器日志。
- 只有在参数冻结后进入正式测试。
- 正式测试每问仅3次机会，不用正式机会做探索。
- 表1中的案例编码、清除数、平均定位清除时间、程序运行时间全部由真实日志生成，禁止手工改数字。
