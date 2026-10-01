"""Candidate history: private temp directories, no actual author workspace."""

import copy
import os
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

import candidates as store
from contracts import ContractError
from test_workflow import request, candidate


class CandidateTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.environment = patch.dict(os.environ, {"WORLDBUILDING_WORKSPACE": self.directory.name, "WORLDBUILDING_PROJECT_ID": "example"})
        self.environment.start()
        req = request()
        self.args = {"candidate_id": "town", "operation_id": "op-1", "expected_head": None,
                     "request": req, "candidate": candidate(req)}

    def tearDown(self):
        self.environment.stop()
        self.directory.cleanup()

    def test_save_retry_revision_history_and_no_change(self):
        first = store.call_tool("world_candidate_save", self.args)
        self.assertEqual(first, store.call_tool("world_candidate_save", self.args))
        latest = store.call_tool("world_candidate_read", {"candidate_id": "town"})
        self.assertEqual("not_revalidated", latest["freshness"])
        second_args = copy.deepcopy(self.args)
        second_args.update(operation_id="op-2", expected_head=first["revision_hash"])
        second_args["candidate"]["content"] += "他们把盐储存在高处。"
        second = store.call_tool("world_candidate_save", second_args)
        self.assertEqual(first["revision_hash"], second["parent_hash"])
        original = store.call_tool("world_candidate_read", {"candidate_id": "town", "revision_hash": first["revision_hash"]})
        self.assertEqual(self.args["candidate"], original["candidate"])
        second_args.update(operation_id="op-3", expected_head=second["revision_hash"])
        unchanged = store.call_tool("world_candidate_save", second_args)
        self.assertTrue(unchanged["no_change"])
        self.assertEqual(second["revision_hash"], unchanged["revision_hash"])
        self.assertFalse(unchanged["canon_promoted"])

    def test_stale_source_conflict_retry_mismatch_and_project_isolation(self):
        first = store.call_tool("world_candidate_save", self.args)
        changed = copy.deepcopy(self.args)
        changed["request"]["context"]["sources"][0]["text"] += "改变"
        with self.assertRaisesRegex(ContractError, "stale"):
            store.call_tool("world_candidate_save", changed)
        changed = copy.deepcopy(self.args)
        changed["candidate"]["content"] = "另一稿"
        with self.assertRaisesRegex(ContractError, "operation_id"):
            store.call_tool("world_candidate_save", changed)
        changed["operation_id"] = "op-2"
        with self.assertRaisesRegex(ContractError, "head changed"):
            store.call_tool("world_candidate_save", changed)
        with patch.dict(os.environ, {"WORLDBUILDING_PROJECT_ID": "other"}):
            with self.assertRaisesRegex(ContractError, "different"):
                store.call_tool("world_candidate_save", self.args)
            with self.assertRaisesRegex(ContractError, "not found"):
                store.call_tool("world_candidate_read", {"candidate_id": "town", "revision_hash": first["revision_hash"]})

    def test_concurrent_saves_only_one_head_and_retry_are_atomic(self):
        other = copy.deepcopy(self.args)
        other["operation_id"] = "op-2"
        other["candidate"]["content"] = "另一稿"

        def attempt(args):
            try:
                return store.call_tool("world_candidate_save", args)
            except ContractError as exc:
                return str(exc)

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(attempt, [self.args, other]))
        self.assertEqual(1, sum(isinstance(result, dict) for result in results))
        self.assertTrue(any("head changed" in result for result in results if isinstance(result, str)))

    def test_default_disabled_and_unknown_candidate_read_has_no_write(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(ContractError, "disabled"):
                store.call_tool("world_candidate_save", self.args)
        with self.assertRaisesRegex(ContractError, "no saved"):
            store.call_tool("world_candidate_read", {"candidate_id": "missing"})
        self.assertEqual([], os.listdir(self.directory.name))


if __name__ == "__main__":
    unittest.main()
