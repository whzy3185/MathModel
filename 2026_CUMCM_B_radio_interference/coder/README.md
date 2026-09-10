# Coder Workspace

当前实现：

- `src/geometry.py`：Q1 楔形半平面交、状态识别、凸包、直径、直径圆覆盖判定。
- `src/q2_candidate_region.py`：Q2 第一可行区域采样、交会角、候选第二点评分。
- `src/simulator_client.py`：严格按附件2实现的串行 HTTP 客户端、幂等 request_id、动作日志。
- `src/offline_simulator.py`：按题面规则构造的离线测试环境（仅用于算法开发，不代替官方模拟器）。
- `tests/`：当前单元测试。

运行：

```bash
python -m unittest discover -s coder/tests -v
```
