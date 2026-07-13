# Task Plan: outreach-tool 专业化优化（销售视角 Wave L+）

## Goal
以专业 LED 外贸销售使用者视角，调研竞品补齐功能短板，实现并验证，让产品达到"专业用户日常好用"标准。

## Phases
- [x] Phase 1: 审计现状（代码/功能/测试基线）
- [x] Phase 2: 竞品与开源调研（Instantly/Smartlead/Lemlist/Apollo + 开源 CRM）
- [x] Phase 3: 写 Spec 12（销售视角差距清单 + 优先级）
- [x] Phase 4: 实现最高价值 Wave L（TDD）
- [x] Phase 5: 全量验证（pytest 204 全绿 + playwright 10 全绿 + 真实 Gmail poll 命中真退信）

## Key Questions
1. 回复内容是否可见？（只有 flag 还是存正文）
2. 模板是否支持变量个性化 {{name}} 等？
3. 有无黑名单/退订抑制机制？
4. 有无退信(bounce)处理？
5. 有无全局搜索/数据备份？

## Constraints（用户既有反馈，不可违反）
- 单批≤20、每渠道日限、随机限速 —— 防封红线
- 不做 warmup
- 手动点发，不做后台定时自动发送
- WA/IG/FB 消息不提公司名、必须带案例图

## Decisions Made
- 只存匹配到 lead 的邮件（不把整个 Gmail 收件箱塞进库）
- 退订关键词命中 → 自动置 do_not_contact（行业实践：suppression 必须自动、立即）
- 退信是 bounce 不是 reply：只标 email_status=invalid，不改 outreach 状态
- 个性化用白名单 token 正则替换，不用 str.format（修复 {未知变量} KeyError 发送失败 bug）
- 不做：AI 意图分类、open/click 追踪、warmup、后台定时发送（见 Spec 12 YAGNI 节）

## Errors Encountered
- 无阻塞性错误；旧 test_poll_uses_injected_fetcher 因接缝升级按新接口改写

## Status
**完成** - Wave L 全部落地并验证；Wave M 候选（deal_value 管道价值/LinkedIn 源/正式报价单 PDF）留待决策
