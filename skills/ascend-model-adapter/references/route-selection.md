# 从交付端选 Ascend 推理路线

先看启动命令与加载调用，确定已有制品、目标运行时和不能改变的条件。仅有裸 ONNX 时可在兼容环境中用原图取得参照；接收端只接受 OM 时，最终探针必须使用该 OM 和目标 runner。已有 OM 先检查 SoC、I/O 描述和真实输入，能直接重放就跳过导出和编译。已有推理服务先核对固定版本是否原生支持该架构及所需功能，包括 tokenizer、量化、图像输入或工具调用等实际使用项。已有支持满足要求时，配置和运行该入口即可交付。

核对**目标版本组合**和已分配的硬件。模型支持表提供候选，发布版的配套表、实际 loader 和目标输入决定能否使用。对显存受限的任务先估算本卡常驻权重的字节下界，再为激活、工作区及实际并发的 KV cache 留空间；落盘的压缩体积不能直接作显存估算。硬约束冲突时给出具体冲突与放宽哪项条件才可继续，例如只能交 OM，而唯一跑通的路径需要 Python 服务进程。[Ascend PyTorch 配套表](https://github.com/Ascend/pytorch/blob/master/COMPATIBILITY.en.md)

| 实际入口 / 路线 | 足以改变路线选择的实验 |
|---|---|
| PyTorch 上游 / `torch-npu` | 用实际模型类和 checkpoint 在分配设备运行关键分支，核对输出及执行设备。eager 已满足任务就保留；有编译收益目标再试图编译。 |
| TorchAir / `torchair` | 同一权重和输入对照 eager 与编译路径；用目标 shape 分布重放，观察重编译、graph break、冷启动与稳态。编译耗时挤占短作业预算时保留 eager 或只编译热点子图。 |
| 上游使用 ORT 加载 ONNX / `ort-cann` | 复用同一 ONNX（含 external data）与预处理，在 CPU EP 建参照。目标构建中创建 CANN session，运行同一 feed，检查关键节点放置与数值。用户要求保留 ORT API 时直接验证这条路。[CANN EP 配套和子图选项](https://onnxruntime.ai/docs/execution-providers/community-maintained/CANN-ExecutionProvider.html) |
| 接收端加载 OM / `onnx-om` | 按所持制品从最近的环节开始。需要导出时先对齐上游与 ONNX 输出，再让目标 runner 加载实际编译的 OM，对照相同 feed。要求动态档位时用同一 OM 覆盖有区分度的档位及尾 batch。 |
| vLLM-Ascend 服务 / `vllm-ascend` | 用交付的模型名和协议走一次真实请求，核对服务实例；涉及 cache 时覆盖 prefill 和后续 decode。并发、长上下文、流式或工具调用按用户声明分别探测。 |
| 确有多种模型执行后端 / `hybrid` | 固定组件间的张量、状态或文件，分别对齐替换边界，再走一个完整业务请求。多个模型都在同一后端可沿用该路线；常规 CPU 解码、分词或读盘单列为前后处理。 |

**ORT 放置核验。** `get_available_providers()` 表示当前安装能选哪些 EP，`session.get_providers()` 表示 session 注册顺序。对关键图或每个实际参与请求的 session，可以在创建时开启 `SessionOptions.enable_profiling`，运行一次后调用 `session.end_profiling()`，查看 JSON 中 `cat == "Node"` 的事件名与 `args.provider`。若版本或融合图未给出归属，改用该版本的分图日志或设备 trace；只观察到 CPU 或无法定位核心计算时，报告实际覆盖。计时另用关闭 profiling 的同一部署。工作流允许合理的 CPU 算子，判断依据是用户要求上卡的计算是否上卡。[ORT 执行提供程序](https://onnxruntime.ai/docs/execution-providers/)、[profiling](https://onnxruntime.ai/docs/performance/tune-performance/profiling-tools.html)

**多模态服务能返回文本，却无法证明视觉分支有效。** 先对照 checkpoint 的 architecture、目标版本注册的模型类和实际 processor。沿一个图文请求追到图像预处理、视觉编码器、投影层和语言模型，核对特征或图像 token 确实传到下一环节。可用同一问题配两张在上游有明确不同答案的图片重放；若输出异常，保存两次实际特征和消费位置。CUDA 扩展命中时，区分仅在安装或导入时出现、可选加速分支、业务请求必经的算子，分别验证延迟导入、等价实现或组件替换。抽出文本 backbone 能验证语言子模型，完整图文交付仍需重放原图文请求。[上游 CUDA 组件检查](https://gitcode.com/Ascend/model-agent/blob/c75448c13fb4a35e7ec0883ce48d05c23eb5b7fa/skills/adaptation/ascend-cuda-compat-check/SKILL.md)、[vLLM-Ascend 适配流程](https://gitcode.com/Ascend/model-agent/blob/c75448c13fb4a35e7ec0883ce48d05c23eb5b7fa/skills/adaptation/vllm-ascend-model-adapter/SKILL.md)

**切换成本。** 切路线前写清哪条约束或哪次测量否定当前方案。只改一个足以区分原因的变量，保留旧输入与参照；缺资源时给出首个目标端探针与成功判据。需要 CPU fallback 时记录组件、数据往返和对端到端目标的影响，有相应实测再给耗时占比。

## Attention 或自定义算子

按目标版本核实 SDPA、eager 或后端融合算子的支持。核对 mask 方向、layout、dtype、GQA/MQA 与缓存语义，用同一序列对比完整 forward 与逐步解码的对应 logits。只改算子的小实验能通过后，再恢复完整模型与服务调度。ONNX 图改写按图接口验证，vLLM attention 按其引擎接口验证。
