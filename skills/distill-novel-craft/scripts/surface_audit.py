#!/usr/bin/env python3
"""Deterministic Chinese-fiction surface signals.

The audit detects reproducible parsing and repetition signals. It never judges
literary quality, character voice, scene causality, or authorial intent.
"""

from __future__ import annotations

import hashlib
import math
import re
import unicodedata
from collections import Counter, defaultdict
from itertools import islice, pairwise
from typing import Any

PROBE_VERSION = "1.0.1"
NORMALIZATION_PROFILE = "zh-fiction-v1"
SEGMENTATION_PROFILE = "markdown-zh-chapter-v1"
BOUNDARY_DEFAULTS = ["不是", "不能", "不等于", "不得", "没有", "不把", "不替", "只限", "只覆盖"]
INSTITUTION_DEFAULTS = ["范围", "授权", "复核", "来源", "未决", "签字", "栏", "表格", "报告", "记录"]
FRAME_PATTERNS = {
    "不是_而是": re.compile(r"不是[^。！？!?；;]{0,48}而是"),
    "没有_也没有": re.compile(r"没有[^。！？!?；;]{0,48}也没有"),
    "不能_也不能": re.compile(r"不能[^。！？!?；;]{0,48}也不能"),
    "不等于": re.compile(r"不等于"),
    "只_不替": re.compile(r"只[^。！？!?；;]{0,48}不替"),
}
SENTENCE_SPLIT_RE = re.compile(r"(?<=[。！？!?；;])")


DEFAULT_THRESHOLDS: dict[str, float] = {
    "parse_coverage_fail": 0.98,
    "expected_char_match_fail": 0.98,
    "exact_duplicate_warn": 0.01,
    "exact_duplicate_fail": 0.03,
    "near_duplicate_warn": 0.015,
    "near_duplicate_fail": 0.04,
    "boundary_lexeme_median_warn_per_1k": 14.0,
    "boundary_lexeme_chapter_warn_per_1k": 22.0,
    "opening_prefix4_top_share_warn": 0.08,
    "opening_prefix4_top_share_fail": 0.15,
    "chapter_surface_similarity_warn": 0.985,
    "chapter_surface_similarity_run": 5,
    "chapter_length_robust_cv_warn_below": 0.05,
    "repeated_phrase_min_occurrences": 4,
    "repeated_phrase_min_chapters": 3,
    "repeated_phrase_length": 10,
    "near_duplicate_similarity": 0.82,
}


def compact(text: str) -> str:
    return re.sub(r"\s+", "", text)


def normalize_surface(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = text.translate(str.maketrans({"，": ",", "。": ".", "；": ";", "：": ":", "！": "!", "？": "?"}))
    return re.sub(r"\s+", "", text)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def percentile(values: list[float], fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = (len(ordered) - 1) * fraction
    lower = math.floor(index)
    upper = math.ceil(index)
    if lower == upper:
        return ordered[lower]
    weight = index - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def median(values: list[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2


def mad(values: list[float]) -> float:
    center = median(values)
    return median([abs(value - center) for value in values])


def shingles(text: str, width: int = 3) -> set[str]:
    return {text[index:index + width] for index in range(max(0, len(text) - width + 1))}


def simhash64(parts: set[str]) -> int:
    weights = [0] * 64
    for part in parts:
        value = int.from_bytes(hashlib.blake2b(part.encode("utf-8"), digest_size=8).digest(), "big")
        for bit in range(64):
            weights[bit] += 1 if value & (1 << bit) else -1
    result = 0
    for bit, weight in enumerate(weights):
        if weight >= 0:
            result |= 1 << bit
    return result


def cosine(left: list[float], right: list[float]) -> float:
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    return dot / (left_norm * right_norm) if left_norm and right_norm else 0.0


def chapter_label(index: int, title: str) -> str:
    return f"C{index:02d}:{title or '未命名'}"


def chapter_features(chapter: dict[str, Any], boundary_lexemes: list[str]) -> list[float]:
    body = chapter["body"]
    paragraphs = chapter["paragraphs"]
    chars = max(1, len(compact(body)))
    sentences = [part for part in SENTENCE_SPLIT_RE.split(body) if compact(part)]
    sentence_lengths = [len(compact(part)) for part in sentences]
    paragraph_lengths = [len(compact(part)) for part in paragraphs]
    dialogue = sum(paragraph.startswith(("“", "「", "『", '"')) for paragraph in paragraphs)
    punctuation = sum(body.count(mark) for mark in "。！？!?；;，,:：")
    boundary = sum(body.count(term) for term in boundary_lexemes)
    return [
        median([float(v) for v in sentence_lengths]) / 100,
        percentile([float(v) for v in sentence_lengths], 0.90) / 200,
        median([float(v) for v in paragraph_lengths]) / 200,
        dialogue / max(1, len(paragraphs)),
        punctuation / chars,
        (boundary * 1000 / chars) / 30,
    ]


def make_finding(metric: str, status: str, value: Any, threshold: Any, locations: list[str], signal: str) -> dict[str, Any]:
    return {
        "metric": metric,
        "status": status,
        "value": value,
        "threshold": threshold,
        "locations": locations,
        "signal": signal,
        "semantic_limit": "This surface signal requires close reading; it does not establish literary quality or authorial intent.",
    }


def apply_exceptions(findings: list[dict[str, Any]], exceptions: list[dict[str, Any]], input_hash: str) -> None:
    for finding in findings:
        finding_locations = set(finding.get("locations", []))
        for exception in exceptions:
            if exception.get("expires_on_text_hash") != input_hash:
                continue
            if exception.get("metric") != finding.get("metric"):
                continue
            exception_locations = set(exception.get("locations", []))
            if exception_locations and not finding_locations.issubset(exception_locations):
                continue
            finding["exception"] = {
                "id": exception.get("id"),
                "disposition": exception.get("disposition"),
                "reason": exception.get("reason"),
            }
            if exception.get("disposition") == "accepted_warning":
                finding["status"] = "WARN"
            break


def audit_surface(
    text: str,
    scope_manifest: dict[str, Any],
    policy: dict[str, Any] | None,
    exceptions: list[dict[str, Any]] | None,
    parse_blocks: Any,
) -> dict[str, Any]:
    policy = policy or {}
    exceptions = exceptions or []
    thresholds = dict(DEFAULT_THRESHOLDS)
    overrides = policy.get("thresholds") or {}
    for key, value in overrides.items():
        if key not in thresholds or isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError("invalid surface threshold")
        if key in {"repeated_phrase_length", "repeated_phrase_min_occurrences", "repeated_phrase_min_chapters", "chapter_surface_similarity_run"}:
            if not 1 <= value <= 200_000 or value != int(value):
                raise ValueError("count thresholds must be positive bounded integers")
        elif "per_1k" in key:
            if not 0 <= value <= 200_000:
                raise ValueError("lexeme threshold out of range")
        elif not 0 <= value <= 1:
            raise ValueError("ratio threshold must be between zero and one")
    thresholds.update(overrides)
    boundary_lexemes = policy.get("boundary_lexemes") or BOUNDARY_DEFAULTS
    institution_lexemes = policy.get("institution_lexemes") or INSTITUTION_DEFAULTS
    ordered_sequences = policy.get("ordered_sequences") or []
    input_hash = sha256_text(text)
    blocks, parse_meta = parse_blocks(text)
    scope_kind = scope_manifest.get("scope_kind")

    if not blocks and scope_kind == "excerpt":
        paragraphs = [line.strip() for line in text.splitlines() if line.strip()]
        blocks = [{"number": None, "title": "excerpt", "body": "\n".join(paragraphs), "paragraphs": paragraphs}]
        parse_meta = {
            **parse_meta,
            "parsed_chars_no_whitespace": len(compact(text)),
            "candidate_body_chars_no_whitespace": len(compact(text)),
            "coverage_ratio": 1.0,
            "fallback": "excerpt",
        }

    chapters: list[dict[str, Any]] = []
    for index, block in enumerate(blocks, start=1):
        chapter = dict(block)
        chapter["index"] = index
        chapter["label"] = chapter_label(index, str(block.get("title", "")))
        chapters.append(chapter)

    findings: list[dict[str, Any]] = []
    blockers: list[str] = []
    coverage_ratio = float(parse_meta.get("coverage_ratio", 0.0))
    if scope_kind != "excerpt" and not chapters:
        blockers.append("expected_chapters_but_none_parsed")
    if coverage_ratio < thresholds["parse_coverage_fail"]:
        blockers.append("parse_coverage_below_threshold")

    expected_chapters = scope_manifest.get("expected_chapters")
    if scope_kind == "whole_work" and not isinstance(expected_chapters, int):
        blockers.append("expected_chapters_required_for_whole_work")
    if isinstance(expected_chapters, int) and len(chapters) != expected_chapters:
        blockers.append("parsed_chapter_count_mismatch")

    numbers = [chapter.get("number") for chapter in chapters if isinstance(chapter.get("number"), int)]
    duplicate_numbers = sorted(number for number, count in Counter(numbers).items() if count > 1)
    missing_numbers: list[int] = []
    missing_ranges: list[dict[str, int]] = []
    missing_count = 0
    if numbers:
        ordered_numbers = sorted(set(numbers))
        missing_ranges = [{"start": left + 1, "end": right - 1}
                          for left, right in pairwise(ordered_numbers) if right - left > 1]
        missing_count = sum(item["end"] - item["start"] + 1 for item in missing_ranges)
        missing_numbers = list(islice((number for item in missing_ranges for number in range(item["start"], item["end"] + 1)), 1000))
    empty_chapters = [chapter["label"] for chapter in chapters if not compact(chapter["body"])]
    if duplicate_numbers:
        blockers.append("duplicate_chapter_numbers")
    if missing_numbers:
        blockers.append("missing_chapter_numbers")
    if empty_chapters:
        blockers.append("empty_chapters")

    expected_chars = scope_manifest.get("expected_chars_no_whitespace")
    input_chars = len(compact(text))
    expected_char_match_ratio = None
    if isinstance(expected_chars, int) and expected_chars > 0:
        expected_char_match_ratio = min(input_chars, expected_chars) / max(input_chars, expected_chars)
        if expected_char_match_ratio < thresholds["expected_char_match_fail"]:
            blockers.append("expected_char_count_mismatch")

    total_body_chars = sum(len(compact(chapter["body"])) for chapter in chapters) or 1
    paragraph_entries: list[tuple[str, str, str]] = []
    for chapter in chapters:
        for paragraph in chapter["paragraphs"]:
            literal = compact(paragraph)
            if literal:
                paragraph_entries.append((chapter["label"], literal, normalize_surface(paragraph)))

    exact_groups: dict[str, list[str]] = defaultdict(list)
    for label, literal, _ in paragraph_entries:
        if len(literal) >= 30:
            exact_groups[literal].append(label)
    duplicate_groups = [(text_value, labels) for text_value, labels in exact_groups.items() if len(labels) > 1]
    exact_excess = sum(len(text_value) * (len(labels) - 1) for text_value, labels in duplicate_groups)
    exact_ratio = exact_excess / total_body_chars
    if exact_ratio > thresholds["exact_duplicate_warn"]:
        status = "FAIL" if exact_ratio > thresholds["exact_duplicate_fail"] else "WARN"
        findings.append(make_finding(
            "exact_duplicate.excess_char_ratio", status, round(exact_ratio, 6),
            {"warn": thresholds["exact_duplicate_warn"], "fail": thresholds["exact_duplicate_fail"]},
            sorted({label for _, labels in duplicate_groups for label in labels}),
            "Long paragraphs recur verbatim across the supplied scope.",
        ))

    near_candidates: list[dict[str, Any]] = []
    prepared: list[tuple[str, str, set[str], int]] = []
    for label, _, normalized in paragraph_entries:
        if len(normalized) >= 40:
            parts = shingles(normalized)
            prepared.append((label, normalized, parts, simhash64(parts)))
    near_excess = 0
    near_locations: set[str] = set()
    used_right: set[int] = set()
    for left_index, (left_label, left_text, left_parts, left_hash) in enumerate(prepared):
        for right_index in range(left_index + 1, len(prepared)):
            right_label, right_text, right_parts, right_hash = prepared[right_index]
            if left_text == right_text or left_label == right_label or right_index in used_right:
                continue
            length_ratio = min(len(left_text), len(right_text)) / max(len(left_text), len(right_text))
            if length_ratio < 0.70 or (left_hash ^ right_hash).bit_count() > 16:
                continue
            union = left_parts | right_parts
            similarity = len(left_parts & right_parts) / len(union) if union else 0.0
            if similarity >= thresholds["near_duplicate_similarity"]:
                near_excess += min(len(left_text), len(right_text))
                near_locations.update((left_label, right_label))
                used_right.add(right_index)
                if len(near_candidates) < 20:
                    near_candidates.append({"left": left_label, "right": right_label, "similarity": round(similarity, 4)})
                break
    near_ratio = near_excess / total_body_chars
    if near_ratio > thresholds["near_duplicate_warn"]:
        status = "FAIL" if near_ratio > thresholds["near_duplicate_fail"] else "WARN"
        finding = make_finding(
            "near_duplicate.excess_char_ratio", status, round(near_ratio, 6),
            {"warn": thresholds["near_duplicate_warn"], "fail": thresholds["near_duplicate_fail"]},
            sorted(near_locations), "Paragraphs with high normalized character-trigram overlap recur across chapters.",
        )
        finding["examples"] = near_candidates
        findings.append(finding)

    phrase_length = int(thresholds["repeated_phrase_length"])
    phrase_occurrences: Counter[str] = Counter()
    phrase_chapters: dict[str, set[str]] = defaultdict(set)
    for chapter in chapters:
        sequence = re.sub(r"[^\u3400-\u9fff]", "", chapter["body"])
        seen_positions: dict[str, int] = {}
        for index in range(max(0, len(sequence) - phrase_length + 1)):
            phrase = sequence[index:index + phrase_length]
            last = seen_positions.get(phrase, -phrase_length)
            if index - last < phrase_length:
                continue
            phrase_occurrences[phrase] += 1
            phrase_chapters[phrase].add(chapter["label"])
            seen_positions[phrase] = index
    repeated_phrases = [
        {"phrase": phrase, "occurrences": count, "chapters": sorted(phrase_chapters[phrase])}
        for phrase, count in phrase_occurrences.items()
        if count >= thresholds["repeated_phrase_min_occurrences"]
        and len(phrase_chapters[phrase]) >= thresholds["repeated_phrase_min_chapters"]
    ]
    repeated_phrases.sort(key=lambda item: (-item["occurrences"], -len(item["chapters"]), item["phrase"]))
    if repeated_phrases:
        findings.append(make_finding(
            "repeated_phrase.cross_chapter_clusters", "WARN", len(repeated_phrases),
            {"min_occurrences": thresholds["repeated_phrase_min_occurrences"], "min_chapters": thresholds["repeated_phrase_min_chapters"]},
            sorted({label for item in repeated_phrases[:20] for label in item["chapters"]}),
            "Fixed-length Chinese character sequences recur in several chapters.",
        ))
        findings[-1]["examples"] = repeated_phrases[:20]

    per_chapter_lexemes: list[dict[str, Any]] = []
    boundary_rates: list[float] = []
    institution_rates: list[float] = []
    for chapter in chapters:
        chars = max(1, len(compact(chapter["body"])))
        boundary_count = sum(chapter["body"].count(term) for term in boundary_lexemes)
        institution_count = sum(chapter["body"].count(term) for term in institution_lexemes)
        boundary_rate = boundary_count * 1000 / chars
        institution_rate = institution_count * 1000 / chars
        boundary_rates.append(boundary_rate)
        institution_rates.append(institution_rate)
        per_chapter_lexemes.append({
            "chapter": chapter["label"],
            "boundary_per_1k": round(boundary_rate, 3),
            "institution_per_1k": round(institution_rate, 3),
        })
    boundary_median = median(boundary_rates)
    boundary_outliers = [item["chapter"] for item in per_chapter_lexemes if item["boundary_per_1k"] >= thresholds["boundary_lexeme_chapter_warn_per_1k"]]
    if boundary_median >= thresholds["boundary_lexeme_median_warn_per_1k"] or boundary_outliers:
        findings.append(make_finding(
            "boundary_lexeme.per_1k", "WARN",
            {"median": round(boundary_median, 3), "p90": round(percentile(boundary_rates, 0.90), 3)},
            {"median_warn": thresholds["boundary_lexeme_median_warn_per_1k"], "chapter_warn": thresholds["boundary_lexeme_chapter_warn_per_1k"]},
            boundary_outliers,
            "Configured negation and boundary lexemes are dense globally or in specific chapters.",
        ))

    frame_counts: dict[str, list[dict[str, Any]]] = {name: [] for name in FRAME_PATTERNS}
    for chapter in chapters:
        chars = max(1, len(compact(chapter["body"])))
        for name, pattern in FRAME_PATTERNS.items():
            count = len(pattern.findall(chapter["body"]))
            frame_counts[name].append({"chapter": chapter["label"], "count": count, "per_1k": round(count * 1000 / chars, 3)})

    prefix_counts: Counter[str] = Counter()
    prefix_locations: dict[str, set[str]] = defaultdict(set)
    eligible_paragraphs = 0
    for chapter in chapters:
        for paragraph in chapter["paragraphs"]:
            prefix_source = re.sub(r"^[\W_]+", "", paragraph, flags=re.UNICODE)
            prefix = compact(prefix_source)[:4]
            if len(prefix) == 4:
                eligible_paragraphs += 1
                prefix_counts[prefix] += 1
                prefix_locations[prefix].add(chapter["label"])
    top_prefix, top_prefix_count = prefix_counts.most_common(1)[0] if prefix_counts else ("", 0)
    top_prefix_share = top_prefix_count / eligible_paragraphs if eligible_paragraphs else 0.0
    if top_prefix_share >= thresholds["opening_prefix4_top_share_warn"]:
        status = "FAIL" if top_prefix_share >= thresholds["opening_prefix4_top_share_fail"] else "WARN"
        findings.append(make_finding(
            "opening.prefix4_top_share", status, {"prefix": top_prefix, "share": round(top_prefix_share, 6)},
            {"warn": thresholds["opening_prefix4_top_share_warn"], "fail": thresholds["opening_prefix4_top_share_fail"]},
            sorted(prefix_locations[top_prefix]), "One four-character paragraph opening accounts for a large share of eligible paragraphs.",
        ))

    sequence_results: list[dict[str, Any]] = []
    for sequence in ordered_sequences:
        lexemes = sequence.get("lexemes") or []
        if not lexemes:
            continue
        window = int(sequence.get("window_chars", 120))
        locations: list[str] = []
        for chapter in chapters:
            body = compact(chapter["body"])
            first_positions = [match.start() for match in re.finditer(re.escape(lexemes[0]), body)]
            matched = False
            for start in first_positions:
                cursor = start + len(lexemes[0])
                limit = start + window
                for lexeme in lexemes[1:]:
                    position = body.find(lexeme, cursor, limit)
                    if position < 0:
                        break
                    cursor = position + len(lexeme)
                else:
                    matched = True
                    break
            if matched:
                locations.append(chapter["label"])
        result = {"id": sequence.get("id", "unnamed"), "chapter_df": len(locations), "locations": locations, "lexemes": lexemes}
        sequence_results.append(result)
        warn_df = int(sequence.get("warn_chapter_df", 4))
        if len(locations) >= warn_df:
            findings.append(make_finding(
                f"ordered_lexeme_sequence.{result['id']}", "WARN", len(locations), warn_df, locations,
                "A configured ordered lexeme sequence recurs within the requested window across chapters.",
            ))

    feature_vectors = [chapter_features(chapter, boundary_lexemes) for chapter in chapters]
    adjacent_similarities = [cosine(feature_vectors[index - 1], feature_vectors[index]) for index in range(1, len(feature_vectors))]
    longest_run = 0
    current_run = 0
    run_locations: list[str] = []
    current_locations: list[str] = []
    similarity_threshold = thresholds["chapter_surface_similarity_warn"]
    for index, similarity in enumerate(adjacent_similarities, start=1):
        if similarity >= similarity_threshold:
            current_run += 1
            if not current_locations:
                current_locations = [chapters[index - 1]["label"]]
            current_locations.append(chapters[index]["label"])
            if current_run > longest_run:
                longest_run = current_run
                run_locations = list(current_locations)
        else:
            current_run = 0
            current_locations = []
    if longest_run >= int(thresholds["chapter_surface_similarity_run"]):
        findings.append(make_finding(
            "chapter_surface_similarity.adjacent_run", "WARN",
            {"adjacent_pairs": longest_run, "minimum_similarity": round(min(adjacent_similarities) if adjacent_similarities else 0.0, 6)},
            {"similarity": similarity_threshold, "run": int(thresholds["chapter_surface_similarity_run"])},
            run_locations, "Several adjacent chapters have highly similar deterministic surface-feature vectors.",
        ))

    chapter_lengths = [float(len(compact(chapter["body"]))) for chapter in chapters]
    robust_cv = mad(chapter_lengths) / median(chapter_lengths) if median(chapter_lengths) else 0.0
    if len(chapter_lengths) >= 5 and robust_cv < thresholds["chapter_length_robust_cv_warn_below"]:
        findings.append(make_finding(
            "chapter_length.robust_cv", "WARN", round(robust_cv, 6),
            {"warn_below": thresholds["chapter_length_robust_cv_warn_below"]},
            [chapter["label"] for chapter in chapters], "Chapter lengths are unusually uniform under the configured project threshold.",
        ))

    apply_exceptions(findings, exceptions, input_hash)
    statuses = {finding["status"] for finding in findings}
    if blockers or "FAIL" in statuses:
        surface_gate = "FAIL"
    elif "WARN" in statuses:
        surface_gate = "WARN"
    else:
        surface_gate = "PASS"

    if scope_kind == "whole_work" and not expected_chapters:
        surface_gate = "INSUFFICIENT_DATA"

    return {
        "probe": {
            "version": PROBE_VERSION,
            "normalization_profile": NORMALIZATION_PROFILE,
            "segmentation_profile": SEGMENTATION_PROFILE,
            "input_sha256": input_hash,
            "scope_kind": scope_kind,
            "input_chars_no_whitespace": input_chars,
        },
        "policy": {
            "id": policy.get("id", "default-zh-fiction-surface-v1"),
            "version": policy.get("version", "1.0.0"),
            "thresholds": thresholds,
            "boundary_lexemes": boundary_lexemes,
            "institution_lexemes": institution_lexemes,
        },
        "parse": {
            **parse_meta,
            "parsed_chapters": len(chapters),
            "expected_chapters": expected_chapters,
            "expected_chars_no_whitespace": expected_chars,
            "expected_char_match_ratio": round(expected_char_match_ratio, 6) if expected_char_match_ratio is not None else None,
            "duplicate_chapter_numbers": duplicate_numbers,
            "missing_chapter_numbers": missing_numbers,
            "missing_chapter_ranges": missing_ranges,
            "missing_chapter_count": missing_count,
            "missing_chapter_numbers_truncated": missing_count > len(missing_numbers),
            "empty_chapters": empty_chapters,
        },
        "metrics": {
            "exact_duplicate": {"excess_char_ratio": round(exact_ratio, 6), "groups": len(duplicate_groups)},
            "near_duplicate": {"excess_char_ratio": round(near_ratio, 6), "examples": near_candidates},
            "repeated_phrases": repeated_phrases[:20],
            "lexeme_load": {
                "boundary_median_per_1k": round(boundary_median, 3),
                "boundary_p90_per_1k": round(percentile(boundary_rates, 0.90), 3),
                "institution_median_per_1k": round(median(institution_rates), 3),
                "institution_p90_per_1k": round(percentile(institution_rates, 0.90), 3),
                "chapters": per_chapter_lexemes,
            },
            "sentence_frames": frame_counts,
            "opening_prefix4": {"prefix": top_prefix, "share": round(top_prefix_share, 6), "eligible_paragraphs": eligible_paragraphs},
            "ordered_sequences": sequence_results,
            "chapter_surface_similarity": {
                "adjacent": [round(value, 6) for value in adjacent_similarities],
                "longest_run": longest_run,
                "run_locations": run_locations,
            },
            "chapter_length": {"robust_cv": round(robust_cv, 6)},
        },
        "findings": findings,
        "blockers": sorted(set(blockers)),
        "gates": {
            "surface_regression_gate": surface_gate,
            "semantic_review_gate": "NOT_ASSESSED",
            "overall_gate": "BLOCKED",
        },
        "limits": [
            "Surface metrics detect reproducible signals, not literary quality or authorial intent.",
            "They cannot determine character voice, scene function, POV correctness, causality, or whether repetition is artistically effective.",
            "A host must complete semantic close reading before making a literary decision.",
        ],
    }
