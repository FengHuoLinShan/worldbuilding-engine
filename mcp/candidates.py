"""Optional, single-project candidate history in a host-configured local directory."""

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from contracts import ContractError, validate
from workflow import CANDIDATE, HASH, IDENTITY, WRITING, candidate_check, digest, tool


TOOLS = [
    tool("world_candidate_save", "Save draft/proposed candidate history to the host-configured project workspace. Checks current source binding, CAS and retry identity; never writes canon.", {
        "type": "object", "additionalProperties": False,
        "required": ["candidate_id", "operation_id", "expected_head", "request", "candidate"],
        "properties": {"candidate_id": IDENTITY, "operation_id": IDENTITY,
                       "expected_head": {"type": ["string", "null"], "pattern": HASH["pattern"]},
                       "request": WRITING, "candidate": CANDIDATE},
    }),
    tool("world_candidate_read", "Read current or exact historic candidate from the configured single-project store. Stored provenance is not live source verification.", {
        "type": "object", "additionalProperties": False, "required": ["candidate_id"],
        "properties": {"candidate_id": IDENTITY, "revision_hash": HASH},
    }),
]


def configured_store():
    workspace = os.environ.get("WORLDBUILDING_WORKSPACE")
    project_id = os.environ.get("WORLDBUILDING_PROJECT_ID")
    if not workspace or not project_id:
        raise ContractError("candidate store disabled: host must set WORLDBUILDING_WORKSPACE and WORLDBUILDING_PROJECT_ID")
    validate(project_id, IDENTITY, "configured project")
    root = Path(workspace).expanduser()
    if not root.is_absolute() or not root.is_dir():
        raise ContractError("configured workspace must be an existing absolute directory")
    database = root.resolve() / "worldbuilding-candidates.sqlite3"
    if database.is_symlink():
        raise ContractError("candidate database must not be a symbolic link")
    return database, project_id


def initialize(database):
    database.execute("CREATE TABLE IF NOT EXISTS revisions (project TEXT, candidate_id TEXT, revision_hash TEXT PRIMARY KEY, parent_hash TEXT, candidate_json TEXT, check_json TEXT, created_at TEXT)")
    database.execute("CREATE TABLE IF NOT EXISTS heads (project TEXT, candidate_id TEXT, revision_hash TEXT, PRIMARY KEY(project, candidate_id))")
    database.execute("CREATE TABLE IF NOT EXISTS operations (project TEXT, operation_id TEXT, request_hash TEXT, receipt_json TEXT, PRIMARY KEY(project, operation_id))")


def save(arguments):
    path, project_id = configured_store()
    if arguments["request"]["context"]["project_id"] != project_id:
        raise ContractError("candidate belongs to a different configured project")
    check = candidate_check(arguments)
    request_hash = digest(arguments)
    candidate_id = arguments["candidate_id"]
    candidate_json = json.dumps(arguments["candidate"], ensure_ascii=False, sort_keys=True)
    database = sqlite3.connect(path, timeout=10, isolation_level=None)
    database.row_factory = sqlite3.Row
    try:
        database.execute("BEGIN IMMEDIATE")
        initialize(database)
        previous = database.execute("SELECT request_hash, receipt_json FROM operations WHERE project=? AND operation_id=?",
                                    (project_id, arguments["operation_id"])).fetchone()
        if previous:
            if previous["request_hash"] != request_hash:
                raise ContractError("operation_id was already used for different input")
            database.commit()
            return json.loads(previous["receipt_json"])
        row = database.execute("SELECT r.* FROM heads h JOIN revisions r ON r.revision_hash=h.revision_hash WHERE h.project=? AND h.candidate_id=?",
                               (project_id, candidate_id)).fetchone()
        head = row["revision_hash"] if row else None
        if head != arguments["expected_head"]:
            raise ContractError("candidate head changed: read the current revision before saving")
        unchanged = row is not None and row["candidate_json"] == candidate_json
        revision_hash = head if unchanged else digest({"project_id": project_id, "candidate_id": candidate_id,
                                                       "parent_hash": head, "candidate": arguments["candidate"]})
        if not unchanged:
            database.execute("INSERT INTO revisions VALUES (?,?,?,?,?,?,?)",
                             (project_id, candidate_id, revision_hash, head, candidate_json,
                              json.dumps(check, sort_keys=True), datetime.now(timezone.utc).isoformat()))
            database.execute("INSERT INTO heads VALUES (?,?,?) ON CONFLICT(project,candidate_id) DO UPDATE SET revision_hash=excluded.revision_hash",
                             (project_id, candidate_id, revision_hash))
        receipt = {"saved": True, "no_change": unchanged, "project_id": project_id, "candidate_id": candidate_id,
                   "revision_hash": revision_hash, "parent_hash": row["parent_hash"] if unchanged else head,
                   "operation_id": arguments["operation_id"], "status": arguments["candidate"]["status"],
                   "canon_promoted": False, "semantic_truth_verified": False}
        database.execute("INSERT INTO operations VALUES (?,?,?,?)",
                         (project_id, arguments["operation_id"], request_hash, json.dumps(receipt, sort_keys=True)))
        database.commit()
        return receipt
    except Exception:
        database.rollback()
        raise
    finally:
        database.close()


def read(arguments):
    path, project_id = configured_store()
    if not path.is_file():
        raise ContractError("candidate store has no saved revisions")
    database = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, timeout=10)
    database.row_factory = sqlite3.Row
    try:
        if "revision_hash" in arguments:
            row = database.execute("SELECT * FROM revisions WHERE project=? AND candidate_id=? AND revision_hash=?",
                                   (project_id, arguments["candidate_id"], arguments["revision_hash"])).fetchone()
        else:
            row = database.execute("SELECT r.* FROM heads h JOIN revisions r ON r.revision_hash=h.revision_hash WHERE h.project=? AND h.candidate_id=?",
                                   (project_id, arguments["candidate_id"])).fetchone()
        if row is None:
            raise ContractError("candidate revision not found in configured project")
        candidate = json.loads(row["candidate_json"])
        expected = digest({"project_id": project_id, "candidate_id": arguments["candidate_id"],
                           "parent_hash": row["parent_hash"], "candidate": candidate})
        if row["revision_hash"] != expected:
            raise ContractError("stored candidate integrity check failed")
        return {"project_id": project_id, "candidate_id": arguments["candidate_id"], "revision_hash": expected,
                "parent_hash": row["parent_hash"], "candidate": candidate, "created_at": row["created_at"],
                "source_check": json.loads(row["check_json"]), "freshness": "not_revalidated",
                "canon_promoted": False, "semantic_truth_verified": False}
    finally:
        database.close()


def call_tool(name, arguments):
    validate(arguments, next(item["inputSchema"] for item in TOOLS if item["name"] == name))
    try:
        return {"world_candidate_save": save, "world_candidate_read": read}[name](arguments)
    except (sqlite3.Error, OSError) as exc:
        raise ContractError("candidate store unavailable; no successful save is claimed") from exc
