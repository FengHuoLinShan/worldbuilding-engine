#!/usr/bin/env python3
"""Minimal stdio MCP adapter for the deterministic worldbuilding engine."""

from __future__ import annotations

import json
import importlib.util
import runpy
import subprocess
import sys
from pathlib import Path
from typing import Any

from contracts import ContractError, validate
import workflow
import candidates


VERSION = "0.8.0"
PLUGIN_ROOT = Path(__file__).resolve().parent.parent
ENGINE = PLUGIN_ROOT / "scripts" / "worldbuild.rb"
CRAFT_PROBE = PLUGIN_ROOT / "skills" / "distill-novel-craft" / "scripts" / "corpus_probe.py"
SURFACE_AUDIT = PLUGIN_ROOT / "skills" / "distill-novel-craft" / "scripts" / "surface_audit.py"
PROTOCOL_VERSION = "2025-11-25"
SUPPORTED_PROTOCOLS = {"2024-11-05", "2025-03-26", "2025-06-18", PROTOCOL_VERSION}
MAX_CRAFT_TEXT_CHARS = 200_000
REVIEW_CONTRACT_VERSION = "0.1.0"

DIAGNOSTIC_LENSES = [
    {
        "id": "domain_term_load",
        "maps_to_layers": [7, 11],
        "question": "Do institutional or specialist terms displace bodies, actions, and scene-specific language?",
    },
    {
        "id": "negation_template_repetition",
        "maps_to_layers": [9, 11, 12],
        "question": "Do negation, disclaimer, or boundary sentence frames recur beyond their dramatic value?",
    },
    {
        "id": "character_voice_differentiation",
        "maps_to_layers": [5, 9, 11],
        "question": "Can speakers be distinguished by experience, register, rhythm, and error rather than role labels alone?",
    },
    {
        "id": "scene_pattern_variation",
        "maps_to_layers": [8, 12],
        "question": "Do adjacent scenes repeat the same carrier, strategy, turn, and exit despite different content?",
    },
    {
        "id": "climax_action_deliberation_balance",
        "maps_to_layers": [3, 4, 8, 10],
        "question": "Does the climax allocate enough experienced action and consequence relative to deliberation and explanation?",
    },
]

CRAFT_FACETS = [
    "创作契约",
    "表达主题",
    "结构",
    "因果与对抗",
    "人物与关系",
    "视角与信息",
    "世界与社会",
    "场景与节奏",
    "对话与行动",
    "情绪与氛围",
    "语言与意象",
    "连载连续性与修订",
]

CRAFT_STEPS = {
    "distill_work": ["盘点材料边界", "十二面浅扫", "选择一个主层深审", "寻找反例与代价", "做同功能名著对照", "输出技法卡"],
    "distill_style": ["记录作品、原作语言与版次/译本", "限定一个风格功能与材料范围", "在相隔位置记录可观察特征", "区分原作语言证据与译本限制", "转成项目叙事控制项与代价", "用原创片段回测并去除声纹"],
    "analyze_excerpt": ["声明局部范围", "十二面浅扫", "选择一个主层近读", "记录进入/退出状态", "输出局部结论与边界"],
    "transfer_to_project": ["核对世界与正典约束", "选择已验证技法卡", "删除作品专属外壳", "交给实际工件所有者", "回归检查下游"],
    "diagnose_revision": ["保护已有优点", "选择一个主审层", "定位根因所有者", "给最小修复动作", "按同一主层复核"],
}


TOOLS: list[dict[str, Any]] = [
    {
        "name": "world_project_template",
        "description": (
            "Create a minimal world-state object from a title and a small creative seed. "
            "All generated authority remains draft; this never promotes canon."
        ),
        "inputSchema": {
            "type": "object",
            "additionalProperties": False,
            "required": ["title", "seed"],
            "properties": {
                "title": {"type": "string", "minLength": 1},
                "seed": {"type": "string", "minLength": 1},
                "language": {"type": "string", "default": "zh-CN"},
            },
        },
    },
    {
        "name": "world_validate",
        "description": (
            "Validate a world-state object for structure, status, evidence, IDs, "
            "dependencies, and invalidation invariants."
        ),
        "inputSchema": {
            "type": "object",
            "additionalProperties": False,
            "required": ["state"],
            "properties": {"state": {"type": "object"}},
        },
    },
    {
        "name": "world_audit",
        "description": (
            "Audit a world-state for causal ledgers, six reproduction loops, 22 facets, "
            "five coupling chains, situated evidence, 12 counterfactual tests, and optional "
            "long-running iteration cadence and saturation guidance."
        ),
        "inputSchema": {
            "type": "object",
            "additionalProperties": False,
            "required": ["state"],
            "properties": {"state": {"type": "object"}},
        },
    },
    {
        "name": "world_route",
        "description": (
            "Choose the current owning skill: state repair or the appropriate fiction-core "
            "world, character, story, outline, prose, or editor layer."
        ),
        "inputSchema": {
            "type": "object",
            "additionalProperties": False,
            "required": ["state"],
            "properties": {"state": {"type": "object"}},
        },
    },
    {
        "name": "world_craft_packet",
        "description": (
            "Build a deterministic evidence-first writing-craft packet with a 12-facet scaffold, "
            "claim-grade rules, optional inline-text surface metrics, and optional world-state "
            "validation/routing. The caller model still performs close reading."
        ),
        "inputSchema": {
            "type": "object",
            "additionalProperties": False,
            "required": ["mode", "source_scope"],
            "properties": {
                "mode": {
                    "type": "string",
                    "enum": ["distill_work", "distill_style", "analyze_excerpt", "transfer_to_project", "diagnose_revision"],
                },
                "source_scope": {"type": "string", "minLength": 1, "maxLength": 500},
                "focus": {"type": "string", "maxLength": 1000},
                "text": {"type": "string", "minLength": 1, "maxLength": MAX_CRAFT_TEXT_CHARS},
                "state": {"type": "object"},
                "style_source": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["work", "original_language", "edition_or_translation"],
                    "properties": {
                        "work": {"type": "string", "minLength": 1, "maxLength": 500},
                        "author": {"type": "string", "maxLength": 300},
                        "original_language": {"type": "string", "minLength": 1, "maxLength": 100},
                        "edition_or_translation": {"type": "string", "minLength": 1, "maxLength": 500},
                    },
                },
            },
        },
    },
    {
        "name": "world_text_surface_audit",
        "description": (
            "Audit inline Chinese-fiction text for parse coverage, exact/near repetition, configured "
            "lexeme load, sentence frames, opening concentration, and chapter surface similarity. "
            "It reports reproducible signals only and always leaves semantic review unassessed."
        ),
        "inputSchema": {
            "type": "object",
            "additionalProperties": False,
            "required": ["text", "scope_manifest"],
            "properties": {
                "text": {"type": "string", "minLength": 1, "maxLength": MAX_CRAFT_TEXT_CHARS},
                "scope_manifest": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["scope_kind"],
                    "properties": {
                        "scope_kind": {"type": "string", "enum": ["whole_work", "chapter_sample", "excerpt"]},
                        "expected_chapters": {"type": "integer", "minimum": 1},
                        "expected_chars_no_whitespace": {"type": "integer", "minimum": 1},
                        "segmentation_profile": {"type": "string", "enum": ["markdown-zh-chapter-v1"]},
                    },
                },
                "policy": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "id": {"type": "string", "minLength": 1, "maxLength": 200},
                        "version": {"type": "string", "minLength": 1, "maxLength": 50},
                        "thresholds": {"type": "object", "additionalProperties": {"type": "number"}},
                        "boundary_lexemes": {"type": "array", "maxItems": 100, "items": {"type": "string", "minLength": 1, "maxLength": 30}},
                        "institution_lexemes": {"type": "array", "maxItems": 100, "items": {"type": "string", "minLength": 1, "maxLength": 30}},
                        "ordered_sequences": {
                            "type": "array",
                            "maxItems": 30,
                            "items": {
                                "type": "object",
                                "additionalProperties": False,
                                "required": ["id", "lexemes"],
                                "properties": {
                                    "id": {"type": "string", "minLength": 1, "maxLength": 100},
                                    "lexemes": {"type": "array", "minItems": 2, "maxItems": 20, "items": {"type": "string", "minLength": 1, "maxLength": 50}},
                                    "window_chars": {"type": "integer", "minimum": 20, "maximum": 1000},
                                    "warn_chapter_df": {"type": "integer", "minimum": 2, "maximum": 1000},
                                },
                            },
                        },
                    },
                },
                "exceptions": {
                    "type": "array",
                    "maxItems": 100,
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["id", "metric", "disposition", "reason", "expires_on_text_hash"],
                        "properties": {
                            "id": {"type": "string", "minLength": 1, "maxLength": 100},
                            "metric": {"type": "string", "minLength": 1, "maxLength": 150},
                            "locations": {"type": "array", "items": {"type": "string", "minLength": 1, "maxLength": 300}},
                            "disposition": {"type": "string", "enum": ["accepted_warning"]},
                            "reason": {"type": "string", "minLength": 1, "maxLength": 1000},
                            "expires_on_text_hash": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                        },
                    },
                },
            },
        },
    },
    {
        "name": "world_craft_review_check",
        "description": (
            "Check whether an external semantic craft review has complete coverage and evidence fields. "
            "It never verifies semantic truth or returns a literary pass."
        ),
        "inputSchema": {
            "type": "object",
            "additionalProperties": False,
            "required": ["source_scope", "coverage_matrix", "diagnostic_lenses", "findings"],
            "properties": {
                "source_scope": {"type": "string", "minLength": 1, "maxLength": 500},
                "coverage_matrix": {"type": "array", "items": {"type": "object"}},
                "diagnostic_lenses": {"type": "array", "items": {"type": "object"}},
                "findings": {"type": "array", "items": {"type": "object"}},
            },
        },
    },
]


WORLD_CHECK_SPEC = importlib.util.spec_from_file_location(
    "worldcheck_adapter", PLUGIN_ROOT / "tools" / "worldcheck" / "mcp_adapter.py"
)
WORLD_CHECK = importlib.util.module_from_spec(WORLD_CHECK_SPEC)
WORLD_CHECK_SPEC.loader.exec_module(WORLD_CHECK)
TOOLS.extend(WORLD_CHECK.TOOLS)
TOOLS.extend(workflow.TOOLS)
TOOLS.extend(candidates.TOOLS)
for tool in TOOLS:
    writes = tool["name"] in {"worldcheck_prepare_review", "worldcheck_record_receipt", "world_candidate_save"}
    tool["annotations"] = {"readOnlyHint": not writes, "destructiveHint": False, "openWorldHint": False}
    tool.setdefault("outputSchema", {"type": "object"})
TOOL_BY_NAME = {tool["name"]: tool for tool in TOOLS}


class ToolFailure(RuntimeError):
    """A safe, user-facing tool error."""


def run_engine(command: str, state: dict[str, Any]) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            ["ruby", str(ENGINE), command, "-", "--json"],
            input=json.dumps(state, ensure_ascii=False),
            text=True,
            capture_output=True,
            timeout=15,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ToolFailure("The deterministic engine could not be started.") from exc

    if completed.returncode not in (0, 1):
        message = completed.stderr.strip().removeprefix("ERROR ")
        raise ToolFailure(message or "The deterministic engine rejected the request.")
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise ToolFailure("The deterministic engine returned invalid output.") from exc


def create_template(arguments: dict[str, Any]) -> dict[str, Any]:
    title = arguments.get("title")
    seed = arguments.get("seed")
    language = arguments.get("language", "zh-CN")
    if not isinstance(title, str) or not title.strip():
        raise ToolFailure("title must be a non-empty string")
    if not isinstance(seed, str) or not seed.strip():
        raise ToolFailure("seed must be a non-empty string")
    if not isinstance(language, str) or not language.strip():
        raise ToolFailure("language must be a non-empty string")
    try:
        completed = subprocess.run(
            [
                "ruby",
                str(ENGINE),
                "template",
                "--title",
                title,
                "--seed",
                seed,
                "--language",
                language,
            ],
            text=True,
            capture_output=True,
            timeout=15,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ToolFailure("The deterministic engine could not be started.") from exc
    if completed.returncode != 0:
        raise ToolFailure(completed.stderr.strip().removeprefix("ERROR ") or "Template creation failed.")
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise ToolFailure("The deterministic engine returned invalid output.") from exc


def probe_inline_text(text: str) -> dict[str, Any]:
    try:
        probe = runpy.run_path(str(CRAFT_PROBE))
        chapters = probe["parse_chapters"](text)
        unit = "chapters"
        if not chapters:
            chapters = [probe["measure"]("excerpt", text.splitlines())]
            unit = "excerpt"
        summary = probe["summarize"](chapters)
    except (OSError, KeyError, TypeError) as exc:
        raise ToolFailure("The writing-craft text probe could not be loaded.") from exc
    return {
        "status": "computed",
        "unit": unit,
        "summary": summary,
        "limits": [
            "Metrics describe text surface only; they do not prove literary causation or quality.",
            "Dialogue ratio is a paragraph-format heuristic, not an exact semantic count.",
        ],
    }


def create_surface_audit(arguments: dict[str, Any]) -> dict[str, Any]:
    text = arguments.get("text")
    scope_manifest = arguments.get("scope_manifest")
    policy = arguments.get("policy")
    exceptions = arguments.get("exceptions")
    if not isinstance(text, str) or not text.strip():
        raise ToolFailure("text must be a non-empty string")
    if len(text) > MAX_CRAFT_TEXT_CHARS:
        raise ToolFailure(f"text exceeds the {MAX_CRAFT_TEXT_CHARS}-character inline limit")
    if not isinstance(scope_manifest, dict):
        raise ToolFailure("scope_manifest must be an object")
    scope_kind = scope_manifest.get("scope_kind")
    if scope_kind not in {"whole_work", "chapter_sample", "excerpt"}:
        raise ToolFailure("scope_manifest.scope_kind is invalid")
    if scope_kind == "whole_work" and not isinstance(scope_manifest.get("expected_chapters"), int):
        raise ToolFailure("whole_work requires scope_manifest.expected_chapters")
    if policy is not None and not isinstance(policy, dict):
        raise ToolFailure("policy must be an object")
    if exceptions is not None and not isinstance(exceptions, list):
        raise ToolFailure("exceptions must be an array")
    try:
        probe = runpy.run_path(str(CRAFT_PROBE))
        audit = runpy.run_path(str(SURFACE_AUDIT))
        return audit["audit_surface"](
            text,
            scope_manifest,
            policy,
            exceptions,
            probe["parse_chapter_blocks"],
        )
    except (OSError, KeyError, TypeError, ValueError) as exc:
        raise ToolFailure("The deterministic surface audit could not be completed.") from exc


def create_review_check(arguments: dict[str, Any]) -> dict[str, Any]:
    source_scope = arguments.get("source_scope")
    coverage = arguments.get("coverage_matrix")
    lenses = arguments.get("diagnostic_lenses")
    findings = arguments.get("findings")
    if not isinstance(source_scope, str) or not source_scope.strip():
        raise ToolFailure("source_scope must be a non-empty string")
    if not isinstance(coverage, list) or not isinstance(lenses, list) or not isinstance(findings, list):
        raise ToolFailure("coverage_matrix, diagnostic_lenses, and findings must be arrays")

    blockers: list[dict[str, Any]] = []
    coverage_by_layer: dict[int, dict[str, Any]] = {}
    for item in coverage:
        if not isinstance(item, dict) or not isinstance(item.get("layer"), int):
            blockers.append({"code": "invalid_coverage_item", "detail": "Each coverage item needs an integer layer."})
            continue
        layer = item["layer"]
        if layer in coverage_by_layer:
            blockers.append({"code": "duplicate_coverage_layer", "detail": layer})
        coverage_by_layer[layer] = item
    for layer in range(1, 13):
        item = coverage_by_layer.get(layer)
        if item is None:
            blockers.append({"code": "missing_coverage_layer", "detail": layer})
            continue
        status = item.get("status")
        if status not in {"finding", "not_applicable", "insufficient_evidence"}:
            blockers.append({"code": "unassessed_or_invalid_coverage", "detail": layer})
        if status == "insufficient_evidence":
            blockers.append({"code": "coverage_insufficient_evidence", "detail": layer})
        if not isinstance(item.get("rationale"), str) or not item["rationale"].strip():
            blockers.append({"code": "coverage_missing_rationale", "detail": layer})
        if status == "finding" and not item.get("evidence_locations"):
            blockers.append({"code": "coverage_finding_missing_evidence", "detail": layer})

    lens_by_id: dict[str, dict[str, Any]] = {}
    required_lens_ids = {lens["id"] for lens in DIAGNOSTIC_LENSES}
    for item in lenses:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str):
            blockers.append({"code": "invalid_lens_item", "detail": "Each lens needs an id."})
            continue
        lens_id = item["id"]
        if lens_id in lens_by_id:
            blockers.append({"code": "duplicate_lens", "detail": lens_id})
        lens_by_id[lens_id] = item
    for lens_id in sorted(required_lens_ids):
        item = lens_by_id.get(lens_id)
        if item is None:
            blockers.append({"code": "missing_diagnostic_lens", "detail": lens_id})
            continue
        status = item.get("status")
        if status not in {"finding", "not_found", "not_applicable", "insufficient_evidence"}:
            blockers.append({"code": "unassessed_or_invalid_lens", "detail": lens_id})
        if status == "insufficient_evidence":
            blockers.append({"code": "lens_insufficient_evidence", "detail": lens_id})
        if not isinstance(item.get("rationale"), str) or not item["rationale"].strip():
            blockers.append({"code": "lens_missing_rationale", "detail": lens_id})
        if status in {"finding", "not_found"} and not item.get("evidence_locations"):
            blockers.append({"code": "lens_missing_sample_locations", "detail": lens_id})

    required_finding_fields = {
        "id", "owner_layer", "priority", "evidence_locations", "reader_effect",
        "root_cause", "recommendation", "claim_grade", "preserve",
    }
    finding_ids: set[str] = set()
    for index, finding in enumerate(findings):
        if not isinstance(finding, dict):
            blockers.append({"code": "invalid_finding", "detail": index})
            continue
        missing = sorted(field for field in required_finding_fields if field not in finding)
        if missing:
            blockers.append({"code": "finding_missing_fields", "detail": {"index": index, "fields": missing}})
            continue
        finding_id = finding.get("id")
        if not isinstance(finding_id, str) or not finding_id.strip() or finding_id in finding_ids:
            blockers.append({"code": "invalid_or_duplicate_finding_id", "detail": finding_id})
        else:
            finding_ids.add(finding_id)
        if finding.get("owner_layer") not in {"world", "character", "story", "outline", "prose", "editor"}:
            blockers.append({"code": "finding_invalid_owner_layer", "detail": finding_id})
        if finding.get("priority") not in {"critical", "high", "medium", "low"}:
            blockers.append({"code": "finding_invalid_priority", "detail": finding_id})
        if finding.get("claim_grade") not in {"E1", "E2", "E3"}:
            blockers.append({"code": "finding_invalid_claim_grade", "detail": finding_id})
        for field in ("evidence_locations", "preserve"):
            if not isinstance(finding.get(field), list):
                blockers.append({"code": "finding_invalid_list_field", "detail": {"id": finding_id, "field": field}})
        for field in ("reader_effect", "root_cause", "recommendation"):
            if not isinstance(finding.get(field), str) or not finding[field].strip():
                blockers.append({"code": "finding_missing_explanation", "detail": {"id": finding_id, "field": field}})

    completeness = "complete" if not blockers else "incomplete"
    return {
        "review_contract_version": REVIEW_CONTRACT_VERSION,
        "source_scope": source_scope.strip(),
        "review_completeness": completeness,
        "ready_for_host_decision": not blockers,
        "semantic_truth_verified": False,
        "blockers": blockers,
        "literary_gate": {
            "passed": False,
            "status": "external_decision_required" if not blockers else "blocked_unassessed",
            "rule": "Completeness is not literary approval; only the host semantic reviewer may decide revision or acceptance.",
        },
    }


def create_craft_packet(arguments: dict[str, Any]) -> dict[str, Any]:
    mode = arguments.get("mode")
    source_scope = arguments.get("source_scope")
    focus = arguments.get("focus")
    text = arguments.get("text")
    state = arguments.get("state")
    style_source = arguments.get("style_source")

    if mode not in CRAFT_STEPS:
        raise ToolFailure("mode must be one of the supported writing-craft workflows")
    if not isinstance(source_scope, str) or not source_scope.strip():
        raise ToolFailure("source_scope must be a non-empty string")
    if len(source_scope) > 500:
        raise ToolFailure("source_scope is too long")
    if focus is not None and (not isinstance(focus, str) or len(focus) > 1000):
        raise ToolFailure("focus must be a string of at most 1000 characters")
    if text is not None:
        if not isinstance(text, str) or not text.strip():
            raise ToolFailure("text must be a non-empty string")
        if len(text) > MAX_CRAFT_TEXT_CHARS:
            raise ToolFailure(f"text exceeds the {MAX_CRAFT_TEXT_CHARS}-character inline limit")
    if state is not None and not isinstance(state, dict):
        raise ToolFailure("state must be an object")

    normalized_style_source: dict[str, str] | None = None
    if mode == "distill_style":
        if not isinstance(style_source, dict):
            raise ToolFailure("style_source must identify the work, original language, and edition or translation")
        allowed_style_source_fields = {"work", "author", "original_language", "edition_or_translation"}
        if set(style_source) - allowed_style_source_fields:
            raise ToolFailure("style_source contains unsupported fields")
        normalized_style_source = {}
        for field, limit in (("work", 500), ("original_language", 100), ("edition_or_translation", 500)):
            value = style_source.get(field)
            if not isinstance(value, str) or not value.strip() or len(value) > limit:
                raise ToolFailure(f"style_source.{field} must be a non-empty string within its length limit")
            normalized_style_source[field] = value.strip()
        author = style_source.get("author")
        if author is not None:
            if not isinstance(author, str) or len(author) > 300:
                raise ToolFailure("style_source.author must be a string of at most 300 characters")
            if author.strip():
                normalized_style_source["author"] = author.strip()
    elif style_source is not None:
        raise ToolFailure("style_source is only supported when mode is distill_style")

    artifact_owner = {
        "distill_work": "distill-novel-craft",
        "distill_style": "distill-novel-craft",
        "analyze_excerpt": "distill-novel-craft",
        "transfer_to_project": "resolve-with-world_route",
        "diagnose_revision": "fiction-core-zh:story-editor",
    }[mode]
    if state is None:
        world_bridge: dict[str, Any] = {
            "attached": False,
            "reason": "No world-state supplied; preserve any external canon and constraints in the host context.",
        }
    else:
        validation = run_engine("validate", state)
        route = run_engine("route", state)
        world_bridge = {
            "attached": True,
            "validation": validation,
            "route": route,
            "rule": "World authority, constraints, knowledge boundaries and invalidations remain upstream of craft advice.",
        }
        if mode == "transfer_to_project" and isinstance(route.get("skill"), str):
            artifact_owner = route["skill"]

    technique_card_fields = [
        "name", "question", "taxonomy_layer", "source_scope", "evidence", "classic_contrast",
        "mechanism", "counterevidence", "transfer_test", "do_not_copy", "application", "verification", "claim_grade",
    ]
    if mode == "distill_style":
        technique_card_fields.extend(["style_evidence", "narrative_controls"])

    return {
        "packet_version": "0.3.0",
        "assessment_phase": "scaffold",
        "mode": mode,
        "source_scope": source_scope.strip(),
        "focus": focus.strip() if isinstance(focus, str) and focus.strip() else None,
        "routing": {
            "advisor_skill": "distill-novel-craft",
            "artifact_owner": artifact_owner,
        },
        "coverage_matrix": [
            {"layer": index, "facet": facet, "status": "unassessed"}
            for index, facet in enumerate(CRAFT_FACETS, start=1)
        ],
        "coverage_status_contract": {
            "scaffold": ["unassessed"],
            "completed_review": ["finding", "not_applicable", "insufficient_evidence"],
            "rule": "unassessed is valid only for scaffolding and always blocks a host literary decision.",
        },
        "diagnostic_lenses": [
            {**lens, "status": "unassessed", "evidence_required": True}
            for lens in DIAGNOSTIC_LENSES
        ],
        "review_contract": {
            "version": REVIEW_CONTRACT_VERSION,
            "checker_tool": "world_craft_review_check",
            "finding_required_fields": [
                "id", "owner_layer", "priority", "evidence_locations", "reader_effect",
                "root_cause", "recommendation", "claim_grade", "preserve",
            ],
            "rule": "The checker verifies report completeness only; it cannot verify semantic truth or issue a literary pass.",
        },
        "evidence_contract": {
            "source_types": ["primary_text", "author_statement", "corpus_metric", "classic_text", "secondary"],
            "claim_grades": ["E0", "E1", "E2", "E3"],
            "rule": "Source type records provenance; claim grade records strength. Inference is not a source type.",
            "transfer_gate": "E3 requires two separated primary-text facts, one counterexample or cost, and one same-function classic contrast.",
        },
        "claim_audit_contract": {
            "required_fields": [
                "claim", "taxonomy_layer", "source_scope", "source_type", "evidence_locations",
                "inference", "counterevidence_or_cost", "relationship_to_existing_atlas",
                "claim_grade", "next_verification",
            ],
            "allowed_relationships": ["duplicate", "candidate", "conflict", "insufficient_evidence"],
            "rules": [
                "Summaries and secondary syntheses start at E1; promote only after direct primary-text verification.",
                "Map every claim to one of the existing 12 facets; a candidate is a mechanism within a facet, not a new facet.",
                "Claims using must, always, or no-exception language require an explicit scope and counterexample search.",
            ],
        },
        "workflow": CRAFT_STEPS[mode],
        "classic_contrast": {
            "required_fields": ["same_problem", "target_method_and_cost", "classic_method_and_cost", "shared_principle", "selection_conditions"],
            "rule": "Compare one function at a time; do not rank whole works or imitate distinctive wording/style.",
        },
        "technique_card_required_fields": technique_card_fields,
        "style_source": normalized_style_source,
        "style_transfer_contract": {
            "available_in_mode": "distill_style",
            "style_evidence_required_fields": ["source_metadata", "separated_locations", "observable_feature", "narrative_function", "counterexample_or_cost", "translation_limit"],
            "narrative_control_required_fields": ["narrative_job", "project_condition", "baseline", "variation_trigger", "allowed_variation", "observable_reader_effect", "costs_and_failure_modes", "verification"],
            "rule": "Translate evidence into project-local controls, not an author label or an imitation request.",
            "translation_limit": "Claims about syntax, cadence, or wording require original-language evidence; translations can support structure, event, or motif observations only.",
            "do_not_copy": ["signature phrases", "syntax fingerprints", "character correspondences", "recognizable scene sequences", "plot skeletons"],
        },
        "prose_transfer_contract": {
            "available_in_modes": ["transfer_to_project", "diagnose_revision"],
            "constraint_partition": {
                "required_fields": ["hard_invariants", "variation_obligations", "prose_freedoms"],
                "rule": "Knowledge, canon, and result locks must not be compiled into mandatory repeated wording or scene choreography.",
            },
            "expression_budget": {
                "full_principle_statement": "Allow a complete explanation at establishment; later uses should normally show a changed consequence, misreading, cost, or short reference.",
                "narrator_restatement_after_clear_dialogue": "Default budget is zero unless the restatement changes viewpoint, stakes, or interpretation.",
                "complete_checklist_readout": "Include only items that change the current decision; summarize unchanged continuity state.",
            },
            "voice_differentiation": {
                "required_per_speaker": ["experience_sources", "register", "rhythm_under_pressure", "error_or_blind_spot"],
                "shared_register_warning": "Do not give every occupation a complete evidence-law or authorization-law syllogism.",
                "translation_rule": "Let workers, patients, merchants, and specialists speak from body, craft, loss, and desire before a recorder formalizes boundaries.",
            },
            "scene_realization": {
                "required_fields": ["conflict_carrier", "decisive_action", "explanation_mode", "ending_shape"],
                "variation_rule": "Adjacent scenes that share document-table, wording challenge, column split, signature, and handoff require explicit justification or a changed carrier.",
            },
        },
        "text_probe": probe_inline_text(text) if isinstance(text, str) else {
            "status": "not-run",
            "reason": "No inline text supplied; the caller must inspect its primary source directly.",
        },
        "semantic_review": {
            "status": "NOT_ASSESSED",
            "performed_by": None,
        },
        "literary_gate": {
            "passed": False,
            "status": "BLOCKED",
            "blockers": ["coverage_unassessed", "diagnostic_lenses_unassessed", "semantic_review_not_performed"],
            "rule": "A generated packet or computed surface metric must never be mapped to literary approval.",
        },
        "world_bridge": world_bridge,
        "limits": [
            "This packet is a deterministic scaffold, not a literary judgment.",
            "A local excerpt cannot prove volume-level or whole-work claims.",
            "Generated craft advice never changes world canon or proposal authority.",
        ],
    }


def tool_result(payload: dict[str, Any], *, is_error: bool = False) -> dict[str, Any]:
    result: dict[str, Any] = {
        "content": [
            {
                "type": "text",
                "text": json.dumps(payload, ensure_ascii=False, indent=2),
            }
        ],
        "isError": is_error,
    }
    if not is_error:
        result["structuredContent"] = payload
    return result


def call_tool(params: dict[str, Any]) -> dict[str, Any]:
    name = params.get("name")
    arguments = params.get("arguments", {})
    if not isinstance(arguments, dict):
        raise ToolFailure("arguments must be an object")
    if name not in TOOL_BY_NAME:
        raise ToolFailure("Unknown tool")
    try:
        validate(arguments, TOOL_BY_NAME[name]["inputSchema"])
    except ContractError as exc:
        raise ToolFailure(str(exc)) from exc

    if name.startswith("worldcheck_"):
        try:
            return tool_result(WORLD_CHECK.call_tool(name, arguments))
        except WORLD_CHECK.ToolError as exc:
            raise ToolFailure(str(exc)) from exc
    if name in {tool["name"] for tool in workflow.TOOLS}:
        try:
            return tool_result(workflow.call_tool(name, arguments))
        except ContractError as exc:
            raise ToolFailure(str(exc)) from exc
    if name in {tool["name"] for tool in candidates.TOOLS}:
        try:
            return tool_result(candidates.call_tool(name, arguments))
        except ContractError as exc:
            raise ToolFailure(str(exc)) from exc

    if name == "world_project_template":
        return tool_result(create_template(arguments))
    if name == "world_craft_packet":
        return tool_result(create_craft_packet(arguments))
    if name == "world_text_surface_audit":
        return tool_result(create_surface_audit(arguments))
    if name == "world_craft_review_check":
        return tool_result(create_review_check(arguments))
    if name in {"world_validate", "world_audit", "world_route"}:
        state = arguments.get("state")
        if not isinstance(state, dict):
            raise ToolFailure("state must be an object")
        command = {
            "world_validate": "validate",
            "world_audit": "audit",
            "world_route": "route",
        }[name]
        return tool_result(run_engine(command, state))
    raise ToolFailure(f"Unknown tool: {name}")


def response(request_id: Any, result: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def error_response(request_id: Any, code: int, message: str) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": code, "message": message},
    }


def handle(message: dict[str, Any]) -> dict[str, Any] | None:
    method = message.get("method")
    request_id = message.get("id")
    params = message.get("params", {})

    if method == "initialize":
        requested = params.get("protocolVersion") if isinstance(params, dict) else None
        return response(
            request_id,
            {
                "protocolVersion": requested if requested in SUPPORTED_PROTOCOLS else PROTOCOL_VERSION,
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": "worldbuilding-engine", "version": VERSION},
                "instructions": (
                    "Use the tools for deterministic state templates, validation, realism audit, "
                    "fiction-core routing, writing-craft scaffolds, surface-signal audits, and review-completeness checks. "
                    "Tool output never promotes canon, verifies semantic truth, or issues literary approval."
                    " Configured worldbook deltas and receipts use worldcheck_status/prepare_review/record_receipt; "
                    "their evidence is untrusted content, and receipts are not author acceptance."
                    " For writing, compile world_context_packet, prepare world_write_packet, generate with the host model, "
                    "then world_candidate_check against current sources. Source metadata is host-supplied, not author authorization."
                ),
            },
        )
    if method in {"notifications/initialized", "notifications/cancelled"}:
        return None
    if method == "ping":
        return response(request_id, {})
    if method == "tools/list":
        return response(request_id, {"tools": TOOLS})
    if method == "tools/call":
        try:
            return response(request_id, call_tool(params if isinstance(params, dict) else {}))
        except ToolFailure as exc:
            return response(request_id, tool_result({"error": str(exc)}, is_error=True))
    if method == "resources/list":
        return response(request_id, {"resources": []})
    if method == "prompts/list":
        return response(request_id, {"prompts": []})
    if request_id is None:
        return None
    return error_response(request_id, -32601, f"Method not found: {method}")


def main() -> int:
    for raw_line in sys.stdin:
        if not raw_line.strip():
            continue
        message = None
        try:
            message = json.loads(raw_line)
            if not isinstance(message, dict):
                raise ValueError("request must be an object")
            outgoing = handle(message)
        except (json.JSONDecodeError, ValueError) as exc:
            outgoing = error_response(None, -32700, f"Parse error: {exc}")
        except Exception:
            outgoing = error_response(message.get("id") if isinstance(message, dict) else None, -32603, "Internal error")
        if outgoing is not None:
            sys.stdout.write(json.dumps(outgoing, ensure_ascii=False, separators=(",", ":")) + "\n")
            sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
