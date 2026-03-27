# AI-Service Render 恢复部署专项 Review

> 评审目标：以最小变更恢复 ai-service 在 Render 的部署，确保前后端服务正常工作。
> 评审日期：2026-03-22

---

## 一、Render 部署配置

### 1.1 后端 Web Service

| 项目 | 值 |
|---|---|
| **服务名** | `marketing-poster-api` |
| **类型** | Web Service (Python) |
| **Plan** | Free |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| **入口文件** | `app/main.py` → FastAPI `app` |
| **Health Check** | `GET /health` 或 `GET /healthz` → `{"ok": true}` |
| **Persistent Disk** | ❌ 未配置（Free plan 不支持） |
| **Preflight 脚本** | 无独立脚本；GCP 凭据写入在 Python 启动时自动执行（见 2.3 节） |

#### ⚠️ Build Command 缺失项

当前 `buildCommand: pip install -r requirements.txt` 缺少字体下载，导致 CJK 渲染回退到点阵字体。**必须修复**：

```yaml
buildCommand: pip install -r requirements.txt && bash scripts/fetch_fonts.sh app/assets/fonts
```

### 1.2 前端静态站点

前端有 **两种部署方式**，当前并存：

| 方式 | 机制 | 状态 |
|---|---|---|
| **A. Render 后端内嵌** | `app/main.py` 末尾 `app.mount("/", StaticFiles(directory=frontend/, html=True))` | ✅ 已配置；后端启动即可访问 |
| **B. GitHub Pages** | `.github/workflows/deploy-frontend.yml` → 构建 `site/` 目录 → deploy-pages | ✅ 已配置；push main 且 `frontend/**` 变更时触发 |

**恢复建议**：两套可以并存。Render 后端根路径 `/` 同时提供前端页面和 API。GitHub Pages 作为独立前端入口。

### 1.3 GitHub Actions 部署脚本检查

`deploy-frontend.yml` 要求：
- ✅ `frontend/templates/registry.json` — 已存在
- ✅ `frontend/.nojekyll` — workflow 自动 touch
- ✅ `site/templates/` — workflow 自动从 `frontend/templates/` 复制

**无阻塞问题。**

---

## 二、环境变量全量盘点

### 2.1 🔴 运行必需（缺失 → 服务起不来）

| 变量 | 用途 | 引用模块 | 缺失表现 | 是否 Secret |
|---|---|---|---|---|
| `GCP_PROJECT_ID` | GCP 项目 ID | vertex_imagen.py, vertex_imagen3.py, main.py | Vertex 初始化失败，v1 海报全部 500 | ❌ |
| `GCP_KEY_B64` | Base64 编码的 GCP 服务账号 JSON | vertex_imagen.py, vertex_imagen3.py | 启动时无法认证 GCP，所有 Vertex 调用失败 | ✅ Secret |

> **GCP 凭据三选一**：`GCP_KEY_B64`（推荐，启动时自动写入 `/opt/render/project/src/gcp-key.json`）、`GOOGLE_APPLICATION_CREDENTIALS_JSON`（原始 JSON 字符串）、或 Render Secret File 挂载到 `/etc/secrets/service-account.json`。

### 2.2 🔴 存储必需（缺失 → 图片无法保存/读取）

| 变量 | 用途 | 默认值 | 是否 Secret |
|---|---|---|---|
| `R2_ENDPOINT` 或 `S3_ENDPOINT` | Cloudflare R2 API 端点 | 无 | ❌ |
| `R2_BUCKET` 或 `S3_BUCKET` | 存储桶名称 | 无 | ❌ |
| `R2_ACCESS_KEY_ID` 或 `S3_ACCESS_KEY` | 存储访问密钥 | 无 | ✅ Secret |
| `R2_SECRET_ACCESS_KEY` 或 `S3_SECRET_KEY` | 存储密钥 | 无 | ✅ Secret |
| `R2_PUBLIC_BASE` 或 `S3_PUBLIC_BASE` | 公开访问 URL 前缀 | 无（缺失时走 presigned URL） | ❌ |

> 缺失任一 Endpoint/Bucket/Key → `store_image_and_url()` 调用失败 → 所有图片生成返回 500。

### 2.3 🟡 鉴权/CORS 必需（缺失 → 前端 401/CORS 拦截）

| 变量 | 用途 | 默认值 | 说明 |
|---|---|---|---|
| `CORS_ALLOW_ORIGINS` | 允许的前端 Origin | `*`（但代码中硬编码了 `zhaojfifa.github.io` 和 `ai-service-x758.onrender.com`） | 如用新 Render 域名需更新 |
| `GOOGLE_APPLICATION_CREDENTIALS` | GCP 凭据文件路径 | render.yaml 写死 `/etc/secrets/service-account.json` | 如用 `GCP_KEY_B64` 方式则由启动脚本自动设置，无需手动配 |

### 2.4 🟡 模型/供应商必需（缺失 → 主场景降级）

| 变量 | 用途 | 默认值 | 缺失表现 |
|---|---|---|---|
| `GCP_LOCATION` | GCP 区域 | `us-central1` | 可不配，用默认值 |
| `VERTEX_IMAGEN_MODEL_GENERATE` | 生成模型 | `imagen-3.0-generate-001` | 可不配，用默认值 |
| `VERTEX_IMAGEN_MODEL_EDIT` | 编辑模型 | `imagen-3.0-edit` (render.yaml) / `imagen-3.0-capability-001` (代码) | ⚠️ render.yaml 与代码默认值不一致 |
| `VERTEX_IMAGEN_ENABLE_EDIT` | 启用 inpainting | `false` | 不影响主生成链路 |
| `VERTEX_TIMEOUT_SECONDS` | 超时 | `60` | 可不配 |
| `VERTEX_SAFETY_FILTER_LEVEL` | 安全过滤 | `block_some` | 可不配 |
| `VERTEX_SEED` | 种子 | `0`（随机） | 可不配 |

### 2.5 🟢 可选（缺失不阻塞启动）

| 变量 | 用途 | 缺失表现 |
|---|---|---|
| `FIREFLY_CLIENT_ID` + `FIREFLY_CLIENT_SECRET` | Adobe Firefly（Poster 2.0 背景） | 自动回退 Vertex Imagen3 |
| `SMTP_HOST` / `SMTP_USERNAME` / `SMTP_PASSWORD` | 邮件发送 | `/api/send-email` 返回错误，不影响其他路由 |
| `EMAIL_ENABLED` | 邮件开关 | 默认 `true` |
| `LOG_LEVEL` | 日志级别 | 默认 `INFO` |
| `RETURN_BINARY_DEFAULT` | 允许二进制图片响应 | 默认 `0`（禁用） |
| `UPLOAD_MAX_BYTES` | 上传大小限制 | 默认 `20MB` |
| `MAX_JSON_BYTES` | 请求体限制 | 默认 `200KB` |
| `TEMPLATE_POSTER_DIR` | 模板目录覆盖 | 用代码内默认路径 |
| `POSTER_FONT_DIRS` / `KP_FONT_DIR` | 字体目录 | 用 `app/assets/fonts` + 系统字体 |
| `DEBUG_KITPOSTER_MASK` | 调试蒙版 | 无调试输出 |

### 2.6 ⚪ 历史遗留/可疑/建议停用

| 变量 | 状态 | 说明 |
|---|---|---|
| `IMAGE_BACKEND=openai` | .env.example 中存在 | 代码中 `IMAGE_PROVIDER_NAME` 硬编码为 `"vertex"`，此变量未被使用 |
| `OPENAI_API_KEY` / `OPENAI_BASE_URL` / `OPENAI_MODEL` | .env.example 中存在 | 仅 `app/image_gen.py` 和 `config.py` 引用；当前主链路不走 OpenAI |
| `GLIB_URL` / `GLIB_KEY` | legacy_api.py | 仅遗留 API 使用，恢复阶段可忽略 |
| `IMAGE_API_BASE` / `IMAGE_API_KEY` / `IMAGE_API_KIND` | image_provider.py | 工厂模式选择 provider，当前默认走 Vertex |
| `GOOGLE_API_KEY` | genai_provider.py | Google GenAI 备用通道，非主链路 |
| `VERTEX_OUTPUT_GCS_URI` | vertex_provider.py | GCS 输出路径，当前未使用 |

---

## 三、入口与路由一致性

### 3.1 唯一后端入口

**`app/main.py:app`** — 这是唯一的 FastAPI 实例，Render 启动 `uvicorn app.main:app`。

⚠️ 仓库根目录存在 `legacy_api.py`，但**未被 render.yaml 引用**，不会被部署。

### 3.2 API 路由清单

| 路由 | 版本 | 说明 | 恢复优先级 |
|---|---|---|---|
| `GET /health` `GET /healthz` | - | 健康检查 | P0 |
| `GET /` | - | 前端页面 / 服务状态 | P0 |
| `POST /api/generate-poster` | v1 | 主海报生成（Vertex inpainting） | P0 |
| `POST /api/image/generate` | v1 | 文生图 | P1 |
| `POST /api/imagen/generate` | v1 | 文生图（别名） | P1 |
| `POST /api/generate-slot-image` | v1 | 槽位图生成 | P1 |
| `POST /api/r2/presign-put` | v1 | R2 上传签名 | P1 |
| `POST /api/template-posters` | v1 | 模板上传 | P2 |
| `GET /api/template-posters` | v1 | 模板列表 | P2 |
| `POST /api/send-email` | v1 | 邮件 | P2 |
| `POST /api/v2/generate-poster` | v2 | Poster 2.0（Firefly/Pillow） | P2 |
| `GET /debug/vertex/ping` | - | 调试 | P2 |
| `GET /debug/vertex/generate` | - | 调试 | P2 |

### 3.3 恢复期风险

1. **CORS 域名变更**：如果 Render 重建后域名变了（不再是 `ai-service-x758.onrender.com`），需要：
   - 更新 `main.py:294` 的 `DEFAULT_CORS_ORIGINS` 硬编码
   - 或在 Render env 中设置新域名到 `CORS_ALLOW_ORIGINS`

2. **前端 API 地址**：`frontend/app.js` 中可能硬编码了后端 URL，需确认是否使用相对路径。

---

## 四、存储与路径

### 4.1 关键路径映射

| 路径 | 类型 | 用途 | 风险 |
|---|---|---|---|
| `/opt/render/project/src/gcp-key.json` | 临时文件 | `GCP_KEY_B64` 解码写入 | Render 重建后无状态，每次启动自动重写 ✅ |
| `/etc/secrets/service-account.json` | Secret File | render.yaml 中引用 | 需在 Render Dashboard 的 Secret Files 中重新配置 |
| `app/assets/fonts/` | 构建产物 | CJK 字体文件 | ⚠️ 当前 buildCommand 未下载字体 |
| `frontend/` | 静态文件 | 前端 HTML/JS/CSS | 随代码部署，无风险 |
| `/tmp/kitposter_debug/` | 临时目录 | 调试蒙版输出 | 仅 `DEBUG_KITPOSTER_MASK` 开启时使用 |

### 4.2 对象存储 Key 模式

| 前缀 | 来源 | 说明 |
|---|---|---|
| `uploads/YYYY/MM/DD/uuid/filename` | `r2_client.make_key()` | 用户上传 |
| `imagen/YYYY/MM/DD/rid/index.png` | `api_imagen_generate` | 文生图输出 |
| `poster2/bg/{trace_id}_{seed}.png` | `poster2/background.py` | Poster 2.0 背景 |

### 4.3 Persistent Disk

**当前未使用**。所有持久化数据走 R2/S3 对象存储。Render 重建不需要恢复磁盘。

---

## 五、Provider / Model 主链路恢复优先级

### 5.1 必须先恢复

| Provider | 依赖 Env | 影响路由 |
|---|---|---|
| **Vertex Imagen3** | `GCP_PROJECT_ID` + `GCP_KEY_B64` | `/api/generate-poster`, `/api/image/generate`, `/api/generate-slot-image` |
| **R2 对象存储** | `R2_ENDPOINT` + `R2_BUCKET` + `R2_ACCESS_KEY_ID` + `R2_SECRET_ACCESS_KEY` | 所有图片保存和读取 |

### 5.2 可后置恢复

| Provider | 依赖 Env | 说明 |
|---|---|---|
| **Adobe Firefly** | `FIREFLY_CLIENT_ID` + `FIREFLY_CLIENT_SECRET` | 仅 Poster 2.0 背景；缺失时自动回退 Vertex |
| **SMTP 邮件** | `SMTP_HOST` + `SMTP_USERNAME` + `SMTP_PASSWORD` | 仅邮件功能 |
| **OpenAI** | `OPENAI_API_KEY` | 当前主链路不使用 |
| **Google GenAI** | `GOOGLE_API_KEY` | 备用通道 |

### 5.3 ⚠️ 编辑模型名称不一致

`render.yaml` 定义 `VERTEX_IMAGEN_MODEL_EDIT=imagen-3.0-edit`，但代码默认值为 `imagen-3.0-capability-001`。

**建议**：以 render.yaml 为准，在 Render Dashboard 中显式配置此值。

---

## 六、恢复验收流程

### 6.1 最小验收 Checklist

```bash
# ── Step 1: 推送主线 ──
git push origin main

# ── Step 2: Render 部署检查 ──
# 在 Render Dashboard 确认：
# - 服务状态：Live
# - Build 日志无 ERROR
# - Build 日志包含 "NotoSansSC-Regular.ttf" 下载成功（字体修复后）

# ── Step 3: 后端健康检查 ──
curl https://<your-render-url>/health
# 期望：{"ok":true}

curl https://<your-render-url>/healthz
# 期望：{"ok":true}

# ── Step 4: 前端访问检查 ──
curl -s -o /dev/null -w "%{http_code}" https://<your-render-url>/
# 期望：200

# ── Step 5: Vertex 连通性 ──
curl https://<your-render-url>/debug/vertex/ping
# 期望：{"ok":true, "name":"publishers/google/models/imagen-3.0-generate-001", ...}

# ── Step 6: 端到端图片生成（可选） ──
curl https://<your-render-url>/debug/vertex/generate -o test.png
# 期望：返回 PNG 文件

# ── Step 7: R2 存储连通性 ──
curl -X POST https://<your-render-url>/api/image/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt":"a red circle on white background","size":"512x512"}'
# 期望：返回 JSON 含 url 字段，URL 可访问

# ── Step 8: GitHub Pages（如使用） ──
# 访问 https://zhaojfifa.github.io/<repo-name>/
# 期望：页面正常加载
```

### 6.2 日志关键字检查

| 日志关键字 | 含义 | 是否正常 |
|---|---|---|
| `VertexImagen3 ready` | Vertex 初始化成功 | ✅ 必须出现 |
| `Runtime configuration resolved` | 配置加载完成 | ✅ 必须出现 |
| `BodyGuardMiddleware ready` | 中间件就绪 | ✅ 必须出现 |
| `Vertex init failed` | GCP 认证失败 | ❌ 需检查 GCP_KEY_B64 |
| `VertexImagen3 initialization failed` | 模型客户端失败 | ❌ 需检查项目ID/区域 |
| `FontRegistry: font not found` | CJK 字体缺失 | ❌ 需修复 buildCommand |
| `Failed to import RejectHugeOrBase64` | 中间件加载失败 | ⚠️ 不阻塞启动，但需关注 |

---

## 七、恢复操作清单（按顺序执行）

### Phase 0: Render Dashboard 配置（5 分钟）

在 Render Dashboard 中为 `marketing-poster-api` 设置以下 env：

**必须项（6 个）：**
```
GCP_PROJECT_ID=<your-gcp-project-id>
GCP_KEY_B64=<base64-encoded-service-account-json>
R2_ENDPOINT=<https://xxx.r2.cloudflarestorage.com>
R2_BUCKET=<your-bucket-name>
R2_ACCESS_KEY_ID=<your-r2-access-key>
R2_SECRET_ACCESS_KEY=<your-r2-secret-key>
```

**推荐项（3 个）：**
```
R2_PUBLIC_BASE=<https://your-cdn-domain.com>
CORS_ALLOW_ORIGINS=https://zhaojfifa.github.io,https://<new-render-url>
GCP_LOCATION=us-central1
```

### Phase 1: 代码修复（2 处）

**修复 1**：`render.yaml` buildCommand 加字体下载
```yaml
buildCommand: pip install -r requirements.txt && bash scripts/fetch_fonts.sh app/assets/fonts
```

**修复 2**（可选）：如 Render 域名变更，更新 `app/main.py` 中 `DEFAULT_CORS_ORIGINS`

### Phase 2: 推送 & 验收

```bash
git push origin main
# 等待 Render 自动部署完成
# 按 6.1 验收 Checklist 逐项检查
```

---

## 八、海报结构控制方案对比分析

### 8.1 核心问题

海报"要素飘"（logo/文字/callout 位置不可控）的根因：

| 层级 | v1 方案 | 问题 |
|---|---|---|
| 背景 + 前景混合 | Vertex inpainting（locked_frame + mask） | AI 会"吃掉"结构元素，文字变形，logo 消失 |
| 文字渲染 | AI 生成 | 不可控：字体、大小、位置全由模型决定 |
| 当前 v2 方案 | Pillow 确定性渲染 | ✅ 架构正确，但 CJK 字体缺失导致回退到点阵字体 |

**结论**：v2 架构已解决结构控制问题，修字体即可验证。

### 8.2 方案全景对比

| 方案 | L1 结构控制 | L2 内容注入 | 服务端 | CJK | 动态锚点/Leader Line | 月费 | 实施量 |
|---|---|---|---|---|---|---|---|
| **A. Pillow v2 + 修字体** | ✅ JSON spec | ✅ 代码注入 | ✅ | ⚠️ 需字体 | ✅ 已实现 | $0 | 1 行 buildCommand |
| **B. HTML/CSS + Puppeteer** | ✅ CSS 布局 | ✅ 模板变量 | ✅ | ✅ 浏览器原生 | ✅ SVG 原生 | $0 | 1-2 天 |
| **C. Bannerbear** | ✅ 可视编辑器 | ✅ REST API | ✅ | ✅ 上传 OTF | ❌ 不支持 | $49+/月 | 0.5 天 |
| **D. Templated.io** | ✅ 拖拽编辑器 | ✅ REST API | ✅ | 未确认 | ❌ 不支持 | $29+/月 |0.5 天 |
| **E. Placid.app** | ✅ 模板层 | ✅ REST API | ✅ | 未确认 | ❌ 不支持 | $19+/月 | 0.5 天 |
| **F. Adobe Express Embed** | ✅ 浏览器编辑器 | ❌ 无服务端 API | ❌ | ✅ | ❌ | License | ❌ 不适用 |
| **G. Adobe Firefly + PSD** | ✅ PSD 模板 | ✅ REST API | ✅ | ✅ | ❌ | 按量 | 1-2 天 |
| **H. SVG 模板 + rsvg** | ✅ SVG 坐标 | ✅ 字符串替换 | ✅ | ⚠️ 需 fontconfig | ✅ SVG 原生 | $0 | 1 天 |

### 8.3 关键结论

1. **Adobe Express 排除** — 没有服务端 REST API，只有浏览器 Embed SDK，不适合后端管线。

2. **Bannerbear / Templated / Placid 均不支持动态锚点和 Leader Line** — 这是你的 feature callout 核心需求，SaaS 方案无法满足。

3. **推荐路径**：

```
今天 → 方案 A：render.yaml 加字体下载，部署验证
       如果 CJK 正常、结构不再飘 → 问题已解决，无需换方案

如果仍有视觉质量问题 → 方案 B：Puppeteer 渲染
       设计用 HTML/CSS + SVG 画 callout，浏览器保证字体和排版
       保留 Pillow 作 fallback

长期如需专业模板运营 → 方案 G：Adobe Firefly + PSD 模板
       Firefly 生成背景 + Photoshop API 注入文字/图片到 PSD 模板
       最接近专业设计工作流，但成本较高
```

### 8.4 Bannerbear 详细能力评估

| 能力 | 支持 | 说明 |
|---|---|---|
| REST API 创建图片 | ✅ | `POST /v2/images`，支持同步/异步 |
| 模板可视编辑器 | ✅ | Web 界面设计模板 |
| 文字层 API 修改 | ✅ | 按 layer name 注入 text |
| 图片层 API 修改 | ✅ | 按 layer name 注入 image_url |
| 自定义字体上传 | ✅ | OTF, WOFF, WOFF2 |
| CJK 字体 | ✅ | 需上传兼容字体 |
| 透明 PNG 输出 | ✅ | `transparent: true` |
| 动态锚点/坐标 | ❌ | 图层位置在模板中固定 |
| Leader Line 绘制 | ❌ | 无矢量绘制能力 |
| 价格 | $49/月 | 1000 张/月 |

**结论**：Bannerbear 适合"固定版式 + 动态文字/图片"场景（如社交媒体图、电商 Banner）。**不适合**需要动态锚点、引导线等结构性定制的海报。

---

## 九、总结

| 维度 | 结论 |
|---|---|
| **部署恢复** | 配置 6 个必需 env + 修 buildCommand 加字体 → 即可恢复 |
| **最小变更** | 仅 `render.yaml` 的 buildCommand 一行改动 |
| **海报结构控制** | v2 Pillow 架构已正确，修字体后验证；SaaS 方案均不支持动态锚点 |
| **Adobe Express** | 排除 — 无服务端 API |
| **Bannerbear** | 可用于简单模板场景，不满足 feature callout 需求 |
| **推荐路径** | 修字体 → 验证 → 如不够再上 Puppeteer |
