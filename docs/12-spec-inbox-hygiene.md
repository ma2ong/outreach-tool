# Spec 12 — Wave L：回复收件箱 + 名单卫生（业务员视角二轮补差）

> 2026-07-13 Allen 要求：以专业外贸销售使用者视角再审产品，调研竞品补差距。
> 调研对象：Instantly Unibox / Smartlead Master Inbox / Mailgun·SES suppression 实践。

## 差距诊断（按"影响赚钱"排序）

1. **回的什么看不见** —— 现在回复检测只匹配发件人打个 flag，客户回了什么内容工具里看不到，
   还得去 Gmail 里翻。竞品的核心卖点就是 Unified Inbox：回复内容集中一处、分类打标。
   → 回复率做上去之后，成交环节反而断在工具外。
2. **退信没人管** —— mailer-daemon 退信躺在收件箱里没人解析。硬退不标记会持续伤发件域名
   信誉（deliverability 行业共识：hard bounce 应立即进抑制名单）。现有 email_status='invalid'
   跳过机制已就位，缺的是"退信→自动标 invalid"这一步。
3. **没有"不再联系"** —— 客户回 "remove me / stop" 后没有任何机制阻止他再次被选中群发或
   躺在序列里继续被跟进。伤域名也伤口碑，是合规底线（竞品全部内置 suppression list）。
4. **个性化变量太弱且脆** —— 只支持 {name}=公司名；模板里若写 {country} 直接 KeyError 发送失败。
   联系人名、国家是冷邮件个性化最基本的变量。
5. **数据无备份** —— outreach.db 是吃饭家伙（940+ 客户、全部触达记录），单文件无备份。

## Wave L 实现范围

- **L1 收件箱**：表 `inbox_messages(lead_no, channel, from_addr, subject, body, received_at,
  read, kind)`，kind=reply/bounce/unsubscribe。IMAP poll 升级为拉整封邮件（头+正文摘要），
  匹配到 lead 才入库。前端新页"收件箱"：未读徽章、kind 标签、点开看正文并可跳客户详情。
- **L2 退信自动处理**：poll 时识别 mailer-daemon/postmaster/undelivered 邮件，从正文提取
  失败地址 → 命中 lead 则 email_status='invalid'（现有 eligibility 自动跳过）+ 入库 kind=bounce。
- **L3 不再联系（suppression）**：leads.do_not_contact 列；email/WA·IG/序列 due 三处 eligibility
  全部排除；回复含 unsubscribe/remove me/stop 类关键词 → 自动置 1 + 入库 kind=unsubscribe；
  详情抽屉可手动开关。
- **L4 安全个性化**：新模块 personalize.render()，支持 {name}(公司)/{contact}(联系人,缺省 "there")/
  {country}/{city}，未知 {token} 原样保留不再崩溃。三条发送路径统一换用。
- **L5 启动自动备份**：启动时把 DB 拷到 backups/（每天一份，保留最近 14 份）。

## 不做（YAGNI / 违约束）
- AI 自动回复/意图分类（先把"看得见"做好，分类价值待验证）
- 邮件 open/click 追踪（需要自建像素域名，反伤送达率）
- warmup（用户明确不做）、后台定时发送（防封红线）
- WA/IG 回复自动抓取（Playwright 抓私信箱风险高，保留手动标记）

## 后续候选（Wave M，本轮不做，供决策）
- 成交金额字段 + 管道价值看板（stage 已有，加 deal_value 即可算 pipeline）
- Google Maps 源已有，补 LinkedIn 公司搜索源
- 报价卡升级为可算总价的正式 PDF 报价单（数量×面积×单价）

## 验证标准
- 后端 pytest 全绿（新增 inbox/suppression/personalize 用例）
- 前端 build 通过 + Playwright 冒烟全绿（新增收件箱页只读用例）
- 真库检查:  poll 对真实 Gmail 跑通（有回复则入库可见）
