# 客户开发 / 触达工具 (Phase 1 MVP)

把 LED B2B 客户开发工作流（搜索候选 → 深挖验证 → 入库去重 → 多渠道触达 → 看板）
产品化成一个单用户本地网页应用。已交付：客户库看板（S1+S2）、邮件触达面板（S3）、
客户开发面板/搜索+深挖+入库（S4）。

## 双击即用（免命令行）
1. **第一次**：双击 `setup.bat`（装依赖 + 导入历史客户 + 构建界面，约几分钟）。
2. **以后每次**：双击 `start.bat` —— 自动启动服务并打开浏览器看板。
   工作时保留弹出的 “outreach-tool-server” 窗口；关掉它即停止工具。

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
- 后端：`cd backend && python -m pytest`
- 前端冒烟：启动后端后 `cd frontend && npx playwright test`

## 架构
- `backend/app/db.py` — SQLite schema + 连接
- `backend/app/repository.py` — 全部 SQL 查询（list/get/find_duplicate/stats）
- `backend/app/migrate.py` — 从 `output/leads` 的 79 文件链 + pipeline JSON 导入
- `backend/app/api/` — 只读 REST：`/api/leads`、`/api/stats`
- `frontend/src/` — React 看板（StatCards + LeadsTable）

## 后续阶段（未实现）
- S3 触达引擎 + Email 发送 + 战役运行器
- S4 发现/深挖引擎（界面里搜索+验证+入库）
- S5 CDP 渠道适配（IG/WA/FB 半自动，含限速与渠道健康）
