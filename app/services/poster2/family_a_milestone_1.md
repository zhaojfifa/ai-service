ummary
Docs
family_a_structural_closeout_diagnosis_v1.md — Root-cause analysis proving why budget tuning fails: in title_gallery_split + dense-quad, title_char_budget collapses to 20 because bottom_shell_top=728 is a structural ceiling, not a tunable parameter.

family_a_structural_closeout_contract_v1.md — Contract spec for all three scopes with exact geometry targets.

A — Bottom structural expansion (template_behavior.py)
Mode	bottom_shell_top	title_char_budget (dense)	Gallery
title_gallery_split (frozen)	728	20	✓
text_only_expanded	656	52–72	✗
text_gallery_expanded	640	44 minimum	✓
bottom_layout_mode and bottom_shell_top emitted in ResolvedBottomBehavior evidence
Frozen baseline untouched
B — Product layout contract (template_behavior.py, contracts.py)
product_layout_mode = single_primary | primary_secondary_dual added to TemplateBehaviorModesSpec
ResolvedProductBehavior now exposes product_primary_slot, product_secondary_slot, product_secondary_slot_rendered, product_secondary_asset_policy
Annotation shell stays on primary slot only; secondary slot is contract-only pending renderer parity
C — Text layer evidence (pipeline.py, contracts.py, schemas/poster2.py, main.py)
Three new first-class layer evidence fields on every generation: title_text_layer, subtitle_text_layer, header_text_layer — each with requested_text → sanitized_text → rendered_excerpt, truncation_applied, slot_bounds, line_clamp, char_budget.