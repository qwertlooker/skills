# Ascend 适配领域启发式

## 目录

1. 环境与依赖
2. 权重和兼容性
3. Pipeline 与后端
4. ONNX/OM
5. 数据与预处理
6. 服务和性能

这些是排查信号，不替代实测、官方兼容矩阵或项目日志证据。

## 1. 环境与依赖

- 镜像中的 CANN、Python、torch、torch_npu、torchvision/torchaudio 应成套；遇到 undefined symbol/ABI 错误先查版本栈。
- 沿用可复现且版本匹配的环境；是否另建 venv/容器取决于依赖冲突与隔离需要。只隔离后端差异时可在同一软件栈切换 `--device cpu`；共享前后处理的正确性另用未改上游或任务标签核对。
- 不先安装 CPU-only PyTorch 再追加 torch_npu；镜像预装时记录镜像 digest 和导入/NPU tensor 证据，不在快速上手中写泛化的 `pip install torch torch-npu`。
- 审计顶层、子模块和 vendor 的 requirements/setup/pyproject。优先顺序：业务 requirements → 安全的 editable 子包 → 顶层 `pip install --no-deps -e .`。
- 只过滤会覆盖核心栈、拉取 CUDA runtime 或阻塞安装的依赖；过滤后用真实入口 import、`--help` 和单样例补齐业务依赖。
- Paddle、vLLM、TorchAir、DrivingSDK、OpenCV、tesseract 等容易冲突；复杂 pipeline 可拆容器，但要记录组件边界和数据交换。
- 版本相关 FAQ 只在实际触发版本下出现，不把历史 workaround 无条件复制到新环境。
- 修改 site-packages 时用 `importlib.util.find_spec('<pkg>')` 定位顶层包，先检查 spec/包路径存在；不要为定位而 import 包。补丁路径和 strip 层数按 `patch-modification-patterns.md` 核对。
- ORT CANN EP 记录实际 ORT 构建版本/来源、CANN、Python/架构与安装方法；核心计算的设备归属按[路线选择](route-selection.md)跟到真实节点。
- 多 requirements/extras 先查包含关系与任务依赖闭环，import 检查覆盖真实模型类、evaluator/normalizer 与实际 NPU tensor；不把只安装成功等同依赖可用。CPU ORT 与 CANN 构建避免在同一环境相互覆盖。

## 2. 权重和兼容性

- 用户提供的 checkpoint 优先；确认类别数、tokenizer、speaker/label map、配置和模型类成套。
- 可信旧 checkpoint 在 PyTorch 2.6+ 可能因 `weights_only=True` 默认策略失败；优先转换 state_dict/safetensors。只有来源和哈希可信且在隔离容器中，才考虑 `weights_only=False`。
- torchaudio 2.9+ 音频加载可能引入 TorchCodec/FFmpeg/ABI 变化；出现问题时检查实际版本，可用 soundfile/librosa 替代 I/O，但要对齐波形和任务指标。
- 模型变体、聚类/阈值/beam/search 和预后处理必须与 checkpoint 对应，不能只用默认 config 推断官方口径。

**加载成功但疑似用错权重。** 找到发布者推理入口实际取用的容器（例如 `model` 或 `ema`），用分片索引定位文件，从张量元数据读取键名、shape 和 dtype，与模型实例逐项核对。去掉 `module.` 等前缀时先预览映射：两个源键落到同一目标键就停下核对来源，字典覆盖会掩盖冲突。检查 loader 返回的缺失键和多余键，尤其是任务头、投影层和 adapter。按组件解释有意缺失或共享的权重。LoRA 单独发包时核对基座 revision 和 adapter 各自的加载覆盖，再用独立样例核验。仅在加载有疑点时做这份盘点。[上游 checkpoint 排查方法](https://gitcode.com/Ascend/model-agent/blob/c75448c13fb4a35e7ec0883ce48d05c23eb5b7fa/skills/adaptation/ascend-checkpoint-forensics/SKILL.md)

## 3. Pipeline 与后端

- 搜索硬编码 `cuda`、`.cuda()`、`torch.cuda`、CUDAExtension、custom op 和 map_location；按组件决定 NPU 等价实现、拆图或 CPU fallback。
- 上游硬编码 ONNX Runtime、TensorRT、TF、Paddle inference、OpenVINO 时，检查同项目的 PyTorch 等价路径。后端替换保持同架构同权重并做数值对齐。
- OCR/VLM/VLA/TTS/diarization/检测+识别先列组件表：实现、权重、输入输出、路线、目标设备、阻塞和耗时。
- CPU fallback 必须是评估后的技术选择；概述、组件表、FAQ 和性能表保持一致。
- 同架构后端替换比较 logits/embedding/中间张量；换模型、权重、tokenizer 或策略后重新跑任务指标。
- 官方 evaluator、normalizer、tokenizer 和预期字段严格失败；不要用简化 metric、宽泛 getattr/try-except 或远端自动 fallback 生成貌似成功但不可比的结果。

## 4. ONNX/OM

- 动态 shape、符号维、多输入输出、control flow、attention、RoPE、cache 和后处理入图是高风险点。
- 导出先跑 checker；需要时采用 shape 固化、onnxsim/onnxslim、MagicONNX/msit surgeon 或拆子图，并记录每一步输入输出 artifact hash。
- 固定 batch 评测处理尾 batch padding，并在输出后裁掉；dynamic shape 明确范围、档位和 custom_sizes。
- 大 ONNX 检查 external data，README 列出不可拆散的文件。
- ATC 命令参数化 SOC_VERSION、input shape 和精度模式；长编译与 cache 行为写入 FAQ。

## 5. 数据与预处理

- 权重、数据、评测工具、protocol、reference label/RTTM 都写来源、版本、目录树和生成命令。
- `prepare_data.py` 区分下载输入、生成中间文件和最终 manifest；每个 dataset/language 分支用最小 fixture dry run。
- 检查 GitHub zip 顶层目录、Hugging Face 原始文件 URL、压缩包类型、文件大小和可选 SHA256。
- 联网获取与推理/评测分开。使用独立 wget/curl、官方客户端或 Python 准备入口，固定资源版本并核对实际文件/大小及可用 SHA。运行入口可使用严格本地模式的 loader，但不能缺文件后隐式联网。受限或分片资源按官方获取方式提供离线准备说明，不为工具统一复制另一套下载器。
- 此下载约定不限制 pip 安装依赖；不预设所有环境都有内部 PyPI 镜像。URL check-only/HEAD 只支持可访问性/metadata 结论，不能代替完整文件校验或权重加载。curl `--fail` 也不能识别 HTTP 200 的 HTML 错误页。
- 提供严格 `--offline` 或等价模式；缺文件时报告具体路径并失败，不联网 fallback。manifest/meta 记录远端 URL、config/split、本地文件、复用/离线状态和样本规模。
- 离线交接先盘点 checkpoint 分片与 index、config/tokenizer/自定义代码、辅助模型、evaluator 和业务依赖。存在目录不代表资源齐全；检查 Git LFS pointer、HTML 错误页、缺失分片及 loader 实际路径。明确区分可执行的加载检查与仅有文件清单，不因目录完整就声称权重可加载。
- 数据准备写入显式指定目录，校验通过才复用，下载到临时文件后替换；检查实际 shard/split，避免只请求 test 却构建全量缓存。多个任务单独准备，必要的整 shard 下载量在文档说明。
- 音频/图像/视频预处理精确复现采样率、声道、resize/crop、归一化、padding 和重采样工具；改动后对齐中间结果或任务指标。
- 原仓没有的 norm stats、label map 或配置必须提供生成依据和命令。

## 6. 服务和性能

- 只有服务入口才验证启动、就绪与真实请求。TorchAir 批处理任务直接验证编译路径的输出及冷/热成本；服务负载与限时吞吐按[验证契约](validation-contract.md)测量。
- vLLM 嵌套配置按固定版本实际 `--help` 的 JSON/CLI 语法书写；server 的 served model、context、client 和 benchmark 名称保持一致。外部 evaluator/agent/tool 仓固定 commit。
- 纯模型 NPU 计时前后同步；端到端测量明确包含数据、网络、排队、后处理和 CPU 组件。
- 首次编译、cache miss、warmup 与稳定性能分开；服务模型同时考虑并发、tokens/s、latency 和错误请求。
- 正式性能的重复与统计要求见验证契约；CPU 性能不用于推断 NPU 加速比。
- 音频默认 RTF，OM 常用 latency/FPS，服务常用 QPS/tokens/s；最终口径仍优先与官方 benchmark 对齐。
- 共享设备与多卡分配按 `environment-container.md`，继承已分配范围，核对容器与进程索引；瞬时空闲不代表可占用，不静默使用 0 卡。
