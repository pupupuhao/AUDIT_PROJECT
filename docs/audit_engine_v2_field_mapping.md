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
| `trace_audit` | `repair_nature`, `is_emergency_repair`, `has_vote_trace`, `need_construction_contract`, `has_construction_contract`, `has_appraisal_contract`, `has_appraisal_report` |
| `process_audit` | `property_raw_value`, `property_value_valid`, `repair_nature`, `is_emergency_repair`, `has_vote_trace`, `vote_pass_rate_by_household`, `vote_pass_rate_by_area`, `vote_legal`, `vote_date`, `vote_date_is_proxy`, `construction_start_date`, `is_before_vote_construct` |
| `amount_info` | `budget_amount`, `contract_amount` |

当前 `trace_audit` 只覆盖表决痕迹、施工合同、审价合同、审价报告。`has_publicity_trace`、`has_budget_trace`、`has_acceptance_trace` 暂未正式实现。

普通维修 trace 默认检查表决痕迹、施工合同、审价合同、审价报告。紧急维修 trace 不默认要求业主表决痕迹，不触发 `TRACE_MISSING_VOTE_TRACE`；紧急维修 trace 仅围绕施工合同、审价/结算、事后资料痕迹进行补充核验。

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

`overall_result` 仍按风险优先级决定，但顶层 `reasons/top_reasons` 和 `missing_items/top_missing_items` 会按主结论优先级合并去重。`entity_audit = non_compliant` 时，本体不合规原因排在首位，不会被 trace/process 的补充材料提示覆盖。

顶层参考依据为汇总型：

- `top_basis_documents`：触发主结论的直接分项依据。
- `all_basis_documents`：`entity_audit -> trace_audit -> process_audit` 的全部法规依据汇总，按法规标题、文号、条文去重。
- `basis_documents`：为兼容前端，等同于 `all_basis_documents`。
- `amount_info` 不进入顶层依据汇总。

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
| `ENTITY_PUBLIC_REPAIR_OBJECT` | entity | strong | 《住宅专项维修资金管理办法》第十八条；《上海市商品住宅维修基金管理办法》第十三条 |
| `ENTITY_PRIVATE_PART_NOT_ELIGIBLE` | entity | strong | 《住宅专项维修资金管理办法》第十八条；《上海市商品住宅维修基金管理办法》第十三条，按用途范围反向解释 |
| `ENTITY_PROPERTY_SERVICE_SCOPE` | entity | strong | 《住宅专项维修资金管理办法》第二十五条；DB31/T 360-2020 第7章（保洁/清洁/卫生适用）、第8章（绿化/树木修剪/绿化养护适用） |
| `ENTITY_OBJECT_UNKNOWN_MANUAL_REVIEW` | entity | weak | 《住宅专项维修资金管理办法》第十八条；《上海市商品住宅维修基金管理办法》第十三条，用于背景性说明对象范围需核验 |
| `ENTITY_FIELD_CONFLICT_MANUAL_REVIEW` | entity | weak | 《住宅专项维修资金管理办法》第十八条；《上海市商品住宅维修基金管理办法》第十三条，用于背景性说明字段冲突需核验 |
| `TRACE_MISSING_VOTE_TRACE` | trace | weak | 《住宅专项维修资金管理办法》第二十二条、第二十三条；表达为“应履行业主表决程序，本系统未发现相关业务痕迹，建议补充核验” |
| `TRACE_MISSING_CONSTRUCTION_CONTRACT` | trace | weak | 《住宅专项维修资金管理办法》第二十四条；表达为“通常应具备施工合同等材料，本系统未发现相关痕迹” |
| `TRACE_MISSING_APPRAISAL_CONTRACT` | trace | weak | 《上海市商品住宅维修基金管理办法》第十三条；表达为审价合同是核验资金合理使用的过程依据 |
| `TRACE_MISSING_APPRAISAL_REPORT` | trace | weak | 《上海市商品住宅维修基金管理办法》第十三条；表达为“通常需审价依据，本系统未发现相关痕迹” |
| `TRACE_NEED_CONSTRUCTION_CONTRACT_NOT_SIGNED` | trace | weak | 《住宅专项维修资金管理办法》第十八条；表达为“通常应具备合同依据，本系统未发现签署痕迹” |
| `PROCESS_NORMAL_VOTE_MISSING` | process | weak | 《住宅专项维修资金管理办法》第二十二条、第二十三条；缺流程信息的背景性提示 |
| `PROCESS_NORMAL_VOTE_NOT_LEGAL` | process | strong | 《住宅专项维修资金管理办法》第二十二条、第二十三条；《民法典》第二百七十八条、第二百八十一条 |
| `PROCESS_VOTE_DATE_MISSING` | process | weak | 《住宅专项维修资金管理办法》第二十二条、第二十三条；缺少表决日期，无法完成时序校验 |
| `PROCESS_CONSTRUCTION_BEFORE_VOTE_CONFIRMED` | process | weak | 《住宅专项维修资金管理办法》第二十二条、第二十三条；施工时间早于表决时间属于流程推导风险，建议核查，不写成直接违法 |
| `PROCESS_VOTE_DATE_PROXY_USED` | process | weak | 《住宅专项维修资金管理办法》第二十二条、第二十三条；代用日期仅用于展示和弱校验 |
| `PROCESS_PROPERTY_VALUE_UNSUPPORTED` | process | weak | 《住宅专项维修资金管理办法》第十八条、第二十四条；工程性质影响普通/紧急路径，需核验输入口径 |
| `PROCESS_EMERGENCY_FLOW_EXEMPTED` | process | strong | 《住宅专项维修资金管理办法》第二十四条；《上海市商品住宅维修基金管理办法》第十四条；沪房管物〔2011〕326号 |
| `PROCESS_EMERGENCY_TRACE_REVIEW_REQUIRED` | process | weak | 《住宅专项维修资金管理办法》第二十四条；沪房管物〔2011〕326号第二条至第四条，用于紧急维修事后资料背景性核验 |
| amount 类 code | amount | none | 不绑定法规，仅展示 |

`ENTITY_IN_WARRANTY` 和 `PROCESS_NORMAL_CONSTRUCTION_BEFORE_VOTE_REVIEW` 保留为历史/预留说明，当前四层审计不主动发出。

## 通过态默认合规依据

当 `trace_audit` 或 `process_audit` 完全通过且未触发任何问题类 `reason_code` 时，后端仍会在分项 `basis_documents` 中补充默认合规依据。默认依据只用于分项展示，不新增 `reason_code`，也不进入顶层问题原因聚合。

| 分项 | 场景 | 默认依据 | 强度 |
|---|---|---|---|
| `trace_audit` | 资料/手续痕迹字段齐备 | 《住宅专项维修资金管理办法》第二十二条、第二十三条 | weak |
| `trace_audit` | 紧急维修资料/手续痕迹字段齐备 | 《住宅专项维修资金管理办法》第二十四条；沪房管物〔2011〕326号第二条至第四条 | strong |
| `process_audit` | 普通维修流程字段初步通过 | 《住宅专项维修资金管理办法》第二十二条、第二十三条 | weak |
| `process_audit` | 紧急维修流程通过态 | 《住宅专项维修资金管理办法》第二十四条 | strong |

使用背景性法规表达的 code 包括：`ENTITY_OBJECT_UNKNOWN_MANUAL_REVIEW`、`ENTITY_FIELD_CONFLICT_MANUAL_REVIEW`、全部 trace 类 code、`PROCESS_NORMAL_VOTE_MISSING`、`PROCESS_VOTE_DATE_MISSING`、`PROCESS_CONSTRUCTION_BEFORE_VOTE_CONFIRMED`、`PROCESS_VOTE_DATE_PROXY_USED`、`PROCESS_PROPERTY_VALUE_UNSUPPORTED`、`PROCESS_EMERGENCY_TRACE_REVIEW_REQUIRED`。这些 code 不写“违反第XX条”或“不符合第XX条规定”，只表达“依据/根据程序要求，当前未发现或无法确认，建议补充核验”。

前端参考依据展示规则：顶层 summary 仅展示 `display_name` 法规条文列表，不展示 `basis_explanation`，默认展示前 3 条，超过后可展开。分项卡片按 `display_name + basis_explanation` 成对展示，每个分项默认展示前 2 组，超过后可展开；不再把所有法条和所有说明分开堆叠。`amount_info` 固定展示“金额层仅展示，不绑定法规依据”。页面不再过滤 `source_type`，也不再回退为“系统审计规则”或“暂无明确法规展示”。

前端颜色映射：`compliant=绿色`、`need_supplement=黄色`、`manual_review=橙色`、`non_compliant=红色`、`info_only=蓝色`。
