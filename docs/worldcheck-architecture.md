# Worldcheck 架构

Worldcheck 为 Markdown 世界书建立内容寻址的变更审查链：扫描页面与政策文件，比较 v2 checkpoint，按依赖与反向链接生成有预算上限的 ReviewPacket，再验证并记录 ReviewReceipt。它不修改世界书，也不把模型审查视为作者采纳。

## 配置

CLI 必须显式接收 `--config PATH`；MCP 只读取进程环境变量 `WORLDCHECK_CONFIG`，工具参数不能传路径。

```json
{
  "schema_version": 1,
  "project_id": "example-world",
  "content_root": "worldbook",
  "page_globs": ["**/*.md"],
  "policy_files": ["policies/rules.json", "policies/design-principles.json"],
  "dependency_file": "policies/dependencies.json",
  "full_gate": {"argv": ["ruby", "scripts/validate.rb", "--strict"]}
}
```

配置文件所在目录就是项目根。配置内路径必须相对项目根，不得为绝对路径、包含 `..`，也不得通过符号链接越界。`page_globs` 必须非空；`dependency_file` 与 `full_gate` 均可省略。完整门禁用固定 argv 直接执行，不经过 shell，也不接受模型提供命令。

## 数据流

```text
配置 → 页面/政策快照 → v2 checkpoint 对比 → 影响闭包
    → 有界 ReviewPacket → 语义审查 → ReviewReceipt → 新鲜度校验
```

- 页面正文统一标为 `untrusted-worldbook-content`。
- Packet 只含变更、依赖闭包、反向链接、相关政策和既有阻断项。
- required 内容因预算被删减时，Packet 变为 `insufficient-evidence`。
- Receipt 只能引用 Packet 内由 `source_id + content_hash + anchor` 标识的证据。
- Packet 生成后页面或政策变化，Receipt 失效且不推进状态。
- `mixed`、`fail`、`author-required` 形成持续阻断；只有新鲜复核能取代它们。

## 接口

CLI：

```text
worldcheck check  --config PATH [--full] [TARGET...]
worldcheck review --config PATH [--budget-chars N] [TARGET...]
worldcheck review --config PATH --record FILE
worldcheck status --config PATH [TARGET]
```

MCP 工具固定为：

- `worldcheck_status`
- `worldcheck_prepare_review`
- `worldcheck_record_receipt`

MCP 不提供文件浏览、完整门禁或世界书写入工具。

## 状态与安全边界

派生状态默认位于用户应用数据目录的 `worldcheck/<project_id>/`，不进入世界书。状态 schema 为 v2，旧版本被明确拒绝，不隐式迁移。扫描前后会重新计算 manifest 与 policy hash；读取期间变化、路径越界、重复标题、非法 target、陈旧 Receipt 和未通过的完整门禁都会阻止 checkpoint 前进。
