# 专业世界观概念设计工作流

本参考定义四种模式共用的门禁、工作卡和交付格式。按任务所需读取相关章节，不要求每轮生产所有资产。

## 1. 路由与最小生产单位

默认单位是一张工作卡：一个主要 Design Question、一个交付档位、一组有共同空间和规则分母的资产。不要以“一次画完整个国家／世界”为单位。

| 用户目标 | 模式 | 默认停止点 |
|---|---|---|
| 讨论方向、建立视觉规则 | `explore` | Direction Gate |
| 完成一张或一组概念图 | `develop` | Image Production / Review |
| 核对已有图像 | `review` | Review Report |
| 整理可交接成果 | `package` | Concept Package |

若用户明确要求端到端完成，可由代理选择推荐方向并继续，但必须记录 `approval: agent-selected`、理由和未由用户确认的风险。正典晋升不能代理批准。

## 2. Gate 0：Production Brief

开始研究或生图前填写：

```markdown
## Production Brief

- mode: explore | develop | review | package
- delivery_profile: exploration | visual-bible | keyframe | production-handoff
- current_maturity: exploration | direction-locked | spatially-verified | production-handoff
- design_question:
- secondary_questions: []
- purpose:
- audience:
- downstream_receiver: author | art-direction | visual-bible | 3d | layout | marketing | other
- asset_scope:
- quantity_and_variants:
- required_views:
- finish_level: thumbnail | structural | polished-concept | production-reference
- dimensions_or_aspect:
- file_formats:
- deadline_or_stop_condition:
- approval_owner:
- feedback_format:
- revision_budget:
- acceptance_criteria: []
```

没有商业 deadline、预算或团队时，不把字段变成问卷。使用默认值：单卡、低成本探索、用户为审批人、一次方向修正加一次定向修正、沿项目惯例保存。

### 2.1 Design Question

错误：“画一座河港城。”

正确：“怎样通过道路、码头、仓储和维修痕迹，让观察者看出这座城市长期适应迁移河道？”

每个验收条件必须能回指 Design Question 或下游生产需要。

### 2.2 正典提取

只提取会改变本轮设计的内容：

| 类别 | 含义 | 处理 |
|---|---|---|
| Hard Canon | 已确认、不能擅改 | 必须满足并附来源 |
| Visual Requirement | 必须被看见的正典信息 | 转成物理／行为证据 |
| Derived Constraint | 从规则必然或高概率推出 | 标来源规则与推理 |
| Unknown | 尚未确定 | 允许探索，保持候选 |
| Forbidden | 禁止出现 | 写入负向参考和 Prompt Avoid |

遇到冲突时暂停该项设计，按项目权威顺序交给 `$worldbuilding-engine`；不要用画面替用户裁定。

## 3. Gate 1：Reference Gate

每轮至少完成一次与 Design Question 直接相关的在线检索。只收集解决机制缺口所需的资料，不按固定数量堆参考。

### 3.1 研究路由

- 地理：水文、地质、海岸、湿地、坡地、气候和灾害。
- 聚落：道路、密度、地形适应、叠建、边界和土地使用。
- 工程：桥、港、渠、矿井、维护、排水、能源和故障。
- 社会生活：生产、搬运、仓储、照护、市场、家庭和规避行为。
- 材料：来源、加工、连接、受力、风化、维修和再利用。

### 3.2 Reference Ledger

```markdown
## Reference Ledger

| Source | Type | Mechanism learned | Applies to | Positive / Negative | Rights/use note | Do not copy |
|---|---|---|---|---|---|---|
```

优先原始、官方、技术或专业从业者来源。保存链接和机制摘要；除非用户已提供并拥有使用权，不复制原图进入公共包。没有可用来源时保留 `research_gap`。

### 3.3 Reference Board Lock

参考板至少区分：

- 正向：结构、比例、材质、光照或行为中需要学习的部分；
- 负向：常见套路、错误技术水平、错误材质、无功能奇观或不适合的完成度；
- 世界专属：已有 Visual Bible、地图、建筑、道具和角色尺度锚点。

进入 Direction Gate 前记录 `reference_gate: approved | agent-selected | blocked`。

## 4. Gate 2：Design Direction Gate

### 4.1 因果链

从世界规则向可见痕迹传导：

```text
世界规律
-> 地质／水文／气候／异常
-> 资源与不可行域
-> 生产与维护
-> 交通与聚落
-> 经济、制度与分配
-> 建筑、工具与服饰
-> 日常行为
-> 磨损、补丁、废弃和历史层
```

每个重要视觉元素都要能回指链上节点。仅用“文化风格”解释造型视为未完成。

### 4.2 Visual Bible 切片

只写本轮需要新增或调用的规则：

```markdown
## Visual Bible Slice

- visual_thesis:
- shape_language:
- scale_language:
- material_grammar:
- aging_grammar:
- engineering_logic:
- color_sources:
- forbidden_imagery:
- continuity_anchors:
```

色彩来自材料、气候、染料、工业、身份和光照条件，不以“每国一个主题色”代替设计。

### 4.3 方向与 Thumbnail

- 重要新设计：3—5 个方向族，总计约 12—30 个低成本 thumbnail；可用一张或少量 contact sheet 承载。
- 普通变体或返修：3—5 个 thumbnail 即可。
- 初期只看 silhouette、massing、空间关系、比例、值域、焦点和信息层级。
- 不在方向锁定前投入精致材质、面部、纹饰、电影光效或高分辨率。

方向评分：

| Criterion | Question |
|---|---|
| Canon | 是否满足 Hard Canon 与 Forbidden？ |
| Design | 是否回答主要 Design Question？ |
| Evidence | 删除文字后能否读出关键设定？ |
| Feasibility | 是否可建造、使用、维护或交给下游？ |
| Continuity | 是否继承既有视觉语法？ |
| Genericness | 替换名称后是否仍只是常见类型？ |

保存推荐方向、淘汰方向和理由。进入高完成度生产前记录 `direction_gate: approved | agent-selected | blocked`。

## 5. Gate 3：Spatial / Functional Gate

### 5.1 地图、环境、城市与建筑

至少验证与任务有关的：

- 俯视平面和垂直剖面；
- 人体、住宅、公共设施、巨构和自然环境的尺度链；
- 道路、入口、装卸、疏散和视线；
- 水流、排水、物流、能源、废弃物和维修通道；
- 前中后景与摄影机位置；
- 模块化、重复件、年代层和更换方式。

### 5.2 建筑、道具、载具与基础设施

按下游需要提供：

- front / side / back / top / three-quarter 视图；
- 尺度参照和关键尺寸；
- 材料区、连接、受力、开合、活动状态和维修口；
- 正常、损坏、维护或历史版本差异；
- 功能 Callout 和不可见内部结构的说明。

### 5.3 证据等级

| Evidence | 允许成熟度 |
|---|---|
| 文字、AI 插画或伪正交图 | `direction-locked` |
| 可核对的平面、剖面、尺寸和流线 | 可记录 `design-verified-2d`，但不改正式成熟度链 |
| 真实 3D／greybox、测量或确定性图纸 | `spatially-verified` |
| 下游所需视图、格式和 Callout 全部核验 | `production-handoff` |

缺少 3D 工具时输出 Blockout Brief：单位、坐标约定、主要体块、尺寸、坡度／高差、流线、相机、必须验证项和禁止脑补项。不得提高成熟度。

## 6. Shot、Visual Evidence 与 Prompt

### 6.1 Shot Card

```markdown
## Shot Card

- narrative_function:
- viewer:
- camera_height:
- lens_or_projection:
- horizon:
- direction:
- foreground_scale_anchor:
- midground_action:
- background_world_information:
- primary_read:
- secondary_read:
- third_read:
- weather_time_light:
```

### 6.2 Visual Evidence

每条重要设定回答：“如果删除所有说明文字，画面中的什么能证明它？”证据优先落到结构、流线、劳动、维护、磨损、补丁、废弃、权限和普通人行为。

### 6.3 Prompt 结构

只有 Direction Gate 通过后才写完整 Prompt：

```text
Use case / Asset type
Design Question and selected direction
Camera / projection
Large spatial structure
Foreground / midground / background
People and observable behavior
Visual evidence
Architecture / materials / aging
Weather / time / lighting
Style and finish level
Exact text, if unavoidable
Constraints / Avoid
```

把设定翻译为可画的物理事实，不把世界书全文塞进 Prompt。需要精确文字、地图标签或尺寸时，生成后必须逐项核对；不可靠时改为后期排版交接。

## 7. Image Production

Codex 默认使用内置图像工具；其他宿主使用可用工具或降级为 Prompt 包。

```text
reference board
-> thumbnail/contact sheet
-> selected structural draft
-> spatial evidence or blockout handoff
-> look development
-> low-cost image
-> structural review
-> one targeted correction
-> final concept
-> optional external paintover/retouch
```

- 每项资产或变体单独执行，避免用同一 Prompt 假装不同资产。
- 编辑时重复不变量，只修改一个目标。
- 先检查主体、构图、结构、文字、比例、视觉证据和禁用项，再谈完成度。
- 不覆盖已有文件；使用 `<asset>-v01`、`v02` 等递增命名。
- 项目使用的最终图像必须进入项目工作区；预览图可留在宿主默认目录。

## 8. Gate 4：Review

| Review | 必须回答 |
|---|---|
| Canon | 是否违背来源状态、地理、制度或 Forbidden？ |
| Logic | 地理、流线、结构、生产、维护和行为是否成立？ |
| Design | Design Question 是否被视觉回答？ |
| Visual Read | 不看说明的独立观察者实际读出了什么？ |
| Genericness | 是否退化为可替换名称的常见类型？ |
| Continuity | 形状、尺度、材料、技术、服饰与既有资产是否一致？ |
| Production | 视图、尺寸、格式、命名和下游需要是否满足？ |
| Reference Rights | 来源、使用权、引用和不可复制边界是否清楚？ |

每项记录 `pass | revise | blocked | not-run`、证据和下一项单点修正。Visual Read 只有独立观察结果才能 `pass`。

## 9. Concept Package

默认只建立一个 Markdown 总包：

```markdown
# Concept Package: <title>

## Status
## Production Brief
## Authority and Canon Extraction
## Reference Ledger and Board Decision
## Causal Model
## Visual Bible Slice
## Direction Exploration and Decision
## Spatial / Functional Evidence
## Shot and Visual Evidence
## Final Prompts
## Asset Manifest
## Reviews
## Canon Feedback
## Open Risks and Next Action
```

### 9.1 资产菜单

按交付档位选择，不强制全做：

- A Hero Establishing Shot
- B Map / Plan
- C Section
- D Architecture Callout
- E Infrastructure Callout
- F Material Sheet
- G Prop Sheet
- H Daily-life Keyframe
- I Weather Variant
- J Historical Layer Diagram
- K Scale Sheet

`exploration` 通常只需参考板、contact sheet 和方向决定；`visual-bible` 选择可复用语法资产；`keyframe` 选择镜头与叙事证据；`production-handoff` 由下游接收者决定必需视图和格式。

### 9.2 Canon Feedback

```markdown
## Canon Feedback

### visual-placeholder
- claim:
  source_asset:
  reason:

### candidate-canon
- atomic_claim:
  evidence:
  affected_downstream:
  decision_needed:

### rejected
- claim:
  reason:
  avoid_in_future:
```

图像中的重复元素、颜色、地名、尺寸、机构、人物或工程结构不会因“看起来合理”自动进入正典。用户明确批准后，才将被点名的原子主张交给 `$worldbuilding-engine` 和项目写入流程。
