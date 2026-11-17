# 交付验收与 ModelZoo 上库

交付和检视共用本清单。实现者交付前逐项自检；检视者核对同一条件及证据，不另设一套通过标准。普通工程只使用通用项；明确以上库为目标时再加载目标仓项。

## 执行方式与范围

- **交付/修复**：整理候选、补齐所需验证、修复问题并重放。
- **只读检视**：固定源码/PR head、base、目标目录和 diff，按同一清单输出 findings 与缺口；源码和 README 默认只读，不为审查新建三份文档。
- 只读检查的输出写入临时目录或已有内部记录，不覆盖被检视的输入、参考结果或用户产物；无法运行的项记录缺口。
- 本地窄范围修复只检查受影响项，不因使用本清单自动升级为上库任务。
- 多模型 PR 按目录检查，共享文件单列。未执行或缺少证据的项标为未验证；已有完整有效证据可核验复用，不为形式重复执行高成本测试。
- 通过表示适用要求有当前有效证据。评论、静态工具成功、历史 CI 和“已写计划”均不能代替真实验证；NPU 未实测须保留缺口。

## 统一验收清单

| 条件 | 如何核验 | 适用范围 |
|---|---|---|
| 版本与变更范围可追溯 | 源码/权重/辅助模型固定，当前 diff 与声明一致；补丁可重放且无无关改动 | 通用 |
| 环境与入口可运行 | 配套版本、业务依赖、真实入口 import/help；命令与 cwd/路径/参数一致，新增依赖无核心栈冲突 | 通用 |
| 数据与错误路径可信 | 实际 manifest/split/样本数、离线复用；wrapper/patch/下载失败传播；改动涉及的异常输入轻量核验 | 通用 |
| NPU 执行与数值正确 | 实际 device/provider、fallback 边界、dtype/shape、关键权重加载；按模型类型选补验 | 声称 NPU 验证时 |
| 精度与性能结论有依据 | 官方口径/可比基线、完整结果、阈值、同步/计时边界及重复结果；续跑汇总和无有效样本边界正确 | 声称完整验收时 |
| 用户文档与候选自包含 | 文档只含公开事实，限制保留；路径/文件/命令可复制，内部记录不混入 | 有文档或候选交付时 |
| 正式目标与贡献要求满足 | 最新目标基线、同名目录范围、许可证/版权/元数据、ModeList 与自测试适用性 | ModelZoo 上库 |
| 干净环境最低路径重放 | 从候选 README 开始，源码/依赖按声明获取，不借用开发环境隐含文件/cache/变量 | ModelZoo 上库；其他任务按要求 |
| 当前 head 的 CI/评论问题闭环 | 回到具体 CodeCheck/SCA/Antipoison 阶段、当前 diff 与证据，不以旧失败/AI摘要直接判定 | 涉及 PR/CI 时 |

技术标准见 `validation-contract.md`，内容边界见 `output-contract.md`，文档/脚本约定见 `style-guide.md`；各处只维护自己的规则。语法和正则扫描只提供线索，不替代运行检查。

## 目标仓基线（仅 ModelZoo）

开始任务与准备提交时查询 master，记录 SHA、时间、拟合入路径 `ACL_PyTorch/built-in/<category>/<model>` 和贡献规范来源 revision。已有目标先比较文件/README，明确保留、替换、删除范围。

```bash
git ls-remote https://gitcode.com/Ascend/ModelZoo-PyTorch.git refs/heads/master
python3 "$SKILL_DIR/scripts/modelzoo_sampler.py" --count 12 --category <category> \
  --keyword <route-or-task> --out /tmp/modelzoo-samples.md
```

按最后实质变更选同领域同路线样本，其次同路线跨领域。记录目录 commit/date 与选择原因，排除批量格式/链接更新。页面解析失败改用固定 HEAD 的 Git 历史；方法与本轮样本见 `modelzoo-sampling.md`。最新观察不静默替换已冻结验收基线。

完整上库工作区维护 README、适配事实、验收方案三类职责；内部文档位置服从工作仓约定。历史版本表、本地路径和源工作仓自动提交/推送约定不推广到其他工程。

## 候选与重放

- 运行 `workflow-delivery.md`：明确逐文件清单，组装独立候选，检查内容边界并按 README 重放。无源码改动不造空 patch。
- ModelZoo 默认排除历史 README、内部适配/验收/分析文档、`.codex-reference/`、开发 checkout、日志、cache、权重和评测大数据；明确的小型功能 fixture 可交付。工作区原文件无需因此删除。
- 许可证、版权头、`modelzoo_level.txt`、ModeList、自测试及其他元数据按当前目标仓规范判断；不能因历史目录缺失就跳过，也不生成虚假通过文件。
- ModelZoo 运行 `modelzoo_pr_quickcheck.py <repo> --target <路径> --strict`，再补模型特定验证。工具启发式命中须核实，不把现有工具的误报当硬规则。
- 仓内有 `tools/audit_model_delivery.py` 时运行基础审计及 `--target-readiness --target-path ...`；缺失时按规范逐项核查，明确该工具未执行。
- 重放保存源码/patch、安装/import、权重、manifest/样本数、NPU、compare 与结果证据；未执行最低路径命令不得假定可用。
- 技术等级、上库候选就绪及合入证明按验证契约分别判断；状态不回填 README。正式合入只由 merged/目标 commit 证明。

## PR 证据与问题闭环

```bash
python3 "$SKILL_DIR/scripts/gitcode_pr_review_sampler.py" \
  --pr-path <PR号>=<目标模型路径> --out /tmp/pr-notes.md --json-out /tmp/pr-notes.json
```

- 同一 PR 多目录重复传精确路径，核对每个路径都出现在 diff。分页不全或抓取失败记录为缺口，不能解释成“没有意见”。
- 区分人工意见、AI 线索、系统事件与 CI；AI 跳过/超时不能计为检视通过。评论指向旧版本时核对当前实现，已经修复的历史意见不再作为当前缺陷。
- 有争议的修复建议回到模型 contract：合法空检测不能被一律禁用，`strict=False` 不能仅因出现就判错，OM 多输出不能未经确认就拼接。
- finding 给严重性、文件/行、触发条件、影响、可复核证据与最小修复。运行/证据失真可阻塞，纯排版建议不升级为技术验收失败。
- 输出一份“条件—证据—结果”报告：通过/不适用（有依据）/缺失或失败。附源码 head、已执行/未执行项及真实设备范围；只读检视报告不写回 README。
- PR 描述按目标仓模板；无模板时可用 Motivation、Modification、Self-test、BC-breaking、Checklist。Self-test 引用当前 head 的实际结果，不用私有路径充当可访问证据。

## 规则来源

基础要求内化自 ModelZoo 工作仓 `AGENTS.md` 与标准流程（来源快照 `eab2246f74aaa932646e61eb212a254a0c16a187`）；后续 PR 采样只增加经当前代码核实的通用条件。来源快照不作为目标 master 最新证明。无需原文件也可运行；在具体工作仓中仍遵循适用 AGENTS 和用户授权。
