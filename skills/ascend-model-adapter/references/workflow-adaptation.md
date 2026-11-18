# 适配执行工作流

输入：上游或已有工程、模型/权重、目标硬件与软件栈、用户要求的验证范围。脚本组织与表达按 `style-guide.md`，验收以有效证据为准。
输出：适配代码、运行入口、验证证据与内部记录。用户文档通过交付工作流更新。

## 1. 确定范围和工作区

- 区分最小修复、功能验证、完整精度性能验证和正式交付；用户要求完成适配和验证时，以真实 NPU 精度与性能为目标。没有设备时继续完成可做工作，并明确缺口。
- 读取已有工程与适用仓库约定。普通适配不强制查询 ModelZoo 或新增三份文档；目标为 ModelZoo 时加载 `modelzoo-delivery.md`。
- 内部记录默认放在 `.ascend-adaptation/<project-id>/`；`NPU_ADAPTATION.md` 记录技术事实、版本、决策和候选清单，`ACCEPTANCE_PLAN.md` 记录基线、阈值、命令与结果。窄范围修复可复用已有记录，不重复建表。
- 已有工程先按 `content-review.md` 审阅文档和实现，形成差距与保留项，再进入修复。复核已有路线和探针证据，仅在缺失或失效时补做；不因重新调用 Skill 重跑全部适配。新工程完成下节审计和路线探针后，再按第 3 节初始化缺少的文件。

## 2. 先建立参照，再改变后端

1. 找到上游或用户已有的真实入口、模型/变体、固定 revision、权重和配套 config/tokenizer/辅助模型与许可。对外给精度结论时查原始数据、split、evaluator 和解码设置。
2. **在改动前留下能判错的东西。** 对代表性输入保存未改入口的期望输出或可核验的任务标签，保留原始输入及关键中间量。已有可信留档直接复用。无法运行上游时，可先验证加载与目标端功能，把语义等价留作未验项。[如何选择参照](validation-contract.md#谁提供正确答案)
3. 按[路线选择](route-selection.md)从已有制品和允许的部署接口开始。核对实际加载路径、配套版本、依赖、custom op、动态分支及组件边界。在用户会用到的输入上证实或否定最可能阻断部署的条件；根据观测决定配置即用、局部补丁、换路线或报告约束冲突。
4. 确认候选可用后才扩展到所需范围。完整验收复用固定的官方 harness 或项目现有的数据、推理、评测、比较入口。先用少量已知好坏输出校验自定义接入层，避免用整批卡时调一个不会报错的比较脚本。

日志初始化和技术等级只按 `adaptation-process-log.md`、`validation-contract.md` 操作；普通工程不适用的 ModelZoo 字段显式标明不适用。新观察到的目标仓 HEAD 作为观察记录，不静默替换已冻结基线。

## 3. 实现和静态检查

需要新骨架时，在路线已选定（或因条件不足而明确暂定）后执行：

```bash
python3 "$SKILL_DIR/scripts/scaffold_adapter.py" <上游URL> <工作区> \
  --category <类别> --route <已决定路线> --layout workspace
```

`--layout workspace` 默认不生成 README；内部文档写入 `.ascend-adaptation/<project-id>/`。`--internal-dir` 可沿用仓库规定的位置；`--with-readme` 显式创建用户文档初稿。`--layout target` 会创建 README 初稿，也仅用于初始化，不能组装已有候选；交付组装见 `workflow-delivery.md`。

骨架打印的 Project ID 供日志命令复用。接手已有工程时以原目录和日志中的 ID 为准，尤其是显示名含中文的旧工程。默认工作区事实表保留初始化时选择的路线及指定的环境；恢复后核对实际执行环境和探针结果。普通工程默认按用户目标填写验收记录；正式上库用 `--profile modelzoo`。离线 OM 路线若直接给出以 `.onnx` 或 `.om` 结尾的制品路径，骨架只生成后续需要的转换步骤。用户指定本轮目标时，用 `--validation-goal "在指定 NPU 上跑通一张图片"` 等实际目标生成相应验收记录。

已有工程通常直接修补缺失内容，不需要重新生成。确需使用骨架补文件时加 `--missing-only`，保留已有 requirements、实现和文档；默认遇到同名文件会整体拒绝写入，不能为了绕过冲突使用 `--force`。生成的 Python 入口只是明确失败的待实现骨架，不会导入某个假定后端；按选定路线补齐依赖与实现。OM 转换模板要求显式设置真实 `INPUT_SHAPE`。多输入保留名称和分号，例如 `INPUT_SHAPE='input_ids:1,128;attention_mask:1,128'`。模板仅在指定 `INPUT_FORMAT` 或 `PRECISION_MODE` 时传入相应选项。先按图的输入及目标 CANN 版本核对默认值，有些版本对 ONNX 默认采用 NCHW；序列输入需要 ND 时显式设置。用 `ASCEND_ENV_SCRIPT` 选择工具链环境，保留生效参数，用生成的 OM 重放相同输入。[ATC 参数概览](https://www.hiascend.com/document/detail/zh/CANNCommunityEdition/850alpha002/devaids/atctool/atlasatc_16_0039.html)

- 优先 patch 固定 commit 上的已有入口；新增入口避免重复实现。
- 默认 `--device npu`，CPU 对照显式选择；保持需要的原有 CPU/CUDA 行为，不静默 fallback。
- 必需依赖在实际使用前严格失败；设备后端可条件导入，`--help` 不应依赖权重或非必要推理依赖。
- 子进程、patch、下载、数据和 compare 失败非零退出。
- 执行 patch check、语法/lint、CLI 和数据最小 fixture 检查；内部记录保存命令、退出码与产物。

## 4. 让验证回答用户的问题

- **单样例。** 在申请的设备上走交付入口，确认关键计算确实在目标后端执行，检查输出字段、形状及任务含义。用可重放的真实权重与输入，报告实测范围。
- **输出偏离。** 从同一原始输入向后查找第一处偏离：预处理不同先查 tokenizer、归一化或 layout；相同 feed 而模型输出不同，按[中间激活比对方法](validation-contract.md#同一输入的模型原始输出已经偏离)缩小到子图、精度或算子；原始输出对齐则查业务解码。PyTorch 推理入口确认实际调用 `eval()`。量化模型需要时对照浮点/量化的同层张量。[PyTorch 推理模式](https://docs.pytorch.org/docs/stable/generated/torch.autograd.grad_mode.inference_mode.html)、[昇腾精度比对示例](https://github.com/Ascend/msit/blob/master/docs/en/msit_quick_start.md)
- **正式验收或优化。** 按[验证契约](validation-contract.md)检查比较器、预期样本覆盖、部署配置与负载，再做相应测量。数值失败先定位，测量无效先修测量。旧预测足够时用原文件重算；改推理实现后补验受影响的行为。

### 训练与断点续训

从实际训练入口固定 checkpoint、少量真实样本和配置。对“跑通微调”，选择有有效标签、学习率生效的一次更新，跨过梯度累积边界，核对 loss、目标参数的有限梯度及更新前后的值。LoRA 可选本步预期变化的 adapter 参数，并抽查一个冻结的基座参数。若 loss 有值而权重未动，核对 optimizer 的参数组、学习率和混合精度溢出跳步。用户要求收敛或任务质量时，再按约定的训练量和验证集评测。[PyTorch 混合精度训练示例](https://docs.pytorch.org/docs/stable/notes/amp_examples.html)

承诺断点续训时，在更新边界保存 checkpoint，从新进程走交付的恢复命令。对照连续运行的下一步，检查 global step、学习率、优化器状态和后续参数更新；若要数值对齐，还需对齐下一批样本及随机状态。按实际训练器核对 scheduler、scaler 或分片状态。仅交付推理用 adapter 时，用指定基座重新加载并验证输出即可。[PyTorch checkpoint 保存与恢复](https://docs.pytorch.org/tutorials/beginner/saving_loading_models.html#saving-loading-a-general-checkpoint-for-inference-and-or-resuming-training)

## 5. 进入交付

修正本次实现影响的用户说明；请求完成适配时提供可复现的最低运行说明，用户明确排除文档时遵从其范围。按 `content-review.md` 复核变更后的文档和脚本。用户要求整理 README 或交付时进入 `workflow-delivery.md`；只有需要独立候选时才打包。内部文档与公开文档只同步版本、命令、指标和限制等事实，不同步状态或完整内容。

不满足实测要求时，在内部记录保留原因和补验计划；在 README 明确用户可见的验证范围。正式候选若要求 NPU 实测，应报告该条件未满足。
