# Method Review — Microgrid Scheduling / MPC / Uncertainty

## Purpose

本项目的方法检索只用于构造候选模型池，不把文献中的方法直接视为对本题适用性的证明。最终模型仍以赛题数据结构、可解释性、因果信息结构和可验证性为优先。

## 1. 线性/混合整数优化用于微网调度

Umeozor 与 Trifkovic（2016）将包含光伏、风电、储能与外网的微网运行调度写成参数化混合整数线性规划，目标为运行净成本最小化，并讨论不同电价结构。这说明将微网能量平衡、储能状态和购电成本组织为线性优化框架是成熟路线。

本题中没有启停机组、互斥离散选择等必须二进制变量的结构；在正电价且储能效率低于 1 时，LP 数值解自然不存在同时充放电，因此选择 LP 而非 MILP。

Reference: E. C. Umeozor, M. Trifkovic, “Operational scheduling of microgrids via parametric programming,” *Applied Energy*, 180 (2016), 672–681. DOI: 10.1016/j.apenergy.2016.08.009.

## 2. MPC / Rolling Horizon 用于光伏—储能微网

Hu, Xu, Cheng 与 Guerrero（2018）研究 PV-Battery 微网，在光伏与负载变化下采用模型预测控制，并通过更新状态维持功率平衡与储能运行。其思想与本题问题 3 的“0/6/12/18 时获得新预报后调整策略”高度匹配，因此把问题 3 组织为滚动时域优化，而不是一次性静态计划。

Reference: J. Hu, Y. Xu, K. W. Cheng, J. M. Guerrero, “A model predictive control strategy of PV-Battery microgrid under variable power generations and load conditions,” *Applied Energy*, 221 (2018), 195–203. DOI: 10.1016/j.apenergy.2018.03.085.

## 3. MPC 与随机优化的比较启示

Pacaud 等（2022）在含光伏和电池的家庭微网中比较 MPC 与 SDDP，并强调 MPC 依赖确定性预测、随机优化显式建模不确定性。对本题而言，数据只给有限历史与四时刻光伏预报，且需要大量 10 分钟结果可复现，因此直接上多阶段随机规划会显著增加假设和计算量。项目采用“因果点预测 + 滚动残差分位安全裕度 + MPC”的折中结构，在不虚构概率分布的前提下处理风险。

Reference: F. Pacaud, P. Carpentier, J.-P. Chancelier, M. de Lara, “Optimization of a domestic microgrid equipped with solar panel and battery: Model Predictive Control and Stochastic Dual Dynamic Programming approaches,” 2022, arXiv:2205.07700.

## 4. 为什么不采用元启发式

当前能量平衡、SOC 动态、充放电上界和分段线性结算均可线性化。成熟 LP 求解器能直接给出全局最优解和约束残差。因此 GA/PSO/SA 不提供更强的最优性证据，反而引入随机种子、收敛参数和重复运行成本。根据“最简单充分模型”原则，不采用元启发式作为主求解器。

## 5. 对本项目的直接结论

- Q1：确定性 LP 是最小充分模型。
- Q2：因果预测 + 分位安全裕度 + LP，比直接假设完整概率分布更稳妥。
- Q3：滚动 MPC 与题面多次预报机制自然一致。
- Q4：价格预测必须满足非前视；真实当日电价只用于结算，完全价格信息模型仅作为 oracle。
- 若需要下一轮现实性增强，优先增加电池退化成本或终端 SOC 价值，而不是更复杂的黑盒优化算法。
