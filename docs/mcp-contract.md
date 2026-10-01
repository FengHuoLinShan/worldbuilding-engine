# 通用世界观 MCP 0.8.0

## 开始一次写作

1. 宿主读取获授权的资料，给每份来源固定 `id/project_id/title/text/kind/status/visible_to`；通过内联来源传入，不提供任意路径。
2. 使用 `world_evidence_search` 提名来源，再用 `world_context_packet` 明确 `selected_ids/excluded_ids`、视角与必需项。`required_ids` 省略时全部选中项均为必需；reader/character 必须给章与 Unicode offset 截止，character 还需人物 ID 与来源 `known_by`。
3. 调用 `world_write_packet`，或者同模式的 `worldbuilding_<mode>` MCP prompt；宿主模型执行其 `host_prompt`，输出可读候选并填写返回的 `candidate_contract`。
4. 宿主回读当前原来源，调用 `world_candidate_check`。来源正文、metadata、排除、视角、预算、任务或保护项变化会使旧结果失效；引用必须逐字命中准入来源的 source hash 与零起始 Unicode 码点区间。
5. 启用候选空间后，可用 `world_candidate_save` 保存，`expected_head=null` 仅用于首次创建；后续读取当前 head 再提交新修订。重复请求沿用相同 operation_id 与完整参数，返回原回执。语义裁定与正典采用仍由作者/宿主领域流程处理。

来源 metadata 是宿主声明，hash 证明绑定和漂移，不证明原来源真实性、账户授权或作者采纳。只给了片段就只检查片段；不声称读取了全部作品或应用 Context confirmation。

## 工具与模式

工具的字段、枚举、边界以 `tools/list` 返回的 inputSchema 为准。

| 工具 | 结果与写入边界 |
|---|---|
| world_project_template / world_validate / world_audit / world_route | 现有世界状态模板、结构、真实性证据与 fiction-core 路由；只读计算 |
| world_craft_packet / world_text_surface_audit / world_craft_review_check | 十二面写作分析、表面信号与外部近读完整性；文学裁定仍未完成 |
| worldcheck_status / worldcheck_prepare_review / worldcheck_record_receipt | 显式配置世界书的变化、依赖、审查包与陈旧回执；只写世界书外派生状态 |
| world_evidence_search | 宿主已提供作者资料的字面检索；只返回提名，不自动准入 |
| world_context_packet | 项目/受众/人物/截止/排除/预算，完整条目遗漏与 blocker；只读 |
| world_write_packet | 资料与硬约束、变化义务、正文自由；宿主写作契约，尚未生成正文 |
| world_candidate_check | 候选来源绑定与逐字引文；不验证所有文字都被来源蕴含 |
| world_change_impact | `from=下游,to=上游` 的影响闭包；只基于输入图，循环可终止 |
| world_candidate_save / world_candidate_read | 固定项目本地候选历史、CAS、幂等与精确版本读取；无正典写入/删除 |

写作模式共14类：create_world、extend_world、revise_world、extract_assets、design_character、story_outline、scene_contract、write_scene、review_world、stress_test、forecast、visual_brief、research_brief、reader_rehearsal。
这些模式与现有 fiction-core 工件职责配合；客户端不安装 Skills 也能读取 MCP prompt 完成任务。

## Context 行为

- 每项来源严格属于本次 project_id，重复身份、未知选中/排除、重叠选择和漏选必需项拒绝。
- 作者资料保留事实、理论、信念、规划、历史和提案标签；reader/character 不准入规划、历史快照、提案、研究或非 canon 内容。
- reader/character 必须命中 visible_to；character 还须 known_by。一般来源还需 available_from；明确 public_baseline 可免时间限制，不能绕过受众/人物/来源类别门禁。
- 相同章节中，以 available_from.offset 与 cutoff.offset 比较；这是宿主预先切分的来源可用位置，MCP 不自动识别完整章节中的揭示点。不可把整章的起点当成章中所有事实都已公开。
- 默认 budget_chars=12000，上限200000；预算包括来源标题与正文。必需项优先，条目整体保留或省略；元数据/JSON 开销、宿主指令与模型 token 限制由宿主额外计入。
- 全部输入（包括排除来源的 hash 对应原文）参与 context hash，准入原文才进入 prompt。必需项未准入返回 ready=false；写作接口拒绝继续。
- Context 与引用偏移以 Python Unicode 码点为单位，不是 UTF-8 字节或 JavaScript UTF-16 code unit。

## 候选空间

宿主配置两个环境变量，默认不启用：

```json
{
  "WORLDBUILDING_WORKSPACE": "/absolute/path/to/private-candidates",
  "WORLDBUILDING_PROJECT_ID": "my-world"
}
```

目录须预先存在。只创建一个 `worldbuilding-candidates.sqlite3`；目录由宿主固定，工具不能更换路径或项目。
候选只能 draft/proposed，保存前重算写作包与引文。SQLite 短事务保护 head/CAS/operation 回执，旧修订仅追加。
同内容与同来源的 no_change 保留 revision；operation 重放必须完整参数相同。内容、任务或来源变化均需新 operation。
历史读取只证明已保存记录的完整性，返回 freshness=not_revalidated；继续写作须再提供当前来源。
工作区应保持私有，候选库与 Worldcheck 派生状态都不能加入公共发布包；备份数据库应通过 SQLite backup API。

## Worldcheck 配置与权限

使用宿主 `WORLDCHECK_CONFIG=/absolute/project/.worldcheck.json` 配置现有世界书；schema、依赖和 full gate 见 [Worldcheck 架构](worldcheck-architecture.md)。
首次 baseline 由用户/宿主运行 CLI `worldcheck check --config PATH --full`，MCP 不提供完整门禁命令。
MCP target 为页面引用，禁止 CLI 选项及控制字符，最多512项；review budget 2000～200000。
正文统一为不可信资料；所需证据不能容纳时保留 insufficient-evidence；源码或政策变动会拒绝旧 receipt。
审查回执可以记录 pass/mixed/fail 等审查意见，但不能授权采用正典。

## 协议与分发

本地 stdio，每行一个 JSON-RPC 对象；支持 2024-11-05、2025-03-26、2025-06-18、2025-11-25 协议协商，未知版本协商为2025-11-25。17 tools、14 prompts、2个固定只读 resources。
服务运行使用 Python≥3.10 与 Ruby≥2.6，无第三方 Python 运行依赖。请求每行最多1000000字符，重复 JSON key、非有限数字和错误参数拒绝；通知不触发写操作。
Python 工具使用有界来源与输入；Ruby engine 子进程15秒、Worldcheck60秒、SQLite等待10秒。同步 stdio 不提供并行调用、采样、联网或即时取消；宿主可结束进程并保留已有保存回执。
表面审计只接受已知、有界、有限阈值；缺章记录保留完整区间与总数，显式编号样例最多1000项，避免章号跨度造成无界内存分配。
后续模型能力、资料文件访问、公开 HTTP 鉴权、正典写入、真实文学质量由宿主独立验收。

设计依据：[MCP tools](https://modelcontextprotocol.io/specification/2025-11-25/server/tools)、[lifecycle](https://modelcontextprotocol.io/specification/2025-11-25/basic/lifecycle)、[prompts](https://modelcontextprotocol.io/specification/2025-11-25/server/prompts)。
