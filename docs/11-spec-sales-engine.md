# 销售引擎升级 — Spec G→K（LED 外贸业务员视角）

> 2026-07-09 Allen 要求：CRM Wave A→F 已完成（详情/阶段/跟进雷达/导出/分页/模板/深挖）。
> 现在站在业务员日常赚钱视角，参考 Instantly / Smartlead / Lemlist / Apollo / Clay 取精华，
> 补齐"漏斗后半段（跟进·成交）"和"漏斗前端质量（多源·验证·分级）"。不照搬企业级重架构。

## 核心判断：钱在跟进和成交，当前系统还漏在这几处

对照吃饭家伙，最能直接提回复率/成交率的三块，恰是 doc 10 当初划进"不做"的：

1. **发完就断线** —— 没有自动跟进序列。冷触达发一次基本没人回，回复几乎全在第 2–4 次跟进。
2. **对已回复的人还在催** —— 没有回复检测，跟进雷达会骚扰已回复客户，伤单。
3. **邮件进垃圾箱** —— 单邮箱群发几十封就被标记，前面找客户全白费。

外加漏斗前端的质量问题：找客户只有"搜索引擎→官网"单条路；抓到的邮箱没验证；客户不分级（租赁公司和终端价值天差地别）。

---

## Wave G：自动跟进序列 + 回复检测（最高优先，盘活存量 940 条）

> 借鉴 Instantly/Lemlist 的 sequence，但**守住防封边界：序列只生成"今日待发队列"，仍由业务员手动点发**，
> 不做真正后台定时自动发送（那会绕过限速+批量上限，触发封号）。

### 设计要点：多步触达绕开老 eligibility

现有 `outreach` 排除 `status IN ('messaged','replied')` 的人——一次性群发用它防重复，正确。
但序列第 2、3 步必须能给"已 messaged"的人发。方案：序列发送走**独立路径**，以 `enrollment` 状态决定发不发，
不受 outreach messaged 排除；发送后照常 `touch_count+1` 记录到 outreach。

### 数据模型
- `sequences(id, name, channel, active INTEGER DEFAULT 1, created_at)`
- `sequence_steps(id, sequence_id, step_order, day_offset, subject, body, image)`
  —— day_offset 相对入组日：0=首发，3=第二触达，7=last touch。
- `sequence_enrollments(id, lead_no, sequence_id, current_step INTEGER DEFAULT 0,
  status TEXT DEFAULT 'active', enrolled_at, next_due_date)`
  —— status: active / completed / stopped / replied。UNIQUE(lead_no, sequence_id)。

### 后端
- `enroll_leads(seq_id, lead_nos)` → 建 enrollment，next_due_date = today + step0.day_offset（=today）。
- `due_queue(channel?)` → 返回 `status=active 且 next_due_date<=today 且 lead 未回复` 的 (enrollment, step, lead)。
- `advance_enrollment(enrollment_id)` → 发送成功后：current_step+1；有下一步则 next_due_date=today+下一步 day_offset；
  无下一步则 status=completed。
- `stop_enrollment` / 回复触发：outreach.reply_received=1 或手动标记已回复 → 该 lead 所有 active enrollment 置 `replied`。
- API：`POST/GET /sequences`、`POST /sequences/{id}/enroll`、`GET /sequences/due?channel=`、
  发送沿用 `/api/send/*` 但带 `enrollment_ids`，成功后 advance。

### G2：邮件回复检测（IMAP）
- `mailbox` 配置读 IMAP；`poll_replies()` 拉近 N 天收件，发件人邮箱匹配 leads.email →
  outreach.reply_received=1 + status='replied'，并把该 lead 的 active enrollment 置 replied。
- 触发方式：`POST /replies/poll` 手动 + start.bat 启动时跑一次（不常驻）。WA/IG 回复仍用界面手动标记（现有蓝徽章）。

### 前端
- 新页"跟进序列"：建序列（名称+渠道+若干步：天数/主题/正文/图）；从客户库勾选"加入序列"。
- 仪表盘"今日待发跟进"卡 + 待发队列页：列出 due 的 (客户+这一步话术)，勾选→点发（复用发送面板，带 enrollment_ids）。
- "拉取邮件回复"按钮 → 调 poll，回来刷新已回复。

---

## Wave H：多源找客户（尤其 LED 专属高价值源）

> 现只有"搜索引擎→官网深挖"。补三类源，全部汇入现有 候选去重→勾选导入 管道。

- **H1 Google Maps** —— 复用 Playwright engine，查 "LED sign/rental/AV {city}"，提取 名称/电话/网站/地址。本地标识厂/活动公司转化高。
- **H2 展会参展商名录** —— ISE / InfoComm / LED China 参展商是这行最精准买家池。做 CSV/粘贴导入 + 公开目录页可抓则抓。
- **H3 竞品经销商页** —— 给 Absen/Leyard/联建 的 "where to buy / distributors" URL，抓各国经销商 = 现成已验证 LED 买家。

每条候选带 `source` 标注来源，导入后可按来源筛选看哪个源质量高。

---

## Wave I：邮件送达率基建

- **I1 多发件邮箱轮换** —— 表 `mailboxes(id, email, smtp_host, port, imap_host, user, password, daily_cap, active)`；
  发送按轮询选下一个 active 邮箱，尊重每箱日限。单箱→多箱，摊薄单域名风险（Smartlead 打法）。
- **I2 邮箱验证** —— enrich 或发送前做 MX 查询 + SMTP RCPT 探测（免费），分类 valid/invalid/role(info@,sales@)/catch-all，
  存 leads.email_status；发送自动跳过 invalid，降 bounce 保送达。
- **I3 发送窗口** —— due 队列只在目标国工作时段内提示发送（时区友好），避免半夜发被当垃圾。

---

## Wave J：ICP 自动分级 + 产品报价卡（LED 专属差异化）

- **J1 ICP 打分** —— enrich 时按官网关键词判类型（rental/fixed-install/reseller/signage/integrator/end-user）+ 算 fit_score 0–100，
  自动填 target_fit + 打标签。客户库可排序/筛选，优先打高价值。
- **J2 产品报价卡** —— 表 `products(model, pixel_pitch, brightness, use_case, ref_price_sqm)`；
  勾产品→生成报价图/PDF→附到触达消息。业务员天天被问规格价格，通用 CRM 给不了。

---

## Wave K：Campaign 分析 + 多语言话术

- **K1 Campaign 分析** —— 每批发送记 campaign_id + template + channel；统计各 campaign/国家/渠道/话术 的 已发/已回复率，指导下一步。
- **K2 按国家自动选语言模板** —— templates 加 `lang`，国家→语言映射；发送面板按勾选客户国家自动推荐对应语言模板（西/葡/阿语回复率翻倍）。

---

## 不做（YAGNI）
多用户/权限、Kanban 拖拽（阶段下拉够用）、**真正后台定时自动发送**（保留手动点发防封）、
WhatsApp 官方 Cloud API 接入（合规但要模板审核，单独立项评估）。

## 优先级与交付
G → H → I → J → K，每个 Wave 内再切小片，**TDD + 独立 commit**（沿用 Wave A–F 节奏）。
G 价值最高（盘活存量、直接提回复率）先做；G2 回复检测与 G1 序列配套，必须一起，否则会骚扰已回复客户。
