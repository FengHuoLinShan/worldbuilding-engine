"""Portable config + stdio smoke, safe to run from an extracted archive."""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main():
    config = json.loads(subprocess.check_output([sys.executable, str(ROOT / "scripts/mcp_config.py")], text=True, encoding="utf-8"))
    server = config["mcpServers"]["worldbuilding-engine"]
    assert Path(server["args"][0]).is_absolute()
    assert "env" not in server  # Optional file access and persistence are disabled.
    request = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-11-25"}},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        {"jsonrpc": "2.0", "id": 3, "method": "prompts/list"},
        {"jsonrpc": "2.0", "id": 4, "method": "resources/read", "params": {"uri": "worldbuilding://contract"}},
        {"jsonrpc": "2.0", "id": 5, "method": "tools/call", "params": {"name": "world_project_template", "arguments": {"title": "潮闸镇", "seed": "潮闸需要盐"}}},
    ]
    result = subprocess.run([server["command"], *server["args"]], input="\n".join(json.dumps(item, ensure_ascii=False) for item in request) + "\n",
                            cwd=ROOT.parent, text=True, encoding="utf-8", capture_output=True, timeout=20, check=True)
    assert not result.stderr, result.stderr
    messages = [json.loads(line) for line in result.stdout.splitlines()]
    assert messages[0]["result"]["serverInfo"]["version"] == "0.8.0"
    assert json.loads((ROOT / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))["version"] == "0.8.0"
    assert len(messages[1]["result"]["tools"]) == 17
    assert len(messages[2]["result"]["prompts"]) == 14
    assert "候选空间" in messages[3]["result"]["contents"][0]["text"]
    assert messages[4]["result"]["structuredContent"]["premise"]["status"] == "draft"
    print("Standalone bundle: portable config, arbitrary cwd, resource and Ruby template passed.")


if __name__ == "__main__":
    main()
