# 营销海报生成服务

该项目实现了“厨厨房”营销海报的三段式工作流：

1. **素材输入 + 版式预览** – 在前端页面中按指定版式录入海报素材并实时预览布局。
2. **海报生成** – 前端调用 Render 托管的 FastAPI 服务，该服务会组装 Glibatree Art Designer 提示词，并在未配置真实接口时生成占位海报图。
3. **营销邮件发送** – 前端输入收件邮箱及营销话术，由 FastAPI 后端通过 SMTP 发送邮件（未配置 SMTP 时则返回“跳过发送”提示）。

前端推荐部署在 GitHub Pages，后端部署在 Render，二者通过 HTTP API 协作完成整个流程。

## 项目结构

```
ai-service/
├── app/                  # FastAPI 后端代码
│   ├── config.py         # 环境变量解析
│   ├── main.py           # API 入口
│   └── services/         # Glibatree、邮件与文案辅助逻辑
├── frontend/             # GitHub Pages 静态站点
│   ├── index.html        # 三步工作流页面
│   ├── styles.css        # 页面样式
│   └── app.js            # 与后端交互的脚本
├── requirements.txt      # 后端依赖
├── render.yaml           # Render 部署模版
└── .gitignore
```

## 本地运行后端（FastAPI）

```bash
python -m venv .venv
source .venv/bin/activate  # Windows 使用 .venv\\Scripts\\activate
pip install -r requirements.txt

# 启动服务
uvicorn app.main:app --reload
```

服务默认监听 `http://127.0.0.1:8000`，核心接口包括：

- `POST /api/generate-poster`：接收素材参数，返回版式预览、Glibatree 提示词、占位海报图（或真实 API 响应）及营销邮件草稿。
- `POST /api/send-email`：将邮件发送请求交给 SMTP 服务执行；未配置 SMTP 时返回 `status=skipped`。
- `GET /health`：健康检查。

### 可选环境变量

| 变量名 | 说明 |
| --- | --- |
| `ALLOWED_ORIGINS` | 允许的跨域来源，逗号分隔；默认 `*`。|
| `GLIBATREE_API_URL` / `GLIBATREE_API_KEY` | 设置后会尝试调用真实的 Glibatree Art Designer API，失败时会自动回退到本地占位图。|
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `EMAIL_SENDER` | 配置后端通过指定 SMTP 账号发送邮件。|
| `SMTP_USE_TLS`, `SMTP_USE_SSL` | 控制 TLS/SSL 行为（默认启用 TLS）。|

## Render 托管后端

1. 将项目推送至 GitHub，并在 Render 控制台选择 “New Web Service”。
2. 仓库选择 `ai-service`，同步分支后 Render 会读取 `render.yaml` 中的部署配置：
   - 使用 Python 环境，执行 `pip install -r requirements.txt`。
   - 以 `uvicorn app.main:app --host 0.0.0.0 --port $PORT` 启动服务。
   - 依赖列表中仅使用纯 Python 版本的 `uvicorn`，避免在 Render 免费方案上编译 `httptools/uvloop` 失败导致构建中断。
3. 在 Render 的 “Environment” 设置界面中填写所需的 Glibatree API 与 SMTP 环境变量。
4. 部署完成后记录 Render 分配的 HTTPS 域名，例如 `https://marketing-poster-api.onrender.com`。

## GitHub Pages 部署前端

仓库已经内置 GitHub Actions 工作流，自动将 `frontend/` 目录发布到 Pages。首次启用时请按照以下步骤配置：

1. 在仓库的 **Settings → Pages** 页面，将 “Build and deployment” 的 Source 改为 **GitHub Actions**。
2. 返回仓库主页，点击 **Actions** 标签页，确认 `Deploy frontend to GitHub Pages` 工作流已启用（首次会提示“我了解我的工作流”并需要手动启用）。
3. 将前端或文档改动推送到 `main` 分支，工作流会自动：
   - 检出仓库代码；
   - 上传 `frontend/` 目录作为 Pages 工件；
   - 发布到仓库的 GitHub Pages 站点。
4. 当工作流执行成功后，`https://<GitHub 用户名>.github.io/ai-service/` 即可访问最新前端页面。
5. 页面加载后，在顶部“环节 0 · 服务配置”输入 Render 后端的 HTTPS 地址，浏览器会将地址保存在 `localStorage` 中，后续刷新无需重新填写。

> 如需在本地调试，可直接通过 `file://` 打开 `frontend/index.html` 或使用任意静态服务器（例如 `python -m http.server`）。

## 使用流程

1. **环节 1 – 素材输入 + 版式预览**：填写品牌、代理、场景、功能点等信息，右侧实时更新文本版式预览，确保素材齐全。
2. **环节 2 – 生成海报**：点击“生成海报与文案”按钮，前端会调用后端接口获取 Glibatree 提示词、海报图（若未配置真实接口则展示占位图）以及营销邮件草稿。
3. **环节 3 – 邮件发送**：确认或修改邮件主题与正文，点击“发送营销邮件”。若 SMTP 已正确配置，后端会完成邮件发送；否则返回未执行的提示，方便调试。

页面默认填充了示例素材，便于快速体验。所有生成的海报图均以内嵌 Base64 数据返回，可直接预览或保存为图片文件。

## 常见问题

- **尚未配置 Glibatree API**：后端会自动生成占位海报图，版式与功能点均对应输入内容。部署正式服务时在 Render 上配置 `GLIBATREE_API_URL` 与 `GLIBATREE_API_KEY` 即可。  
- **邮件未发送成功**：检查 Render 环境变量中 SMTP 相关配置，并确认端口与 TLS 设置正确。若未配置，则接口返回 `status=skipped` 并提示“邮件服务未配置”。
- **前端跨域问题**：可通过设置 `ALLOWED_ORIGINS` 限制或允许特定域名，例如 `https://username.github.io`。

欢迎根据业务需求扩展页面样式或接入真实的 Glibatree 与邮件服务。
