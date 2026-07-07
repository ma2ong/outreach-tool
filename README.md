# Maxcolor 客户开发系统 (outreach-tool)

把 LED B2B 客户开发工作流（搜索候选 → 深挖验证 → 入库去重 → 多渠道触达 → 看板）
产品化成一个单用户本地网页应用。SaaS 级界面：侧边栏四页 + 深浅双主题。

## 功能一览
| 页面 | 能力 |
|---|---|
| 仪表盘 | 统计卡（总数/各渠道已发/已回复）+ 今日 WA·IG 发送额度 + 国家分布 |
| 客户库 | 全列表格：公司(官网链接)/国家/城市/邮箱(mailto)/电话(点击打开 wa.me)/IG/FB(可点跳转)/三渠道状态徽章（绿=已回复、蓝=已触达、灰=未触达，点蓝色即标记已回复）。筛选：国家/渠道/状态(含未触达)/有电话·IG·邮箱/搜索。勾选后底部浮出触达操作条（Email/WhatsApp/Instagram 群发） |
| 客户开发 | 关键词搜索 → 深挖官网自动提取邮箱/电话/WhatsApp/IG/FB/LinkedIn → 候选表去重 → 勾选导入 |
| 渠道连接 | WhatsApp 扫码 / Instagram 弹窗登录，一次登录长期保持（Playwright 持久化浏览器） |

发送防护：单批硬上限 20 条、每渠道日上限 40、强制随机限速、WA/IG 自动附带案例图、已回复客户自动排除。

## 双击即用（免命令行）
1. **第一次**：双击 `setup.bat`（装依赖 + 导入历史客户 + 构建界面，约几分钟）。
2. **以后每次**：双击 `start.bat` —— 自动启动服务并打开浏览器看板。
   工作时保留弹出的 "outreach-tool-server" 窗口；关掉它即停止工具。

## 命令行方式（可选）
一次性准备：
1. `cd backend && python -m pip install -r requirements.txt`
2. `cd backend && python -m app.migrate`
3. `cd frontend && npm install && npm run build`

启动：
```
cd backend && python -m uvicorn app.main:app --port 8000
```
浏览器打开 http://127.0.0.1:8000

## 开发模式（热更新）
- 后端：`cd backend && python -m uvicorn app.main:app --reload --port 8000`
- 前端：`cd frontend && npm run dev`（自动代理 /api 到 8000）

## 测试
- 后端：`cd backend && python -m pytest`（75 用例）
- 前端冒烟：启动后端后 `cd frontend && npx playwright test`（7 用例，只读+勾选，绝不触发真实发送）

## 架构
- `backend/app/db.py` — SQLite schema + 连接 · `repository.py` — 全部 SQL（含 untouched/has 筛选）
- `backend/app/enrich.py` — 官网抓取（邮箱/电话/wa.me/IG/FB/LinkedIn）· `discovery.py` — 搜索深挖管道
- `backend/app/outreach.py` / `channel_outreach.py` — Email / WA·IG 发送编排（限速+批量上限+日额度）
- `backend/app/playwright_engine.py` — 每渠道持久化有头浏览器
- `backend/app/api/` — REST：leads / stats / send / discover / channels
- `frontend/src/theme.css` — 双主题 design tokens；`App.tsx` — AppShell + 页面切换；`components/` — Dashboard / LeadsTable / OutreachPanel / DiscoveryPanel / ConnectionPanel

## 已知边界
- 官网没留的联系方式抓不到（深挖只提取公开信息）。
- WA/IG 自动私信违反平台 ToS，有封号风险；限速+批量上限只能降低、不能消除。
- 多租户/登录/计费 = Phase 2，未开始。
