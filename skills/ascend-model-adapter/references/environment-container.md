# 执行位置、设备与容器

准备运行环境、选卡、处理无设备/离线或依赖冲突时读取。先复用用户指定且可复现的环境；需要新环境时才创建，不默认重装宿主框架或启动容器。

## 确认在哪里执行

区分编辑工作区与执行端。根据用户提供的 SSH、容器、调度作业和已有脚本确认执行位置、代码 revision、路径映射、Python 解释器、设备分配与结果取回位置。连接信息优先从已授权配置查找；缺少影响执行的信息时只问缺项，同时继续本地静态工作。

在实际执行端检查设备与路线依赖。`npu-smi` 不在 PATH、Python 包导入失败、设备不可见分别定位，不统一判断为“没有 NPU”。`torch_npu` 探针只用于 PyTorch 路线；OM 路线检查其 ATC/ACL/runner，不为环境检查额外安装 PyTorch。

可用于已选 PyTorch 执行环境的只读信息查询（不是 NPU 推理证据）：

```bash
command -v python3
command -v npu-smi
npu-smi info
python3 -c "import sys, torch, torch_npu; print(sys.executable); print(torch.__version__, torch_npu.__version__, torch.npu.is_available())"
```

随后在已分配设备上完成该路线的最小计算/加载探针，再尝试模型全链路。记录实际解释器、配套版本和失败原文；只 import 成功不能支持设备可运行结论。

## 共享设备与多层编号

- 沿用调度器、容器或用户已经分配的可见设备与 rank 设置；不无条件重设为 0 卡，也不覆盖已有可见列表。共享机器上的瞬时空闲不等于已获分配，没有可确认资源时询问设备范围，继续不占卡的工作。
- 区分宿主物理 ID、容器逻辑 ID 和进程内索引。可见列表过滤后，程序的设备索引对应过滤后的列表，不能再次套宿主卡号。单卡探针和多卡 local rank 都核对实际映射及进程可见卡数。
- `ASCEND_RT_VISIBLE_DEVICES` 的可用性及与 profiling/DCMI/HCCN 等工具的限制依目标版本确认；不要为排障擅自清空已分配的可见范围。编号关系与限制分别见 [CANN 设备 ID 说明](https://www.hiascend.com/doc_center/source/zh/canncommercial/900/API/runtimeapi/aclcppdevg_03_2057.html) 和 [环境变量参考](https://www.hiascend.com/doc_center/source/en/CANNCommunityEdition/910/maintenref/envvar/envref_07_0028.html)，使用时切换到目标版本文档。
- 每个任务使用独立输出、日志和必要的可写 cache；多卡任务补充实际 rank/HCCL/网络配置，不为单卡任务增加分布式条件。

## 创建容器时

从目标硬件和软件版本的官方镜像启动说明生成实际命令，记录 tag/digest 与必要配置。没有一条能覆盖所有设备代际与路线的通用挂载命令；路径、设备节点和驱动配套必须在执行端核对。

- 只挂载分配的计算设备及该运行时要求的管理节点；不把所有 `/dev/davinci*` 默认开放给任务。
- 挂载明确的工程、权重、输入与输出目录。输入和权重可只读时用只读挂载，输出使用独立可写目录；不能整份挂载 `/root/.cache` 代替资源准备。只读绑定的语义见 [Docker bind mounts](https://docs.docker.com/engine/storage/bind-mounts/)。
- root、`--privileged`、host 网络/IPC 仅在已确认需要时加入，并说明原因；不把含这些配置的开发容器当作不可信代码隔离保证。设备与权限语义见 [Docker 运行参考](https://docs.docker.com/engine/containers/run/#runtime-privilege-and-linux-capabilities)。
- shm、端口、容器名称按任务规模和现有资源选择；启动新服务前确认端口，记录本轮 PID/容器 ID 和日志。编译期间存活不等于就绪，按实际 readiness 与一次请求确认；失败时仅清理本轮拥有的进程/容器，不使用宽泛 `pkill` 或删除共享缓存。
- 工具链环境脚本路径按镜像确定；生成的 OM 转换入口可用 `ASCEND_ENV_SCRIPT` 指定。环境加载后复核实际工具来源与版本。

## 资源不足时继续推进

| 实际条件 | 可继续的工作 | 暂不做出的结论 |
|---|---|---|
| 只有代码，无 NPU 或执行端暂不可达 | 内容审阅、静态修改、CLI/数据 fixture、暂定路线和明确探针 | NPU 可运行、性能达标 |
| 有设备，缺权重或受限数据授权 | 环境探针、加载路径检查、资源清单和用户提供文件接入 | 随机权重/合成数据达到正式精度 |
| 离线，资源已本地提供 | 核对来源/revision/哈希与完整性，再走严格本地加载 | 缺文件时联网 fallback 或换模型成功 |
| 共享卡繁忙、内存不足或编译超时 | 保存日志，定位设备/输入规模/编译边界，选择可检验的下一步 | 缩短 context、减 batch 或降精度后沿用原配置指标 |

依赖报错先核对当前解释器与核心栈，再按 `adaptation-heuristics.md` 修复业务依赖。若重试没有新诊断依据，保留错误和恢复命令，转做独立工作；不反复重装、无限拉取或重启同一失败任务。
