#!/usr/bin/env python3
"""Print portable client config; never edits the host's settings."""

import argparse
import json
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worldcheck-config", type=Path)
    parser.add_argument("--workspace", type=Path)
    parser.add_argument("--project-id")
    arguments = parser.parse_args()
    if bool(arguments.workspace) != bool(arguments.project_id):
        parser.error("--workspace and --project-id must be supplied together")
    root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(root / "mcp"))
    from contracts import ContractError, validate
    from workflow import IDENTITY

    env = {}
    if arguments.worldcheck_config:
        config = arguments.worldcheck_config.expanduser().resolve()
        if not config.is_file():
            parser.error("Worldcheck config must be an existing file")
        env["WORLDCHECK_CONFIG"] = str(config)
    if arguments.workspace:
        workspace = arguments.workspace.expanduser().resolve()
        if not workspace.is_dir():
            parser.error("workspace must be an existing directory")
        try:
            validate(arguments.project_id, IDENTITY)
        except ContractError:
            parser.error("invalid project id; use letters, digits, underscore, hyphen, dot or colon")
        env.update(WORLDBUILDING_WORKSPACE=str(workspace), WORLDBUILDING_PROJECT_ID=arguments.project_id)
    server = {"command": sys.executable, "args": [str(root / "mcp/server.py")]}
    if env:
        server["env"] = env
    print(json.dumps({"mcpServers": {"worldbuilding-engine": server}}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
