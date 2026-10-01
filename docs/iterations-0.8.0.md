# 0.8.0 五轮迭代证据

所有素材均为独立合成资料；无付费模型、应用 DB 或真实稿件。每轮在上一轮代码上检查、修改并回归。

## 第1轮：整合与契约

- 盘点 NovelCraft 12 个领域的可迁移能力，见 capability-map；原有七工具与 Worldcheck 三工具统一入口。
- 修复原适配器未执行 inputSchema、initialize 回显任意协议版本以及 Ruby 路径绑定 macOS 的问题。
- 基线：Ruby engine 9 tests/38 assertions；Worldcheck 15 tests/78 assertions；Python MCP 8 tests、adapter 6 tests 全通过。
- 修改后主 MCP 9 tests 通过；闭合参数、错误类型、未知协议均有失败路径检查。
- 本轮提交：`10e1706`。

## 第2轮：来源到写作

- 新增内联来源检索、Context 包、14 类宿主写作/审查模式、候选来源与引文检查。
- 同项目、明确选中/排除、受众、人物知情、章/offset 截止、完整条目预算纳入绑定；所需资料无法准入时阻断写作。
- 修改来源、排除项、任务、保护约束后拒绝旧候选；逐字引用绑定 source hash 与 Unicode 码点区间。
- `python3 mcp/test_workflow.py`：6 tests 全通过；主 MCP 9 tests 全通过。
- 创作与语义审查由宿主完成；完整性检查不等于文学通过，不自动采用 canon。

## 第3轮：候选与变化

执行中。

## 第4轮：对抗与互操作

待执行。

## 第5轮：独立分发与发布

待执行。
