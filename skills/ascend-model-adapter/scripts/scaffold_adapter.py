#!/usr/bin/env python3
"""Create an Ascend adaptation workspace or a flat ACL target scaffold."""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import stat
from pathlib import Path
from urllib.parse import unquote, urlparse

from delivery import render_facts
from project_log import ROUTES, add_git_exclude, slug

DEFAULT_IMAGE = None
DEFAULT_HARDWARE = None


def infer_name(url: str) -> str:
    parts = [part for part in urlparse(url).path.split("/") if part]
    name = re.sub(r"\.git$", "", unquote(parts[-1]) if parts else "model")
    return re.sub(r"[^\w.+-]+", "-", name).strip("-_") or "model"


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
{('Export ' + model + ' to ONNX after replacing the model-specific TODO.')!r}

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
if [ -z "${INPUT_SHAPE:-}" ] || [[ "${INPUT_SHAPE}" == *TODO* ]]; then
  echo "ERROR: set INPUT_SHAPE to the exported model's actual input names and shapes" >&2
  exit 2
fi
if [ ! -f "${ONNX_PATH}" ]; then
  echo "ERROR: ONNX file does not exist: ${ONNX_PATH}" >&2
  exit 2
fi
compile_options=()
if [[ -n "${INPUT_FORMAT:-}" ]]; then
  compile_options+=("--input_format=${INPUT_FORMAT}")
fi
if [[ -n "${PRECISION_MODE:-}" ]]; then
  compile_options+=("--precision_mode_v2=${PRECISION_MODE}")
fi
ASCEND_ENV_SCRIPT=${ASCEND_ENV_SCRIPT:-/usr/local/Ascend/ascend-toolkit/set_env.sh}
source "${ASCEND_ENV_SCRIPT}"
atc --framework=5 --model="${ONNX_PATH}" --output="${OUTPUT_PREFIX}" \
  --soc_version="${SOC_VERSION}" --input_shape="${INPUT_SHAPE}" \
  "${compile_options[@]}"
"""


def infer(model: str, route: str) -> str:
    return f'''#!/usr/bin/env python3
{('Optional ' + model + ' inference entry; prefer patching an upstream entry.')!r}

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description={(model + ' inference')!r})
    parser.add_argument("--model-path", required=True)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", default="outputs")
    parser.add_argument("--device", choices=["npu", "cpu"], default="npu")
    args = parser.parse_args()
    if args.device == "npu":
        raise NotImplementedError("TODO: implement NPU inference and route-specific dependencies for route={route}")
    raise NotImplementedError("TODO: implement explicit CPU/upstream fallback")


if __name__ == "__main__":
    main()
'''


def npu_adaptation(model: str, url: str, category: str, profile: str,
                   route: str, hardware: str | None, image: str | None) -> str:
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

- 初始化所选路线：{route}
- 指定硬件：{hardware or "未指定"}
- 指定镜像：{image or "未指定"}
- 实际设备、环境、路线探针结果和 patch：待记录
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


def acceptance_plan(model: str, scope: str | None, profile: str) -> str:
    if scope or profile == "generic":
        return f"""
# {model} 验收方案与结果

- 本轮验收目标：{scope or "按用户要交付的结果确定"}
- 适用的模型版本、权重、输入与执行环境：待记录
- 验证命令、实际设备、输出和判定依据：待记录
- 执行结果与尚缺条件：待记录
"""
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

TODO：可交付的同一部署版本、原始精度结果及实际读取它的 compare、阈值来源和独立参照。
对照与候选共用改过的预后处理时，保留未改上游样例或独立标注，检查双方一起出错的情况。

同一部署的正式性能至少独立执行 3 次，保存每次结果并报告中位数；按照用户要求的负载与计时边界验收。

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
    parser.add_argument("model_url", help="Upstream source or existing model artifact URL/path")
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--model-name")
    parser.add_argument("--validation-goal", help="Requested acceptance outcome for workspace notes")
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
    writes = parser.add_mutually_exclusive_group()
    writes.add_argument("--force", action="store_true", help="Replace generated files, including existing implementations")
    writes.add_argument("--missing-only", action="store_true", help="Create only absent files; preserve existing implementations and docs")
    args = parser.parse_args()

    model = args.model_name or infer_name(args.model_url)
    output = args.output_dir
    files = {
        output / "requirements.txt": (
            "# Model dependencies only. Preserve the target environment's runtime stack.\n"
        ),
    }
    if args.layout == "target" or args.with_readme:
        files[output / "README.md"] = readme(
            model, args.model_url, args.image, args.hardware_model
        )
    if args.layout == "workspace":
        raw_id = f"{args.category}__{model}"
        if not args.project_id and not raw_id.isascii():
            # Keep distinct display names even when ASCII normalization drops them.
            raw_id += "-" + hashlib.sha256(raw_id.encode()).hexdigest()[:12]
        project_id = slug(args.project_id or raw_id)
        internal = args.internal_dir or Path(".ascend-adaptation") / project_id
        if not internal.is_absolute():
            internal = output / internal
        files[internal / "NPU_ADAPTATION.md"] = npu_adaptation(
            model, args.model_url, args.category, args.profile, args.route,
            args.hardware_model, args.image
        )
        files[internal / "ACCEPTANCE_PLAN.md"] = acceptance_plan(model, args.validation_goal, args.profile)
    executable: set[str] = set()
    if args.route == "onnx-om":
        suffix = Path(urlparse(args.model_url).path).suffix.lower()
        if suffix not in {".onnx", ".om"}:
            files[output / "export_onnx.py"] = export_onnx(model)
            executable.add("export_onnx.py")
        if suffix != ".om":
            files[output / "convert_om.sh"] = convert_om()
            executable.add("convert_om.sh")
    if args.with_infer:
        files[output / "infer.py"] = infer(model, args.route)
        executable.add("infer.py")

    collisions = [
        path for path in files if path.exists() or path.is_symlink()
    ]
    if collisions and not (args.force or args.missing_only):
        raise FileExistsError(
            "Refusing partial scaffold write; existing files: "
            + ", ".join(str(path) for path in collisions)
        )
    # Check all destination links before writing any file, including with --force.
    for path in files:
        if any(parent.is_symlink() for parent in [path, *path.parents]):
            raise ValueError(f"Refusing to write through symbolic link: {path}")
        if path.exists() and not path.is_file():
            raise ValueError(f"Expected a file, found another filesystem entry: {path}")
    if args.missing_only:
        files = {path: content for path, content in files.items() if not path.exists()}
    output.mkdir(parents=True, exist_ok=True)
    for path, content in files.items():
        atomic_write(path, content, path.name in executable)
    if args.layout == "workspace":
        add_git_exclude(output, internal if args.internal_dir else None)
        print(f"Project ID: {project_id}")

    print(f"Created scaffold: {output}")
    print(f"Route: {args.route}; layout: {args.layout}")
    print("Files: " + ", ".join(sorted(str(path) for path in files)))
    print(
        "Scaffold only. Keep execution notes private; prepare user documentation through the delivery workflow."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
