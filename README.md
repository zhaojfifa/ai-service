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
│   ├── prompts/          # 提示词预设（Prompt Inspector 读取）
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
- `POST /api/r2/presign-put`：在配置 Cloudflare R2 后，为前端生成直传所需的预签名 PUT URL 与对象 Key。
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
| `S3_ENDPOINT`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`, `S3_REGION`, `S3_BUCKET`, `S3_PUBLIC_BASE`, `S3_SIGNED_GET_TTL` | （可选）启用 Cloudflare R2 存储生成的海报与上传素材。未配置时自动回退为 Base64。`S3_PUBLIC_BASE` 可指向自定义域名，`S3_SIGNED_GET_TTL` 控制私有桶生成的预签名 GET 有效期。|
| `UPLOAD_MAX_BYTES`, `UPLOAD_ALLOWED_MIME` | （可选）限制前端直传文件大小与允许的 MIME 类型，默认分别为 `20000000` 字节与 `image/png,image/jpeg,image/webp`。|

## Render 托管后端

1. 将项目推送至 GitHub，并在 Render 控制台选择 “New Web Service”。
2. 仓库选择 `ai-service`，同步分支后 Render 会读取 `render.yaml` 中的部署配置：
   - 使用 Python 环境，执行 `pip install -r requirements.txt`。
   - 以 `uvicorn app.main:app --host 0.0.0.0 --port $PORT` 启动服务。
   - 依赖列表中仅使用纯 Python 版本的 `uvicorn`，避免在 Render 免费方案上编译 `httptools/uvloop` 失败导致构建中断。
3. 在 Render 的 “Environment” 设置界面中填写所需的 Glibatree API、SMTP 与（可选的）Cloudflare R2 环境变量。
   - `ALLOWED_ORIGINS` 支持逗号分隔多个域名，后端会在启动时自动剥离路径部分。例如填写
     `https://your-account.github.io/ai-service/` 时，会被规范化为 `https://your-account.github.io`，避免跨域校验失败。
   - 若通过 OpenAI 1.x SDK 调 Glibatree，请提供 `GLIBATREE_API_KEY`，并根据实际需求配置 `GLIBATREE_CLIENT=openai`、`GLIBATREE_MODEL` 以及（可选的）`GLIBATREE_PROXY`。SDK 现在会自动构建 httpx 客户端并兼容代理参数。
   - 如需将生成的成品图与用户上传的素材统一存放到 Cloudflare R2，以避免超大 JSON 造成浏览器连接中断，可额外提供：
     `S3_ENDPOINT`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`, `S3_REGION`（默认 `auto`）、`S3_BUCKET`、`S3_PUBLIC_BASE`（可选，自定义公开域名）与 `S3_SIGNED_GET_TTL`（私有桶生成预签名 GET 的有效期秒数）。前端还可以通过 `UPLOAD_MAX_BYTES`、`UPLOAD_ALLOWED_MIME` 控制直传文件大小与 MIME 类型。未配置这些变量时，接口会保持原有的 Base64 返回方式，便于本地教学或离线调试。
   - 配置完成后，前端会在上传素材时先请求 `POST /api/r2/presign-put` 获取预签名 PUT URL，再由浏览器直传到 R2；生成海报时只需把对象 Key 发送给后端即可。
4. 部署完成后记录 Render 分配的 HTTPS 域名，例如 `https://marketing-poster-api.onrender.com`。

## Cloudflare Worker 反向代理

部署在 GitHub Pages 的前端会优先调用 Cloudflare Worker，以规避跨域预检和 Render 免费实例的冷启动延迟。仓库根目录的 `worker/worker.js` 已提供代理脚本，核心要点如下：

- 仅转发 `/api/*` 与 `/health` 请求，其余路径直接返回 `404 Not found`。
- `GET /api/health` 在 Worker 内部直接返回 `200 ok`，前端能在 1 个 RTT 内判断 Worker 是否可用；其它 `/api/*` 和 `/health` 请求都会透传到 Render。
- 所有响应统一注入：
  - `Access-Control-Allow-Origin`（默认 `*`，可通过 `ALLOWED_ORIGINS` 限定 GitHub Pages 域名与 Worker 自身域名）；
  - `Access-Control-Allow-Methods: GET,POST,PUT,PATCH,DELETE,OPTIONS`；
  - `Access-Control-Allow-Headers: *`；
  - `Access-Control-Expose-Headers: *`；
  - `Access-Control-Max-Age: 86400`；
  - 预检 `OPTIONS` 请求固定返回 204。
- Worker 会自动剥离浏览器附带的 Cookie，禁止向 Render 透传凭据。

> **部署步骤**
>
> 1. 在 Cloudflare 控制台创建新的 Worker，并将 `worker/worker.js` 粘贴为脚本内容。
> 2. 配置 Worker 环境变量：
>    - `RENDER_ORIGIN`：Render 服务的根地址，例如 `https://marketing-poster-api.onrender.com`；
>    - `ALLOWED_ORIGINS`：允许的前端域名，支持 JSON / 逗号分隔写法，例如 `"[\"https://username.github.io\",\"https://render-proxy.username.workers.dev\"]"`；
>    - 如需自定义跨域头，可选填 `CORS_ALLOW_METHODS`、`CORS_ALLOW_HEADERS`、`CORS_EXPOSE_HEADERS`、`CORS_MAX_AGE`。
> 3. 为 Worker 绑定 `render-proxy.<your-subdomain>.workers.dev` 或自定义域名，确保 GitHub Pages 能访问。

## 前端的基址优先级与健康探测

- `getApiCandidates` 会按 “手动输入 → Worker → Render → 其它备选” 的优先级收集基址，并缓存最近 60 秒的健康状态。
- `warmUp` / `pickHealthyBase` 会先探测 `GET /api/health`（Worker 快速响应），若 404 再回退 `GET /health`（Render）。
- `postJsonWithRetry` 允许传入相对路径或完整的绝对 URL；若传入绝对地址，会直接发送请求而不会与基址重复拼接。
- 在发起 `POST /api/generate-poster` 之前，前端会校验请求体大小不超过 300KB，且素材字段不能携带 `data:` 协议的 Base64 字符串，避免浏览器因超大 JSON 断开连接。

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

1. **环节 1 – 素材输入 + 版式预览**：在 `index.html` 顶部先选择锁版模板，页面会加载模板规范并展示挂点预览。表单会读取模板的 `materials` 元数据：`type=image` 的槽位若声明 `allowsPrompt=true` 会提供“上传图像 / 文字生成”切换，若 `allowsPrompt=false` 则仅保留上传项；`type=text` 或 `allowsUpload=false` 则强制走文字描述，由 AI 生成素材。底部小图的数量、提示语和默认占位也由模板的 `count`、`label`、`promptPlaceholder` 定义，必须准备足量素材才能继续流程。点击“构建版式预览”后即可在页面下方看到分区预览与结构说明，数据会暂存于浏览器 `sessionStorage`，方便跳转下一环节。若后端已配置 Cloudflare R2 环境变量，页面会在上传素材时先调用 `/api/r2/presign-put` 获取预签名 URL，并由浏览器将文件直接写入 R2，仅把对象 Key 保存在会话状态里；未配置时则继续沿用本地 Data URL。
2. **环节 2 – 生成海报**：`stage2.html` 会读取上一环节的素材概览，并锁定已选模板（如需更换可返回环节 1）。右侧 Canvas 会根据模板与当前素材渲染挂点示意，同时提供“Prompt Inspector”面板：可以为场景、产品与底部小图选择预设、调整正/负向提示词、设置 Seed 并一键 A/B 生成。点击“生成海报与文案”后，前端会携带素材模式、提示词配置与模板 ID 调用 FastAPI。后端先依据模板元数据判断哪些槽位需要 AI 生成或处理，再执行锁版渲染并仅在蒙版透明区调用 OpenAI Images Edit 补足背景。接口会返回结构化提示词、主图与可选变体、评分信息以及营销文案，页面将结果缓存以便跳转下一环节或再次生成。
3. **环节 3 – 邮件发送**：`stage3.html` 会显示最新海报与提示词，填写客户邮箱后点击“发送营销邮件”。若 SMTP 已正确配置，后端会完成发送；否则返回未执行的提示，便于调试。

## 模板锁版与局部生成

- **模板目录**：`frontend/templates/` 为每套模板提供 `template.png`（锁死元素）、`mask_*.png`（AI 可编辑的透明区域）与 `spec.json`（槽位坐标、尺寸及 `materials` 定义）。`materials` 字段会为每个槽位提供 `label`、`type`、`count`、`allowsPrompt`、`allowsUpload`、`promptPlaceholder` 等元数据，前端据此渲染表单文案、限制素材数量并切换上传/AI 模式，后端则据此判断哪些槽位需要在渲染前调用 AI 生成素材。
- **提示词预设**：`frontend/prompts/presets.json` 汇总了常见的 Prompt Preset（如白底产品、厨房场景、灰度小图等），Prompt Inspector 会自动加载并允许按模板设定默认 Preset；后端也会回传经标准化后的 Prompt Bundle，方便在多端保持一致。若需要扩展主题，可在该文件中新建预设并提交。
- **品牌规范**：`docs/brand-guides/kitchen_campaign.md` 描述了品牌色板、字号、连线样式等规则。Canvas 预览与 Pillow 渲染均按照该文档执行。
- **后端流水线**：`app/services/glibatree.py` 会先调用 `prepare_poster_assets`，对所有标记为“文字生成”的槽位请求 OpenAI 生成素材（缺少 API Key 时自动跳过），随后按模板绘制 Logo、标题、功能点连线与底部小图，再通过 OpenAI Images Edit（`image + mask`）仅在透明区域补足背景氛围，失败时回退到同模板的本地渲染图。
- **质量守护**：生成完成后会把蒙版外的像素覆盖回程序绘制的元素，防止模型篡改 Logo、标题或功能点。模板选择也会同步保存在 `sessionStorage`，便于多次生成或返回环节 1 调整素材。

页面默认填充了示例素材，便于快速体验。若部署环境已配置 Cloudflare R2，后端会将生成海报上传到对象存储并返回公开 URL；否则保持以 Base64 数据返回的旧行为。浏览器还会缓存模板 ID、素材模式以及 `gallery_limit` 等信息，以便多次往返页面时自动匹配模板要求。

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
