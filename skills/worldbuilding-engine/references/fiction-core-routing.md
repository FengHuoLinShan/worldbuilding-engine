# fiction-core 编排与失效路由

## 1. 分工原则

世界观创设引擎是“约束、状态、真实性与编排层”，不复制 fiction-core 的专项创作能力。一次请求可同时触发本技能与一个或多个 fiction-core 技能，但每个工件必须有唯一主要所有权层。

世界层也遵守唯一所有权：引擎负责种子契约、权威与真实性门；`world-architect` 负责完整世界工件。`seed` 档的最小候选可由引擎直接完成；`candidate`／`instance` 档采用“引擎设门 → world-architect 主写 → 引擎复审”，不得并行生成两份竞争版本。

`distill-novel-craft` 是横向研究／顾问层：它拥有范例作品近读、同功能名著对照和可迁移 `technique_card`，不拥有用户项目的世界、人物、故事、细纲或正文。诊断用户自己的稿件时，`story-editor` 拥有 finding 与返修归因，`distill-novel-craft` 只提供比较证据。

## 2. 六层所有权

| 层 | 主要所有者 | 负责内容 | 进入条件 |
|---|---|---|---|
| world | `fiction-core-zh:world-architect` | 本体、地理、文明、制度、经济、日常与后果 | 种子、约束与权威边界明确 |
| character | `fiction-core-zh:character-architect` | 欲望、需要、误信、恐惧、关系、能动性、知识边界与角色弧 | 世界压力足以塑造选择 |
| story | `fiction-core-zh:story-architect` | premise、中央问题、目标、对抗、因果链、转折、危机、高潮和结局 | 世界与主要人物过门 |
| outline | `fiction-core-zh:outline-planner` | 分卷、章节、场景、Beat、信息释放与 Scene Contract | 故事架构被确认 |
| prose | `fiction-core-zh:scene-prose-writer` | 场景、章节、过渡、改写与行文精修 | Scene Contract、连续性和知识边界有效 |
| editor | `fiction-core-zh:story-editor` | architecture、developmental、scene、reader、line、copy、continuity 单一模式审查 | 有明确审查对象和模式 |

## 3. 默认顺序与可跳过条件

```text
world gate → character gate → story gate → outline/Scene Contract gate → prose gate
      ↘ editor 可在任一工件后审查，并把问题送回拥有者
```

如果用户只审查世界设定，可停在 world；如果已有已确认人物与故事，可读取其状态后从 outline 或 prose 开始。不得因为用户说“直接写”就忽略已知硬约束和角色知识边界。

## 4. 路由决策

按第一个未过门的层路由：

0. 用户要求研究范例写法、蒸馏技法或名著对照：`distill-novel-craft`；若要迁移进项目，再回到下列实际工件所有者；
1. 状态结构错误、权威混乱、依赖断裂：`worldbuilding-engine`；
2. 核心规则、地区、制度或社会真实性不闭合：`world-architect`；
3. 世界可用但人物没有能动性、知识边界或关系压力：`character-architect`；
4. 人物可用但故事缺因果、转折、风险或结局选择：`story-architect`；
5. 架构已确认但没有可写 Scene Contract：`outline-planner`；
6. Scene Contract 有效且用户要正文：`scene-prose-writer`；
7. 用户要求审查，或下游问题来源不明：`story-editor`，一次只选一种模式。

## 5. 失效矩阵

| 变更所有者 | 必查下游 | 默认动作 |
|---|---|---|
| world | character、story、outline、prose | `needs-review`；若硬规则冲突则 `invalidated` |
| character | story、outline、prose | 检查目标、选择、关系和知识边界 |
| story | outline、prose | 重大转折／结局变化通常 `invalidated` |
| outline | prose | 对应 Scene Contract 变化则重写相关场景 |
| prose | 无自动上游变更 | 仅在审查证据指向上游时回送 |
| editor | 由 finding 的 `owner_layer` 决定 | 不能用行文补丁掩盖架构或世界问题 |

## 6. 上下文包

路由给专项技能时，只传它需要的最小充分上下文：

- `canon_refs`：已确认来源；
- `proposals`：候选及状态；
- `constraints`：硬边界与不可行域；
- `knowledge_boundaries`：人物与读者边界；
- `continuity_state`：时间、地点、资源、关系、伤势、秘密；
- `invalidations`：上游变化和待复核工件；
- `acceptance`：本轮验收标准；
- `technique_cards`：已达到证据门、且剥离范例作品专属外壳的顾问材料；
- `variation_obligations`：相邻章节必须变化的人物声线、冲突载体、节奏、感官中心和结束形态；
- `prose_freedoms`：不改变硬事实时可由正文所有者自由决定、无须逐项解释的实现空间；
- `expression_budget`：原则完整解释、旁白复述和清单朗读的项目预算。
- `resolution_brief`：仅在复杂概念、历史分叉、相似体系或认知误读会改变设计时传递概念边界、历史分层、关系裁定与认知生态；简单任务省略。

不要把整座 Vault 无差别塞进每一层。

## 7. 编辑返修归因

每条 finding 至少标：

- `owner_layer`；
- `evidence`；
- `impact`；
- `repair_scope`；
- `canon_risk`；
- `downstream_invalidations`。

例：角色在正文里准确说出作者层真相，表面是台词问题，所有者可能是 prose；若整份细纲都把该真相当成公开知识，所有者是 outline 或 world 的知识边界。

若使用 MCP 辅助正文审查，`world_craft_packet` 的十二面与五个诊断镜头初始均为 `unassessed`，不能作为通过证据；`world_text_surface_audit` 只提供需要近读的表面信号。`story-editor` 填写 finding 后，`world_craft_review_check` 只检查覆盖与字段完整性；其 `ready_for_host_decision` 不是文学 PASS，最终裁定必须由宿主保存证据、范围和正文哈希。

## 8. 标准 handoff

调用 fiction-core 技能后，保留其标准交接信息，并补充引擎状态：

```yaml
handoff:
  from_skill: worldbuilding-engine
  to_skill: fiction-core-zh:world-architect
  task: expand
  state_file: path/to/world-state.json
  canon_refs: []
  proposal_refs: []
  constraints: []
  knowledge_boundaries: []
  resolution_brief:
    concept_boundaries: []
    historical_layers: []
    relation_verdicts: []
    epistemic_ecology: []
  invalidated_layers: []
  acceptance:
    - 因果账本闭合
    - 候选与正典分离
    - 完成真实性审计
```

专项技能完成后应把新工件、状态、未决项和失效关系写回项目状态或明确交给下一个技能。

`resolution_brief` 是 skill-level handoff，不写入 `world-state` schema，也不要求 CLI／MCP 解析。上游 World Architect 的对应修改规范见 [World Architect vNext 上游补丁规范](world-architect-v-next-patch.md)。
