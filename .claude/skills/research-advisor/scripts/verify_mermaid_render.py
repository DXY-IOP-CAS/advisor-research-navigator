#!/usr/bin/env python3
"""Render-check Mermaid blocks in final professor documents.

This is a deterministic smoke check: it proves Mermaid code blocks can be
rendered by the configured Mermaid CLI. It does not judge whether a diagram
is pedagogically useful.
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence


DOCS = [
    "00_材料导读.md",
    "01_基础画像.md",
    "02_领域地图.md",
    "03_论文路线.md",
    "04_学习向导.md",
]
MERMAID_BLOCK_RE = re.compile(r"```mermaid\s*\n(.*?)\n```", re.DOTALL)


@dataclass(frozen=True)
class MermaidBlock:
    filename: str
    index: int
    code: str


@dataclass
class VerifyResult:
    ok: bool
    messages: list[str]


def extract_mermaid_blocks(prof_dir: Path | str) -> list[MermaidBlock]:
    prof = Path(prof_dir)
    blocks: list[MermaidBlock] = []
    for filename in DOCS:
        path = prof / filename
        if not path.exists():
            continue

        text = path.read_text(encoding="utf-8")
        for index, match in enumerate(MERMAID_BLOCK_RE.finditer(text), start=1):
            blocks.append(MermaidBlock(filename=filename, index=index, code=match.group(1).strip()))
    return blocks


def verify_blocks(
    blocks: Sequence[MermaidBlock],
    renderer: Callable[[MermaidBlock], object],
) -> VerifyResult:
    if not blocks:
        return VerifyResult(False, ["[FAIL] 未找到 Mermaid 代码块"])

    messages: list[str] = []
    ok = True
    for block in blocks:
        try:
            renderer(block)
        except Exception as exc:
            ok = False
            messages.append(f"[FAIL] {block.filename} Mermaid #{block.index} render failed: {exc}")
        else:
            messages.append(f"[OK] {block.filename} Mermaid #{block.index} rendered")
    return VerifyResult(ok, messages)


def _renderer_command(use_npx: bool = False) -> list[str] | None:
    mmdc = shutil.which("mmdc")
    if mmdc:
        return [mmdc]

    if use_npx:
        npx = shutil.which("npx")
        if npx:
            return [npx, "--yes", "@mermaid-js/mermaid-cli"]

    return None


def render_block_with_command(block: MermaidBlock, command: Sequence[str], temp_dir: Path) -> None:
    safe_name = f"{Path(block.filename).stem}_{block.index}"
    input_path = temp_dir / f"{safe_name}.mmd"
    output_path = temp_dir / f"{safe_name}.svg"
    input_path.write_text(block.code + "\n", encoding="utf-8")

    completed = subprocess.run(
        [*command, "-i", str(input_path), "-o", str(output_path)],
        cwd=temp_dir,
        capture_output=True,
        text=True,
        timeout=60,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "unknown Mermaid render error").strip()
        raise RuntimeError(detail)
    if not output_path.exists() or output_path.stat().st_size == 0:
        raise RuntimeError("renderer produced no SVG output")


def verify_prof_dir(prof_dir: Path | str, use_npx: bool = False) -> VerifyResult:
    command = _renderer_command(use_npx=use_npx)
    if command is None:
        return VerifyResult(
            False,
            [
                "[FAIL] Mermaid renderer not found: install mmdc or rerun with --use-npx to use @mermaid-js/mermaid-cli",
            ],
        )

    blocks = extract_mermaid_blocks(prof_dir)
    with tempfile.TemporaryDirectory(prefix="pilot-test-mermaid-") as tmp:
        temp_dir = Path(tmp)
        return verify_blocks(blocks, lambda block: render_block_with_command(block, command, temp_dir))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render-check Mermaid diagrams in professor documents.")
    parser.add_argument("--prof-dir", required=True, help="Professor output directory containing 00-04 Markdown files.")
    parser.add_argument(
        "--use-npx",
        action="store_true",
        help="Use npx --yes @mermaid-js/mermaid-cli when mmdc is not installed.",
    )
    args = parser.parse_args(argv)

    result = verify_prof_dir(args.prof_dir, use_npx=args.use_npx)
    for message in result.messages:
        print(message)
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
