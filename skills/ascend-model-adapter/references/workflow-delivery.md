# 用户文档与候选交付工作流

输入：当前候选代码/入口、有效验证证据、用户或目标仓的交付要求。
输出：自包含 README；需要独立候选交付时另提供文件清单与候选目录。仅整理文档时就地编辑并核对相关运行入口，不为打包增加目录和报告。内部记录和进度报告单独保留。

本文的“候选源码目录”是待交付 README 和脚本所在目录，也是 `--source` 的根目录；它可以就是现有模型工作区。“项目私有目录”默认是工作区内的 `.ascend-adaptation/<project-id>/`。组装后的“候选目录”是单独的新目录，例如工作区内的 `candidate/`。命令中的 `<...>` 均须换成实际值，文件清单中的相对路径以 `--source` 为基准。

## 1. 确定公开事实

先读 `output-contract.md` 和 `style-guide.md` 的对应部分，并按 `content-review.md` 阅读当前文档与入口实现；已有有效审阅记录只需复核受影响项。核对源码/patch、权重、环境和评测配置与证据是否匹配；有变化的指标不能沿用。不要把内部文档或聊天历史直接摘要成 README。

按模型、环境、安装、数据、运行、评测、限制、FAQ 和来源提取最小公开事实。每项事实在内部保留来源或证据关联；公开事实本身不携带阶段、门禁、证据 ID 或内部路径。

通常直接按公开事实编辑文档即可。需要生成新 README 时，可在项目私有目录维护 `public-facts.json`，使用下列封闭字段。除可选的 `faq`、`sources` 外，所有字段必填且为非空 Markdown 字符串：

`title`、`overview`、`environment`、`installation`、`data`、`inference`、`evaluation`、`limitations`、`faq`、`sources`。

字段对应 `assets/readme.md.template` 的用户章节。未知项写真实范围，例如“尚未在 Ascend NPU 上实测，未提供 NPU 精度或性能结果”；不编造版本、命令或指标。FAQ 没有实际问题时省略 `faq` 或留空，不生成填充章节。来源关联另存在内部记录，不能作为额外字段混入公开事实。

`data` 只写单样例所需权重与输入；正式评测数据准备放入 `evaluation`。模板将 `limitations` 放在操作前。来源已在相应章节就近链接时可省略 `sources`，不能因此遗漏必要的源码/权重/数据来源；目标仓要求来源清单时仍提供。

## 2. 编写或更新 README

- 已有 README：按受影响章节编辑，保留有效使用说明；不整篇覆盖，不加入执行进度。
- 新建 README：使用模板或同任务目标仓风格，依据公开事实编写。可选命令：

```bash
python3 "$SKILL_DIR/scripts/delivery.py" render \
  --facts <项目私有目录>/public-facts.json --output <候选源码目录>/README.md
```

脚本拒绝未知字段和覆盖已有文件；`--force` 仅用于用户确实要求重新生成的文档。渲染不会执行或验证运行命令，也不能自动证明事实真实。

- 公开的版本、命令、指标和限制须能追溯到当前有效证据。限制不能为了通过检查被删掉；内部等级不能充当公开验证结论。
- 按 `content-review.md` 逐段核对用途、命令和结论，修正文档与实现不一致处并记录复核结果；仅委托改文档时，超出范围的实现问题报告为缺口。

## 3. 边界检查与按需组装

```bash
python3 "$SKILL_DIR/scripts/delivery.py" check <候选源码目录>/README.md
```

单文件检查拦截明确的内部标识、引用和流程性段落；目录检查还检查混入的内部文件。工作区中的私有目录无需删除，按清单组装后再检查整个独立候选。脚本不能替代语义审阅、依赖检查、NPU 验证或目标仓验收。

仅整理文档时跳过下面的组装，直接进入第 4 节，验证位置使用当前工程目录。

在项目私有目录保存 `candidate-files.json`，内容为相对候选源码根目录的逐文件 JSON 数组，例如 `["README.md", "requirements.txt", "infer.py", "diff.patch"]`，只列实际存在的文件。不用脚手架重新生成已完成的工程。

```bash
python3 "$SKILL_DIR/scripts/delivery.py" assemble \
  --source <候选源码目录> --files <项目私有目录>/candidate-files.json \
  --output <不存在的独立候选目录> \
  --report <项目私有目录>/delivery-report.json
```

只复制清单内文件；拒绝内部记录、链接、越界路径、现有输出目录和现有报告文件。报告在候选外记录文件 SHA256 和 POSIX 执行位。每轮交付使用新的候选和报告位置，候选重命名失败时会撤回本次报告，可使用原参数重试。内部文件不在清单时无需删除或移动。

候选可以是工作区内一个尚不存在的子目录，例如 `<工作区>/candidate`；逐文件清单不会递归收集该目录。直接以原工程为 source，无需为满足目录位置要求额外暂存整份源码。候选不能等于或包含 source，报告仍须留在候选外。

## 4. 验证交付结果

仅更新文档时在当前工程验证受影响的命令。有独立候选时，从**已组装的候选**复制出临时工作目录，在副本内按 README 重放。Python 导入会产生字节码，推理或评测可能写相对输出，安装也可能生成包元数据。把这些文件留在副本，接收方拿到的候选仍与组装报告对应。

下面假设 `CANDIDATE` 指向刚组装的目录，样例的 README 入口是 `python3 infer.py`。在接收方可用的运行环境里，把最后一行换成该项目 README 中实际的安装、数据准备和运行命令。长任务需要留证时，将必要的结果保存在候选外。

```bash
(
  set -eu
  python3 "$SKILL_DIR/scripts/delivery.py" check "$CANDIDATE"
  replay_dir=$(mktemp -d)
  trap 'rm -rf -- "$replay_dir"' EXIT
  cp -a -- "$CANDIDATE/." "$replay_dir/"
  cd -- "$replay_dir"
  python3 infer.py
)
```

临时目录只隔离文件写入。使用按 README 准备的解释器或容器，排除开发 checkout 的 editable install 和私有 `PYTHONPATH`，保留声明的 CANN 等运行环境。怀疑导入错包时，在副本内用同一解释器查看目标模块的 `__file__` 或 `importlib.util.find_spec(...).origin`。模块应来自候选副本或声明的依赖。若只有让开发目录参与导入才能成功，定位缺失的模块、依赖或安装步骤并重新组装。

- 完整交付覆盖安装、最小推理和声明的评测。已有当前有效运行证据可核验复用，ModelZoo 的独立重放要求仍然适用。交付前运行 `python3 "$SKILL_DIR/scripts/delivery.py" verify --report "$DELIVERY_REPORT"`，其中 `DELIVERY_REPORT` 为本轮组装报告。此命令核对候选文件集合、SHA256 和 POSIX 执行位。Linux 候选在实际 POSIX 文件系统上完成验证。ModelZoo 同时用该报告关联审计和独立重放证据。
- 分开验证“只跑单样例”和“执行正式评测”两条路径；前者不应意外要求完整评测数据。已有结果的续跑仅按脚本实际支持的参数进行，不假定每个入口都有 `--resume`。
- README 需下载或 clone 的资源按明确 URL/revision 获取，不能禁止 README 自身声明的上游获取过程。
- 核对文档所有文件名、参数、输入输出、数据口径与真实运行一致。缺设备时报告未执行项，不能用内容检查代替实测。
- 按 `modelzoo-delivery.md` 的统一清单核对交付证据；普通工程只检查适用的通用项，ModelZoo 候选再增加目标仓要求。
- 对话报告交付位置、实际检查和剩余缺口。阶段和就绪状态按内部验证契约记录，不回填 README。
