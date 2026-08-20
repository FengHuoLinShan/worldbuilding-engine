#!/usr/bin/env python3

from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path
from typing import Any


SERVER = Path(__file__).resolve().with_name("server.py")
LENSES = [
    "domain_term_load",
    "negation_template_repetition",
    "character_voice_differentiation",
    "scene_pattern_variation",
    "climax_action_deliberation_balance",
]


class MCPServerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.process = subprocess.Popen(
            ["python3", str(SERVER)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

    def tearDown(self) -> None:
        if self.process.poll() is None:
            self.process.terminate()
            self.process.wait(timeout=5)
        for stream in (self.process.stdin, self.process.stdout, self.process.stderr):
            if stream is not None:
                stream.close()

    def request(self, method: str, params: dict[str, Any] | None = None, request_id: int = 1) -> dict[str, Any]:
        assert self.process.stdin is not None
        assert self.process.stdout is not None
        payload: dict[str, Any] = {"jsonrpc": "2.0", "id": request_id, "method": method}
        if params is not None:
            payload["params"] = params
        self.process.stdin.write(json.dumps(payload, ensure_ascii=False) + "\n")
        self.process.stdin.flush()
        line = self.process.stdout.readline()
        if not line:
            stderr = self.process.stderr.read() if self.process.stderr else "server closed"
            self.fail(stderr or "server closed without a response")
        return json.loads(line)

    def call(self, name: str, arguments: dict[str, Any], request_id: int) -> dict[str, Any]:
        return self.request("tools/call", {"name": name, "arguments": arguments}, request_id=request_id)["result"]

    def test_initialize_and_list_tools(self) -> None:
        initialized = self.request(
            "initialize",
            {"protocolVersion": "2025-03-26", "capabilities": {}, "clientInfo": {"name": "test", "version": "1"}},
        )
        self.assertEqual("worldbuilding-engine", initialized["result"]["serverInfo"]["name"])
        self.assertEqual("0.5.0", initialized["result"]["serverInfo"]["version"])
        listed = self.request("tools/list", {}, request_id=2)
        names = {tool["name"] for tool in listed["result"]["tools"]}
        self.assertEqual(
            {
                "world_project_template", "world_validate", "world_audit", "world_route",
                "world_craft_packet", "world_text_surface_audit", "world_craft_review_check",
            },
            names,
        )

    def test_template_validate_audit_and_route(self) -> None:
        template = self.call(
            "world_project_template",
            {"title": "潮誓港", "seed": "每次公开违誓都会让港湾退潮一寸"},
            3,
        )
        self.assertFalse(template["isError"])
        state = template["structuredContent"]
        self.assertEqual("draft", state["premise"]["status"])

        validated = self.call("world_validate", {"state": state}, 4)
        self.assertTrue(validated["structuredContent"]["valid"])
        audited = self.call("world_audit", {"state": state}, 5)["structuredContent"]
        self.assertFalse(audited["gates"]["foundation"])
        routed = self.call("world_route", {"state": state}, 6)["structuredContent"]
        self.assertEqual("fiction-core-zh:world-architect", routed["skill"])

    def test_craft_packet_is_a_blocked_scaffold(self) -> None:
        state = self.call(
            "world_project_template",
            {"title": "潮誓港", "seed": "每次公开违誓都会让港湾退潮一寸"},
            7,
        )["structuredContent"]
        packet = self.call(
            "world_craft_packet",
            {
                "mode": "transfer_to_project",
                "source_scope": "测试文本两章",
                "focus": "信息如何推动行动",
                "text": "# 测试\n### 第一章 开始\n他醒了。\n“谁？”\n### 第二章 继续\n风停了！",
                "state": state,
            },
            8,
        )
        self.assertFalse(packet["isError"])
        content = packet["structuredContent"]
        self.assertEqual("0.3.0", content["packet_version"])
        self.assertEqual("scaffold", content["assessment_phase"])
        self.assertEqual(12, len(content["coverage_matrix"]))
        self.assertTrue(all(item["status"] == "unassessed" for item in content["coverage_matrix"]))
        self.assertEqual(5, len(content["diagnostic_lenses"]))
        self.assertTrue(all(item["status"] == "unassessed" for item in content["diagnostic_lenses"]))
        self.assertEqual("chapters", content["text_probe"]["unit"])
        self.assertEqual(2, content["text_probe"]["summary"]["chapters"])
        self.assertFalse(content["literary_gate"]["passed"])
        self.assertEqual("BLOCKED", content["literary_gate"]["status"])
        self.assertIn("variation_obligations", content["prose_transfer_contract"]["constraint_partition"]["required_fields"])
        self.assertTrue(content["world_bridge"]["validation"]["valid"])
        self.assertEqual("draft", state["premise"]["status"])

        style = self.call(
            "world_craft_packet",
            {
                "mode": "distill_style",
                "source_scope": "目标作品两个相隔场景",
                "style_source": {
                    "work": "测试作品", "author": "测试作者", "original_language": "中文",
                    "edition_or_translation": "用户提供的校对本",
                },
            },
            9,
        )
        self.assertFalse(style["isError"])
        self.assertIn("style_evidence", style["structuredContent"]["technique_card_required_fields"])
        self.assertFalse(style["structuredContent"]["literary_gate"]["passed"])

    def test_surface_audit_parses_markdown_and_reports_signals(self) -> None:
        repeated = "这是一段足够长的公告文字，用来验证跨章节完全重复不能被正常章长掩盖。"
        text = (
            "# 合订本\n## 第一部·白面\n### 第一章 开始\n" + repeated + "\n"
            "不能由记录推出安全，也不能替别人签字。\n"
            "### 第二章 继续\n" + repeated + "\n"
            "不能把一次运行写成安全，也不能替下一班签字。\n"
            "### 第三章 结束\n" + repeated + "\n"
            "没有写成同意，也没有写成拒绝。\n"
        )
        result = self.call(
            "world_text_surface_audit",
            {
                "text": text,
                "scope_manifest": {"scope_kind": "whole_work", "expected_chapters": 3},
                "policy": {
                    "id": "test-policy",
                    "version": "1",
                    "thresholds": {"exact_duplicate_warn": 0.001, "exact_duplicate_fail": 0.01},
                    "ordered_sequences": [
                        {"id": "boundary-sequence", "lexemes": ["不能", "替"], "warn_chapter_df": 2}
                    ],
                },
            },
            10,
        )
        self.assertFalse(result["isError"])
        audit = result["structuredContent"]
        self.assertEqual(3, audit["parse"]["parsed_chapters"])
        self.assertEqual(1.0, audit["parse"]["coverage_ratio"])
        self.assertEqual("NOT_ASSESSED", audit["gates"]["semantic_review_gate"])
        self.assertEqual("BLOCKED", audit["gates"]["overall_gate"])
        metrics = {finding["metric"] for finding in audit["findings"]}
        self.assertIn("exact_duplicate.excess_char_ratio", metrics)
        self.assertIn("ordered_lexeme_sequence.boundary-sequence", metrics)

    def test_surface_audit_flags_same_length_template_pollution(self) -> None:
        chapters = []
        for index, name in enumerate(("甲", "乙", "丙", "丁", "戊", "己"), start=1):
            chapters.append(
                f"### 第{index}章 模板{index}\n"
                f"{name}把登记纸压在桌面上，先核对来源，再核对范围，最后把未决项目移到附页。"
                f"有人问能不能继续，{name}划掉过宽的结论，另开一栏，签下自己的名字，把文件交给下一张桌。"
            )
        audit = self.call(
            "world_text_surface_audit",
            {
                "text": "\n".join(chapters),
                "scope_manifest": {"scope_kind": "whole_work", "expected_chapters": 6},
                "policy": {
                    "thresholds": {
                        "near_duplicate_warn": 0.001,
                        "near_duplicate_fail": 0.01,
                        "near_duplicate_similarity": 0.70,
                    }
                },
            },
            16,
        )["structuredContent"]
        metrics = {finding["metric"] for finding in audit["findings"]}
        self.assertIn("near_duplicate.excess_char_ratio", metrics)
        self.assertEqual("BLOCKED", audit["gates"]["overall_gate"])

    def test_surface_audit_rejects_scope_mismatch_and_bad_chapters(self) -> None:
        text = "### 第一章 一\n有内容。\n### 第一章 重复\n\n### 第三章 三\n有内容。"
        audit = self.call(
            "world_text_surface_audit",
            {"text": text, "scope_manifest": {"scope_kind": "whole_work", "expected_chapters": 25}},
            11,
        )["structuredContent"]
        self.assertEqual("FAIL", audit["gates"]["surface_regression_gate"])
        self.assertIn("parsed_chapter_count_mismatch", audit["blockers"])
        self.assertIn("duplicate_chapter_numbers", audit["blockers"])
        self.assertIn("missing_chapter_numbers", audit["blockers"])
        self.assertTrue(audit["parse"]["empty_chapters"])

    def test_review_check_blocks_empty_and_never_passes_complete(self) -> None:
        incomplete = self.call(
            "world_craft_review_check",
            {"source_scope": "完整稿", "coverage_matrix": [], "diagnostic_lenses": [], "findings": []},
            12,
        )["structuredContent"]
        self.assertEqual("incomplete", incomplete["review_completeness"])
        self.assertFalse(incomplete["ready_for_host_decision"])
        self.assertFalse(incomplete["literary_gate"]["passed"])

        coverage = [
            {
                "layer": layer,
                "status": "finding" if layer == 11 else "not_applicable",
                "rationale": "已近读并记录范围内判断。",
                "evidence_locations": ["C01:L1"] if layer == 11 else [],
            }
            for layer in range(1, 13)
        ]
        lenses = [
            {
                "id": lens,
                "status": "finding" if lens == "negation_template_repetition" else "not_found",
                "rationale": "抽查开头、中段和结尾。",
                "evidence_locations": ["C01:L1", "C02:L8"],
            }
            for lens in LENSES
        ]
        findings = [
            {
                "id": "F-1",
                "owner_layer": "prose",
                "priority": "high",
                "evidence_locations": ["C01:L1", "C02:L8"],
                "reader_effect": "句式节拍趋同。",
                "root_cause": "边界规范被编译为固定措辞。",
                "recommendation": "保留原则，改以不同人物经验承载。",
                "claim_grade": "E2",
                "preserve": ["证据边界"],
            }
        ]
        complete = self.call(
            "world_craft_review_check",
            {"source_scope": "完整稿", "coverage_matrix": coverage, "diagnostic_lenses": lenses, "findings": findings},
            13,
        )["structuredContent"]
        self.assertEqual("complete", complete["review_completeness"])
        self.assertTrue(complete["ready_for_host_decision"])
        self.assertFalse(complete["semantic_truth_verified"])
        self.assertFalse(complete["literary_gate"]["passed"])
        self.assertEqual("external_decision_required", complete["literary_gate"]["status"])

    def test_surface_audit_is_deterministic(self) -> None:
        arguments = {
            "text": "### 第一章 一\n门开了。\n### 第二章 二\n门又开了。",
            "scope_manifest": {"scope_kind": "whole_work", "expected_chapters": 2},
        }
        first = self.call("world_text_surface_audit", arguments, 14)["structuredContent"]
        second = self.call("world_text_surface_audit", arguments, 15)["structuredContent"]
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
