---
name: world-concept-designer
description: 将小说、世界书或正典资料转化为可验证、可迭代、可交接的世界观概念设计，用于地图、环境、城市、建筑、基础设施、物质文化、Visual Bible 与剧情 Keyframe。适用于需要从 Design Question、因果和视觉证据出发完成参考研究、方向探索、图像生成、审查或概念包的任务；普通插画润色、无世界设计目标的生图或自动正典写入不适用。
---

# World Concept Designer

把世界资料转成能回答设计问题、服务后续生产的视觉工件。概念图不是正典，也不是仅供欣赏的插画；它必须说明对象为何如此形成、怎样工作、如何被使用和维护。

## 按需读取

- 执行 `explore`、`develop`、`review` 或 `package` 时，读取 [references/workflow.md](references/workflow.md)。
- 先读取用户提供的附件、项目规则、实时 Vault／Wiki／仓库及既有视觉资产；同步镜像不能替代项目指定的当前事实源。
- 需要补写缺失世界设定时交给 `fiction-core-zh:world-architect`；需要管理来源、权威状态、依赖、失效或正典晋升时交给 `$worldbuilding-engine`。

## 模式

- `explore`：建立 Production Brief、正典提取、参考板、因果链、Visual Bible 切片和方向探索。边界不清时默认此模式。
- `develop`：从已锁定方向进入空间／功能验证、镜头、Look Development、Prompt、图像生成和单点迭代。
- `review`：只审查已有图像或概念包；除非用户明确要求，不生成或修改图像。
- `package`：整理已选资产、审查结果、Prompt、生产交接和候选正典反馈，不补造缺失成果。

用户说“先讨论”“先看提示词”或同义表达时，停在对应工件，不调用图像工具。

## 交付档位

- `exploration`：参考板、方向族和 thumbnail。
- `visual-bible`：可复用的形状、尺度、材料、老化、工程和禁用语法。
- `keyframe`：镜头、人物行为、光照、叙事功能和视觉证据。
- `production-handoff`：经核验的比例、平剖面／正交视图、材料与功能 Callout。

成熟度只写入 Markdown 概念包：

```text
exploration -> direction-locked -> spatially-verified -> production-handoff
```

AI 成图默认最多为 `direction-locked`。地图坐标、尺度、流线、精确文字、正交结构或透视关键设计，必须有人工测量、确定性图纸或真实 3D／greybox 证据才能继续晋级。

## 不变量

1. **先 Brief，后设计**：明确用途、下游接收者、交付物、完成度、审批人、修改预算和验收条件；不从“画一个……”直接跳到 Prompt。
2. **先权威，后推导**：区分 `Hard Canon`、`Visual Requirement`、`Derived Constraint`、`Unknown`、`Forbidden`，保留每条来源与原状态。
3. **每轮研究**：默认在线检索现实机制并记录来源、适用范围、权利风险和不得复制之处。用户禁止联网时写 `research: user-supplied-only`；联网不可用时写明阻塞，不伪造研究。
4. **一图一问**：一张工作卡只解决一个主要 Design Question，最多三个次要问题。
5. **先结构，后完成度**：重要设计先做方向族和低成本 thumbnail，再做空间、功能、镜头、材质和光照。
6. **现实机制，不复制造型**：参考用于解释地理、结构、材料、劳动、维护和行为，不用于拼贴受保护的独特设计。
7. **视觉必须举证**：每条重要设定都要有删除说明文字后仍可看到的物理或行为证据。
8. **空间验证不冒充**：AI 伪正交图、透视插画或文字自洽不能替代图纸、测量或 3D blockout。
9. **图像非破坏迭代**：每轮只修一个明确问题，保留原图并使用递增版本名；不以“更宏伟、更电影感、更多细节”掩盖结构错误。
10. **Visual Read 必须独立**：由用户或未读取说明的独立审查者完成；未执行写 `not-run`，当前代理不得自称盲测通过。
11. **AI 不晋升正典**：新内容只能是 `visual-placeholder`、`candidate-canon` 或 `rejected`；只有用户明确采纳的原子主张才能交给正典流程。
12. **无图像工具也要可交接**：输出相同 Brief、参考账、视觉证据、镜头、Prompt、禁用项和审查清单，不假装已经生图。

## 执行顺序

1. 建立 Production Brief 和权威边界。
2. 完成 Reference Gate，并锁定正向／负向参考。
3. 建立因果链、Visual Bible 切片和方向评分，锁定设计方向。
4. 按资产类型完成空间／功能验证；证据不足时降低成熟度并给出外部 blockout 交接。
5. 方向锁定后才生成 contact sheet、结构稿、Look Development 或 Keyframe；用宿主图像工具逐项执行并检查。
6. 完成 Canon、Logic、Design、Visual Read、Genericness、Continuity、Production 和 Reference Rights Review。
7. 保存概念包、版本化图像和候选正典反馈；正典写入保持为用户明确授权后的独立操作。

## 交付

项目有既定输出规则时遵循项目规则；否则项目型成果放在：

```text
deliverables/concept-design/<slug>/
|-- concept-package.md
`-- images/
    `-- <asset>-vNN.<ext>
```

预览或讨论任务可以只在对话中交付。最终说明本轮模式、交付档位、成熟度、研究状态、实际图像路径、未通过门禁、候选正典和下一步唯一最高收益动作。
