# 2026 高教社杯全国大学生数学建模竞赛 B 题研究工作区（branch `b`）

题目：**无线电干扰源的快速自动定位与清除**。

本工作区按“Question -> Model -> Computation -> Evidence -> Validation -> Conclusion”证据链组织；原始赛题与附件只读保存，不覆盖、不改写。

## 目录

- `problem/`：原题、附件、SHA-256 与规则审计。
- `modeler/`：Modeling Brief、需求矩阵、模型候选、假设、Failure Regions、v0.1/v0.2 Model Specification、阶段状态。
- `coder/`：几何算法、Q2候选区、Q3/Q4策略、官方HTTP客户端、离线开发模拟器、实验脚本、结果与测试。
- `writer/`：论文结构草案；尚不填写未验证正式结果。
- `reviewer/`：审核记录、异常日志、Claim-Evidence Ledger。
- `docs/`：Modeling Brief 的 DOCX/PDF 固定产物及清单。

## 当前 Gate

- Problem Understanding: **PASS**
- Data/Protocol Readiness: **PASS**
- Ready for Modeling: **YES**
- Offline Model Specification: **PASS v0.2**
- Unit tests: **10/10 PASS**
- Q1 random bounded-error validation: **300/300**
- Q3 offline stress: **200/200 full clear**
- Q4 offline worst-radius stress: **100/100 full clear**
- Official Simulator Validation: **NOT VERIFIABLE**
- Final Paper Results Ready: **NO**

## 当前主策略

- Q1：±1°有界误差半平面交 + 多边形直径 + MEC。
- Q2：保守扇环的分布无关二次可检测候选区。
- Q3：中心+六环点确定性发现，机会式定位，最近邻批量清除。
- Q4：边长≤1000m三角网格方向鲁棒发现，多点交会 + 可见半平面短步 fallback。

## 证据边界

官方模拟器案例的隐藏干扰源数量、频道、位置、接收半径、定向方向都不能直接读取；正式测试还必须由官方模拟器产生原名加密日志。因此本仓库**不会填写任何伪造的正式测试案例编码、清除数、平均定位清除时间或程序运行时间**。离线模拟器结果只用于模型筛选和压力测试。

程序读取 `svd_deg` 时使用 1.005° 数值包络来覆盖两位小数输出最多约0.005°的量化偏差；题面数学模型仍严格采用±1°。
