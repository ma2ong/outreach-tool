# CRM 化升级 — Spec（以 LED 外贸业务员视角）

> 2026-07-09 Allen 要求：把系统当真正 SaaS 产品，从"找客户+群发"升级为"能跟进、能成交"的销售 CRM。参考开源 CRM/外联工具（Twenty、EspoCRM、ERPNext CRM、Monica、Instantly/Lemlist 的话术库与跟进逻辑）取其精华，不照搬重量级架构。

## 业务员真实痛点（当前系统做不到）

当前是"漏斗前半段"工具：找→群发。但**外贸的钱在跟进和成交**，这层完全缺失：

1. 发完就断线——没有"谁该跟进了"（发了 7 天没回复的，靠脑子记）。
2. 没有客户阶段——只有"已发/已回复"，没有"洽谈中/已报价/成交/无效"这种销售管道。
3. 沟通无记录——打过电话、要过报价、聊到哪，全无痕迹。
4. 无法在界面改客户信息（深挖漏了电话只能改数据库）。
5. 话术只有一条硬编码，不同市场/场景想换话术要改代码。
6. 名单导不出，和现有几十个 Excel 工作流割裂。
7. 940 条只能看前 200，不能翻页/排序。

## 设计（分批交付，每批 TDD + 独立 commit）

### Wave A：客户 CRM 内核（详情抽屉 + 编辑 + 阶段 + 标签 + 跟进记录）
- 表：leads 加列 `stage`（new/contacted/replied/negotiating/won/lost，默认 new）、`tags`（逗号分隔）、`follow_up_date`、`next_action`；新表 `notes(id, lead_no, created_at, text)`。
- 后端：`update_lead(no, fields)`、`add_note/list_notes`、set_stage/tags 走 update_lead；`GET /leads/{no}` 带 notes。API：`PATCH /leads/{no}`、`POST/GET /leads/{no}/notes`。
- 前端：点表格行→右侧详情抽屉（全字段 + 内联编辑 + 阶段下拉 + 标签 + 跟进日期 + 备注时间线）。

### Wave B：跟进雷达（业务员最值钱的功能）
- 后端：`list_leads` 加 `follow_up=due`（已触达 + N 天无回复 + 未成交/无效）。
- 前端：仪表盘"该跟进了"卡片 + 客户库快捷筛选"待跟进"。

### Wave C：Excel/CSV 导出
- `GET /leads/export?<同筛选参数>&fmt=xlsx|csv` → openpyxl 生成，带联系方式/阶段/标签列。前端筛选栏"导出"按钮。

### Wave D：客户库分页 + 排序
- `list_leads` 加 `sort`/`order`/`limit`/`offset` + 返回总数；前端表头点击排序 + 底部翻页。

### Wave E：话术模板库
- 表 `templates(id, name, channel, subject, body)`；`GET/POST/DELETE /templates`；OutreachPanel 顶部模板下拉，选中填入。默认内置现有 Email/DM 两条。

### Wave F：深挖抓取增强
- enrich 提取 WhatsApp 专用链接文案里的号码、多邮箱优选、页面标题猜公司名；候选表显示更全。

## 不做（YAGNI）
多用户/权限、Kanban 拖拽看板（用阶段下拉替代）、自动化 sequence 定时发送、邮件收件解析回复。

## 优先级
A（内核）→ B（跟进雷达）→ C（导出）→ D（分页排序）→ E（模板）→ F（深挖）。A、B 价值最高先做。
