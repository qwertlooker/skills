#!/usr/bin/env python3
"""Create an Ascend adaptation workspace or a flat ACL target scaffold."""

from __future__ import annotations

import argparse
import os
import re
import stat
from pathlib import Path
from urllib.parse import urlparse

from delivery import render_facts
from project_log import add_git_exclude, slug

DEFAULT_IMAGE = None
DEFAULT_HARDWARE = None
ROUTES = ["onnx-om", "torch-npu", "torchair", "vllm-ascend", "hybrid"]


def infer_name(url: str) -> str:
    parts = [part for part in urlparse(url).path.split("/") if part]
    name = re.sub(r"\.git$", "", parts[-1] if parts else "model")
    return re.sub(r"[^A-Za-z0-9_.+-]+", "-", name).strip("-_") or "model"


def atomic_write(path: Path, content: str, executable: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    try:
        temporary.write_text(content.lstrip(), encoding="utf-8")
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)
    if executable:
        path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def readme(model: str, url: str, image: str | None, hardware: str | None) -> str:
    environment = "软件和硬件兼容范围尚未经过实测确认。"
    if image:
        environment += f"\n\n指定镜像：`{image}`（尚未实测）。"
    if hardware:
        environment += f"\n\n指定硬件：{hardware}（尚未实测）。"
    return render_facts({
        "title": f"{model} 推理指导",
        "overview": f"模型来源：{url}。",
        "environment": environment,
        "installation": "安装方法尚未提供，当前文件不能直接用于部署模型。",
        "data": "固定源码版本、权重、配置、数据和许可证信息尚未提供。",
        "inference": "可执行的模型运行方法尚未提供。",
        "evaluation": "未提供 NPU 精度与性能结果。",
        "limitations": "尚未在 Ascend NPU 上实测；可运行范围和依赖兼容性尚未确认。",
        "faq": "",
        "sources": f"- 上游源码：{url}",
    })


def export_onnx(model: str) -> str:
    return f'''#!/usr/bin/env python3
"""Export {model} to ONNX after replacing the model-specific TODO."""

import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-path", required=True)
    parser.add_argument("--output", default="model.onnx")
    parser.add_argument("--opset", type=int, default=17)
    args = parser.parse_args()
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    raise NotImplementedError("TODO: load model, export ONNX, run checker, and record artifact hash")


if __name__ == "__main__":
    main()
'''


def convert_om() -> str:
    return r"""#!/usr/bin/env bash
set -euo pipefail
ONNX_PATH=${1:-model.onnx}
OUTPUT_PREFIX=${2:-model}
SOC_VERSION=${3:-${SOC_VERSION:-}}
if [ -z "${SOC_VERSION}" ]; then
  echo "ERROR: set SOC_VERSION" >&2
  exit 2
fi
INPUT_SHAPE=${INPUT_SHAPE:-"TODO_input:1,3,224,224"}
INPUT_FORMAT=${INPUT_FORMAT:-NCHW}
PRECISION_MODE=${PRECISION_MODE:-mixed_float16}
source /usr/local/Ascend/ascend-toolkit/set_env.sh
atc --framework=5 --model="${ONNX_PATH}" --output="${OUTPUT_PREFIX}" \
  --soc_version="${SOC_VERSION}" --input_shape="${INPUT_SHAPE}" \
  --input_format="${INPUT_FORMAT}" --precision_mode_v2="${PRECISION_MODE}"
"""


def infer(model: str, route: str) -> str:
    return f'''#!/usr/bin/env python3
"""Optional {model} inference entry; prefer patching an upstream entry."""

import argparse
import importlib
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="{model} inference")
    parser.add_argument("--model-path", required=True)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", default="outputs")
    parser.add_argument("--device", choices=["npu", "cpu"], default="npu")
    args = parser.parse_args()
    Path(args.output).mkdir(parents=True, exist_ok=True)
    if args.device == "npu":
        importlib.import_module("torch_npu")
        raise NotImplementedError("TODO: implement NPU inference for route={route}")
    raise NotImplementedError("TODO: implement explicit CPU/upstream fallback")


if __name__ == "__main__":
    main()
'''


def npu_adaptation(model: str, url: str, category: str, profile: str) -> str:
    target_scope = (
        f"ModelZoo 目标路径：`ACL_PyTorch/built-in/{category}/{model}`；master/路径状态/样本/贡献门禁：TODO"
        if profile == "modelzoo" else "用户交付目标和验证范围：TODO；ModelZoo 上库约束不适用。"
    )
    return f"""
# {model} NPU 适配事实

## 任务范围

- {target_scope}
- 检查日期、候选文件与排除项：TODO

## 版本边界

- Upstream：{url}
- Upstream commit：TODO
- 权重 revision/文件/SHA：TODO
- Config/tokenizer/辅助模型：TODO
- 非目标变体：TODO

## 适配与验证事实

- 设备节点、route 和 patch：TODO
- 依赖/import/py_compile/help：TODO
- 权重/数据路径与校验：TODO
- CPU/CUDA/NPU 已执行命令和结果：TODO
- 未执行项、原因和补验方式：TODO

## 正式候选清单与排除项

- 候选文件：TODO
- 默认排除：`NPU_ADAPTATION.md`、`ACCEPTANCE_PLAN.md`、`upstream/`、日志、权重、数据、cache、`.ascend-adaptation/`

## 当前状态

- S0–S4：未定级
- 下一等级缺失证据：TODO
- target_ready：false
"""


def acceptance_plan(model: str) -> str:
    return f"""
# {model} 验收方案与结果

## 验收目标与版本边界

TODO：当前模型/权重/变体、排除项、目标 S3 或用户要求的 S4。

## 原始公开/官方基线

TODO：dataset/split/样本规模、metric、normalizer/后处理、decode 参数、checkpoint 和来源。

## 数据准备与固定输入

TODO：独立准备命令、manifest/meta、离线模式、SHA、样本数和可读性检查。

## 功能验证（S2）

TODO：干净环境安装、真实权重/输入、CPU/CUDA/NPU 端到端命令、输出 sidecar。

## L2 精度/质量与性能（S3）

TODO：NPU evaluator、自动 compare、阈值来源；公开基线不可比或 patch 改语义时补 CPU 精度对照。

性能至少独立执行 3 次，保存每次结果并报告中位数；说明 pure model/E2E、同步、warmup、batch/并发和峰值 HBM。

## 扩展验收（S4，可选）

TODO：长稳、L3、业务集、并发或用户明确扩展项。

## 最低正式验收清单

- [ ] 数据准备和 metadata 可执行。
- [ ] 功能推理输出独立目录和 sidecar。
- [ ] NPU 精度/质量结果和 compare 非零失败门禁。
- [ ] NPU 性能 3 次和中位数。
- [ ] 报告记录 S0–S4、未完成项和结论。
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model_url")
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--model-name")
    parser.add_argument("--category", required=True)
    parser.add_argument(
        "--layout",
        choices=["workspace", "target"],
        required=True,
        help="Initialize a workspace or a flat target scaffold; this does not assemble a delivery",
    )
    parser.add_argument("--route", choices=ROUTES, required=True)
    parser.add_argument("--image", default=DEFAULT_IMAGE)
    parser.add_argument("--hardware-model", default=DEFAULT_HARDWARE)
    parser.add_argument("--profile", choices=["generic", "modelzoo"], default="generic")
    parser.add_argument("--project-id", help="Stable internal project ID; defaults to category__model")
    parser.add_argument("--internal-dir", type=Path, help="Internal docs directory, relative to output or absolute")
    parser.add_argument("--with-readme", action="store_true", help="Explicitly create a public README draft")
    parser.add_argument("--with-infer", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    model = args.model_name or infer_name(args.model_url)
    output = args.output_dir
    files = {
        output / "requirements.txt": (
            "# Business dependencies only. Keep the image-provided torch stack intact.\n"
        ),
    }
    if args.layout == "target" or args.with_readme:
        files[output / "README.md"] = readme(
            model, args.model_url, args.image, args.hardware_model
        )
    if args.layout == "workspace":
        project_id = slug(args.project_id or f"{args.category}__{model}")
        internal = args.internal_dir or Path(".ascend-adaptation") / project_id
        if not internal.is_absolute():
            internal = output / internal
        files[internal / "NPU_ADAPTATION.md"] = npu_adaptation(
            model, args.model_url, args.category, args.profile
        )
        files[internal / "ACCEPTANCE_PLAN.md"] = acceptance_plan(model)
    executable: set[str] = set()
    if args.route == "onnx-om":
        files[output / "export_onnx.py"] = export_onnx(model)
        files[output / "convert_om.sh"] = convert_om()
        executable.update({"export_onnx.py", "convert_om.sh"})
    if args.with_infer:
        files[output / "infer.py"] = infer(model, args.route)
        executable.add("infer.py")

    collisions = [
        path for path in files if path.exists() or path.is_symlink()
    ]
    if collisions and not args.force:
        raise FileExistsError(
            "Refusing partial scaffold write; existing files: "
            + ", ".join(str(path) for path in collisions)
        )
    # Check all destination links before writing any file, including with --force.
    for path in files:
        if any(parent.is_symlink() for parent in [path, *path.parents]):
            raise ValueError(f"Refusing to write through symbolic link: {path}")
    output.mkdir(parents=True, exist_ok=True)
    for path, content in files.items():
        atomic_write(path, content, path.name in executable)
    if args.layout == "workspace":
        add_git_exclude(output)

    print(f"Created scaffold: {output}")
    print(f"Route: {args.route}; layout: {args.layout}")
    print("Files: " + ", ".join(sorted(str(path) for path in files)))
    print(
        "Scaffold only. Keep execution notes private; prepare user documentation through the delivery workflow."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
