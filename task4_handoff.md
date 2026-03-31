# Task 4 Handoff — Family A Final Alignment

## 【任务进度锚点】

- Task 1 (canonical `bottom_layout_mode` — always mirrors `.mode`) ✅ committed
- Task 2 (bottom v2 geometry — `_FROZEN_BASELINE_BOTTOM_SHELL_TOP`, peer_gap for `text_gallery_expanded`) ✅ committed
- Task 3 (product dual-image v2 geometry — `_PRODUCT_DUAL_PRIMARY_PAD` / `_PRODUCT_DUAL_SECONDARY_PAD` constants) ✅ committed

**下一局唯一目标 → Task 4**:
Feature vs product-annotation responsibility cleanup —
remove the late override block in `_build_layer_render_status()` inside `pipeline.py`.

---

## 【赛博纪律：严禁越权】

- **检索限制**：绝对禁止 `grep` 整个文件或 `Read` 整个文件。
  必须且只能使用 `rg -n -C 5 "product_annotation"` 等精准命令查看局部代码。
- **行为限制**：
  - 拿到确认方案前，禁止自动修改代码。
  - 禁止自动运行任何测试。
  - 禁止扫描无关文件。
  - 每次只改一个小项，改完等待 commit 指令。

---

## 【pipeline.py 当前状态预检】

`_build_layer_render_status()` 函数内存在两块关于 `product_annotation_shell_layer` /
`product_annotation_items_layer` 的赋值：

### 第一块（正确 — 使用 `product_policy.annotation_mode`，lines ~594–717）

```python
product_annotation_visible = min(
    behavior.product_policy.visible_annotation_count,
    len([item for item in spec.features if item and item.strip()]),
)
product_annotation_rendered = (
    behavior.product_policy.annotation_mode == "product_anchor_callouts"
    and behavior.feature_policy.mode == "product_anchor_callouts"
    and product_annotation_visible > 0
)
# ... (inside layer_status dict literal)
"product_annotation_shell_layer": {
    "rendered": product_annotation_rendered,
    "reason_code": (
        None
        if product_annotation_rendered
        else (
            "annotation_mode_none"
            if behavior.product_policy.annotation_mode == "none"
            ...
        )
    ),
    "source_binding": behavior.product_policy.annotation_mode,
    "count": 1 if product_annotation_rendered else 0,
    "collapsed": not product_annotation_rendered,
},
"product_annotation_items_layer": {
    "rendered": product_annotation_rendered,
    ...
    "count": product_annotation_visible if product_annotation_rendered else 0,
    "collapsed": not product_annotation_rendered,
},
```

### 第二块（需要删除的 late override — 使用 `feature_policy.mode`，lines ~783–800）

```python
annotation_active = behavior.feature_policy.mode == "product_anchor_callouts"
annotation_item_count = behavior.feature_policy.visible_item_count if annotation_active else 0
layer_status["product_annotation_shell_layer"] = {
    "rendered": annotation_active,
    "reason_code": None if annotation_active else "product_annotation_mode_none",
    "source_binding": "template_dual_v2.product_annotation_shell",
    "count": 1 if annotation_active else 0,
    "collapsed": not annotation_active,
}
layer_status["product_annotation_items_layer"] = {
    "rendered": annotation_active and annotation_item_count > 0,
    "reason_code": None if (annotation_active and annotation_item_count > 0) else (
        "product_annotation_mode_none" if not annotation_active else "features_empty"
    ),
    "source_binding": "features",
    "count": annotation_item_count,
    "collapsed": not annotation_active or annotation_item_count == 0,
}
return layer_status
```

### 操作方案

删除第二块（lines ~783–800，从 `annotation_active = ...` 到 `}` 的最后一行，
保留 `return layer_status`）。
第一块（正确来源 `product_policy.annotation_mode`）保持不动。

删除后 `return layer_status` 直接跟在 `layer_status` dict 的 `"bottom_tagline_layer"` 条目之后。
