# GitHub Pages vs. docs/ sources

Network access to download the deployed GitHub Pages HTML was blocked in this environment (`curl ... github.io` returned HTTP 403). Because the deployed pages could not be fetched, a line-by-line diff against the current `docs/` sources was not produced.

If you want to regenerate this comparison with network access available, run:

```
curl -L https://zhaojiffa.github.io/ai-service/index.html -o docs/_deployed_index.html
curl -L https://zhaojiffa.github.io/ai-service/stage2.html -o docs/_deployed_stage2.html
git diff --no-index docs/index.html docs/_deployed_index.html
git diff --no-index docs/stage2.html docs/_deployed_stage2.html
```

This repository state reflects only the local `docs/` sources.
