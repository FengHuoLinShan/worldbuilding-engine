# World Architect vNext 上游补丁规范

## 目标与边界

把复杂世界观中的概念解耦、内生吸引力、涌现式历史、关系裁定与认知生态加入 `fiction-core-zh:world-architect`，同时保持它对完整世界工件的唯一所有权。

本规范面向可维护的 fiction-core 源仓。不要修改 Codex 安装缓存，不新增技能、必填 schema 字段、MCP、项目适配器或正典写入能力。

## 修改 `SKILL.md`

在“核心流程”中，把下列步骤插在“提炼世界前提”与“建立规则契约”之间；只在 `connect`／`implicate` 或实际存在复杂概念、古代遗留、历史分叉、相似体系、宗教认知误差时启用：

### 先解耦，再连接

1. **概念边界**：逐项说明它是什么、做什么、依赖什么、失去什么仍能存在、明确不等于什么。
2. **历史分层**：区分原始压力、设计目的、实现机制、共同故障、应急处置、幸存底盘和现代再利用／误读。
3. **关系裁定**：在同一实体、谱系后裔、制度继承、权限继承、技术依赖、功能趋同、表面相似中明确选择；不得从功能相似直接推出继承。
4. **认知生态**：涉及宗教、遗迹、独立 AI 或智慧自然现象时，推演真实机制、可观察现象、民间解释、仪式反馈、解释权组织、异端与失败预言。

当用户指出一个国家／组织只有工具性质，或要求它尚未登场就足以吸引读者时，在规则契约前再执行：

### 先证明值得追问

1. 移除主角和邻国需求后，找出该对象仍未完成的使命、核心谜团和自我矛盾。
2. 设计能在境外提前出现的物件、病人、禁运、异常、制度后果或矛盾证言。
3. 明确它相信自己在守护什么，以及何种真相会摧毁其合法性或自我解释。
4. 用户要求多个方向时，各方向必须拥有不同的因果核心、伦理代价和揭谜回报；资源或视觉换皮不算不同方向。

当用户要求现代形态从古代工程、重启、灾难或长期惯性中“涌现”时，在设计现代国家前执行：

### 先重建涌现链

按“古代干预／基础功能 → 幸存底盘 → 非均匀失效 → 地点与劳动筛选 → 实践社会化 → 制度化 → 复苏路径强化 → 现代结果”推演。区分基础功能、后期叠加、失效惯性、现代再利用、必然压力与偶然分叉；古代起点可保持多个假说，现代因果约束不能空缺。古代巨构任务还要说明存续、衰变、负遗迹和现代维护代价。

补充审查问题：

- 是否用新专名掩盖源头、中枢、介质、操作者和后继者之间的角色混淆？
- 是否以后世用途倒推古代唯一目的，或把功能趋同误写成血统、法统、权限或技术连续？
- 移除主角和邻国需求后，该国家／组织是否仍有自己的使命、谜团与揭谜代价？
- 现代制度是否经过幸存底盘、非均匀失效、必要劳动、社会化与路径强化，而非由古代目的直接生成？

简单节日、单条规则和第一轮灵感必须允许直接跳过，不把短表升级为通用问卷。

## 修改 `references/world-design.md`

在规则契约之后加入“复杂概念拓扑”小节，复用以下最小结构：

```yaml
resolution_brief:
  intrinsic_attractor:
    internal_mission:
    core_mystery:
    self_contradiction:
    offstage_leaks: []
    revelation_cost:
  concept_boundaries:
    - concept:
      role:
      depends_on: []
      survives_loss_of: []
      not_equivalent_to: []
  historical_layers:
    original_pressure:
    base_function:
    later_overlays: []
    implementation:
    common_failure:
    emergency_response:
    surviving_substrate:
    failure_inertia:
    modern_reuse_or_misreading:
  emergence_chain:
    substrate:
    nonuniform_failures: []
    selected_sites_and_labor: []
    social_reproduction: []
    institutionalization: []
    path_reinforcement:
    modern_outcomes: []
  contingency_and_necessity:
    necessary_pressures: []
    contingent_forks: []
    locked_outcomes: []
    open_origins: []
  non_inheritance_guard:
    excluded_continuities: []
    surviving_dependencies: []
  survival_ledger:
    persistence_mechanisms: []
    inputs_or_stored_gradients: []
    decay_and_failure_morphologies: []
    observable_and_negative_ruins: []
    present_maintenance_labor: []
  relation_verdicts:
    - pair: []
      verdict: same-entity | lineage | institutional-succession | authority-succession | technical-dependency | functional-convergence | surface-resemblance
      evidence: []
      exclusions: []
  epistemic_ecology:
    true_mechanism:
    observable_phenomena: []
    folk_models: []
    ritual_feedback: []
    interpretation_authorities: []
    heresies_and_failed_predictions: []
```

这是可选输出片段。未触发的区块应整体省略，尤其不能让普通局部任务填写 `intrinsic_attractor`、完整涌现链或巨构存续账。现有 `world-architecture.schema.json` 顶层允许附加字段，因此无需改变必填字段或 schema 版本。

## 修改模板

`world-bible-template.md` 在“核心规则”后增加可选的“内生吸引力、概念边界、历史分层与涌现链”，在“公开叙事与真实运行”下提示认知生态；古代巨构任务再显示存续账。

`world-element-template.md` 在“功能与边界”后增加：

- `不等于什么`
- `与相似体系的关系裁定`
- `最初目的／后来用途／现代误读`
- `内在使命／境外泄露迹象／揭谜代价`
- `幸存底盘／失效筛选／社会化／现代结果`

模板提示必须标注“复杂任务按需使用”，不能成为每次输出的必填章节。

## `canon_diff` 约束

保留现有 `additions`／`modifications`／`deprecations` 结构，不改 schema。每项只写一个原子命题，并允许同一工件同时表达：

- 已采用或建议采用的正向命题；
- 仍为 `proposed`／`author-required` 的开放项；
- 明确排除的等价、继承、万能化或知识泄漏解释。

页面、章节或工件整体通过不等于其中每个命题拥有同一权威状态。

## 上游评测

1. **共同源头与自毁中枢**：以共同源头、协调中枢、古代维护者和现代调律师为中性样例；必须区分基础使命与后期叠加，给出非均匀失效—劳动社会化—路径强化的历史链，并把现代相似能力裁定为功能趋同而非继承。
2. **没有人格神的宗教**：必须从真实但有限的遗迹／AI／自然反馈推出至少两种竞争解释、仪式、服务组织、获益者、失败预言和普通人体验；不得偷渡人格神。
3. **复杂度保护**：面对“神庙配水的沙漠小镇有哪些节日”这类局部请求，只从配水、季节与合法性生成少量节日；不得强制输出完整 `resolution_brief`。
4. **远方城邦的内生吸引力**：先诊断资源供应地的工具化，再提出因果核心、伦理代价与揭谜回报真正不同的使命／谜团方向；登场前须有境外可见泄露迹象。
5. **分段采纳**：作者只采用第一、二部分时，第三至第五部分及其开放问题继续保持候选，不得整体晋升。
6. **替换级地理迁移**：用改名案例把旧平面地图替换为垂直地理；旧地图降权但保留形成史，只同步直接影响项，不重写历史记录。

验收同时检查：概念非等价、历史层次、明确关系 verdict、作者／专家／公众知识边界、普通人生活和故事压力；不按固定措辞评分。
