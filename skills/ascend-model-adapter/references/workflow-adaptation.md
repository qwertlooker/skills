# 适配执行工作流

输入：上游或已有工程、模型/权重、目标硬件与软件栈、用户要求的验证范围。脚本组织与表达按 `style-guide.md`，验收以有效证据为准。
输出：适配代码、运行入口、验证证据与内部记录。用户文档通过交付工作流更新。

## 1. 确定范围和工作区

- 区分最小修复、功能验证、完整精度性能验证和正式交付；用户要求完成适配和验证时，以真实 NPU 精度与性能为目标。没有设备时继续完成可做工作，并明确缺口。
- 读取已有工程与适用仓库约定。普通适配不强制查询 ModelZoo 或新增三份文档；目标为 ModelZoo 时加载 `modelzoo-delivery.md`。
- 内部记录默认放在 `.ascend-adaptation/<project-id>/`；`NPU_ADAPTATION.md` 记录技术事实、版本、决策和候选清单，`ACCEPTANCE_PLAN.md` 记录基线、阈值、命令与结果。窄范围修复可复用已有记录，不重复建表。
- 已有 README 保持为使用说明，执行进度写入内部记录。先完成下节审计和路线探针，再按第 3 节初始化缺少的文件；已有工程直接进入实现。

## 2. 审计和路线探针

1. 固定 upstream commit、模型变体、权重 revision/SHA、config/tokenizer/辅助模型和 license。
2. 查明官方/公开 dataset、split、样本规模、metric、normalizer/后处理、decode 参数与基线来源。
3. 审计 requirements/setup/pyproject、子模块、vendor、在线下载与加载逻辑，避免覆盖配套框架栈。
4. 搜索 CUDA、custom extension、动态 shape、control flow、硬编码后端与 pipeline 组件。
5. 按 `route-selection.md` 运行最小探针，记录选定路线、失败探针和 fallback 原因；提供或复用数据准备 → 推理 → evaluator → compare → report 的可执行路径。固定官方 harness 已提供等价能力时直接给 revision 与完整命令，不为文件名另造脚本。

日志初始化和技术等级只按 `adaptation-process-log.md`、`validation-contract.md` 操作；普通工程不适用的 ModelZoo 字段显式标明不适用。新观察到的目标仓 HEAD 作为观察记录，不静默替换已冻结基线。

## 3. 实现和静态检查

需要新骨架时，在路线已确定后执行：

```bash
python3 "$SKILL_DIR/scripts/scaffold_adapter.py" <上游URL> <工作区> \
  --category <类别> --route <已决定路线> --layout workspace
```

默认不生成 README；内部文档写入 `.ascend-adaptation/<project-id>/`。`--internal-dir` 可沿用仓库规定的位置；`--with-readme` 显式创建用户文档初稿。`--layout target` 也仅初始化，不能用来组装已完成的候选；交付组装见 `workflow-delivery.md`。

- 优先 patch 固定 commit 上的已有入口；新增入口避免重复实现。
- 默认 `--device npu`，CPU 对照显式选择；保持需要的原有 CPU/CUDA 行为，不静默 fallback。
- 必需依赖在实际使用前严格失败；设备后端可条件导入，`--help` 不应依赖权重或非必要推理依赖。
- 子进程、patch、下载、数据和 compare 失败非零退出。
- 执行 patch check、语法/lint、CLI 和数据最小 fixture 检查；内部记录保存命令、退出码与产物。

## 4. 功能和精度性能验证

- 干净环境安装，使用真实权重和输入完成端到端输出，记录实际 device/provider。单条样例只证明功能链路。
- 输出独立目录与 sidecar，记录版本、权重/manifest SHA、命令和环境。
- 数据准备与模型执行分开；CPU/NPU 使用同一固定 manifest，记录 config/split、seed/limit、实际样本数与可读性检查。公开基线的完整评测不能被 smoke 输入替代。
- NPU 完整精度对齐声明的数据与 evaluator；公开基线不可比或 patch 改语义时补 CPU 精度对照。
- 正式 NPU 性能口径、同步、重复次数与阈值按验证契约执行。compare 阈值失败须返回非零。
- 验证失败、路线改变和恢复执行时保留历史，检查旧证据是否仍适用；不能用旧等级替代当前证据复核。

## 5. 进入交付

用户要求 README 或交付时读取 `workflow-delivery.md`：从当前候选代码和有效证据提取公开事实，再更新用户文档。内部文档与公开文档只同步版本、命令、指标和限制等事实，不同步状态或完整内容。

不满足实测要求时，在内部记录保留原因和补验计划；在 README 明确用户可见的验证范围。正式候选若要求 NPU 实测，应报告该条件未满足。
