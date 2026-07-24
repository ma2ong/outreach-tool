# Spec 13 — Wave N：LED 商机管道与成交预测

> 目标：把 outreach-tool 从“客户开发 CRM”补成“能管理 LED 项目并推动成交”的销售工作台。
> 参考 HubSpot 的 deal amount / probability / weighted forecast，以及 Pipedrive 的 next activity / rotting。

## 为什么必须独立商机

- 一个客户可能同时有租赁屏、户外广告屏、会议室小间距等多个项目，不能把金额和规格直接塞在客户字段里。
- 客户回复不等于有真实项目；只有明确需求、报价或谈判中的项目才进入销售预测。
- 业务员每天需要先处理“下一步逾期”和“长时间没动”的项目，而不是重新翻所有客户。

## 数据模型

`opportunities`

- 关联：`lead_no`
- 基本：`title`、`stage`、`amount`、`currency`、`probability`
- 时间：`expected_close_date`、`next_action_date`、`last_activity_at`
- 行动：`next_action`
- LED 需求：`use_case`、`indoor_outdoor`、`width_m`、`height_m`、`quantity`、`pixel_pitch`
- 交易：`destination`、`incoterm`、`competitor`、`loss_reason`

阶段：

1. `qualified` — 已确认有项目
2. `requirements` — 正在确认规格
3. `quoted` — 已报价
4. `negotiation` — 谈判中
5. `won` — 成交
6. `lost` — 丢单

默认概率依次为 20% / 40% / 60% / 80% / 100% / 0%。

## 管道卫生规则

- 进入 `requirements`：需填写用途或像素间距。
- 进入 `quoted`：需填写金额和下一步动作。
- 进入 `negotiation`：需填写金额、预计成交日和下一步动作。
- 进入 `won`：需填写最终金额。
- 进入 `lost`：需填写丢单原因。
- 客户回复、添加跟进记录、修改商机都会刷新 `last_activity_at`。
- 停滞阈值：确认项目 7 天、确认规格 10 天、已报价 7 天、谈判 5 天。

## 用户界面

- 新页“商机管道”：开放金额、加权预测、本月预计成交、逾期动作、停滞商机。
- 表格默认优先显示逾期/停滞项目；可按阶段筛选。
- 客户详情抽屉可快速创建商机并查看该客户全部项目。
- 商机编辑器集中维护金额、日期、下一步和 LED 需求。

## 验证

- CRUD、阶段规则、加权金额、逾期/停滞、客户阶段同步均有后端测试。
- 客户新增备注与收到回复会刷新商机活跃时间。
- 前端 production build 和 Playwright 冒烟通过。

