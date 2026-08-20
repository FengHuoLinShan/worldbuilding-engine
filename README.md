# 世界观创设引擎

一套面向奇幻、科幻、架空历史与其他叙事世界的通用工具箱。它把灵感、候选设定和既有世界书整理为可追溯、可审查、能收敛的世界观工程，并提供写作技法蒸馏、候选反向审查和世界书增量门禁。

> A general-purpose toolkit for auditable worldbuilding, candidate review, transferable fiction craft, and content-addressed worldbook checks.

## 包含内容

- `worldbuilding-engine`：世界模型、因果账本、社会再生产、知识边界、正典治理与迭代收敛。
- `worldbuilding-candidate-audit`：对尚未被作者采用的对话候选进行证据化反向审查。
- `distill-novel-craft`：从用户合法提供的文本中提炼可迁移机制，并做“问题—策略—代价”功能对照。
- `tools/worldcheck`：显式配置、只读扫描、ReviewPacket/Receipt 与 v2 派生状态。
- Ruby 与 Python MCP 适配器、测试和公共架构文档。

仓库不包含任何作品正文、世界书、研究底本、私有统计、会话记录或项目状态。

## 安装

```sh
git clone https://github.com/FengHuoLinShan/worldbuilding-engine.git
cd worldbuilding-engine
```

Codex 可通过本地 marketplace 安装本插件；也可把 `skills/` 下需要的目录链接到 Codex Skill 目录。DSH 直接把同一目录链接到其 Skill 目录，避免维护副本：

```sh
ln -s "$PWD/skills/worldbuilding-engine" ~/.dsh/skills/worldbuilding-engine
ln -s "$PWD/skills/worldbuilding-candidate-audit" ~/.dsh/skills/worldbuilding-candidate-audit
ln -s "$PWD/skills/distill-novel-craft" ~/.dsh/skills/distill-novel-craft
```

Worldcheck MCP 需要由宿主固定配置文件位置：

```sh
codex mcp add --env WORLDCHECK_CONFIG=/path/to/project/.worldcheck.json \
  worldcheck -- "$PWD/tools/worldcheck/mcp_adapter.py"
```

`.worldcheck.json` 属于具体项目，不应提交到本仓库。完整配置与安全边界见 [Worldcheck 架构](docs/worldcheck-architecture.md)。

## 验证

```sh
ruby scripts/test_worldbuild.rb
python3 mcp/test_server.py
ruby tools/worldcheck/test_worldcheck.rb
python3 tools/worldcheck/test_mcp_adapter.py
```

## 权利

本仓库未授予开源许可证。详见 [RIGHTS.md](RIGHTS.md)。
