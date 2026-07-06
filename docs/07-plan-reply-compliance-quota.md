# Reply Marking + Email Compliance + Daily Quota

**Goal:** 补齐 spec 中 pipeline 的 replied 环节、冷邮件合规、渠道健康的"今日额度"。

1. **回复标记**：`POST /api/leads/{no}/reply {channel}` 把 outreach 状态置为 replied；已回复的客户从所有渠道的 eligible 查询中排除（不再自动触达）；表格里渠道状态变成可点击 chip（messaged 点一下 → replied），顶部加"已回复/已触达"筛选。
2. **退订声明**：邮件默认模板加一行 unsubscribe 声明（CAN-SPAM）。纯模板文案，无后端改动。
3. **今日额度**：`channel_outreach.DAILY_CAP = {whatsapp: 40, instagram: 40}`（单批 20 × 2 批/天）；按 `message_sent_date = today` 计数，发送时取 `min(单批20, 日剩余)`；`GET /api/send/quota` 返回各渠道今日已发/上限，OutreachPanel 显示"今日已发 X/40"。

**Tasks:**

- [x] Task 1: replied 标记 + eligibility 排除（TDD）+ UI chip/筛选 → commit `feat: mark-replied + exclude replied from campaigns`
- [x] Task 2: 邮件模板退订声明 → commit `feat: unsubscribe line in default email template`
- [x] Task 3: DAILY_CAP + quota API（TDD）+ UI 今日额度显示 → commit `feat: per-channel daily send quota (40/day)`
