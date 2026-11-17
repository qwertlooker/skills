# 内部验证、证据与状态契约

本文件统一定义内部技术等级和验收条件。等级、就绪状态、门禁进度与证据位置写在内部记录或用户要求的报告中；README 只公开 `output-contract.md` 允许的事实。普通任务按用户要求验收；“上库候选就绪”仅适用于明确的 ModelZoo 交付。

## S0–S4 技术状态

| 状态 | 项目日志必需成功证据 | 允许的结论 |
|---|---|---|
| 未定级 | 仅初始化日志 | 已建项目，不能写“分析完成” |
| S0 分析完成 | `target_baseline`、`upstream_audit`；目标仓/上游/权重已冻结 | 完成适配分析 |
| S1 静态适配完成 | `static_check`；需要 patch 时另有 `patch_check` | 静态门禁通过 |
| S2 功能验证完成 | route/硬件已确认；`functional_inference`：CPU/CUDA/NPU 至少一条真实端到端输出 | 指定设备功能链路实测通过 |
| S3 L2 迁移对齐完成 | `npu_accuracy`、`npu_performance`、`comparison_report` | NPU L2 精度/质量和性能对齐通过 |
| S4 扩展验收通过 | `extended_validation` | 用户要求的长稳、L3 或业务扩展验收通过 |

`set-status` 只允许依次设置 S0→S4。失败证据必须保留真实非零退出码，不能解锁状态。dummy/单条样例最多支持 S2；文档、patch、compile 最多支持 S1。

## 上库候选就绪

技术状态与上库就绪分开：

- 至少达到 S3。
- `target_audit` 必须包含 `tools/audit_model_delivery.py <model_dir> --target-readiness --target-path ...` 或目标仓等价门禁。
- `clean_room_replay` 必须从独立候选目录按 README 重放最低正式路径，不读取内部记录、未声明的开发 checkout/cache 或环境变量；允许按 README 的固定 URL/revision 获取上游源码和依赖。
- 满足后才运行 `project_log.py set-target-ready`。正式合入仍只能由目标仓 PR merged/commit 证明。

## 每条证据至少记录

- 类型、时间、完整命令、退出码和可验证 claim。
- 目标仓 commit、源码 commit/PR head、权重 revision/SHA、镜像 tag/digest。
- 对外硬件型号、CANN、Python、torch/torch_npu 和路线相关工具版本。
- 日志路径；权重、manifest、ONNX、OM、配置或结果文件 SHA256。
- 数据集版本/split、样本数、过滤规则、评测脚本 revision 和输出目录。

S0 前冻结的目标仓/上游/权重上下文不能在同一日志中静默改变；需要新 baseline 时创建新的项目日志。S2 后 route/硬件改变同样需要新日志，避免旧证据继续解锁状态。

## 验证层级

1. **S0 分析**：用户交付目标、upstream/权重/官方测试集与指标；ModelZoo 任务额外检查实时 master、路径、样本和贡献门禁。
2. **S1 静态**：patch check、语法、lint、冲突标记、路径、下载 check 与适用的内部验证记录；交付时另检查用户文档和候选清单。
3. **S2 功能**：干净环境安装、权重/功能输入、真实端到端输出；注明实际 device/provider。
4. **S3 L2**：NPU 完整精度/质量、NPU 性能、自动 compare 和报告；官方公开基线不可比或 patch 改语义时补 CPU 精度对照。
5. **S4 扩展**：并发、长稳、错误请求、cache 冷热、L3/业务集等用户明确项。

## 性能计时

- NPU 操作异步。纯模型/设备计时前后 synchronize；端到端计时明确数据、排队、后处理、网络和异步完成边界。
- 参数拒绝 `loop <= 0`、`record <= 0`、空数据集和非法 batch。
- 首次编译/cache miss 与稳定阶段分开。
- 正式性能至少独立执行 3 次，报告中位数；同时保留每次结果、样本数，适用时补分位数和峰值 HBM。
- CPU 性能不用于推断 NPU 加速比。
- 同步目标与实际执行的后端/逻辑设备一致，不能只同步默认设备；输入或分支跳过某子模型时记录实际执行范围，不能仍称整链路性能。

## 精度结论

- 直接对齐官方指标必须保持 checkpoint、完整数据集/split、配置、随机种子、预后处理和 evaluator 一致。
- 替换权重、tokenizer、聚类、阈值或子模型后重新跑任务指标，并声明不可直接比较项。
- 公开基线不可比、patch 改变算法语义或需要隔离版本漂移时，补同环境 `--device cpu` 精度对照；CPU 对照不用于性能。
- 小样例、输出文件或截图不能冒充任务精度。
- CUDA 对照是可选增强，不强制具备 GPU。公开基线未发布时明确说明，选用的固定集/CPU 对照只支持相应迁移对齐结论，不能冒充官方指标复现。
- 对比结果按稳定样本/session ID 对齐，CPU/NPU 保持同一 manifest、预后处理与参数，写独立结果；报告入口输出实际指标、差异与通过判定，不能只有验收计划。
- 续跑汇总基于当前声明样本集合的全部有效结果，按稳定 ID 去重；部分续跑或全部已完成时不能只统计本次新样本，更不能以零覆盖已有总结果。记录损坏行/跳过项和覆盖率，避免成功标识掩盖缺失结果。
- 区分合法的单样本空预测与无有效比较：空评测集、NaN/Inf 或未执行核心分支不支持“精度对齐通过”。空预测按官方指标语义处理，不能无依据填零或要求每张图必有检测框。
- 改为仅从 config 初始化子模型时，验证 checkpoint 关键权重确实覆盖。允许的 missing/unexpected keys 须有模型依据；不能让随机初始化关键模块在仅告警后继续产出验收数字。
- 多输出 ONNX/OM 按导出 contract 核对名称、数量、shape、dtype 与 decoder 预期；不因历史代码只取 outputs[0] 就假定单输出，也不照评论建议盲目拼接。

## 阈值和按类型补验

阈值依次参考官方容差、baseline 重复运行波动、patch 前后同设备误差、已验证 dtype/backend 的工程容差。初始建议值标为暂定并待 baseline 校准，不能直接作为“通过”的依据。随机训练或动态 benchmark 按任务记录 seed、重复运行与方差；不为普通推理追加训练验收。

只读取和执行模型实际涉及的行：

| 模型/执行形态 | 关键补验 |
|---|---|
| ORT / provider | 固定 ONNX SHA；核实实际 session provider，必要时用 profiling 查关键节点 CPU 分区，不仅看可用列表 |
| Transformers / embedding | model/tokenizer/remote-code 固定 revision；同样本单条与 padding batch 对齐；embedding smoke 不替代下游任务指标 |
| vLLM / 服务 | server/client/benchmark 模型名一致，context 与固定 prompt 规模真实；结构化输出、tool/reasoning/streaming 按交付功能检查 |
| Agent / 外部工具 | 固定框架、配置、数据、judge/工具版本、context/并发和运行次数；服务 smoke 不等同完整 agent benchmark |
| ASR / diarization | 固定 manifest/reference/UEM、normalizer、collar/overlap；evaluator 依赖可导入，结果按稳定 ID 对齐 |

生成式首 token 分叉可能级联，token agreement 只用于定位，结合任务质量指标判断。多卡交付另记录实际卡数、挂载、rank/HCCL 与网络配置，不为单卡任务增加多卡门禁。

## 证据失效

源码/patch、权重/config、镜像核心栈、目标硬件、数据 split、evaluator、性能参数或计时实现变化会使对应证据失效。README 与 PR 公布的版本、命令、指标和限制必须追溯到当前有效证据；不把内部状态同步到用户文档。`project_log.py` 不自动检测这些变化；恢复与变更处理按 `adaptation-process-log.md`，不能把记录器通过当成证据有效性证明。
