# Channel Send Hardening — S5 Part 2 补完

**Goal:** 补齐 S5 Part 2 对照实战规矩的三个缺口：

1. **单批上限 20 条**（防封号）：`channel_outreach.MAX_BATCH = 20`，超出部分计入 `deferred` 返回，UI 明示"本批只发前 20 家"。教训：2026-05-15 WhatsApp 超量发送触发账户受限。
2. **WA/IG 发图**：`send_message` 增加 `image` 参数；WhatsApp 发完文字后经附件按钮上传图片并发送，Instagram 经 DM 文件输入上传（选中即发）。API 默认附带案例图（与 Email 同一张 `DEFAULT_ATTACHMENT`），路径不存在时 400 拒绝。规矩：DM 必须同步发案例图。
3. **IG 实测**：真实 Instagram 账号发一条带图 DM，验证选择器有效。浏览器渠道选择器无法单测，实测是唯一验证手段（沿用 Part 1 的 live-verify 模式）。

**Tasks:**

- [x] Task 1: MAX_BATCH=20 + deferred（后端 TDD + UI 提示）→ commit `feat: hard cap 20 per browser-channel batch (anti-ban)`
- [x] Task 2: image 参数贯穿 FakeEngine / channel_outreach / API / PlaywrightEngine + UI 提示 → commit `feat: WA/IG send with case-image attachment`
- [ ] Task 3: IG live verify（需 Allen 登录 IG + 指定测试目标）→ 结果记录在本文档

## Live verify 记录

- WhatsApp：2026-05 已实测真实发送 ✓
- Instagram：待测（Task 3）
