# Final Delivery Manifest

本清单用于核对本地最终二进制交付物与 GitHub 中的可复现源文件。GitHub 连接器当前主要同步 UTF-8 文本/代码；大型 PDF、DOCX、XLSX 的最终字节快照以 SHA-256 固定，便于后续人工或其他 Git 客户端上传后逐字节核验。

| 交付物 | 字节数 | SHA-256 |
|---|---:|---|
| 微网与外部电网日前日内协同调度.pdf | 675113 | `e43e1ffef50a0990eade79195347d1bed1dd5facad447cef9678b0897de757ee` |
| writer/Paper_Final.pdf | 675113 | `e43e1ffef50a0990eade79195347d1bed1dd5facad447cef9678b0897de757ee` |
| writer/Paper_Final.docx | 286324 | `4f777dad260a27fbc3d54ec165146fb8cf91806c4c83af0d1b7d0dca7263d30c` |
| results/result1.xlsx | 7721 | `f1f2220efd4dfac986ffe8a120259afb08ce6a4438d6fe4b27d53f805c3f7fe0` |
| results/result2.xlsx | 607042 | `b1d86ea338e4ad5f114ab8e713bb40092681724cac16e4d6059f2266fe0ba70f` |
| results/result3.xlsx | 1089999 | `3042146e464a73674831a92812b9cd9753423aa044fe5befac71231fe7195119` |
| results/result4-2.xlsx | 611136 | `a9c4b953f3d0ecc43232e514149e1b2ac74a67aca5320c437f0711131cf13d5d` |
| results/result4-3.xlsx | 1091112 | `069e72b9d3d09dc87503d5ba2df4e200f8909d1845f14b7d2934d8d02fb1c0ff` |

## Source-side reproducibility

已同步到分支 `c` 的源文件包括：

- `modeler/`：题意、模型候选、方法检索与 Round-2 改进；
- `coder/solve_microgrid.py`、`coder/refinement_round2.py` 与验证日志；
- `coder/scripts/`：科研图和 Graphviz 结构图生成脚本；
- `figures_reaslab/*.png.metadata`：图表数据血缘与程序统计洞察；
- `writer/`：按 ReasLab 中文 CUMCM 结构拆分的完整 LaTeX 正文与核心求解代码附录；
- `reviewer/ReasLab_Visual_Final_Audit.md`：最终论文、数值、图形和证据审查。

最终 PDF 与 `writer/Paper_Final.pdf` 的 SHA-256 完全一致，说明顶层提交版就是通过审查的 Writer 编译版，没有在审查后再次手工改数。
