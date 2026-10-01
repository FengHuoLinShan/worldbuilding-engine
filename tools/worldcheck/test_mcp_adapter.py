#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("worldcheck_mcp", HERE / "mcp_adapter.py")
assert SPEC and SPEC.loader
MCP = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MCP)


class McpAdapterTest(unittest.TestCase):
    def test_initialize_and_tools_list(self) -> None:
        initialized = MCP.handle(
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-11-25"}}
        )
        self.assertEqual("worldcheck", initialized["result"]["serverInfo"]["name"])
        self.assertIn("worldcheck_status first", initialized["result"]["instructions"])
        self.assertIn("not author acceptance", initialized["result"]["instructions"])
        listed = MCP.handle({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        names = [tool["name"] for tool in listed["result"]["tools"]]
        self.assertEqual(
            ["worldcheck_prepare_review", "worldcheck_record_receipt", "worldcheck_status"],
            names,
        )
        self.assertFalse(any("full" in name or "file" in name or "write" in name for name in names))
        for tool in listed["result"]["tools"]:
            self.assertFalse(tool["inputSchema"]["additionalProperties"])
            self.assertIn("outputSchema", tool)

    def test_all_three_tool_calls_return_structured_content(self) -> None:
        packet_hash = "sha256:" + "a" * 64
        responses = [
            {"ok": True, "command": "review", "packet": {}, "issues": []},
            {"ok": True, "command": "review-record", "recorded": True, "status": "pass", "issues": []},
            {"ok": True, "command": "status", "issues": []},
        ]
        with mock.patch.object(MCP, "run_cli", autospec=True, side_effect=responses) as run:
            calls = [
                ("worldcheck_prepare_review", {"targets": ["Alpha"], "budget_chars": 3000}),
                (
                    "worldcheck_record_receipt",
                    {"packet_hash": packet_hash, "receipt": {"receipt_version": "1.0"}},
                ),
                ("worldcheck_status", {"target": "Alpha"}),
            ]
            for index, (name, arguments) in enumerate(calls, 1):
                response = MCP.handle(
                    {
                        "jsonrpc": "2.0",
                        "id": index,
                        "method": "tools/call",
                        "params": {"name": name, "arguments": arguments},
                    }
                )
                result = response["result"]
                self.assertFalse(result["isError"])
                self.assertIsInstance(result["structuredContent"], dict)
            self.assertEqual(3, run.call_count)
            record_stdin = run.call_args_list[1].args[1]
            self.assertEqual(packet_hash, json.loads(record_stdin)["packet_hash"])

    def test_invalid_receipt_hash_is_safe_tool_error(self) -> None:
        response = MCP.handle(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "worldcheck_record_receipt",
                    "arguments": {
                        "packet_hash": "sha256:" + "a" * 64,
                        "receipt": {"packet_hash": "sha256:" + "b" * 64},
                    },
                },
            }
        )
        self.assertTrue(response["result"]["isError"])
        self.assertNotIn("traceback", response["result"]["content"][0]["text"].lower())

    def test_cli_nonzero_timeout_and_invalid_json_are_tool_errors(self) -> None:
        failed = subprocess.CompletedProcess(
            args=[],
            returncode=2,
            stdout=json.dumps({"issues": [{"message": "bad receipt"}]}),
            stderr="",
        )
        with mock.patch.dict(os.environ, {"WORLDCHECK_CONFIG": "/safe/project/worldcheck.json"}):
            with mock.patch.object(MCP.subprocess, "run", autospec=True, return_value=failed) as run, self.assertRaisesRegex(MCP.ToolError, "bad receipt"):
                MCP.run_cli(["status"])
            self.assertEqual(
                [MCP.RUBY, MCP.CLI, "status", "--config", "/safe/project/worldcheck.json", "--json"],
                run.call_args.args[0],
            )
            self.assertEqual(Path("/safe/project"), run.call_args.kwargs["cwd"])
            invalid = subprocess.CompletedProcess(args=[], returncode=0, stdout="not json", stderr="")
            with mock.patch.object(MCP.subprocess, "run", autospec=True, return_value=invalid), self.assertRaisesRegex(MCP.ToolError, "invalid JSON: exit 0"):
                MCP.run_cli(["status"])
            blocked = subprocess.CompletedProcess(
                args=[], returncode=126, stdout="", stderr="sandbox denied child process"
            )
            with mock.patch.object(MCP.subprocess, "run", autospec=True, return_value=blocked), self.assertRaisesRegex(MCP.ToolError, "exit 126"):
                MCP.run_cli(["status"])
            with mock.patch.object(MCP.subprocess, "run", autospec=True, side_effect=subprocess.TimeoutExpired([], 60)), self.assertRaisesRegex(MCP.ToolError, "unavailable"):
                MCP.run_cli(["status"])

    def test_cli_requires_environment_config(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True), self.assertRaisesRegex(MCP.ToolError, "WORLDCHECK_CONFIG is required"):
            MCP.run_cli(["status"])

    def test_targets_cannot_inject_cli_options(self) -> None:
        for target in ["--record", "--config", "--full", "", "\nAlpha", "-", "x" * 1001]:
            with mock.patch.object(MCP, "run_cli", autospec=True) as run:
                with self.assertRaises(MCP.ToolError):
                    MCP.call_tool("worldcheck_prepare_review", {"targets": [target]})
                with self.assertRaises(MCP.ToolError):
                    MCP.call_tool("worldcheck_status", {"target": target})
                run.assert_not_called()

    def test_stdio_stdout_is_json_rpc_only(self) -> None:
        requests = "\n".join(
            json.dumps(request)
            for request in [
                {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
                {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
                {"jsonrpc": "2.0", "id": 3, "method": "missing"},
            ]
        ) + "\n"
        completed = subprocess.run(
            [sys.executable, str(HERE / "mcp_adapter.py")],
            input=requests,
            text=True,
            capture_output=True,
            check=True,
        )
        lines = completed.stdout.splitlines()
        self.assertEqual(3, len(lines))
        self.assertTrue(all(json.loads(line)["jsonrpc"] == "2.0" for line in lines))
        self.assertEqual("", completed.stderr)


if __name__ == "__main__":
    unittest.main()
