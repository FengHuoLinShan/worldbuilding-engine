# 通用 MCP 能力迁移清单

来源是 NovelCraft 的公开领域契约与算法，不包含其数据库、账户、作品、私有任务记录或服务运行时。
以下列出已核对的功能族及最终交付位置；“宿主”表示有明确交接而非已实现该产品运行时。

| 功能族与来源 | 通用交付 | 保留的边界 |
|---|---|---|
| World 创设中心、Core/Design checkpoint | 世界状态模板、写作包、候选版本 | AI 内容只为 proposed，不采用正典 |
| World 22 面、6 循环、5 耦合链、12 压力测试 | 现有 world_audit，stress_test 写作模式 | 结构覆盖与语义真实性分开 |
| World 世界书全量/增量复核 | Worldcheck 三工具整合 | 独立配置、原文只读、陈旧回执拒绝 |
| World 对象、关系、别名整理 | extract_assets 写作模式与候选检查 | 长期资产、同名不擅自合并、别名附着对象 |
| World 共创、多轮修订与决策 | revise_world 模式与候选历史 | 未涉及内容保留，作者决定不被模型覆盖 |
| World 采用包、Canon、发布/回滚 | 候选落盘、版本读取；正典采纳交回宿主 | 无 canon 采用工具，无硬删除 |
| World reader safety | context 包的受众、知情人物、章节/offset 截止 | 不把作者真相、历史、规划当读者知识 |
| World 地图、视觉概念、图片 | visual_brief 模式与概念设计技能 | 空间关系有来源；不编造坐标、不自动采用图像 |
| Evidence 搜索、精确回读 | 内联来源检索、来源 hash 与逐字引文校验 | 检索不是准入；不读任意文件或 URL |
| Evidence Context、排除与 confirmation | 显式 selected/excluded/required 的来源包 | 不导出应用 confirmation 身份；由宿主重验授权 |
| Evidence hidden guard / 截止 | 只过滤知识边界并绑定完整输入 hash | 不将被排除或截止后原文加入写作包 |
| Evidence budget 与覆盖回执 | 完整条目预算、遗漏清单、required blocker | 不截断后宣称完整覆盖 |
| Writing 人物、Scene、正文与定向返修 | design_character / scene_contract / write_scene / revise_world | 世界、结构、正文的所有权和不变量分开 |
| Writing 连续性、批注、编辑台 | review_world / 既有 craft/surface/review 工具 | 批注和近读是建议；不自动修改采用正文 |
| Story 总纲、Scene Contract、伏笔/揭示 | story_outline / scene_contract 模式 | 规划不冒充已经发生的事实 |
| Imports 深度导入、定向补抽、组级整理 | extract_assets 模式与来源证据 | 文件解包/OCR/LLM 由宿主提供；不分发正文 |
| Collaboration 隔离试改、源版本、CAS、历史 | 候选存储、预期 head、operation 幂等回执 | 不复制授权服务、PG lease、成员自治或领域合并 |
| Assistant forecast / 后续观察 | forecast 模式与变更影响闭包 | 推测不是事实、不后台自动运行 |
| Collaboration world_stress / research | stress_test / research_brief 模式 | 研究包不证明联网已完成，不暗调模型 |
| RP reader/character、顺序盲读 | reader_rehearsal 模式与受限 context | 只排演；不实现用户账号/互动旅程运行时 |
| Fiction craft 十二面、五镜头、表面信号 | 现有 craft_packet / surface_audit / review_check | 文学通过仍需外部近读与作者裁定 |
| Project / Identity / Accounts | 宿主配置单项目候选空间 | 不包含账户密钥、认证系统或跨项目数据库 |
| Jobs / Assets / Infrastructure | 本地 stdio、有界计算、超时、可下载包 | 不引入队列、常驻基础设施或付费 API |
| 前端编辑器、地图画布、导入界面 | 宿主 UI；返回结构化内容与易读写作交接 | MCP 不宣称交付 GUI 或图片/视频质量 |

写作模式负责给宿主模型可执行的资料与契约；MCP 不把模板冒充已生成的文学内容。
离线合成验证覆盖协议与算法，不证明真实作品质量、知名作品准确度或生产验收。
