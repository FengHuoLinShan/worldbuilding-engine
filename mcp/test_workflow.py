"""Synthetic source-bound checks, no model calls or user files."""

import copy
import unittest

from contracts import ContractError
import workflow as w


def context():
    return {"project_id": "example", "sources": [
        {"id": "rule", "project_id": "example", "title": "潮闸", "text": "😀潮闸每天消耗盐。",
         "kind": "fact", "status": "canon", "visible_to": ["author", "reader", "character"],
         "known_by": ["worker"], "available_from": {"chapter": 1, "offset": 0}},
        {"id": "secret", "project_id": "example", "title": "秘密", "text": "UNSEEN_SECRET", "kind": "fact",
         "status": "canon", "visible_to": ["author"], "available_from": {"chapter": 2, "offset": 0}},
    ], "selected_ids": ["rule"], "excluded_ids": ["secret"], "visibility": "author"}


def request():
    return {"mode": "create_world", "goal": "写潮闸镇生活", "context": context(), "hard_invariants": ["潮闸需要盐"]}


def candidate(req):
    packet = w.call_tool("world_write_packet", req)
    return {"title": "潮闸镇", "content": "居民轮流搬盐。", "status": "proposed",
            "context_hash": packet["context_hash"], "writing_hash": packet["writing_hash"],
            "citations": [{"source_id": "rule", "source_hash": w.text_hash(req["context"]["sources"][0]["text"]),
                           "start": 1, "quote": "潮闸每天消耗盐。"}]}


class WorkflowTest(unittest.TestCase):
    def test_full_generation_binding_and_unicode_citation(self):
        req = request()
        packet = w.call_tool("world_write_packet", req)
        self.assertNotIn("UNSEEN_SECRET", packet["host_prompt"])
        checked = w.call_tool("world_candidate_check", {"request": req, "candidate": candidate(req)})
        self.assertTrue(checked["integrity_valid"])
        self.assertFalse(checked["semantic_truth_verified"])
        self.assertFalse(checked["canon_promoted"])

    def test_scope_and_source_changes_make_candidate_stale(self):
        original = request()
        result = candidate(original)
        for change in ("text", "exclusion", "goal", "constraint"):
            req = copy.deepcopy(original)
            if change == "text":
                req["context"]["sources"][0]["text"] += "修订"
            elif change == "exclusion":
                req["context"]["excluded_ids"] = []
            elif change == "goal":
                req["goal"] = "另一任务"
            else:
                req["hard_invariants"] = []
            with self.assertRaisesRegex(ContractError, "stale"):
                w.call_tool("world_candidate_check", {"request": req, "candidate": result})

    def test_visibility_cutoff_knowledge_and_budget_fail_closed(self):
        ctx = context()
        ctx.update(visibility="character", character_id="worker", cutoff={"chapter": 1, "offset": 0})
        self.assertTrue(w.call_tool("world_context_packet", ctx)["ready"])
        for update, reason in [({"character_id": "stranger"}, "character_unknown"),
                               ({"cutoff": {"chapter": 0, "offset": 0}}, "after_cutoff"),
                               ({"budget_chars": 1}, "budget")]:
            result = w.call_tool("world_context_packet", {**ctx, **update})
            self.assertFalse(result["ready"])
            self.assertEqual(reason, result["blockers"][0]["reason"])
            self.assertEqual([], result["items"])
        with self.assertRaises(ContractError):
            w.call_tool("world_context_packet", {**ctx, "character_id": ""})

    def test_unknown_overlapping_duplicate_cross_project_sources(self):
        for mutation in ("overlap", "unknown", "duplicate", "project"):
            ctx = context()
            if mutation == "overlap":
                ctx["excluded_ids"].append("rule")
            elif mutation == "unknown":
                ctx["selected_ids"].append("missing")
            elif mutation == "duplicate":
                ctx["sources"].append(copy.deepcopy(ctx["sources"][0]))
            else:
                ctx["sources"][1]["project_id"] = "other"
            with self.assertRaises(ContractError):
                w.call_tool("world_context_packet", ctx)

    def test_invented_quotes_and_canon_promotion_rejected(self):
        req = request()
        for mutation in ("quote", "start", "source", "status"):
            result = candidate(req)
            if mutation == "status":
                result["status"] = "canon"
            elif mutation == "source":
                result["citations"][0]["source_id"] = "secret"
            elif mutation == "start":
                result["citations"][0]["start"] = 2
            else:
                result["citations"][0]["quote"] = "凭空引用"
            with self.assertRaises(ContractError):
                w.call_tool("world_candidate_check", {"request": req, "candidate": result})

    def test_modes_and_search_are_host_assignments_only(self):
        for mode in w.MODES:
            req = request()
            req["mode"] = mode
            if mode == "reader_rehearsal":
                req["context"].update(visibility="reader", cutoff={"chapter": 1, "offset": 0})
            self.assertEqual("host_model_required", w.call_tool("world_write_packet", req)["generation_status"])
        result = w.call_tool("world_evidence_search", {"project_id": "example", "sources": context()["sources"], "query": "潮闸"})
        self.assertEqual("rule", result["hits"][0]["source_id"])
        self.assertFalse(result["authorizes_context"])


if __name__ == "__main__":
    unittest.main()
