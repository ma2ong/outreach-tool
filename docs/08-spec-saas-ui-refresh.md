# SaaS 级 GUI 改版 + 名单数据完整化 + 深挖抓取增强 — Spec

> 2026-07-07 与 Allen 确认：范围 = **自用但界面做到 SaaS 产品级**（不做多租户/登录/计费）；视觉 = **深浅双主题可切换**。方案 = 渐进改造现有 React 前端，不换框架、不加 UI 库依赖。

## 问题

1. 界面是单页堆叠 + 内联样式，未达产品级。
2. 名单表格不显示电话/WhatsApp/IG/FB（数据库字段都有、很多老数据有值），无法点击跳转。
3. 已触达/未触达标记不清晰，无"未触达"筛选（选发送目标时最需要）。
4. 深挖（Discovery）只抓邮箱，不抓电话/WhatsApp/IG/FB/LinkedIn。

## 设计

### 1. 页面结构（SPA，state 切页，无路由依赖）

侧边栏导航 + 顶栏（产品名 + 主题切换按钮，localStorage 记住）：

| 页面 | 内容 |
|---|---|
| 仪表盘 | 统计卡（总数/各渠道已触达/已回复/今日额度）+ 国家分布 |
| 客户库 | 筛选栏 + 完整列表格 + 勾选后底部浮出触达操作条（原 OutreachPanel） |
| 客户开发 | 搜索深挖 + 候选表（加电话/IG/FB 列）+ 导入 |
| 渠道连接 | 原 ConnectionPanel |

**客户库表格列**：公司(官网链接) / 国家 / 城市 / 邮箱 / 电话(点击开 wa.me) / IG(点击跳 instagram.com/handle) / FB(点击跳转) / 渠道状态徽章。
**状态徽章**：每渠道一枚——绿=已回复、蓝=已触达、灰=未触达；点击"已触达"徽章 → 标记已回复（沿用现有 API）。
**筛选**：国家 / 渠道+状态组合（含"未触达"）/ 有电话·有IG·有邮箱 / 搜索。

### 2. 深挖抓取增强（后端）

`enrich_domain` 从 contact 页/首页提取：`tel:` 链接、`wa.me` 链接、国际电话正则、`instagram.com/<handle>`、`facebook.com/<page>`、`linkedin.com/company|in/<x>`。Candidate/import 全字段入库。诚实边界：官网没留的信息抓不到。

### 3. 筛选后端

`list_leads` 新增：`status=untouched`（指定渠道时=该渠道无 messaged/replied 记录；未指定渠道时=任何渠道都没发过）+ `has=phone|instagram|email`。

### 4. 主题系统

`theme.css` 定义 CSS 变量两套 token（`[data-theme="dark"]` / `[data-theme="light"]`），组件全部改用变量 + 公共 class（卡片/按钮/输入/表格/徽章），去掉散落的内联颜色。

### 5. 测试

后端新查询/enrich 全 TDD；前端 tsc + build + smoke（选择器随新布局更新）；完成后起服务器截图人工确认两套主题。

## 不做（YAGNI）

多租户/登录/计费、表格排序、图表库、路由库、FB/LinkedIn 发送渠道。
