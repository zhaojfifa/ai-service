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
│   ├── index.html        # 环节 1：素材输入与版式预览
│   ├── stage2.html       # 环节 2：AI 海报生成
│   ├── stage3.html       # 环节 3：营销邮件发送
│   ├── styles.css        # 页面样式
│   ├── app.js            # 多页面脚本，负责状态存储与 API 交互
│   └── templates/        # 锁版模板 Base64 文本、蒙版与规范（供前后端共用）
├── docs/
│   └── brand-guides/     # 品牌色板、字体与版式规范
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
| `GLIBATREE_CLIENT` | 可选，取值 `http`（默认根据 URL 自动判定）或 `openai`。当使用 OpenAI 1.x SDK 代理 Glibatree 接口时请选择 `openai`。|
| `GLIBATREE_MODEL` | 可选，指定 OpenAI 生成图像时使用的模型名称，默认 `gpt-image-1`。|
| `GLIBATREE_PROXY` | 可选，HTTP(S) 代理地址；配置后会通过 `httpx` 客户端转发至 OpenAI SDK。|
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `EMAIL_SENDER` | 配置后端通过指定 SMTP 账号发送邮件。|
| `SMTP_USE_TLS`, `SMTP_USE_SSL` | 控制 TLS/SSL 行为（默认启用 TLS）。|

## Render 托管后端

1. 将项目推送至 GitHub，并在 Render 控制台选择 “New Web Service”。
2. 仓库选择 `ai-service`，同步分支后 Render 会读取 `render.yaml` 中的部署配置：
   - 使用 Python 环境，执行 `pip install -r requirements.txt`。
   - 以 `uvicorn app.main:app --host 0.0.0.0 --port $PORT` 启动服务。
   - 依赖列表中仅使用纯 Python 版本的 `uvicorn`，避免在 Render 免费方案上编译 `httptools/uvloop` 失败导致构建中断。
3. 在 Render 的 “Environment” 设置界面中填写所需的 Glibatree API 与 SMTP 环境变量。
   - `ALLOWED_ORIGINS` 支持逗号分隔多个域名，后端会在启动时自动剥离路径部分。例如填写
     `https://your-account.github.io/ai-service/` 时，会被规范化为 `https://your-account.github.io`，避免跨域校验失败。
   - 若通过 OpenAI 1.x SDK 调 Glibatree，请提供 `GLIBATREE_API_KEY`，并根据实际需求配置 `GLIBATREE_CLIENT=openai`、`GLIBATREE_MODEL` 以及（可选的）`GLIBATREE_PROXY`。SDK 现在会自动构建 httpx 客户端并兼容代理参数。
4. 部署完成后记录 Render 分配的 HTTPS 域名，例如 `https://marketing-poster-api.onrender.com`。

## GitHub Pages 部署前端

仓库已经内置 GitHub Actions 工作流，自动将 `frontend/` 目录发布到 Pages。首次启用时请按照以下步骤配置：

1. 在仓库的 **Settings → Pages** 页面，将 “Build and deployment” 的 Source 改为 **GitHub Actions**。
2. 返回仓库主页，点击 **Actions** 标签页，确认 `Deploy frontend to GitHub Pages` 工作流已启用（首次会提示“我了解我的工作流”并需要手动启用）。
3. 将前端或文档改动推送到 `main` 分支，工作流会自动：
   - 检出仓库代码；
   - 执行 `scripts/decode_template_assets.py`，把提交中的 Base64 文本解码为实际的模板 PNG/蒙版；
   - 上传 `frontend/` 目录作为 Pages 工件；
   - 发布到仓库的 GitHub Pages 站点。
4. 当工作流执行成功后，`https://<GitHub 用户名>.github.io/ai-service/` 即可访问最新前端页面。
5. 页面加载后，在页头右上角的“后端 API 地址”输入框中填写 Render 后端的 HTTPS 地址，浏览器会将地址保存在 `localStorage` 中，后续刷新无需重新填写。

> 如需在本地调试，可直接通过 `file://` 打开 `frontend/index.html` 或使用任意静态服务器（例如 `python -m http.server`）。

## 模板资源解码

由于 GitHub 不再直接存储二进制模板图片，`frontend/templates/` 中的 `*.b64` 文件保存了 Base64 文本。需要在本地或流水线中执行
以下脚本将其还原为 PNG：

```bash
python scripts/decode_template_assets.py
```

脚本会在同目录下生成对应的 `.png` 文件（已在 `.gitignore` 中忽略），生成多次也不会重复写入。后端服务会在缺少 PNG 时自动
从 `.b64` 文件解码模板与蒙版，当前端页面需要直接引用模板图片或蒙版时，请确保已执行上述脚本。

## 使用流程

1. **环节 1 – 素材输入 + 版式预览**：在 `index.html` 顶部先选择锁版模板，页面会加载模板规范并展示挂点预览。表单会读取模板的 `materials` 元数据：`type=image` 的槽位若声明 `allowsPrompt=true`，会显示“上传图像 / 文字生成”模式切换；若为 `allowsPrompt=false`，则仅保留上传项。底部小图的数量、提示语和默认占位也由模板的 `count`、`label`、`promptPlaceholder` 定义，必须准备足量素材才能继续流程。点击“构建版式预览”后即可在页面下方看到分区预览与结构说明，数据会暂存于浏览器 `sessionStorage`，方便跳转下一环节。
2. **环节 2 – 生成海报**：`stage2.html` 会读取上一环节的素材概览，并锁定已选模板（如需更换可返回环节 1）。右侧 Canvas 会根据模板与当前素材渲染挂点示意，点击“生成海报与文案”后，前端会携带各素材的模式信息调用 FastAPI。后端会在需要时先通过 OpenAI 生成缺失的场景、产品或底部小图，再执行模板渲染，返回最新的 Glibatree 提示词、海报预览（或本地回退图）以及营销文案，并将结果保存供下一环节使用。
3. **环节 3 – 邮件发送**：`stage3.html` 会显示最新海报与提示词，填写客户邮箱后点击“发送营销邮件”。若 SMTP 已正确配置，后端会完成发送；否则返回未执行的提示，便于调试。

## 模板锁版与局部生成

- **模板目录**：`frontend/templates/` 为每套模板提供 `template.png`（锁死元素）、`mask_*.png`（AI 可编辑的透明区域）与 `spec.json`（槽位坐标、尺寸及 `materials` 定义）。`materials` 字段会为每个槽位提供 `label`、`type`、`count`、`allowsPrompt`、`promptPlaceholder` 等元数据，前端据此渲染表单文案、限制素材数量并切换上传/AI 模式，后端则据此判断哪些槽位需要在渲染前调用 AI 生成素材。
- **品牌规范**：`docs/brand-guides/kitchen_campaign.md` 描述了品牌色板、字号、连线样式等规则。Canvas 预览与 Pillow 渲染均按照该文档执行。
- **后端流水线**：`app/services/glibatree.py` 会先调用 `prepare_poster_assets`，对所有标记为“文字生成”的槽位请求 OpenAI 生成素材（缺少 API Key 时自动跳过），随后按模板绘制 Logo、标题、功能点连线与底部小图，再通过 OpenAI Images Edit（`image + mask`）仅在透明区域补足背景氛围，失败时回退到同模板的本地渲染图。
- **质量守护**：生成完成后会把蒙版外的像素覆盖回程序绘制的元素，防止模型篡改 Logo、标题或功能点。模板选择也会同步保存在 `sessionStorage`，便于多次生成或返回环节 1 调整素材。

页面默认填充了示例素材，便于快速体验。所有生成的海报图均以内嵌 Base64 数据返回，可直接预览或保存为图片文件。浏览器还会缓存模板 ID、素材模式以及 `gallery_limit` 等信息，以便多次往返页面时自动匹配模板要求。

## 命令行快速体验

若希望在终端快速验证三段式流程，可使用根目录下的 `poster_workflow.py` 脚本：

1. 准备配置文件（项目已提供 `examples/sample_workflow.json` 作为示例），字段与前端填写内容一致：
   - `poster`：对应 `PosterInput` 的各项素材与文案字段，支持可选的 Base64 图片数据，并包含 `template_id`、素材模式（`scenario_mode`/`product_mode`）以及带文案或 AI 描述的 `gallery_items`；
   - `email`：可选，包含收件人、主题与自定义正文，未配置时脚本会生成默认营销话术。
2. 运行脚本并指定输入文件，可选地指定输出目录保存结果：

   ```bash
   python poster_workflow.py --input examples/sample_workflow.json --output-dir out/
   ```

   终端会依次输出版式预览、Glibatree 提示词、海报生成信息及营销邮件草稿；若素材标记为“文字生成”，脚本会在生成海报前调用 OpenAI 生成对应槽位的图片。`out/` 目录中会生成对应的 `.txt` 文本与海报图片。
3. 若在环境变量中正确配置了 SMTP（参见上文），可以追加 `--send-email` 直接完成邮件发送：

   ```bash
   python poster_workflow.py --input config.json --send-email
   ```

   当未配置邮件服务时脚本会提示“邮件服务未配置，已跳过真实发送”，便于在开发环境调试。

## 常见问题

- **尚未配置 Glibatree API**：后端会自动生成占位海报图，版式与功能点均对应输入内容。部署正式服务时在 Render 上配置 `GLIBATREE_API_URL` 与 `GLIBATREE_API_KEY` 即可。
- **邮件未发送成功**：检查 Render 环境变量中 SMTP 相关配置，并确认端口与 TLS 设置正确。若未配置，则接口返回 `status=skipped` 并提示“邮件服务未配置”。
- **前端跨域问题**：可通过设置 `ALLOWED_ORIGINS` 限制或允许特定域名，例如 `https://username.github.io`。
- **本地缺少 `origin` 远端**：某些教学/沙箱环境拉取仓库时不会自动保存 GitHub 远端。若运行 `git fetch origin` 报错，可执行 `git remote add origin https://github.com/<用户名>/ai-service.git`（或 SSH 地址）后再同步，确保 `git remote -v` 能看到 `origin`。

欢迎根据业务需求扩展页面样式或接入真实的 Glibatree 与邮件服务。
