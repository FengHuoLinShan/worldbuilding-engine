# 小说技法工作流

把“研究所有写作方面”变成有限的覆盖图、四条任务流程和可检查的交付物。不要一次审完所有层；先选主问题，再沿依赖扩展。

## 导航

- [十二层覆盖图](#十二层覆盖图)
- [按需加载](#按需加载)
- [证据与优先级](#证据与优先级)
- [流程一：蒸馏已有作品](#流程一蒸馏已有作品)
- [流程二：分析局部](#流程二分析局部)
- [流程三：规划原创](#流程三规划原创)
- [流程四：诊断与改稿](#流程四诊断与改稿)
- [反过拟合与反表面仿写](#反过拟合与反表面仿写)
- [交付门槛](#交付门槛)

## 十二层覆盖图

沿用 [craft-atlas.md](craft-atlas.md) 的十二层；完整定义和机制只在该文件维护。覆盖时称“检查面”，安排深审和根因依赖时称“层”，两者指同一组十二项。此表只用于定范围和修订依赖，不得因遇到新现象临时增加“第十三层”。

| 层 | 检查面 | 本层最小产出 |
|---|---|---|
| 1 | 创作契约 | 目标读者、载体、类型承诺、硬约束 |
| 2 | 表达与主题 | 主题问题、价值张力、拒绝给出的简单答案 |
| 3 | 全书与分部结构 | 中央因果、阶段变化、高潮与结局承诺 |
| 4 | 因果与对抗 | 目标、行动、反制、代价、不可逆后果 |
| 5 | 人物与关系 | 欲望、知识边界、选择、关系变化、人物弧 |
| 6 | 视角与信息 | POV、读者所知、悬念、揭示、伏笔与回收 |
| 7 | 世界与社会 | 规则及其制度、经济、历史、日常后果 |
| 8 | 场景与节奏 | 进入状态、目标、策略、转折、退出状态 |
| 9 | 对话与行动 | 话语/行动策略、潜台词、规则运用、可见后果 |
| 10 | 情绪与氛围 | 建立、侵入、转向、释放、余波 |
| 11 | 语言与意象 | 叙述声音、句段、具体性、意象、重复与 copy |
| 12 | 连载、连续性与修订 | 单章闭合、追读压力、状态一致、修订顺序 |

默认从上游修到下游。第 3–7 层会互相约束，可来回校正；编号是覆盖顺序，不是僵硬的创作瀑布。规划原创时先让最小世界规则足以约束人物，再锁定人物与故事架构；仍须指定一个主层，避免把一次任务扩成无边界总审。

用户要求“所有方面”时分两遍：第一遍只做十二行浅层覆盖矩阵，标记 `finding / not_applicable / insufficient_evidence` 和优先级；第二遍按优先级逐层深审，每次只设一个主层。停止门在覆盖矩阵完成后才生效。MCP 新建骨架的 `unassessed` 只表示尚未近读，不能参与完成判断。

正文全稿或返修回归还必须检查五个跨层镜头：`domain_term_load`、`negation_template_repetition`、`character_voice_differentiation`、`scene_pattern_variation`、`climax_action_deliberation_balance`。它们分别映射既有世界／语言、对话／语言／修订、人物／对话／语言、场景／修订、结构／因果／场景／情绪，不增加第十三层。表面探针只能提供取样位置，镜头结论必须由近读填写。

```yaml
coverage:
  - layer:
    status: finding | not_applicable | insufficient_evidence
    strongest_evidence:
    priority: critical | high | medium | low | none
    deep_review_needed: true | false
```

## 按需加载

只加载当前判断需要的材料；“可能以后有用”不是加载理由。

| 当前任务 | 加载 | 不加载 |
|---|---|---|
| 跨层定位或查机制定义 | `craft-atlas.md` 的相关小节 | 全部作品证据、全部名著对照 |
| 对指定作品提出具体结论 | 用户提供的合法原文中与问题直接相关的片段 | 小说全文、无关卷次 |
| 与名著作功能对照 | `classic-comparisons.md` 中同功能条目；必要时核对原作 | 只因“有名”而加入的作品 |
| 章长、段落、对话占比等量化问题 | 运行 `scripts/corpus_probe.py`，抽查异常点原文 | 用指标代替节奏或质量判断 |
| 规划原创 | 本文件 + `craft-atlas.md` 的相关机制 | 默认加载参考作品情节和无关案例 |
| 局部诊断 | 目标片段、必要前后文、其上游约束、一个主层 | 结局真相、无关人物档案、十二层全审 |

当前证据足以做出范围内判断时停止加载。只有出现冲突、证据不足或跨层根因时才扩展相邻章节、分部或 reference。

## 证据与优先级

### 证据等级

| 等级 | 要求 | 允许的结论 |
|---|---|---|
| `E3 可迁移` | 目标作品或主语料至少两个相隔位置的原文事实；一个反例、代价或失效处；一部名著的同功能异方法对照 | 条件化技法，可用于原创规划 |
| `E2 局部成立` | 精确位置及必要上下文足以支持该段、该章或该卷的观察；作者自述只能证明其自述意图 | 局部分析或诊断，不外推为普遍规律 |
| `E1 待验证` | 单一例子、摘要、指标、二手评论或尚未核对的作者说法 | 假说和后续取证方向 |
| `E0 印象` | 凭记忆、气氛判断、无位置判断 | 不得进入结论或原创规则 |

等级跟随**结论范围**，不跟随样本篇幅自动升降：短样本若满足 E3 的全部证据门，只能把一个明确限于该样本的窄机制标为 E3；任何卷级或全书外推都须另行取证并单独定级。

量化数据只证明它直接测量的事实。章长不能单独证明节奏好，对话占比不能单独证明人物鲜活。

每条证据写成：

```yaml
- location: 作品 / 卷章 / 场景
  source_type: primary_text | author_statement | corpus_metric | classic_text | secondary
  observation: 可复核的文本事实；以转述为主
  inference: 该事实支持什么，不支持什么
  limit: 反例、替代解释或适用边界
```

`source_type` 只说明来源；整条结论另记 `claim_grade: E0 | E1 | E2 | E3`。推断不是证据来源。

### 问题优先级

- `critical`：破坏创作契约、中央因果、正史/连续性或读者基本理解；阻塞下游工作。
- `high`：显著削弱人物能动性、叙事发动机、信息公平、场景结果或主要情绪兑现。
- `medium`：局部节奏、关系、氛围或表达问题，修后明显提升但不改故事根基。
- `low`：偏好、微调和 copy 问题；只在上游稳定后处理。

依赖高于数量：一个上游根因优先于二十个由它造成的句段症状。

## 流程一：蒸馏已有作品

用于从整部、分卷或跨章样本中提炼可迁移机制。

1. 写一句研究问题，指定主层、范围和目标用途。例如：“长篇换地图时如何保留连续感”，而不是“分析写法”。
2. 设计最小样本：机制建立处、一次典型运行、一次变化或失效处。跨卷结论必须覆盖卷界；不得用单章证明全书规律。
3. 为每个样本建立证据卡。先记录事实，再解释效果；把作者自述、文本效果和读者推断分开。
4. 选择一部解决相同叙事问题的名著。对照“问题—方法—效果—代价”，不比题材皮肤，也不做高下排名。
5. 主动寻找反例和替代解释。若无法排除，只输出 `E1/E2` 假说。
6. 把观察压缩为条件规则：`适用条件 → 操作 → 可观察效果 → 代价/失效 → 验证方法`。
7. 只有达到 `E3` 才称“可迁移技法”；否则保留为作品局部特征。

输出下列唯一规范技法卡；其他流程引用它，不另造字段同义的模板：

```yaml
technique_card:
  name:
  question:
  taxonomy_layer:
  source_scope:
  evidence: []
  classic_contrast:
    same_function:
    different_method:
    tradeoff:
  mechanism:
    conditions: []
    operation:
    reader_effect:
    costs_and_failure_modes: []
  counterevidence: []
  transfer_test:
  do_not_copy: []
  application:
  verification:
  claim_grade: E0 | E1 | E2 | E3
  style_evidence: # 仅在蒸馏名家风格时填写
    source_metadata:
      work:
      author:
      original_language:
      edition_or_translation:
    separated_locations: []
    observable_feature:
    narrative_function:
    counterexample_or_cost:
    translation_limit:
  narrative_controls: # 仅在蒸馏名家风格时填写
    narrative_job:
    project_condition:
    baseline:
    variation_trigger:
    allowed_variation:
    observable_reader_effect:
    costs_and_failure_modes: []
    verification:
```

### 风格蒸馏附加门

名家风格不是一个可直接调用的作者标签。先记录作品、原作语言、版次或译本与最小材料范围；再在至少两个相隔位置记录可观察特征和叙事功能，并给出反例、代价或失效处。

句法、节奏、用词和声调的结论必须由原作语言支持；译本只能支持结构、事件、意象或功能层面的观察，并把译本限制写入 `translation_limit`。最后用 `narrative_controls` 把结论改成原创项目的基线、触发器、允许变化和可回测的读者效果；不得复制作者的标志性措辞、句法指纹、人物对应、场景顺序或情节骨架。

## 流程二：分析局部

用于片段、场景、章节或相邻少量章节的技法分析。

1. 确定材料边界和一个主层；读取必要前后文及该片段必须服从的上游约束。
2. 先说明片段试图完成什么、最有效的部分和本次不判断的范围。
3. 标记进入/退出状态与关键变化，再按 `证据 → 读者体验 → 机制/根因` 分析。
4. 需要解释更高层原因时只上溯到最近根因；不要顺势扩成全书审稿。
5. 对超出材料边界的推断降为 `E1`，并列出验证它所需的最小新增材料。

输出：

```yaml
local_analysis:
  scope:
  primary_layer:
  intended_job:
  protected_strengths: []
  state_change:
    entry:
    exit:
  findings:
    - location:
      evidence:
      reader_effect:
      mechanism_or_root_cause:
      claim_grade: E1 | E2
  limits: []
  next_material_if_needed: []
```

## 流程三：规划原创

用于把已蒸馏的机制转成新故事方案，不用于复刻来源作品。

1. 固定创作契约：读者、载体、长度/更新约束、类型承诺、禁区；再写主题问题，不先选参考作品模板。
2. 建立最小世界门：关键规则及限制/代价、资源与权力分配、至少一条二阶后果、时代矛盾；未决定处留白。
3. 建立人物门：主要人物的外在目标、内在需要、世界位置、知识边界、独立行动和可能变化。
4. 从人物欲望、权限、阻力、信息和代价推导叙事发动机，再锁定结构与因果；世界、人物和结构可往返校正。
5. 建立信息阶梯、场景/连载单位；只调用解决当前问题的技法卡。
6. 为每个借用机制重算适用条件和代价。原故事没有提出的问题，不得因参考作品存在而加入。
7. 做去皮测试：删去专名和题材词后，若卷序、身份链、组织仪式或关键转折仍能与来源逐项对应，重新设计因果。
8. 到场景层再确定语言与意象；不要用“冷静白描”等表面声纹替代故事机制。

输出：

```yaml
original_plan:
  contract:
    readers:
    medium_and_length:
    promises: []
    constraints: []
  thematic_question:
  world_gate:
    rules_limits_and_costs: []
    power_and_resources:
    second_order_consequences: []
    structural_conflict:
  character_gate: []
  narrative_engine:
  architecture:
    central_causality:
    stage_changes: []
    ending_answer:
  information_plan: []
  scene_and_serial_rules: []
  borrowed_mechanisms:
    - technique:
      story_specific_need:
      changed_conditions_and_costs:
  originality_check:
  open_risks: []
```

## 流程四：诊断与改稿

用于找根因、安排修订，或在明确授权后改写。

1. 选一个主审层，说明作品意图、读者承诺、范围和 `protected_strengths`。高层未稳定时不做全面 line/copy。
2. 每项问题使用具体证据，记录读者影响、根因和优先级；合并同根症状。
3. 按依赖排序修订：契约/主题 → 世界/正史约束 → 人物/结构/因果（按根因往返）→ 信息/场景/情绪 → 语言 → copy/连续性复核。
4. 默认只诊断和规划。用户明确要求改稿时，先把约束分为 `hard_invariants`、`variation_obligations` 和 `prose_freedoms`，再做最小范围重写；不得把硬约束机械翻译成所有人物共享的句法和场景程序。
5. 为跨章修订建立表达预算：原则首次可完整建立，后续写变化／误读／代价；对白已清楚表达时默认不再由旁白复述；不改变决定的清单只概括变化项。
6. 对主要说话者记录经验来源、语域、压力下节奏和盲点；对相邻场景记录冲突载体、决定动作、解释方式和结束形态，检查是否连续复用同一实现机器。
7. 改后用同一主层复核，并回归检查被它影响的知识、物件、时间、关系、伏笔和后续场景。

输出：

```yaml
revision_report:
  scope:
  primary_layer:
  intent_and_promise:
  protected_strengths: []
  findings:
    - id:
      priority: critical | high | medium | low
      location:
      evidence:
      evidence_locations: []
      owner_layer: world | character | story | outline | prose | editor
      reader_effect:
      root_cause:
      recommendation:
      claim_grade: E1 | E2 | E3
      preserve: []
  revision_order:
    - target:
      prerequisites: []
      invalidates: []
      verification:
  fixed_facts_if_rewriting: []
  constraint_partition:
    hard_invariants: []
    variation_obligations: []
    prose_freedoms: []
  expression_budget:
  voice_differentiation: []
  scene_realization: []
  diagnostic_lenses: []
  open_questions: []
```

## 反过拟合与反表面仿写

- 不把八卷顺序、每卷换身份、固定聚会、序列升级、日记载体或悲剧卷末当成通用配方。
- 不规定伏笔数、牺牲频率、章长、感官点或信息间隔；除非目标载体和实测约束确实需要。
- 区分“文本中反复出现”“作者声称有意为之”“对读者有效”“适合新故事”四种不同命题。
- 名著对照只选同功能异方法；相似措辞、时代装饰和题材标签不构成机制证据。
- 风格研究先问“这个形式替叙事完成什么工作”，再填写 `narrative_controls`；只会命名某位作者而不能写出项目条件与验证方式，结论不得迁移。
- 迁移因果，不迁移专名、句式指纹、场景排列、人物对应关系或可识别桥段。
- 每条技法必须写代价和失效条件。只列成功案例的规则一律降级。
- 平台连载策略与一般小说原理分开；服务日更追读的做法不自动适合出版或短篇。
- 引用以位置和转述为主，只保留说明判断所需的极短原文，不输出大段受版权保护文本。

## 交付门槛

1. **范围门**：有明确主问题、主层、材料边界和不处理项。
2. **证据门**：局部判断至少 `E2`；可迁移规则必须 `E3`。
3. **对照门**：名著与目标作品解决同一功能问题，并写出方法差异和代价。
4. **迁移门**：原创机制由新故事约束推导；去皮后不能与来源逐项对应。
5. **修订门**：先修上游根因，保护有效部分，改后以同模式验证并检查受影响状态。
6. **停止门**：证据已支持范围内结论时停止加载和列举；额外材料必须能改变当前判断。
