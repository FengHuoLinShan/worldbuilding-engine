"""Wire-level adversarial requests: reject and keep subsequent requests usable."""

import json
import subprocess
import sys
import unittest
from pathlib import Path

SERVER = Path(__file__).with_name("server.py")


class ProtocolTest(unittest.TestCase):
    def exchange(self, lines):
        completed = subprocess.run([sys.executable, str(SERVER)], input="\n".join(lines) + "\n",
                                   text=True, capture_output=True, timeout=10, check=True)
        self.assertEqual("", completed.stderr)
        return [json.loads(line) for line in completed.stdout.splitlines()]

    def test_bad_envelopes_numbers_duplicate_keys_and_notifications(self):
        messages = [
            "broken-json", "[]", '{"jsonrpc":"2.0","id":1,"method":"ping","params":{"x":NaN}}',
            '{"jsonrpc":"2.0","id":1,"method":"ping","id":2}',
            json.dumps({"jsonrpc": "2.0", "id": True, "method": "ping"}),
            json.dumps({"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": []}),
            json.dumps({"jsonrpc": "2.0", "method": "unknown-notification"}),
            json.dumps({"jsonrpc": "2.0", "method": "tools/call", "params": {"name": "world_candidate_save"}}),
            json.dumps({"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": []}}),
            json.dumps({"jsonrpc": "2.0", "id": 5, "method": "ping"}),
        ]
        result = self.exchange(messages)
        self.assertEqual(8, len(result))
        self.assertEqual([-32700, -32600, -32700, -32700, -32600, -32602], [item["error"]["code"] for item in result[:6]])
        self.assertTrue(result[6]["result"]["isError"])
        self.assertEqual({}, result[7]["result"])

    def test_oversize_line_is_drained_before_next_request(self):
        for prefix in ('"', ' '):
            result = self.exchange([prefix * 1_000_100, '{"jsonrpc":"2.0","id":8,"method":"ping"}'])
            self.assertEqual(2, len(result))
            self.assertEqual(-32700, result[0]["error"]["code"])
            self.assertEqual({}, result[1]["result"])

    def test_prompts_resources_and_option_injection(self):
        params = [
            ("prompts/get", {"name": "worldbuilding_create_world", "arguments": {"request_json": "bad-json"}}),
            ("resources/read", {"uri": "file:///private/file"}),
            ("tools/call", {"name": "worldcheck_prepare_review", "arguments": {"targets": ["--record"]}}),
            ("tools/call", {"name": "worldcheck_status", "arguments": {"target": "--config"}}),
        ]
        messages = [json.dumps({"jsonrpc": "2.0", "id": index, "method": method, "params": arguments})
                    for index, (method, arguments) in enumerate(params, 1)]
        result = self.exchange(messages)
        self.assertEqual([-32602, -32602], [item["error"]["code"] for item in result[:2]])
        self.assertTrue(all(item["result"]["isError"] for item in result[2:]))
        self.assertNotIn("/Users/", json.dumps(result))


if __name__ == "__main__":
    unittest.main()
