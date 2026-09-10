# Modeling Brief

## 1. Overall Objective

研究非孤岛式微网在小区负载、光伏发电、储能状态和外部电价共同作用下的购电与储能调控策略，使供电满足负载约束，同时降低购电成本。

## 2. Problem Map

|问题|数学任务|
|-|-|
|问题1|确定性条件下的储能调度优化|
|问题2|全年时序数据下日前购电优化与紧急购电控制|
|问题3|滚动预测修正的动态调度优化|
|问题4|实时波动电价下的鲁棒调控优化|

## 3. Requirement Matrix

### Q1
Input: 电价、负载、光伏预测、储能参数
Output: 10分钟购电计划、充放电计划
Objective: 最小购电成本
Constraint: 供电不低于负载，首末SOC一致

### Q2
增加全年负载与实际光伏数据，允许高成本紧急购电。

### Q3
增加0/6/12/18时预测更新机制，研究滚动调整策略。

### Q4
引入实时波动电价，重新评估Q2/Q3。

## 4. Candidate Models

Primary:
- Mixed Integer Linear Programming / Linear Programming
- Rolling Horizon Optimization

Baseline:
- 无储能调度
- 贪心低价充电高价放电策略

Alternative:
- 鲁棒优化
- MPC模型预测控制

## 5. Strong Assumptions

- 储能效率固定90%
- 充放电功率限制确定
- 预测数据作为外部输入
- 电力交换不存在线路损耗

## 6. Failure Regions

- 光伏预测误差过大
- 极端负荷峰值
- 电价剧烈波动
- 储能SOC边界频繁触发

## Current Gate

Problem Understanding: PASS
Data Audit: PENDING
Modeling Ready: NO
