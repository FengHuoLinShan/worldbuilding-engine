# 世界观创设引擎

一套面向奇幻、科幻、架空历史与其他叙事世界的通用工具箱。它把灵感、候选设定和既有世界书整理为可追溯、可审查、能收敛的世界观工程，并提供专业视觉概念设计、写作技法蒸馏、候选反向审查和世界书增量门禁。

> A general-purpose toolkit for auditable worldbuilding, candidate review, transferable fiction craft, and content-addressed worldbook checks.

0.8.0 提供一个通用本地 MCP：**17个工具、14个写作/审查提示词、2个契约资源**。
可从内联资料完成检索、知识边界、世界观/人物/故事/场景写作交接、引文检查、候选保存与版本读取；原 Worldcheck、世界状态、技法和概念设计能力保留。
写作由宿主模型完成，无隐藏付费 API、账户密钥或业务数据库依赖；结构/引文检查不会自动采用正典或批准文学质量。

## 包含内容

- `worldbuilding-engine`：世界模型、因果账本、社会再生产、知识边界、正典治理与迭代收敛。
- `world-concept-designer`：从 Production Brief、正典、因果和视觉证据进入参考、方向、空间、图像、审查与生产交接。
- `worldbuilding-candidate-audit`：对尚未被作者采用的对话候选进行证据化反向审查。
- `distill-novel-craft`：从用户合法提供的文本中提炼可迁移机制，并做“问题—策略—代价”功能对照。
- `tools/worldcheck`：显式配置、只读扫描、ReviewPacket/Receipt 与 v2 派生状态。
- Ruby 与 Python MCP 适配器、测试和公共架构文档。

仓库不包含任何作品正文、世界书、研究底本、私有统计、会话记录或项目状态。

## 安装 MCP

下载 [v0.8.0 发布包](https://github.com/FengHuoLinShan/worldbuilding-engine/releases/tag/v0.8.0) 并解压，或克隆固定版本：

```sh
git clone https://github.com/FengHuoLinShan/worldbuilding-engine.git
cd worldbuilding-engine
git checkout v0.8.0
python3 scripts/mcp_config.py
```

需要 Python≥3.10、Ruby≥2.6，二者应在宿主运行环境可用。没有第三方 Python 运行依赖。
把脚本输出的 `mcpServers.worldbuilding-engine` 合并到客户端配置，再重启连接。脚本生成绝对路径，服务可从任意 cwd 启动。
客户端使用 MCP prompts 时，可选择 `worldbuilding_create_world` 等模式，把 `world_write_packet` 同结构参数 JSON 放入 `request_json`；只支持 tools 的宿主直接使用工具即可。

候选保存默认关闭。启用时先创建私有候选目录，再生成指定项目的配置：

```sh
python3 scripts/mcp_config.py --workspace /absolute/private/candidates --project-id my-world
```

世界书检查可追加 `--worldcheck-config /absolute/project/.worldcheck.json`；第一次 baseline 由用户运行 `ruby tools/worldcheck/worldcheck check --config PATH --full`。
源文件检查与候选存储可独立启用；详细工作流、字段与权限见 [MCP 契约](docs/mcp-contract.md)，全部迁移结果见 [能力清单](docs/capability-map.md)。

## 可选 Skills

Codex 可通过本地 marketplace 安装本插件；也可把 `skills/` 下需要的目录链接到 Codex Skill 目录。DSH 直接把同一目录链接到其 Skill 目录，避免维护副本：

```sh
ln -s "$PWD/skills/worldbuilding-engine" ~/.dsh/skills/worldbuilding-engine
ln -s "$PWD/skills/world-concept-designer" ~/.dsh/skills/world-concept-designer
ln -s "$PWD/skills/worldbuilding-candidate-audit" ~/.dsh/skills/worldbuilding-candidate-audit
ln -s "$PWD/skills/distill-novel-craft" ~/.dsh/skills/distill-novel-craft
```

`.worldcheck.json` 属于具体项目，不应提交到本仓库。完整配置与安全边界见 [Worldcheck 架构](docs/worldcheck-architecture.md)。

## 验证

```sh
ruby scripts/test_worldbuild.rb
ruby tools/worldcheck/test_worldcheck.rb
python3 tools/worldcheck/test_mcp_adapter.py
python3 -m unittest discover -s mcp -p 'test_*.py'
python3 scripts/test_bundle.py
# 官方 SDK 仅用于互操作验收，不是服务运行依赖：
uv run --no-project --with 'mcp==2.2.0' --with 'jsonschema==4.26.0' python mcp/verify_sdk.py
```

[五轮迭代证据](docs/iterations-0.8.0.md) 区分合成工程验证与真实模型/文学验收。CI验证 Linux/macOS；Windows 提供路径适配，但本版未实机验收。

## 权利

本仓库未授予开源许可证。详见 [RIGHTS.md](RIGHTS.md)。
