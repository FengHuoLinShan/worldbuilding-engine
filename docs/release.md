# 固定版本发布

在独立主题分支完成五轮迭代、全回归、SDK互操作与文档同步。保持作者工作区、作品和权限文件独立；公共包仅包含通用库的固定 Git 对象。

标准归档命令：

```sh
git archive --format=zip --prefix=worldbuilding-engine-0.8.0/ --output=worldbuilding-engine-0.8.0.zip HEAD
git archive --format=tar.gz --prefix=worldbuilding-engine-0.8.0/ --output=worldbuilding-engine-0.8.0.tar.gz HEAD
```

对归档内文件逐项检查敏感路径、作品正文、密钥、运行状态与越界链接，计算 SHA-256，独立解包后运行 README 中的验证。发布 release-manifest.json 与 SHA256SUMS，manifest 明确 source_commit、工具数、测试范围和未验收项。
向现有公共库推送主题分支，等待固定 SHA 的 Linux/macOS CI 成功后，创建对应 tag 与 GitHub Release。发布授权不改变 RIGHTS、不自动合并主分支或安装/替换用户插件配置。
