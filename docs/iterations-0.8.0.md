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

- 新增固定项目候选保存/精确历史读取、SQLite 短事务、预期 head CAS、operation_id 回执幂等与 no_change；默认关闭、没有删除或 canon 写入接口。
- 增加变更影响闭包：按 dependent → upstream 计算跨 World/Story/Scene 影响；循环也可终止，未知引用拒绝。
- `python3 mcp/test_candidates.py`：4 tests，通过保存/重试/旧历史/冲突/源变化/不同项目/两线程竞争/默认关闭与无写入读取。
- workflow 7 tests、主 MCP 9 tests 通过。读取旧稿标记 not_revalidated，不能冒充当前资料已核实。

## 第4轮：对抗与互操作

- 发现并封住 Worldcheck target 被解释为 --record/--config 等 CLI 选项的入口；控制字符、过量目标与超大 review budget 拒绝。
- 补14个标准 MCP prompts 与2个固定 URI resources；通知不调用写工具，参数/信封错误、重复 JSON key、非有限数字、超量请求拒绝且后续请求仍可用。
- 候选 revision hash 同时绑定内容与来源检查，损坏检查记录读取失败关闭；Worldcheck 状态支持标准 XDG 与 Linux/Windows 默认目录，保留 macOS 旧路径。
- 发现原 surface_audit 按最大章号展开 range 可造成无界内存、负 repeated_phrase_length 可造成超大循环；在共享计算处修复，缺号以完整区间/总数和最多1000条样例表示，阈值限制为已知有限值。
- 主 MCP10、protocol3、candidate5、Worldcheck Ruby16（81 assertions）、adapter7通过。
- 官方 mcp==2.2.0 + jsonschema==4.26.0 独立客户端：17工具全部实际调用并验证声明 schema、14 prompts、2 resources，异地 cwd 运行的合成生成/检查/保存/读取与世界书 baseline→变化→packet→receipt→status 全通过。
- SDK 样例候选是宿主手写合成内容，没有付费模型；不是作者真实作品的文学质量验收。

## 第5轮：独立分发与发布

- 新增绝对路径客户端配置生成器，optional 文件检查与候选存储默认关闭；提供固定版本安装说明和 Linux/macOS CI。
- 新候选库 POSIX权限0600，stdio 固定 UTF-8；最低 Python3.10.20 实际运行25个核心 Python tests，而非只做语法检查。
- 完整本地回归：25 core Python + 7 adapter + 9 Ruby engine + 17 Ruby Worldcheck = 58 tests；Ruby合计124 assertions，全部通过。官方 mcp2.2.0/jsonschema4.26.0 实际客户端全部17工具、prompts/resources与完整合成世界书回执流程通过。
- 首次远端 Ruby3.3 CI 暴露旧 YAML.safe_load 位置参数不兼容，基线全部失败（run36940409930）；改为 Ruby2.6/3.3 共用 keyword 参数。增加对象标签与YAML alias拒绝回归，保留 Date 白名单与aliases=false；不通过降级 Ruby 或放宽 YAML 安全门禁处理。
- Ruff（target py310）检查修改涉及的 Python 工具、测试和表面审计通过；git diff --check 通过；NovelCraft 收尾 docs-check BASE_REF=origin/main 通过。
- 独立包用 Git 固定对象归档，保留 RIGHTS；不纳入工作区WIP、真实作品、候选库、原始请求、私有路径或密钥。包的固定 SHA、文件校验和与独立启动结果随 release-manifest.json 发布，远端CI状态以该 SHA 的 Actions 为准。
- 本版本交付工程能力；真实模型写作/编辑质量、作者采用、Windows 实机、公开HTTP鉴权与生产部署未验收，工具包不宣称这些状态。
