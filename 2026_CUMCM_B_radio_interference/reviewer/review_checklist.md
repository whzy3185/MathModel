# Independent Review Checklist

Reviewer 只审，不直接修正文/代码。

## Requirement / Mathematics

- [ ] 四问全部回答，Q3/Q4按题目表1格式给真实结果。
- [ ] Q1题面数学误差写±1°；实现层1.005°只解释为两位小数安全包络。
- [ ] Q1 EMPTY/UNBOUNDED/退化情况有处理。
- [ ] “直径为D的圆一定覆盖”没有错误断言；给判据与反例。
- [ ] 20m清除使用MEC半径<=20等严格条件，而非仅D<=40。
- [ ] Q2 Primary不依赖未给出的概率分布；若出现期望评分明确标注设计先验。
- [ ] Q3对未发现频道有完整的全向覆盖证明和停止逻辑。
- [ ] Q4 no_signal 不被当成“无源”。
- [ ] Q4三角网格保证同时满足“凸包围”和每相关顶点距源<=1000m。
- [ ] Q4 31点只称安全补丁，除非后续证明最小。

## Implementation / Reproducibility

- [ ] `/clear` 不错误改变测向机当前频道。
- [ ] accepted=false 的 virtual_time_s=0 未误当当前时刻。
- [ ] request_id 幂等重试严格复用相同动作内容。
- [ ] 不并发发送不同动作。
- [ ] `/enter` 的 remaining_real_duration_s 被用于现实截止控制。
- [ ] 所有失败/超时/结果反转保留在 anomaly log。
- [ ] Exploratory 与 Confirmatory 运行分开，策略参数在正式测试前冻结。

## Evidence / Writing

- [ ] Q3/Q4清除率、平均时间来自真实日志，不手工填写。
- [ ] 正式三次测试日志原名保留且与案例编码关联。
- [ ] 离线模拟器结果没有被写成官方模拟器性能。
- [ ] baseline参数公平；没有只展示最好随机种子。
- [ ] Claim–Evidence Ledger 所有强结论都有可追溯证据。
- [ ] 没有把相关性写成因果、局部压力测试写成普适规律。
