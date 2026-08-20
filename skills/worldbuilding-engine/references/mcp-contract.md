# MCP 适配层契约

## 1. 定位

MCP 适配层把模板、结构校验、真实性审计、fiction-core 路由、写作分析骨架和确定性文本表面审计暴露给支持 MCP 的模型。它不是第二个语言模型，也不在服务端隐藏调用外部模型。

创意扩展和文学近读发生在调用方模型；MCP 只负责让输入输出可重复、可校验、可组合。**工具调用成功、骨架生成完成、统计已计算和报告字段完整，均不得被解释为文学通过。**

## 2. 工具

### `world_project_template`

输入标题、创意种子和可选语言；输出符合当前 schema 的最小 `world-state`。所有自动内容为 `draft`，无正典晋升。

### `world_validate`

对 `state` 做确定性结构与不变量检查，输出 `valid`、`errors`、`warnings`、`stats`。

### `world_audit`

审计规则账本、六环、二十二面、五链、情境测试、压力测试、阻断缺口、建议动作和可选迭代节律。无单一“真实性百分比”。

### `world_route`

按第一个未过门的层返回当前主要技能、理由、进入条件和最小上下文域。

### `world_craft_packet`

输入：

- `mode`：`distill_work`、`distill_style`、`analyze_excerpt`、`transfer_to_project` 或 `diagnose_revision`；
- `source_scope`：结论允许覆盖的材料范围；
- `focus`：可选主要问题；
- `text`：可选内联文本，最多 200,000 字符，不接受路径；
- `state`：可选 `world-state`；
- `style_source`：仅 `distill_style` 必填。

输出是 `assessment_phase: scaffold` 的分析骨架：

- 十二面全部初始为 `unassessed`；
- 五个跨层诊断镜头全部初始为 `unassessed`；
- `semantic_review.status` 固定为 `NOT_ASSESSED`；
- `literary_gate.passed` 固定为 `false`；
- 可选的章长、段落、对话起始段和句长指标仅描述表面；
- `prose_transfer_contract` 将正文约束拆为硬不变量、变化义务和行文自由，并提供表达预算、人物声线分流与场景实现去重契约。

五个诊断镜头是既有十二面的跨层入口，不是第十三至十七层：

1. `domain_term_load`；
2. `negation_template_repetition`；
3. `character_voice_differentiation`；
4. `scene_pattern_variation`；
5. `climax_action_deliberation_balance`。

### `world_text_surface_audit`

输入内联中文小说文本、`scope_manifest`、可选项目政策和可选有时效的例外。`whole_work` 必须声明 `expected_chapters`。

确定性输出包括：

- 输入哈希、Markdown 中文章节解析、覆盖率、缺章／重章／空章；
- 完全重复和近重复长段；
- 跨章固定短语；
- 配置化边界词、制度词和有序词项序列；
- 句式族、段首集中、相邻章表面向量、章长稳健变异；
- 每个 finding 的位置、阈值、信号说明与语义边界。

门状态：

- `surface_regression_gate`: `PASS | WARN | FAIL | INSUFFICIENT_DATA | ERROR`；
- `semantic_review_gate`: 永远是 `NOT_ASSESSED`；
- `overall_gate`: 永远是 `BLOCKED`。

表面审计可以指出“某种信号需要近读”，不能推出文风好坏、人物是否同质、场景功能是否重复、POV 是否越界、Scene Contract 是否兑现，或回环是否有效。

例外必须带精确 metric、位置、理由和当前文本 SHA-256；只可把命中的 finding 降为 `accepted_warning`，不能删除证据。

### `world_craft_review_check`

输入由外部 `story-editor` 或人工近读完成的：

- 十二面覆盖矩阵；
- 五个诊断镜头；
- 带所有者、位置、读者影响、根因、建议、证据等级和保护项的 findings。

工具只校验字段、覆盖和证据位置是否完整。输出：

- `review_completeness: complete | incomplete`；
- `ready_for_host_decision`；
- `semantic_truth_verified: false`；
- `literary_gate.status: blocked_unassessed | external_decision_required`；
- `literary_gate.passed: false`。

即使报告完整，也只是允许宿主开始裁定，不是自动 PASS。

## 3. 两阶段审稿数据流

```text
宿主读取正文
→ world_craft_packet 生成阻断中的骨架
→ world_text_surface_audit 生成可复算表面信号
→ story-editor／人工近读填写十二面、五镜头和 findings
→ world_craft_review_check 检查完整性
→ 宿主基于语义证据决定返修／接受／继续取证
```

宿主不得把 `computed`、`PASS` 的 surface gate 或 `ready_for_host_decision` 改写成 literary PASS。若要保存最终裁定，必须同时保存裁定者、范围、正文哈希、证据位置和未决项。

## 4. 正文生产交接

`transfer_to_project` 和 `diagnose_revision` 应按三类约束交接：

```yaml
constraint_partition:
  hard_invariants: []       # 正典、知识边界、场景结果
  variation_obligations: [] # 人物声线、场景载体、节奏和感官中心必须变化之处
  prose_freedoms: []        # 无须逐条解释、可由写手决定的实现
```

表达预算默认规则：

- 原则建立处可完整说明，后续优先写变化、误读、代价或简短索引；
- 对话已经清楚表达时，叙述者默认没有重复解释预算；
- 完整清单只朗读会改变当前决定的项目，未变化状态可概括；
- 人物从身体、职业、欲望和损失说话，正式记录者再将其转译成制度边界；
- 相邻场景若连续复用“文件到桌—质疑措辞—分栏—签字—转交”，须改变冲突载体或给出明确功能理由。

这些是生产控制契约，不会自动生成项目结论，也不能改写正典。

## 5. 安全边界

- 七个 MCP 工具均为无状态、只读计算；
- 不接受任意文件路径，不读取 Vault，不写正典；
- 不执行用户提供的命令；
- 不在服务端调用隐藏模型；
- 错误不暴露堆栈或本机敏感路径；
- 项目文件读写、正典晋升、语义近读和最终文学裁定由宿主按权限执行。

## 6. 版本

- MCP/server：`0.5.0`；
- MCP 协议：`2025-03-26`；
- world-state schema：`0.1.0`；
- craft packet：`0.3.0`；
- surface probe：`1.0.0`；
- review contract：`0.1.0`。

世界状态 schema 本轮无迁移。

## 7. 调用示例

```json
{
  "name": "world_text_surface_audit",
  "arguments": {
    "text": "### 第一章……",
    "scope_manifest": {
      "scope_kind": "whole_work",
      "expected_chapters": 25,
      "segmentation_profile": "markdown-zh-chapter-v1"
    },
    "policy": {
      "id": "project-surface-v1",
      "version": "1.0.0",
      "ordered_sequences": [
        {
          "id": "minimum-service",
          "lexemes": ["最低排水", "饮水", "诊院冷却", "消防"],
          "window_chars": 180,
          "warn_chapter_df": 4
        }
      ]
    }
  }
}
```

## 8. 后续演进候选

- Vault／Git／数据库适配器；
- schema 迁移工具与依赖图可视化；
- 经用户授权的真实缺陷评测集；
- 多模型语义审稿对照与裁定记录；
- 权限化 `apply_change`，默认关闭；
- 分卷／分块审计及跨块聚合协议。
