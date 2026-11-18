---
name: ascend-model-adapter
description: 将真实模型迁移到昇腾 Ascend NPU，选择或修复推理路线，排查训练与微调，验证部署的精度与性能，接手已有工程或审查 ModelZoo PR。覆盖 ONNX/OM、ORT CANN EP、torch_npu、TorchAir、vLLM-Ascend 与多组件模型。
---

# Ascend Model Adapter

从使用者的入口反推验收。找出他会交给部署端的模型或制品、必须支持的输入或负载、拿到什么输出就能做决定。例如“在分配的卡上生成一段能播放的音频”可以用一次真实请求验收；“在原有质量下满足在线延迟”需要把两项结果对应到同一套可部署配置。沿用工作仓适用的 `AGENTS.md` 和用户指定范围。

## 按当前问题进入

| 用户现在需要什么 | 动作与结束条件 |
|---|---|
| 判断可行性或选路线 | 从交付端实际能加载的格式和运行时倒推。先核对固定版本的原生支持，用最便宜的实验排除会违反硬约束的路线。交付判断、依据和仍需验证的条件。[路线选择](references/route-selection.md) |
| 跑通或修复 | 沿实际入口复现，保留指定权重和输入。优先取得独立参照，局部替换受阻组件并重放到实际业务输出。暂缺参照时先验证功能，注明语义等价待验。只要求单样例时到此验收。[适配工作流](references/workflow-adaptation.md) |
| 跑通训练、微调或断点续训 | 从上游训练命令进入，验证一次有效参数更新。要求续训时从落盘的 checkpoint 恢复并再走一步。[训练验收](references/workflow-adaptation.md#训练与断点续训) |
| 做精度、性能验收或优化 | 确认测量能发现目标故障、结果来自要交付的配置，再投入整套评测。性能未达标时用该负载的关键路径选优化对象。[验证契约](references/validation-contract.md) |
| 接手或只读审查 | 从当前 README、入口、实际结果和现有 diff 重建已完成部分；复核决定当前结论的调用链。修复任务重放受影响操作，审查任务报告可复现的问题、影响和缺口。[内容审阅](references/content-review.md) |
| 整理文档或上库 | 按接收者能拿到的文件核对运行方法和指标来源。文档就地更新，独立候选按清单组装并重放。ModelZoo 另核对目标仓贡献要求。[交付工作流](references/workflow-delivery.md)、[验收清单](references/modelzoo-delivery.md) |

## 执行与交接

- 在实际执行端核对资源分配、版本与设备映射，沿用已授权的远端、容器或调度环境。审阅安装与加载代码的副作用，按需挂载。缺卡时可用原模型取得 CPU 参照、离线重算指标或核验产物，再给出尚缺的目标端验证。[执行环境](references/environment-container.md)
- 优先复用上游入口和官方 evaluator。设备变更、计算精度变更和算法变更分开验证；多组件模型先确认承担目标计算的组件及其实际后端。权重加载成功但结果可疑时，按组件核对 checkpoint 键与实际加载覆盖；依赖与管线排障也见[适配经验](references/adaptation-heuristics.md)，修改上游见[补丁参考](references/patch-modification-patterns.md)。
- 完成时交付实际命令、产物及结论适用的配置；分清已测失败、缺少测量和不可比。用户 README 保留可复现的结果及限制，内部等级、私有路径与排障记录留在项目内。[输出契约](references/output-contract.md)、[风格指南](references/style-guide.md)

需要跨次维护证据时可用[项目日志](references/adaptation-process-log.md)，默认路径为 `<workspace>/.ascend-adaptation/<project-id>/`。复核旧项目先看原始产物；当前仍可用的结果可直接复算，缺少旧日志也能继续。ModelZoo 样本采集见[采样参考](references/modelzoo-sampling.md)。参考命令中的 `SKILL_DIR` 为本文件所在目录的绝对路径。
