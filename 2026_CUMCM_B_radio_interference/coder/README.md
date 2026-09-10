# Coder Workspace

## 核心实现

- `src/geometry.py`：Q1 楔形半平面交、空/无界/有界分类、凸包、直径、直径圆判定、最小覆盖圆(MEC)。
- `src/q2_candidate_region.py`：Q2 分布无关保证候选区 + 可选先验评分模型。
- `src/search_policy.py`：Q3七点全向覆盖与Q4安全三角网格。
- `src/q3_policy.py`：Q3 全向源在线策略。
- `src/q4_policy.py`：Q4 混合源策略与定向源保守 fallback。
- `src/simulator_client.py`：附件2严格串行 HTTP 客户端、幂等重试、动作日志。
- `src/offline_simulator.py`：按公开规则实现的离线开发模拟器；**不替代官方模拟器**。

## 复现

```bash
python -m unittest discover -s coder/tests -v
python coder/run_initial_validation.py
python coder/run_q3_monte_carlo.py
python coder/run_q3_stress.py
python coder/run_q4_stress.py
```

结果位于 `coder/results/`，解释见 `coder/experiments/experiment_summary_v0.1.md`。
