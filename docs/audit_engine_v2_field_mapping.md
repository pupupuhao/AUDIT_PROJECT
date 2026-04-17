# audit-engine v2 字段映射与四层审计说明

## 标准字段定义表

| 标准字段 | 中文说明 | 类型 | 审计用途 |
|---|---|---|---|
| `project_name` | 工程名称 | string | 本体合规、目录映射 |
| `project_item_code` | 工程/项目编号 | string | 解释与追踪 |
| `property_raw_value` | `property` 原始值 | string/null | 输入解释与人工复核 |
| `property_value_valid` | `property` 是否属于当前支持范围 | boolean | 非法值触发人工复核 |
| `is_emergency_repair` | 是否紧急维修 | boolean/null | 流程分支 |
| `repair_nature` | 维修性质：`normal` / `emergency` / `unknown` | enum | 流程分支 |
| `is_public_part` | 是否共用部位或共用设施设备 | boolean/null | 本体合规 |
| `is_private_part` | 是否专有部分 | boolean/null | 本体合规 |
| `is_property_service_scope` | 是否物业日常服务或维保范围 | boolean/null | 本体合规 |
| `warranty_status` | 保修状态展示字段 | enum | 仅展示/解释，不参与本轮合规结论 |
| `has_vote_trace` | 是否存在表决痕迹 | boolean | 资料痕迹、普通流程 |
| `vote_pass_rate_by_household` | 按户通过率 | number/null | 普通流程 |
| `vote_pass_rate_by_area` | 按面积通过率 | number/null | 普通流程 |
| `vote_legal` | 表决是否达到当前口径 | boolean/null | 普通流程 |
| `vote_date` | 表决日期 | date/null | 普通维修时序校验 |
| `vote_date_is_proxy` | 表决日期是否为代用日期 | boolean/null | 弱提示 |
| `is_before_vote_construct` | 是否确认先开工后表决 | boolean/null | 普通维修时序风险 |
| `need_construction_contract` | 是否需要施工合同 | boolean/null | 资料痕迹 |
| `has_construction_contract` | 是否已签施工合同 | boolean | 资料痕迹、流程 |
| `has_appraisal_contract` | 是否已签审价合同 | boolean | 资料痕迹 |
| `has_appraisal_report` | 是否已有审价报告 | boolean | 资料痕迹 |
| `construction_start_date` | 实际开工日期 | date/null | 普通维修时序校验 |
| `budget_amount` | 预算金额 | number/null | 金额展示 |
| `contract_amount` | 合同金额 | number/null | 金额展示 |

## 字段映射规则

| 来源 | 原字段/来源 | 标准字段 | 规则 |
|---|---|---|---|
| `T_Workspace` / `Blueprint_draft` / `Blueprint` | `property` | `property_raw_value`, `property_value_valid`, `is_emergency_repair`, `repair_nature` | 当前仅支持 `1=一般维修`、`2=急修`。其他非空值不静默处理，进入人工复核。 |
| `Blueprint_draft` / `Blueprint` | `expirer_remark` | `warranty_status` | 当前 demo 口径：缺失或空字符串 -> `in_warranty`；含“过保/保修期外/出保”等 -> `out_of_warranty`；其他 -> `in_warranty`。仅作展示说明，不参与本轮合规结论。 |
| `Hou_notion_sum` | 记录存在 | `has_vote_trace` | 有记录即 true；无记录时可按 `T_Workspace.is_voted` 辅助映射。 |
| `Hou_notion_sum` | 户数、面积字段 | `vote_pass_rate_by_household`, `vote_pass_rate_by_area`, `vote_legal` | 按同意户数/总户数、同意面积/总面积计算；字段不足则为 null。 |
| `Hou_notion_sum` | `request_enddate` | `vote_date` | 最高优先级，作为表决完成时点。 |
| `Hou_notion_sum` | `request_startdate` | `vote_date` | `request_enddate` 缺失时使用，写入“代用日期” warning。 |
| `Hou_notion_sum` | `reg_date` | `vote_date` | 前两者都缺失时使用，写入“代用日期” warning。 |
| 派生 | `construction_start_date/vote_date` | `is_before_vote_construct` | 仅普通维修且两个日期均存在时计算；`construction_start_date < vote_date` 为 true。 |
| `Project_contract` | `startup_date` | `construction_start_date` | `YYYYMMDD` 或 ISO 日期规范化为 `YYYY-MM-DD`。 |
| `Ws_project` | `is_signed_pc`, `is_signed_esc`, `is_signed_esr`, `need_con` | 合同/审价痕迹字段 | `1/true/是/Y` 为 true，`0/false/否/N` 为 false。 |
| `Project_contract` / `Ws_project` / `Blueprint` / `Blueprint_draft` | `orgn_amt`, `contract_amt` | `budget_amount`, `contract_amount` | 转 number，仅用于金额展示。 |
| 目录映射 | `project_name` + `repairable_object_catalog.json` | `is_public_part`, `is_private_part`, `is_property_service_scope` | 字段映射层辅助推断；冲突时进入人工复核。 |

## 子审计字段清单与边界

| 子审计 | 当前使用标准字段 |
|---|---|
| `entity_audit` | `project_name`, `is_public_part`, `is_private_part`, `is_property_service_scope`, `repair_nature` |
| `trace_audit` | `has_vote_trace`, `need_construction_contract`, `has_construction_contract`, `has_appraisal_contract`, `has_appraisal_report` |
| `process_audit` | `property_raw_value`, `property_value_valid`, `repair_nature`, `is_emergency_repair`, `has_vote_trace`, `vote_pass_rate_by_household`, `vote_pass_rate_by_area`, `vote_legal`, `vote_date`, `vote_date_is_proxy`, `construction_start_date`, `is_before_vote_construct` |
| `amount_info` | `budget_amount`, `contract_amount` |

当前 `trace_audit` 只覆盖表决痕迹、施工合同、审价合同、审价报告。`has_publicity_trace`、`has_budget_trace`、`has_acceptance_trace` 暂未正式实现。

当前 `warranty_status` 是展示口径，不会让 `entity_audit` 或顶层主结论自动变成 `manual_review`。

## 流程时序判断

- 仅普通维修执行时序校验。
- `construction_start_date` 与 `vote_date` 都存在时：
  - `construction_start_date < vote_date` -> `is_before_vote_construct = true`，触发 `PROCESS_CONSTRUCTION_BEFORE_VOTE_CONFIRMED`。
  - 否则 `is_before_vote_construct = false`。
- 有开工日期但无 `vote_date` 时，输出 `PROCESS_VOTE_DATE_MISSING`，不伪造“先开工后表决”。
- `vote_date` 来自 `request_startdate` 或 `reg_date` 时，输出弱提示 `PROCESS_VOTE_DATE_PROXY_USED`；该 code 单独出现时不应让主结论变黄。
- 紧急维修不走普通维修时序校验。

## 顶层结果聚合

`overall_result` 仍按风险优先级决定，但顶层 `reasons/top_reasons` 和 `missing_items/top_missing_items` 从 `entity_audit`、`process_audit`、`trace_audit` 合并去重。`amount_info` 只展示金额，不进入顶层主原因。

前端 summary 区只保留：项目名称、主结论、原因说明、参考依据；不再展示“缺口说明”。

## Excel 行映射预留能力

`backend/modules/audit_engine/services/excel_row_mapper.py` 提供：

```python
map_excel_row_to_audit_request(row: Dict[str, Any]) -> Dict[str, Any]
```

支持中文列名包括：`工程名称`、`工程性质`、`保修备注`、`总户数`、`同意户数`、`总面积`、`同意面积`、`征询结束日期`、`征询开始日期`、`录入日期`、`开工日期`、`预算金额`、`合同金额`。无法识别的列进入 `unmapped_columns`。

下一步 Excel 上传只需完成文件上传 API、xlsx 解析为逐行 dict、逐行调用该 mapper，再调用现有审计流程。

## reason_code 法规来源表

| reason_code | 层级 | 强度 | 法规/依据 |
|---|---|---|---|
| `ENTITY_PUBLIC_REPAIR_OBJECT` | entity | strong | 《住宅专项维修资金管理办法》第十八条；《上海市商品住宅维修基金管理办法》第十三条；《民法典》共有/专有条款 |
| `ENTITY_PRIVATE_PART_NOT_ELIGIBLE` | entity | strong | 《住宅专项维修资金管理办法》第十八条；《上海市商品住宅维修基金管理办法》第十三条；《民法典》共有/专有条款 |
| `ENTITY_PROPERTY_SERVICE_SCOPE` | entity | strong | 《住宅专项维修资金管理办法》第十八条、第二十五条；DB31/T 360-2020 第8章 |
| `ENTITY_OBJECT_UNKNOWN_MANUAL_REVIEW` | entity | weak | 维修对象目录映射复核规则 |
| `ENTITY_FIELD_CONFLICT_MANUAL_REVIEW` | entity | weak | 标准字段冲突复核规则 |
| trace 类 code | trace | weak | 系统中暂未发现对应业务痕迹，建议补充核验 |
| `PROCESS_NORMAL_VOTE_MISSING` | process | strong | 《住宅专项维修资金管理办法》第二十二条、第二十三条；《民法典》第二百七十八条、第二百八十一条 |
| `PROCESS_NORMAL_VOTE_NOT_LEGAL` | process | strong | 同上 |
| `PROCESS_VOTE_DATE_MISSING` | process | weak | 缺少日期字段，无法完成时序校验 |
| `PROCESS_CONSTRUCTION_BEFORE_VOTE_CONFIRMED` | process | strong | 普通维修表决程序法规 |
| `PROCESS_VOTE_DATE_PROXY_USED` | process | weak | 代用日期弱提示 |
| `PROCESS_EMERGENCY_FLOW_EXEMPTED` | process | strong | 《住宅专项维修资金管理办法》第二十四条；《上海市商品住宅维修基金管理办法》第十四条；沪房管物〔2011〕326号 |
| `PROCESS_EMERGENCY_TRACE_REVIEW_REQUIRED` | process | strong | 沪房管物〔2011〕326号 |
| amount 类 code | amount | none | 不绑定法规，仅展示 |

`ENTITY_IN_WARRANTY` 和 `PROCESS_NORMAL_CONSTRUCTION_BEFORE_VOTE_REVIEW` 保留为历史/预留说明，当前四层审计不主动发出。
