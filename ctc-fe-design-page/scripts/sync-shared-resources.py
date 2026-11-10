#!/usr/bin/env python3
"""维护用途：比较或同步同版本资料到审查技能；不参与页面生成或运行。"""

import argparse
from pathlib import Path
import re
import shutil
import sys

SOURCE = Path(__file__).resolve().parents[1]
SHARED = (
    "references/layout-contract.md",
    "references/page-spec.schema.json",
    "references/page-spec.examples.json",
    "assets/layout-tokens.css",
    "assets/layout-spec.html",
    "templates/TablePageLayout.vue",
    "scripts/check-package.py",
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", type=Path, required=True, help="审查技能目录")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="仅比较（默认）")
    mode.add_argument("--apply", action="store_true", help="同步上述资料，保留目标 SKILL.md")
    args = parser.parse_args()
    target = args.target.resolve()
    try:
        if target == SOURCE or not (target / "SKILL.md").is_file():
            raise ValueError("目标必须是已存在的审查技能目录")
        content = (target / "SKILL.md").read_text(encoding="utf-8")
        if not re.search(r"^name: ctc-fe-code-auditor$", content, re.M):
            raise ValueError("目标 SKILL.md 的名称不是 ctc-fe-code-auditor")
        changed = []
        for relative in SHARED:
            source, destination = SOURCE / relative, target / relative
            if not source.is_file() or source.is_symlink():
                raise ValueError(f"维护源缺少普通文件：{relative}")
            if not destination.resolve().is_relative_to(target) or destination.is_symlink():
                raise ValueError(f"目标路径越界或为符号链接：{relative}")
            if not destination.exists() or source.read_bytes() != destination.read_bytes():
                changed.append(relative)
        if not changed:
            print("两份技能的配套资料一致。")
            return 0
        for relative in changed:
            print(("同步：" if args.apply else "待同步：") + relative)
            if args.apply:
                destination = target / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(SOURCE / relative, destination)
        return 0 if args.apply else 1
    except (OSError, ValueError) as error:
        print(f"同步失败：{error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
