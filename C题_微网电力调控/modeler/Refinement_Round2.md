# Model Refinement Round 2

## 1. Observed limitation A：Q3 向下调整结算歧义

题面规定：计划购电量高于调整购电量的部分，违约电价为交易时刻电价的 50%；调整量高于计划量的超出部分按 1.5 倍电价。

主解释将下调后的实际支付写成

`p*min(g0,g) + 0.5p*(g0-g)_+ + 1.5p*(g-g0)_+`，

等价于

`p*g0 - 0.5p*(g0-g)_+ + 1.5p*(g-g0)_+`。

其经济含义是：被取消的计划量不再按 100% 支付，但仍承担该部分 50% 的违约结算。

### Alternative interpretation

另做更保守口径：计划购电费全部支付，再对向下调整量额外收取 `0.5p` 罚金，即

`p*g0 + 0.5p*(g0-g)_+ + 1.5p*(g-g0)_+`。

### Evidence

2/1-12/31：
- 主解释总费用：14,679,141.98 元；紧急购电 261,002.46 kWh。
- 保守解释总费用：14,927,429.70 元；紧急购电 221,251.39 kWh。
- 保守解释相对主解释增加约 248,287.72 元（约 1.69%）。

### Decision

**Retain primary interpretation, but explicitly state the settlement equation and report the conservative sensitivity.** 这样避免只依赖文字歧义，同时证明结论不由单一口径制造。

---

## 2. Observed limitation B：Q4 价格信息前视偏差

第一轮 Q4 在优化时直接使用附件 4 当天完整真实价格轨迹，等价于 perfect foresight/oracle，不符合“实时波动”下严格因果的决策信息结构。

## 3. Proposed modification：因果价格预测层

比较典型日均价、1 日滞后、7 日滞后、7 日 EWMA、28 日中位数后，7 日滞后同时段价格预测误差最低。

对第 d 天：

`p_hat(d,t) = p(d-7,t)`，d<7 时用附件1典型日价格。

优化决策仅使用 `p_hat`，最终费用按附件4真实 `p(d,t)` 结算。这样消除未来电价泄露。

预测性能（2/1-12/31）：
- MAE 0.047151 元/kWh；
- RMSE 0.065348 元/kWh；
- 相关系数 0.981085。

## 4. Round-2 Q4 results

| 模型 | 因果总费用/元 | Oracle/元 | 因果相对 Oracle 溢价 |
|---|---:|---:|---:|
| Q4-2 | 15,774,011.24 | 15,603,450.52 | 1.0931% |
| Q4-3 | 15,507,241.00 | 15,338,096.77 | 1.1028% |

Q4-3 比 Q4-2 节省 **1.6912%**，说明滚动预测更新的经济价值在严格因果价格设定下仍然存在。

## 5. Validation

Round-2 因果 Q4：
- SOC 始终位于 1200–10800 kWh（数值误差约 1e-11）；
- 单时段充/放电量不超过 833.333 kWh；
- 同时充放电次数为 0；
- 跨日 SOC 连续误差为 0；
- 实际供需平衡最小 slack 仅为浮点误差量级（~1e-13）。

## 6. Accept / Reject

- Q3 主结算解释：**ACCEPT WITH SENSITIVITY DISCLOSURE**。
- Q4 perfect foresight 作为正式模型：**REJECT**。
- Q4 perfect foresight 作为 oracle lower bound：**ACCEPT**。
- Q4 7 日滞后价格预测 + 实际价格结算：**ACCEPT AS PRIMARY**。
