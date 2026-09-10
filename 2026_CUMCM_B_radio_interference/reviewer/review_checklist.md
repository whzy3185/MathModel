# Independent Review Checklist

Reviewer 只审，不直接改正文/代码。

- [ ] 四问全部回答，输出格式与题目一致
- [ ] Q1 ±1° 误差未被当成随机正态事实
- [ ] Q1 EMPTY/UNBOUNDED/退化有处理
- [ ] “直径为D的圆一定覆盖”未出现错误断言
- [ ] Q2 候选区域定义可计算，权重有敏感性
- [ ] Q3 对未发现频道有完整覆盖/停止逻辑
- [ ] Q3 清除率、平均时间来自日志而非手工
- [ ] Q4 no_signal 不被当成无源
- [ ] Q4 定向覆盖保证证明满足距离<=1000条件
- [ ] /clear 不错误改变当前测向频道
- [ ] accepted=false 的 virtual_time_s=0 未误用
- [ ] request_id 幂等重试符合附件2
- [ ] 所有失败/超时保留在 anomaly_log
- [ ] baseline 参数公平
- [ ] 正式三次测试日志原名保留
- [ ] Claim-Evidence Ledger 所有强结论有证据
