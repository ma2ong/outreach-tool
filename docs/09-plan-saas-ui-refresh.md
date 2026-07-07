# SaaS UI Refresh Implementation Plan

> Spec: `08-spec-saas-ui-refresh.md`。后端任务 TDD；前端任务以 tsc+build+smoke 验证。每任务一个 commit。

- [ ] **T1 enrich 抓取增强**：`extract_phones`（tel:/wa.me/国际号码正则）+ `extract_socials`（IG/FB/LinkedIn 链接），`enrich_domain` 返回 phone/instagram/facebook/linkedin。
  commit: `feat: enrich extracts phone/whatsapp/IG/FB/LinkedIn`
- [ ] **T2 深挖管道贯通**：`run_discovery` 候选带新字段；`Candidate`/`import_leads` 全字段入库。
  commit: `feat: discovery candidates carry phone/socials into import`
- [ ] **T3 筛选后端**：`list_leads` 支持 `status=untouched`（有/无 channel 两种语义）+ `has=phone|instagram|email`；API 透传。
  commit: `feat: untouched + has-contact lead filters`
- [ ] **T4 主题系统 + AppShell**：`theme.css`（双主题 token + 卡片/按钮/输入/表格/徽章公共类）；侧边栏 4 页导航 + 顶栏主题切换（localStorage）。
  commit: `feat: design system + app shell (sidebar, dual theme)`
- [ ] **T5 客户库页**：筛选栏（国家/渠道+状态/有联系方式/搜索）+ 全列表格（wa.me/IG/FB 链接、三渠道状态徽章、点击标记回复）+ 选中浮出触达条。
  commit: `feat: leads page with full columns, contact links, status badges`
- [ ] **T6 仪表盘 + 客户开发 + 渠道页**：统计卡/额度卡；候选表加电话/IG/FB 列；ConnectionPanel 迁入新样式。
  commit: `feat: dashboard, discovery and channels pages in new shell`
- [ ] **T7 冒烟更新 + 全量验证 + 截图确认双主题**。
  commit: `test: smoke for new shell layout`
