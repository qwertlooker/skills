# 适配 patch 修改参考

写 patch 时按实际涉及的部分读取。路线选择见 [route-selection.md](route-selection.md)，依赖和数据排查见 [adaptation-heuristics.md](adaptation-heuristics.md)，正确性证据按 [validation-contract.md](validation-contract.md)。样本是定位线索，不是兼容性保证。

## 先读什么

先沿用户入口和生效配置确认受阻代码确实会执行。可选 CUDA 加速已有等价实现时，先用正常配置关闭该分支并比较实际输出与成本；仅在目标仍未满足时实现替换。需要查同任务、同路线样本时读取对应 patch、固定源码版本和应用命令；扩大样本范围可运行：

```bash
python3 "$SKILL_DIR/scripts/patch_pattern_miner.py" <ACL_PyTorch/built-in> --out <内部报告路径>
```

挖掘器只按新增行与文件名分类。回到实际调用链判断必要改动，不把统计频次当路线依据，也不向用户默认交付挖掘报告。历史样本来源与采集边界见 [modelzoo-sampling.md](modelzoo-sampling.md)。

## 设备、后端和权重

- 搜索 `cuda`、`.cuda()`、`torch.cuda`、CUDAExtension、map_location 与硬编码后端。推理/评测默认 NPU，CPU 对照显式选择，后端注册按选择导入；不要用静默 fallback 掩盖 NPU 不可用。
- 继承执行端分配的可见卡，宿主、容器和环境变量的映射按目标版本核对。框架/API 所需的可见设备内逻辑索引按实际映射使用，不把 `npu:0` 或 `InferSession(0, ...)` 的字面出现自动判为物理卡硬编码。
- Lightning/第三方框架若依赖 `accelerator='gpu'` 触发 transfer shim，验证实际设备并说明原因，不盲目替换为框架不支持的值。
- 上游固定 ORT、TF、Paddle 等后端时，先检查同架构同权重的可用路线；ORT 是否运行 NPU 要查实际 session provider 和节点分区，不能仅凭包名推断。
- 替换为 OM runner 时只替换核心调用，保持预后处理；按固定版本 API 核对输入输出、dynamic shape 和缓冲区大小。不能默认取第一个输出或未经确认拼接。
- 用户 checkpoint 优先。旧 checkpoint 加载策略与安全边界统一按启发式“权重和兼容性”处理；不得为使加载成功静默换权重、忽略关键 missing keys 或使用随机初始化模块。

## 按触发条件选择修改

| 触发条件 | 可考虑的局部修改 | 必须核实 |
|---|---|---|
| 复数/FFT/fbank 不支持或异常 | 等价实虚部计算、明确的 CPU 前处理或拆子图 | 实际设备、数值与精度；不要仅凭 warning 判 fallback |
| dtype/算子支持限制 | 调整受影响张量 dtype，或改用后端等价算子 | 输入输出 dtype、溢出与任务精度；不能全局盲换 dtype |
| attention/custom CUDA op | 条件编译、Ascend 等价算子、局部 eager 或拆图 | mask/layout/cache 与算子语义；细节见路线选择 |
| 固定 batch / 动态输入 | 参数化 shape，尾 batch padding 后裁掉输出 | 有效样本数、动态档位与 decoder contract |
| 服务/图编译性能不足 | 必要的编译配置、缓存、预热与调度参数 | 冷启动/稳态、cache 命中、并发和端到端口径 |
| ASR/多子模型 | 分离 encoder、decoder、joiner、LM/CTC 与搜索边界 | 状态流和 cache 的名称、shape、dtype；保持原搜索与 tokenizer |
| 生成式 cache 布局变化 | 明确 list/flat tensor/OM I/O 映射，参数化长度 | 前几步 logits/token 对齐及任务质量；首 token 分叉可级联 |
| NPU 预处理优化 | 只在瓶颈或图内需求成立时迁移 resize/normalize 等 | CPU/NPU 中间张量对齐，不能只看最终输出存在 |
| 大 ONNX / external data | 按工具限制拆图或外置权重 | 文件清单完整、artifact hash、转换与加载均可复现 |
| 上游量化图不适用 | 先建立可用浮点基线，再评估目标路线量化 | 目标版本/硬件支持与重新评测；不把禁用量化当普遍要求 |

## 依赖补丁与应用路径

- 只修改会覆盖配套核心栈、引入不适配 runtime 或阻塞安装的条目；用真实入口与 evaluator 检查补齐业务依赖，不随意把完整依赖表改为短白名单。
- 优先用明确安装顺序和 `--no-deps` 控制解析；metadata 本身错误时才 patch setup/pyproject。不要复制旧版本 API workaround 到未触发问题的环境。
- 必须 patch site-packages 时单独成 patch。用 `importlib.util.find_spec()` 定位顶层包并检查存在，避免为定位而 import 包。
- diff 头为 `a/<pkg>/...` / `b/<pkg>/...` 时，从 site-packages 根目录用 `-p1`；直接为 `<pkg>/...` 时核实 `-p0`。README 写目标版本、应用位置、dry run 与恢复方法。

## 完成前核对

- 在固定上游版本验证 `git apply --check` 或实际采用工具的 dry run，并核对应用后的实现；已应用 patch 应在干净副本重放，不把重复应用失败当 patch 错误。
- 移除本地绝对路径、调试残留、无关格式化和重复逻辑；每个硬编码 batch/shape/SOC 都有依据或参数。
- 保留可运行的 CPU/upstream 精度对照；fallback 边界与性能说明一致。
- 按内容审阅复核改动调用链及 README，再执行受影响的功能、精度和性能验证；patch 能应用不等于适配正确。
