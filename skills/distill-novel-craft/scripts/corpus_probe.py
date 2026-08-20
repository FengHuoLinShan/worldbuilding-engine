#!/usr/bin/env python3
"""Split Chinese novel chapters and report lightweight, reproducible metrics."""

from __future__ import annotations

import argparse
import json
import re
import statistics
from pathlib import Path
from typing import Any


MARKDOWN_HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s*(.*?)\s*#*\s*$")
CHAPTER_RE = re.compile(r"^第\s*([零〇一二三四五六七八九十百千万两0-9]+)\s*章[ \t　]*(.*)$")
SECTION_RE = re.compile(
    r"^(?:第\s*[零〇一二三四五六七八九十百千万两0-9]+\s*(?:部|卷)(?:[·・:： \t　].*)?|"
    r"第[零〇一二三四五六七八九十百千万两0-9]+部总结|完本感言|上架感言|后记|番外)"
)
SENTENCE_RE = re.compile(r"[。！？!?；;]+|…{1,2}")
CHINESE_DIGITS = {"零": 0, "〇": 0, "一": 1, "二": 2, "两": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}
CHINESE_UNITS = {"十": 10, "百": 100, "千": 1000, "万": 10000}


def strip_heading(line: str) -> tuple[str, bool]:
    match = MARKDOWN_HEADING_RE.match(line)
    return (match.group(1).strip(), True) if match else (line.strip(), False)


def chinese_number(value: str) -> int | None:
    if value.isdigit():
        return int(value)
    total = 0
    section = 0
    number = 0
    try:
        for char in value:
            if char in CHINESE_DIGITS:
                number = CHINESE_DIGITS[char]
            elif char in CHINESE_UNITS:
                unit = CHINESE_UNITS[char]
                if unit == 10000:
                    section = (section + number) * unit
                    total += section
                    section = 0
                    number = 0
                else:
                    section += (number or 1) * unit
                    number = 0
            else:
                return None
        return total + section + number
    except (TypeError, ValueError):
        return None


def parse_chapter_blocks(text: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    candidate_chars = 0
    parsed_chars = 0
    metadata_lines: list[str] = []

    for line_number, line in enumerate(text.splitlines(), start=1):
        stripped, was_heading = strip_heading(line)
        chapter_match = CHAPTER_RE.match(stripped)
        if chapter_match:
            if current is not None:
                current["body"] = "\n".join(current.pop("lines"))
                current["paragraphs"] = [part.strip() for part in current["body"].splitlines() if part.strip()]
                blocks.append(current)
            current = {
                "number_raw": chapter_match.group(1),
                "number": chinese_number(chapter_match.group(1)),
                "title": chapter_match.group(2).strip(),
                "heading_line": line_number,
                "lines": [],
            }
            continue
        if SECTION_RE.match(stripped) or (was_heading and current is None):
            if stripped:
                metadata_lines.append(stripped)
            continue
        if was_heading:
            if stripped:
                metadata_lines.append(stripped)
            continue
        if current is not None:
            current["lines"].append(line)
            chars = len(re.sub(r"\s+", "", line))
            candidate_chars += chars
            parsed_chars += chars
        elif stripped:
            # Non-heading material outside chapters is visible as uncovered input.
            candidate_chars += len(re.sub(r"\s+", "", line))

    if current is not None:
        current["body"] = "\n".join(current.pop("lines"))
        current["paragraphs"] = [part.strip() for part in current["body"].splitlines() if part.strip()]
        blocks.append(current)

    coverage = parsed_chars / candidate_chars if candidate_chars else (1.0 if blocks else 0.0)
    return blocks, {
        "candidate_body_chars_no_whitespace": candidate_chars,
        "parsed_chars_no_whitespace": parsed_chars,
        "coverage_ratio": round(coverage, 6),
        "metadata_lines": metadata_lines,
        "fallback": None,
    }


def parse_chapters(text: str) -> list[dict[str, object]]:
    blocks, _ = parse_chapter_blocks(text)
    return [measure(str(block["title"]), list(block["body"].splitlines())) for block in blocks]


def measure(title: str, lines: list[str]) -> dict[str, object]:
    paragraphs = [line.strip() for line in lines if line.strip()]
    body = "\n".join(paragraphs)
    sentences = [re.sub(r"\s+", "", part) for part in SENTENCE_RE.split(body)]
    sentences = [part for part in sentences if part]
    dialogue = sum(p.startswith(("“", "「", "『", '"')) for p in paragraphs)
    return {
        "title": title,
        "chars": len(re.sub(r"\s+", "", body)),
        "paragraphs": len(paragraphs),
        "dialogue_paragraph_ratio": round(dialogue / len(paragraphs), 4) if paragraphs else 0,
        "median_sentence_chars": round(statistics.median(map(len, sentences)), 1) if sentences else 0,
    }


def percentile(values: list[int | float], fraction: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0
    index = (len(ordered) - 1) * fraction
    lower = int(index)
    upper = min(lower + 1, len(ordered) - 1)
    weight = index - lower
    return float(ordered[lower] * (1 - weight) + ordered[upper] * weight)


def summarize(chapters: list[dict[str, object]]) -> dict[str, object]:
    chars = [int(c["chars"]) for c in chapters]
    paragraphs = [int(c["paragraphs"]) for c in chapters]
    dialogue = [float(c["dialogue_paragraph_ratio"]) for c in chapters]
    sentences = [float(c["median_sentence_chars"]) for c in chapters]
    return {
        "chapters": len(chapters),
        "chapter_chars": {
            "p10": int(percentile(chars, 0.10)),
            "median": int(statistics.median(chars)) if chars else 0,
            "p90": int(percentile(chars, 0.90)),
        },
        "median_paragraphs_per_chapter": round(statistics.median(paragraphs), 1) if paragraphs else 0,
        "median_dialogue_paragraph_ratio": round(statistics.median(dialogue), 4) if dialogue else 0,
        "median_sentence_chars": round(statistics.median(sentences), 1) if sentences else 0,
    }


def markdown(path: Path, summary: dict[str, object]) -> str:
    lengths = summary["chapter_chars"]
    assert isinstance(lengths, dict)
    return "\n".join(
        [
            f"# {path.name}",
            "",
            f"- 章节数：{summary['chapters']}",
            f"- 章长（去空白字符）：P10 {lengths['p10']} / 中位 {lengths['median']} / P90 {lengths['p90']}",
            f"- 每章段落数中位：{summary['median_paragraphs_per_chapter']}",
            f"- 对话起始段占比中位：{summary['median_dialogue_paragraph_ratio']:.1%}",
            f"- 章内句长中位数的全书中位：{summary['median_sentence_chars']}",
        ]
    )


def self_test() -> None:
    sample = "# 书名\n## 第一部·开始\n### 第一章 开始\n他醒了。\n“谁？”\n## 第一部总结\n### 第二章 继续\n风停了！"
    blocks, meta = parse_chapter_blocks(sample)
    chapters = parse_chapters(sample)
    assert [c["title"] for c in chapters] == ["开始", "继续"]
    assert [block["number"] for block in blocks] == [1, 2]
    assert chapters[0]["chars"] == 8
    assert meta["coverage_ratio"] == 1.0
    assert summarize(chapters)["chapters"] == 2


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", nargs="?", type=Path)
    parser.add_argument("--chapters", action="store_true", help="include per-chapter metrics in JSON")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        print("ok")
        return
    if args.chapters and not args.json:
        parser.error("--chapters requires --json")
    if not args.file:
        parser.error("file is required unless --self-test is used")

    text = args.file.read_text(encoding="utf-8-sig")
    chapters = parse_chapters(text)
    if not chapters:
        raise SystemExit("no chapter headings found")
    summary = summarize(chapters)
    if args.json:
        payload: dict[str, object] = {"file": str(args.file), "summary": summary}
        if args.chapters:
            payload["chapters"] = chapters
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(markdown(args.file, summary))


if __name__ == "__main__":
    main()
