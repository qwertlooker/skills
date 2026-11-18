# 项目级适配日志

每个项目只使用自己的私有日志：

```text
<workspace>/.ascend-adaptation/<category>__<model>/worklog.json
```

不要把多个项目写入同一个固定文件，也不要把 `.ascend-adaptation` 提交到 ModelZoo。`scripts/project_log.py init` 会拒绝覆盖已有日志，并在 Git 工作区的 `.git/info/exclude` 中加入本地排除项。内部技术事实和验收方案默认也放在同一项目私有目录。窄范围修复复用已有记录；仓库明确要求根目录文档时保留其位置，交付时按文件清单排除。README 按 `workflow-delivery.md` 独立维护。

## 初始化与恢复

```bash
python3 "$SKILL_DIR/scripts/project_log.py" init \
  --workspace <工作区> --project-id <category>__<model> \
  --model-url <URL> --target-path <交付目标路径> \
  --mode adapt --route undecided --hardware-model unconfirmed
```

初始化时沿用骨架打印的项目 ID；上述 undecided 和 unconfirmed 仅用于确实未确定的字段。已选择的路线和目标硬件可从私有事实表核对。接手时从现有日志读取项目 ID，沿用原路径。

普通适配的 target baseline 表示用户要求的交付位置与约束；无目标仓时 `target_repo_commit=not-applicable`，`target_path_exists` 记录本地目标路径状态。ModelZoo 基线另按交付配置查询。

仓库已有私有记录位置时，骨架和日志命令均可传 `--internal-dir <项目私有目录>`：相对路径以 `--workspace`（骨架的输出工作区）为基准，绝对路径直接使用。日志直接位于该目录的 `worklog.json`，不会再追加项目 ID；每个项目使用独立目录，每次日志命令都传同一路径。工具拒绝用另一项目 ID 读写该日志，不自动迁移已有文件。Git 仓内的自定义私有目录会加入本地 exclude。

恢复时先按 `content-review.md` 阅读当前文档和实现，再核对源码/patch、权重、软件栈、数据、evaluator 与记录是否一致。脚本是记录器，检查字段、各类最新执行结果和已登记产物哈希，不能证明内容合规、命令真实执行或未登记的源码/环境仍一致。当前工具不支持撤销等级，`status` 是历史达到的等级，不自动证明当前仍通过。冻结的模型基线、路线或硬件变更时另建项目 ID；同一范围内重新评测可在原日志中追加，保留旧结果。没有旧日志无需补造历史。

## 基本字段

- `project_id`：稳定项目标识，推荐 `<category>__<model>`。
- `model_url`、`target_repo_commit`、`target_path`、`target_path_exists`、`mode`、`route`、`hardware_model`、`patch_required`。
- `source_revision`、`checkpoint`：审计后用 `update-context` 从 `unconfirmed` 改为固定值；不适用时显式写 `not-applicable`。
- `status`：未定级或 S0–S4；`target_ready` 与技术状态分开。
- `evidence`：命令、退出码、claim、环境、日志和产物 SHA256。
- `decisions`：路线、权重、fallback、依赖和口径决策。
- `issues`：症状、无效尝试、根因、修复和复用价值。

## 添加与复核证据

执行失败且没有生成预测时，登记真实非零退出码与可用日志。日常排障可直接用 `add-evidence` 记录命令、退出码、`--claim`、`--environment` 和可选产物。局部探针用 `other` 或对应非验收类型。一个验收类型对应本次冻结范围的完整结论，多子任务保留各自结果并登记汇总。所有相对文件路径按调用时 cwd 解析；远端工件可取回本地，另记原位置。

**要形成 S3 联合结论时**，优先直接使用精度运行和性能运行各自生成的 JSON 元数据。用 `--subject-fields` 选取完整的部署字段（顶层键，可包括嵌套对象），两次记录可有不同顺序、时间戳和测量负载。字段应能区分实际权重、实现/patch 或 OM、运行栈、硬件及生效的 dtype、量化等推理设置；只选同名模型或 checkpoint 会漏掉版本差异。工具核对选中字段的值，并保存原文件哈希。检查未选的差异确实只属于负载、时间或测量输出。没有共用字段时，也可用 `--subject` 指向实际运行使用的完整部署描述，两端按文件字节匹配。原始记录无法证明归属时，保留各自数字并说明缺哪一项。

以下为已有三次操作的登记示意。shell 数组 `project` 保存同一工作区与项目 ID；大写变量取自各次真实命令与退出码。示例假定项目原生 sidecar 将完整部署描述放在 JSON 的 `deployment` 对象中；扁平元数据可传多个实际字段名。结果使用各次独立留存的路径。先按[验证契约](validation-contract.md)确认结果内容和实际执行设备。

```bash
project=(--workspace "$WORKSPACE" --project-id "$PROJECT_ID")
log="$SKILL_DIR/scripts/project_log.py"
python3 "$log" add-evidence "${project[@]}" --type npu_accuracy --subject "$EVAL_META" --subject-fields deployment \
  --command "$EVAL_COMMAND" --exit-code "$EVAL_RC" --claim "$EVAL_SCOPE" --artifact "$SCORES"
python3 "$log" add-evidence "${project[@]}" --type npu_performance --subject "$BENCH_META" --subject-fields deployment \
  --command "$BENCH_COMMAND" --exit-code "$BENCH_RC" --claim "$LOAD_SCOPE" --artifact "$BENCH_RESULT"
python3 "$log" add-evidence "${project[@]}" --type comparison_report \
  --command "$COMPARE_COMMAND" --exit-code "$COMPARE_RC" --claim "$VERDICT" \
  --artifact "$COMPARE_REPORT" --compared-field candidate_sha256
```

- `--artifact` 对精度记录表示本次比较实际消费的候选结果，可重复指定。首选从原比较报告读取当时记录的输入 SHA256：`--compared-field` 指向一个顶层字段（64 位十六进制字符串或其数组），`--artifact` 给这一个原生 JSON 报告。字段名以实际 evaluator 为准。正式 S3 要求评分时记录的输入摘要。若 evaluator 没有原生摘要，由执行评分的入口在当次读取时记录输入摘要并随报告保存。`--compared 文件` 可保留历史输入关联。旧结果没有评分时的摘要时，用仍有效的预测重做 compare。比较结论从其输入继承部署身份，参考端、评测器版本和阈值来源由报告记录。判据或基线改变时用保留的原始结果重新打分。若同一个官方程序同时打分和判阈值，使用它真实产生且包含两项事实的工件，不另造比较程序；从报告中核验用于判定的分数来源。额外执行日志用 `--log-path`。
- 各项保存文件 SHA256。正式等级检查要求同一部署描述且非空的测量/报告，比较输入按内容与当前精度产物对应。新精度结果覆盖旧结论时，旧报告只能证明它实际评过的内容。用新预测重新 compare 即可，仍匹配的性能结果可复用。S4 扩展验证、上库审计和独立重放各自也需对应同一部署并留原始结果或执行日志。
- 正式 `comparison_report` 需要布尔 `passed` 或任务的 `--require FIELD OP VALUE`。只有实际判阈值且经失败用例确认会返回非零的外部比较命令，才用 `--exit-code-is-verdict`。比较器退出成功后仍核对报告的评分输入摘要。对于纯数值的 `npu_performance` 或 `extended_validation`，按任务使用 `--require`，如 `--require p95_e2e_ms lt 150`。升级和复核会重新应用已声明的判据。独立读取文件可用[验证契约中的 check-report](validation-contract.md#先验证评测能发现错误)。比较器自身按任务判定退出时沿用该入口；单个 JSON 比较报告明确给出布尔 `passed=false` 时，退出码 0 也不能用于晋级。
- 每类取最新记录，最新失败阻止升级与就绪，追加相关证据清除旧就绪标志。文件缺失或改写时按原始来源核实并重新登记。脚本检查指定字段和文件关系。模型指标的定义、样本与任务的关系，以及进程实际加载的设置仍须从原运行中核实。

## 提升状态与复核

前序状态和该级全部证据齐全后再执行，例如当前已是 S2 且 S3 三项证据已记录：

```bash
python3 "$log" set-status "${project[@]}" --status S3
```

脚本只允许逐级提升。每项必需证据须有非空的 `--log-path` 或 `--artifact`，并通过最新执行结果和哈希复核。S0 后 target/upstream/weight baseline 冻结，S2 后 route/硬件冻结；需要改变时另建项目日志，避免旧证据解锁新上下文。达到 S3/S4 后，审计和独立重放都要从同一份组装报告开始。登记 `target_audit` 与 `clean_room_replay` 时分别加 `--candidate-manifest <组装报告>`，保留各自的原始证据。`set-target-ready` 复核技术状态、两个记录使用的组装报告及候选现有文件。

普通 `show` 输出历史快照。引用既有等级或就绪状态前，用 `show --verify` 复核。候选仅有文档变更时可用 `show --verify --technical-only` 独立复核技术等级，然后按新候选补审计和重放。复核正式部署还可给当前生效配置：

```bash
python3 "$log" show "${project[@]}" --verify --subject "$CURRENT_META" --subject-fields deployment
```

返回非零时保留原日志。旧日志仍可阅读。当前等级缺少依赖的证据绑定时，先核对原始产物，再追加符合新校验的记录。仍有效且完整的预测可直接离线重做比较。只有对应材料缺失或部署已改变时才补测。没有日志的项目可以直接审阅原始文件，日常 smoke、只读审阅或整理文档均无需建立 S3 记录。

冻结前 `update-context` 的实际变更也会保留变更历史并使受影响证据失效：baseline 变化使全部证据失效，patch 要求变化保留 S0，路线/硬件变化保留 S0 与静态/patch 检查。失效记录不会删除或因改回旧值自动恢复，核实后重新登记；相同值更新不使证据失效。工具保留静态记录不代表新路线无需修改代码，实际代码变化仍按验证契约补验。

## 必须记录的问题

- 排查耗时较长、反复出现或依赖外部提示。
- 导致路线、权重、评测配置或 CPU fallback 变化。
- patch/安装/下载/helper 错误未传播，曾造成假成功。
- accuracy/performance 口径、数据 split 或计时边界发生变化。
- 动态 shape、custom op、cache、长时间编译、依赖冲突、数据生成或许可证问题。

进入交付阶段时按 `output-contract.md` 提取用户复现所需事实。公开事实可记录于同目录的 `public-facts.json`；来源/证据关联单独留在内部记录。内部等级、门禁、账号、路径、临时日志与完整排障历史不进入 README。
