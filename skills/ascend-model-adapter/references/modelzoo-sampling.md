# ModelZoo 样本与意见采集

## 本轮可追溯快照

采集日期：2026-11-17。实时 `git ls-remote` 与独立浅克隆 HEAD 均为 `c96a5cb797ef0c1ab9bb6802770571440f040bde`，最后提交日期 2026-11-16。下表为该快照的近期实质变更，不代表以后任务的最新基线。

| PR | 精确目标目录（ACL_PyTorch/built-in/ 下） | 已核对的参考价值 |
|---|---|---|
| [7769](https://gitcode.com/Ascend/ModelZoo-PyTorch/pull/7769) | embodied_ai/FlashOCC_for_PyTorch | 修复执行分支；少量 parity 和正式任务指标须区分 |
| [7760](https://gitcode.com/Ascend/ModelZoo-PyTorch/pull/7760) | cv/Trident | 权重、设备感知同步与配置检查；评论中已删除/改动路径不能作当前缺陷 |
| [7727](https://gitcode.com/Ascend/ModelZoo-PyTorch/pull/7727) | embodied_ai/BevFusion | 多模态/自定义算子交付；AI 因变更过大跳过，不能解释为检视通过 |
| [7740](https://gitcode.com/Ascend/ModelZoo-PyTorch/pull/7740) | cv/RemoteSAM | 当前 common.py 已加入关键权重检查、路径归一化，部分历史意见已闭环 |
| [7765](https://gitcode.com/Ascend/ModelZoo-PyTorch/pull/7765) | cv/SmolVLM2 | 当前续跑按选定 ID 去重并纳入历史结果；保留此做法，不把旧 summary 问题当现状 |
| [7776](https://gitcode.com/Ascend/ModelZoo-PyTorch/pull/7776) | cv/ByteTrack | 核对导出与 decoder 的输出 contract、实际业务依赖；不照搬未实测的多输出猜测 |
| [7758](https://gitcode.com/Ascend/ModelZoo-PyTorch/pull/7758) | ocr/DBNET（另含 PyTorch/DINO） | 最小导入修复与失败分支检查；CPU 宿主逻辑验证不冒充 NPU 回归 |

另读取 PR [7743](https://gitcode.com/Ascend/ModelZoo-PyTorch/pull/7743)（cv/Grounded-SAM-2）、[7742](https://gitcode.com/Ascend/ModelZoo-PyTorch/pull/7742)（cv/EdgeSAM）的 diff 与意见，作为额外线索；未将其声称为本轮 master 的最新已合入模型。

九个 PR 都已通过各自 diff 核对精确路径。按页码与 end_id/end_system_id 游标采集共 20 页、1664 个讨论条目（含系统事件），去噪去重后保留 203 条记录（含 AI/机器人意见，并非 203 条人工结论）。规则归入统一验收清单、验证契约与风格指南，不另维护检视规则集。

## 采样方法与降级

- 按任务/路线挑少量近期实质变更，记录路径 commit/date 与原因；新模型、推理链路、环境/评测或结果变更优先，批量格式/链接更新不能作为实质样本。
- `modelzoo_sampler.py` 的 HTML 解析在本轮返回零条，故改用固定 HEAD 的 Git 历史。不要反复重试旧页面解析器或把离线目录数声称最新。
- 独立 clone 不覆盖已有工作区；`--clone-dir` 只能用不存在或空目录。按需 sparse-checkout 相关路径，浅历史不足则 deepen，不能用浅边界伪造最后实质变更时间。

```bash
git -C <目标仓> rev-parse HEAD
git -C <目标仓> log -20 --date=iso-strict --format='%H %ad %s' -- ACL_PyTorch/built-in
git -C <目标仓> log -1 --format='%H %ad %s' -- <参考模型路径>
```

通过提交正文的关联 PR 和对应 diff 确认路径，不按 PR 标题猜目录。本轮排除了 PR 7741 与猜测目录不匹配的样本。页面列表、提交正文、当前源码与 PR head 是不同快照，应分别记录。

## 评论证据边界

- 脚本为 best-effort 获取器；接口结构、总数变化、缺少游标、重复页面、超过分页上限或缺 head 均报告证据缺口。不能用 `--allow-unverified` 输出支撑正式通过结论。
- 分页必须传递连续游标并核对总数；仅增加 page 会重复获得内容，返回的 total/page_count 也可能造成误判。
- 评论保留其原始版本语境。先核对当前实现再决定是否仍需修复；历史已修问题可提炼预防性条件，不重复报为当前缺陷。
- AI 摘要只是线索；例如“空检测一律失败”“strict=False 一律错误”“多输出直接拼接”等建议都须核实模型 contract。CI 仍只认当前 head 对应的具体阶段。
- 本轮只抓取并静态读取源码与评论，未执行模型代码、安装依赖、NPU 推理、精度或性能验证。已合入与评论“未发现问题”都不等于本 Skill 已复现实测。
