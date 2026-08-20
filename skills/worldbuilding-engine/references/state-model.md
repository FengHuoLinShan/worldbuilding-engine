# 世界观工程状态模型

## 1. 双层产物

每个项目同时保留两类产物：

1. **机器状态**：`world-state.json`，保存权威、规则、覆盖、证据、依赖、失效和 fiction-core 阶段；
2. **人类文档**：Wiki、设定集、审计报告、变更记录、人物卡、故事纲要和正文。

机器状态不是正典正文，正文也不能替代状态。二者通过 `artifacts`、`sources` 和 `evidence` 相互指向。

## 2. 权威状态

| 状态 | 含义 | 谁可推动 |
|---|---|---|
| `draft` | 工作草稿，尚未形成稳定候选 | 模型或用户 |
| `proposed` | 已闭合到可审查程度，但不是正典 | 模型提出，用户审查 |
| `canon` | 用户或项目授权流程已明确采纳 | 仅显式授权 |
| `author-required` | 涉及不可代理的核心决定 | 用户本人 |
| `deprecated` | 曾使用但已被替代，保留历史 | 授权变更流程 |

不允许通过“写得很完整”把 `proposed` 自动升为 `canon`。

### 2.1 持久化范围是独立轴

权威状态不决定内容能否写入文件。持续项目可在 `extensions.iteration.persistence_scope` 记录：

- `conversation-only`：只在对话中工作；
- `candidate-files`：可写项目允许的候选页与变更记录，但不得晋升正典；
- `canon-files`：仅在明确采纳和项目协议授权后写正典面。

“无需每轮确认，暂不写正史”通常是 `candidate-files`。这不会改变任何条目的 `proposed`／`author-required` 状态。

## 3. 覆盖状态

| 状态 | 含义 |
|---|---|
| `gap` | 没有回答，或没有可追溯证据 |
| `partial` | 有结构或片段，但链条未闭合 |
| `covered` | 当前范围内已闭合并有证据 |
| `not-applicable` | 对当前范围确实不适用，必须写理由 |

压力测试另用 `not-run`、`pass`、`mixed`、`fail`。fiction-core 阶段使用 `not-started`、`ready`、`in-progress`、`valid`、`needs-review`、`invalidated`、`blocked`。

## 4. 顶层结构

`world-state.json` 的权威机器定义见 `world-state.schema.json`。顶层分区如下：

| 区域 | 作用 |
|---|---|
| `project` | 标题、种子、语言、模式、版本与时间 |
| `authority` | 事实源、只读区、约束、锁定决策、作者必决与开放问题 |
| `premise` | 核心差异、体验承诺、尺度、审美外衣与主题候选 |
| `knowledge_layers` | 作者真相、专家模型、公众信念、读者未知 |
| `rules` | 可行／不可行、账本、故障、维护、反制、权限与依赖 |
| `reproduction_loops` | 六个社会再生产循环 |
| `facets` | 二十二面，分别记录通用框架与具体实例成熟度 |
| `coupling_chains` | 权利、技术、身份、证据、分配五链 |
| `situated_tests` | 普通日、七日故障、一生、十年反馈 |
| `pressure_tests` | 十二项反事实测试 |
| `actors`／`places`／`institutions`／`history` | 可寻址的世界实体与事件 |
| `fiction_core` | 世界、人物、故事、细纲、正文、编辑六阶段状态 |
| `dependencies` | 工件之间的要求、告知、冲突与派生关系 |
| `change_log` | 变更、来源、理由、失效与授权 |
| `audit` | 最近一次确定性审计摘要 |

## 5. 标识与引用

- 所有规则、实体、事件和依赖目标使用项目内稳定 ID；改名不改 ID。
- `dependencies.from` 和 `dependencies.to` 必须指向已存在的 ID 或已登记工件路径。
- `evidence` 可写 WikiLink、绝对或项目相对路径、条款 ID、测试 ID，不可只写“见设定”。
- 相同 ID 不得重复；废弃对象保留为 `deprecated`，不要复用其 ID。

推荐前缀：`RULE-`、`ACT-`、`PLC-`、`ORG-`、`HIS-`、`ART-`。项目可替换，但须一致。

## 6. 变更失效传播

变更按所有权层向下传播：

```text
world → character → story → outline → prose
                    ↘ editor 可把问题回送到任一所有权层
```

最小规则：

- 世界规则、历史、制度或知识边界变化：人物、故事、细纲、正文都至少 `needs-review`；
- 人物欲望、误信、秘密、关系或知识边界变化：故事、细纲、正文 `needs-review`；
- 故事因果、转折或结局变化：细纲、正文 `invalidated` 或 `needs-review`；
- Scene Contract 变化：对应正文 `invalidated`；
- 正文问题只有在证据指向上游时才升级，不能为修一句话随意改世界宪法。

每次传播写入 `change_log.invalidated_layers` 与各阶段的 `invalidated_by`。

## 7. 操作语义

### `init`

创建最小状态。只记录用户原始种子，不自动生成正典。

### `validate`

检查 JSON 结构、枚举、必需字段、ID 唯一性、依赖引用、状态与证据的基本一致性。它不判断文学质量。

### `audit`

基于已记录证据检查：规则账本、六环、二十二面、五链、情境证据、压力测试和 fiction-core 就绪度。输出缺口而非“真实度百分比”。

状态文件尚不存在时，宿主可用相同字段做人工语义审计，并记录 `machine_audit: not-run`；一次性灵感探索不需要为了运行命令而创建持久文件。

若存在 `extensions.iteration`，`audit` 还会报告轮次、检查点是否到期、当前纵切和框架／实例饱和差。该结果只是工作节律建议，不会自动写文件或运行项目验证器。

### `route`

选择当前唯一主要所有权层。存在结构错误时先回本引擎；世界层未过门时不得直接路由正文。

### `invalidate`

登记上游变更并按规则修改下游状态。写操作必须保留旧状态摘要和原因。

### `promote`

框架 `0.3` 不提供无人值守晋升。项目必须通过用户授权和自己的正典协议完成。

## 8. 建议目录

```text
world-project/
├── world-state.json
├── PROJECT.md
├── canon/
├── proposals/
├── audits/
├── characters/
├── story/
├── outlines/
└── prose/
```

已有 Vault 或仓库不必迁移到此结构；只需在状态中记录适配路径。

## 9. 一致性不变量

1. `canon` 条目必须有显式来源或变更记录证据；
2. `covered` 与成熟度大于 0 必须有证据或具体说明；
3. `not-applicable` 必须有理由；
4. 核心规则必须同时具有 capability 与 impossibility；
5. 可重复能力若没有成本、失败和维护，审计不得判为闭合；
6. 具体实例成熟度不能高于其有证据支持的层级；
7. 上游失效时，下游不能保持未经复核的 `valid`；
8. 作者必决项不得由自动化删除或静默回答；
9. 机器审计结果不得被写成世界内角色可见事实；
10. 所有自动生成内容保留 `draft`／`proposed` 状态和来源。

## 10. 版本迁移

`schema_version` 与 `engine_version` 分开：前者描述数据形状，后者描述审计算法。字段变更必须提供向前迁移；审计规则变化必须允许同一状态在新版重新计算，而不篡改旧审计记录。
