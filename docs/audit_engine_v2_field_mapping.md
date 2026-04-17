# audit-engine v2 字段映射与四层审计说明

## 标准字段定义表

| 标准字段 | 中文说明 | 类型 | 审计用途 |
|---|---|---|---|
| `project_name` | 工程名称 | string | 本体合规、目录映射 |
| `project_item_code` | 工程/项目编号 | string | 解释与追踪 |
| `is_emergency_repair` | 是否紧急维修 | boolean | 流程分支 |
| `repair_nature` | 维修性质：`normal` / `emergency` | enum | 流程分支 |
| `is_public_part` | 是否共用部位或共用设施设备 | boolean/null | 本体合规 |
| `is_private_part` | 是否专有部分 | boolean/null | 本体合规 |
| `is_property_service_scope` | 是否物业日常服务或维保范围 | boolean/null | 本体合规 |
| `warranty_status` | 保修状态 | enum/null | 本体合规 |
| `has_vote_trace` | 是否存在表决痕迹 | boolean | 资料痕迹、普通流程 |
| `vote_pass_rate_by_household` | 按户通过率 | number/null | 普通流程 |
| `vote_pass_rate_by_area` | 按面积通过率 | number/null | 普通流程 |
| `vote_legal` | 表决是否达到当前口径 | boolean/null | 普通流程 |
| `need_construction_contract` | 是否需要施工合同 | boolean/null | 资料痕迹 |
| `has_construction_contract` | 是否已签施工合同 | boolean | 资料痕迹、流程 |
| `has_appraisal_contract` | 是否已签审价合同 | boolean | 资料痕迹 |
| `has_appraisal_report` | 是否已有审价报告 | boolean | 资料痕迹 |
| `construction_start_date` | 实际开工日期 | date/null | 流程解释 |
| `budget_amount` | 预算金额 | number/null | 金额展示 |
| `contract_amount` | 合同金额 | number/null | 金额展示 |

所有字段的中文说明同步维护在 `backend/modules/audit_engine/rules/standard_field_definitions.json`。

## 字段映射规则表

| 来源 | 原字段/来源 | 标准字段 | 规则 |
|---|---|---|---|
| `T_Workspace` / `Blueprint_draft` / `Blueprint` | `property` | `is_emergency_repair` | `property == 2` 为 true，否则 false。当前版本仅区分普通维修/紧急维修。 |
| 派生 | `is_emergency_repair` | `repair_nature` | true 为 `emergency`，否则 `normal`。 |
| `Blueprint_draft` / `Blueprint` | `expirer_remark` | `warranty_status` | 空或其他文本为 `in_warranty`；含“过保”等为 `out_of_warranty`。该口径仅适用于当前数据展示。 |
| `Ws_project` | `is_signed_pc` | `has_construction_contract` | `1/true/是/Y` 为 true，`0/false/否/N` 为 false。 |
| `Ws_project` | `is_signed_esc` | `has_appraisal_contract` | `1/true/是/Y` 为 true，`0/false/否/N` 为 false。 |
| `Ws_project` | `is_signed_esr` | `has_appraisal_report` | `1/true/是/Y` 为 true，`0/false/否/N` 为 false。 |
| `Ws_project` / `T_Workspace` | `need_con` / `need_pro_contract` | `need_construction_contract` | `1/true/是/Y` 为 true，`0/false/否/N` 为 false。 |
| `Hou_notion_sum` | 记录存在 | `has_vote_trace` | 有记录即 true；无记录时可按 `T_Workspace.is_voted` 辅助映射。 |
| `Hou_notion_sum` | 户数、面积字段 | `vote_pass_rate_by_household`, `vote_pass_rate_by_area`, `vote_legal` | 按同意户数/总户数、同意面积/总面积计算；字段不足则为 null。 |
| `Project_contract` | `startup_date` | `construction_start_date` | `YYYYMMDD` 或 ISO 日期规范化为 `YYYY-MM-DD`。 |
| `Project_contract` / `Ws_project` / `Blueprint` / `Blueprint_draft` | `orgn_amt` | `budget_amount` | 转 number，按来源优先级取第一个可解析值。 |
| `Project_contract` | `contract_amt` | `contract_amount` | 转 number。 |
| 目录映射 | `project_name` + `repairable_object_catalog.json` | `is_public_part`, `is_private_part`, `is_property_service_scope` | 只在字段映射层辅助推断；如与来源字段冲突，进入人工复核。 |

集中规则文件：`backend/modules/audit_engine/rules/field_mapping_rules.json`。

## 每个子审计使用字段清单

| 子审计 | 使用标准字段 |
|---|---|
| `entity_audit` | `project_name`, `is_public_part`, `is_private_part`, `is_property_service_scope`, `warranty_status`, `repair_nature` |
| `trace_audit` | `has_vote_trace`, `need_construction_contract`, `has_construction_contract`, `has_appraisal_contract`, `has_appraisal_report` |
| `process_audit` | `repair_nature`, `is_emergency_repair`, `has_vote_trace`, `vote_pass_rate_by_household`, `vote_pass_rate_by_area`, `vote_legal`, `construction_start_date` |
| `amount_info` | `budget_amount`, `contract_amount` |

输出中的每个子审计使用 `used_standard_fields` 明示字段清单，不再输出 `facts_used`。

## 需要人工复核场景

- 目录映射与来源字段或项目语义冲突，例如目录为共用设施，但项目名称或输入显示为专有部分。
- `Hou_notion_sum` 存在，但缺少计算表决通过率所需字段。
- 普通维修表决合法性无法确认，或有开工日期但表决合法性未确认。
- 紧急维修只豁免普通流程，本体合规不足时仍需本体层复核或否决。
- `warranty_status` 来自 `expirer_remark` 当前展示口径时，需要人工确认正式保修责任。

## reason_code 分类说明

| 分类 | reason_code |
|---|---|
| entity | `ENTITY_PUBLIC_REPAIR_OBJECT`, `ENTITY_PRIVATE_PART_NOT_ELIGIBLE`, `ENTITY_PROPERTY_SERVICE_SCOPE`, `ENTITY_IN_WARRANTY`, `ENTITY_OBJECT_UNKNOWN_MANUAL_REVIEW`, `ENTITY_FIELD_CONFLICT_MANUAL_REVIEW` |
| trace | `TRACE_MISSING_VOTE_TRACE`, `TRACE_MISSING_CONSTRUCTION_CONTRACT`, `TRACE_MISSING_APPRAISAL_CONTRACT`, `TRACE_MISSING_APPRAISAL_REPORT`, `TRACE_NEED_CONSTRUCTION_CONTRACT_NOT_SIGNED` |
| process | `PROCESS_NORMAL_VOTE_MISSING`, `PROCESS_NORMAL_VOTE_NOT_LEGAL`, `PROCESS_NORMAL_CONSTRUCTION_BEFORE_VOTE_REVIEW`, `PROCESS_EMERGENCY_FLOW_EXEMPTED`, `PROCESS_EMERGENCY_TRACE_REVIEW_REQUIRED` |
| amount | `AMOUNT_BUDGET_DISPLAY`, `AMOUNT_CONTRACT_DISPLAY`, `AMOUNT_INFO_MISSING` |

trace 类 reason_code 只作为补充材料提示，不直接作为违法结论。amount 类 reason_code 只用于信息展示，不参与总体结论聚合。
