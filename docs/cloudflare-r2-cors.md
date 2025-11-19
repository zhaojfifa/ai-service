# Cloudflare R2 CORS 配置与排查

浏览器直传 R2 若命中 CORS 限制，会在 Console 抛出类似错误：

```
Access to fetch at 'https://<account>.r2.cloudflarestorage.com/...'
from origin 'https://<your-frontend-host>' has been blocked by CORS policy
```

若出现上述提示，按以下步骤校准桶的 CORS 规则。

## 推荐的 JSON 规则

在 Cloudflare 控制台选择对应 R2 桶，进入 **Settings → CORS policy**，粘贴如下内容并保存：

```json
{
  "rules": [
    {
      "allowed": {
        "origins": [
          "https://<your-frontend-host>",
          "https://<your-api-host>"
        ],
        "methods": ["GET", "PUT", "HEAD", "POST", "OPTIONS"],
        "headers": ["*"]
      },
      "max_age": 86400
    }
  ]
}
```

保存后等待几秒，刷新前端页面并重新上传即可。

## 操作指引

1. 打开 Cloudflare 控制台，进入 **R2**。
2. 选择目标 **Bucket** → **Settings** → **CORS policy**。
3. 将上方 JSON 粘贴到文本框中保存。
4. 重新在浏览器上传素材，观察 Console 是否仍有 CORS 报错。

## 自查清单

- Origin 拼写必须与浏览器地址栏一致（含 https，不含路径）。GitHub Pages 示例：`https://zhaojiffa.github.io`；Render 示例：`https://ai-service-x758.onrender.com`。
- `methods` 中需要包含 `PUT` 和 `OPTIONS`，否则预检会失败。
- 如果直传时自定义了 `Content-Type` 或其他头部，确认它们包含在 `headers` 中；最简单的做法是使用 `"*"` 放行全部。
- 如切换到自建域名，请将 `origins` 中的地址替换为新的前端域名并重新保存。

## 用 curl 快速验证预检

```bash
curl -i -X OPTIONS \
  -H "Origin: https://zhaojiffa.github.io" \
  -H "Access-Control-Request-Method: PUT" \
  "https://<account-id>.r2.cloudflarestorage.com/<bucket>/<test-object>"
```

响应头中若包含 `Access-Control-Allow-Origin: https://zhaojiffa.github.io` 和 `Access-Control-Allow-Methods` 中的 `PUT`，即可确认规则已生效；否则浏览器仍会在预检阶段拦截上传。

完成以上检查后，前端调用 `/api/r2/presign-put` 获取的预签名地址即可通过浏览器成功直传到 R2。
