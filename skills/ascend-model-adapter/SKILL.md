---
name: ascend-model-adapter
description: 将模型适配到华为昇腾 Ascend NPU，验证推理、精度与性能，整理用户文档，或审查已有适配与 ModelZoo PR。适用于 ONNX/OM、torch_npu、TorchAir、vLLM-Ascend 和多组件模型迁移。
---

# Ascend Model Adapter

交付可复现的模型运行方法和有证据的结果。任务范围以用户要求为准；适配执行、内部验证记录和用户文档分别维护。

## 选择任务和交付目标

- **adapt**：实现或修复 NPU 适配，按要求验证。读取 [适配工作流](references/workflow-adaptation.md)。
- **deliver**：整理用户文档与候选文件。读取 [交付工作流](references/workflow-delivery.md) 和 [输出契约](references/output-contract.md)。adapt 包含文档或交付要求时，在执行后进入此阶段。
- **review** 是交付验收的只读执行方式：按 [统一验收清单](references/modelzoo-delivery.md) 的适用项检查工程/PR，输出 findings 与证据缺口；默认不修改源码或 README。
- **继续已有任务（resume）**：读取原项目记录，先复核代码、权重、环境和评测配置的变化，再决定补验范围；不要直接从旧等级跳到下一门禁。

这里指继续未完成的适配、交付或检视；评测脚本的 `--resume` 则指复用已有评测结果，以该脚本帮助和已验证用法为准。

交付自检与只读检视共用 [统一验收清单](references/modelzoo-delivery.md)。普通工程检查适用的通用项，明确上库时才增加 ModelZoo 项。进入现有工作仓先读适用的 `AGENTS.md` 及其要求的补充流程；用户明确指令优先于本 Skill 默认值。

模型适配解决版本、设备、数据与可执行验证闭环；上库交付额外解决目标仓、候选范围、贡献规范和独立重放。编写文档或脚本时读取 [风格指南](references/style-guide.md) 的对应部分，风格不替代技术验收。

将本文件所在目录记为绝对路径 `SKILL_DIR`，脚本用 `python3 "$SKILL_DIR/scripts/<name>.py"` 调用。

## 信息边界

README 的读者是模型使用者，内容用于安装、运行、评测、解释结果和理解限制。

- 内部状态、阶段编号、`target_ready`、门禁进度、agent 计划、证据 ID、临时路径和排障历史仅进入内部记录或对话进度报告。
- 项目内部记录默认位于 `<workspace>/.ascend-adaptation/<project-id>/`。仓库要求其他位置时遵守原约定；已有内部文件不自动搬迁。
- README 依据候选运行入口与经过核实的公开事实编写，不能直接摘要 `worklog.json`、内部验收文档或聊天过程。公开事实的范围、示例与检查见输出契约。
- README 公布的版本、命令、指标和限制必须与有效证据一致；内部进度无需同步到 README。
- 真实限制必须保留。例如“已完成 CPU 功能测试，尚未在 Ascend NPU 上实测”；不要改写成阶段编号，也不能删除缺口后声称已验证。
- 已有 README 按受影响章节更新，保留有效使用说明。独立审查任务只报告问题，除非用户同时要求修复。

## 工程正确性

1. 推理、评测与 benchmark 默认 NPU，物理卡通过 `ASCEND_RT_VISIBLE_DEVICES` 选择；CPU baseline/fallback 显式选择并说明边界。
2. 固定 upstream revision、权重及 config/tokenizer/label map；用户提供的 artifact 优先，替换须说明并重新验证。
3. 静态检查、导出、材料生成和 CPU-only 结果不能支持 NPU 通过结论。记录实际 device/provider，不能虚构转换、精度、性能或 CI 证据。
4. 精度优先对齐同 checkpoint、完整声明数据集/split、evaluator 和预后处理；公开基线不可比时补 CPU/upstream 对照并说明差异。
5. 正式 NPU 性能至少独立执行 3 次，保留结果并报告中位数，区分模型、端到端、首次编译和 CPU fallback；CPU 性能不用于推断 NPU 加速比。
6. 执行前审计不可信仓库的安装、下载与模型加载代码；隔离环境只挂载实际需要的目录和设备。容器配置见 [环境参考](references/environment-container.md)，按实际信任边界选择权限。

## 按需参考

- 路线决策：[route-selection.md](references/route-selection.md)。先上游审计和最小探针，再选路线。
- 依赖、数据、pipeline 排查：[adaptation-heuristics.md](references/adaptation-heuristics.md)。
- 写 patch 时：[patch-modification-patterns.md](references/patch-modification-patterns.md)。
- 记录或复核验证状态时：[validation-contract.md](references/validation-contract.md)；日志操作见 [adaptation-process-log.md](references/adaptation-process-log.md)。阶段编号属于内部验证模块。
- ModelZoo 样本采集失败时：[modelzoo-sampling.md](references/modelzoo-sampling.md)。

进度报告与最终对话说明实际完成项、验证范围、未完成项和结果位置。只有用户或仓库要求时才报告内部等级；这些内容不自动进入 README。
