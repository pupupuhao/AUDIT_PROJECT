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
| `warranty_status` | 保修状态 | enum | 本体合规 |
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
| `T_Workspace` / `Blueprint_draft` / `Blueprint` | `property` | `property_raw_value`, `property_value_valid`, `is_emergency_repair`, `repair_nature` | 当前仅支持 `1=一般维修`、`2=急修`。`1 -> normal`，`2 -> emergency`，其他非空值不静默处理，进入人工复核。 |
| `Blueprint_draft` / `Blueprint` | `expirer_remark` | `warranty_status` | 当前 demo 口径：字段缺失或空字符串 -> `in_warranty`；含“过保/保修期外/出保”等 -> `out_of_warranty`；其他 -> `in_warranty`。该口径仅用于当前数据集展示，不代表正式业务规则。 |
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

## 子审计字段清单与当前边界

| 子审计 | 当前使用标准字段 |
|---|---|
| `entity_audit` | `project_name`, `is_public_part`, `is_private_part`, `is_property_service_scope`, `warranty_status`, `repair_nature` |
| `trace_audit` | `has_vote_trace`, `need_construction_contract`, `has_construction_contract`, `has_appraisal_contract`, `has_appraisal_report` |
| `process_audit` | `property_raw_value`, `property_value_valid`, `repair_nature`, `is_emergency_repair`, `has_vote_trace`, `vote_pass_rate_by_household`, `vote_pass_rate_by_area`, `vote_legal`, `construction_start_date` |
| `amount_info` | `budget_amount`, `contract_amount` |

当前 `trace_audit` 只覆盖表决痕迹、施工合同、审价合同、审价报告。`has_publicity_trace`、`has_budget_trace`、`has_acceptance_trace` 暂未正式实现。

当前 `process_audit` 尚未实现完整 `vote_date` 和 `is_before_vote_construct` 时序字段；如开工日期存在但表决合法性无法确认，仅输出人工复核提示。

输出中的每个子审计使用 `used_standard_fields` 明示字段清单，不输出 `facts_used`。

## 需要人工复核场景

- `property` 为非 `1/2` 的非法值。
- 目录映射与来源字段或项目语义冲突，例如目录为共用设施，但项目名称或输入显示为专有部分。
- `Hou_notion_sum` 存在，但缺少计算表决通过率所需字段。
- 普通维修表决合法性无法确认，或有开工日期但表决合法性未确认。
- 紧急维修只豁免普通流程，本体合规不足时仍需本体层复核或否决。
- `warranty_status` 来自 `expirer_remark` 当前 demo 口径时，需要人工确认正式保修责任。

## Excel 行映射预留能力

新增 `backend/modules/audit_engine/services/excel_row_mapper.py`，提供：

```python
map_excel_row_to_audit_request(row: Dict[str, Any]) -> Dict[str, Any]
```

输入示例：

```json
{
  "工程名称": "3号楼电梯主机维修",
  "工程性质": 1,
  "保修备注": "",
  "是否已签订施工合同": "是",
  "是否已签订审价合同": "是",
  "是否已出具审价报告": "是",
  "是否需要签订施工合同": "是",
  "总户数": 100,
  "同意户数": 80,
  "总面积": 1000,
  "同意面积": 800,
  "预算金额": 120000,
  "合同金额": 118000,
  "未知列": "调试用"
}
```

输出结构：

```json
{
  "project_name": "3号楼电梯主机维修",
  "sources": {
    "t_workspace": { "property": 1, "wsname": "3号楼电梯主机维修" },
    "blueprint_draft": { "expirer_remark": "", "wsname": "3号楼电梯主机维修" },
    "ws_project": {
      "is_signed_pc": "是",
      "is_signed_esc": "是",
      "is_signed_esr": "是",
      "need_con": "是"
    },
    "hou_notion_sum": {
      "count_hou": 100,
      "agree_hou": 80,
      "sum_area": 1000,
      "agree_area": 800
    },
    "project_contract": {
      "name": "3号楼电梯主机维修",
      "orgn_amt": 120000,
      "contract_amt": 118000
    },
    "text": { "project_name": "3号楼电梯主机维修" }
  },
  "unmapped_columns": ["未知列"]
}
```

下一步 Excel 上传只需完成：文件上传 API、xlsx 解析为逐行 dict、逐行调用 `map_excel_row_to_audit_request()`、再调用现有 `/engine/judge` 同等审计流程。

## reason_code 法规来源表

| reason_code | 层级 | 强度 | 法规/依据 |
|---|---|---|---|
| `ENTITY_PUBLIC_REPAIR_OBJECT` | entity | strong | 《住宅专项维修资金管理办法》第十八条；《上海市商品住宅维修基金管理办法》第十三条；《民法典》第二百七十一条至第二百七十四条 |
| `ENTITY_PRIVATE_PART_NOT_ELIGIBLE` | entity | strong | 《住宅专项维修资金管理办法》第十八条；《上海市商品住宅维修基金管理办法》第十三条；《民法典》第二百七十一条至第二百七十四条 |
| `ENTITY_PROPERTY_SERVICE_SCOPE` | entity | strong | 《住宅专项维修资金管理办法》第十八条、第二十五条；DB31/T 360-2020 第8章 |
| `ENTITY_IN_WARRANTY` | entity | weak | 当前数据展示口径，需人工确认正式保修责任 |
| `ENTITY_OBJECT_UNKNOWN_MANUAL_REVIEW` | entity | weak | 维修对象目录映射复核规则 |
| `ENTITY_FIELD_CONFLICT_MANUAL_REVIEW` | entity | weak | 标准字段冲突复核规则 |
| `TRACE_MISSING_VOTE_TRACE` | trace | weak | 系统中暂未发现对应业务痕迹，建议补充核验 |
| `TRACE_MISSING_CONSTRUCTION_CONTRACT` | trace | weak | 系统中暂未发现对应业务痕迹，建议补充核验 |
| `TRACE_MISSING_APPRAISAL_CONTRACT` | trace | weak | 系统中暂未发现对应业务痕迹，建议补充核验 |
| `TRACE_MISSING_APPRAISAL_REPORT` | trace | weak | 系统中暂未发现对应业务痕迹，建议补充核验 |
| `TRACE_NEED_CONSTRUCTION_CONTRACT_NOT_SIGNED` | trace | weak | 系统中暂未发现对应业务痕迹，建议补充核验 |
| `PROCESS_NORMAL_VOTE_MISSING` | process | strong | 《住宅专项维修资金管理办法》第二十二条、第二十三条；《民法典》第二百七十八条、第二百八十一条 |
| `PROCESS_NORMAL_VOTE_NOT_LEGAL` | process | strong | 《住宅专项维修资金管理办法》第二十二条、第二十三条；《民法典》第二百七十八条、第二百八十一条 |
| `PROCESS_NORMAL_CONSTRUCTION_BEFORE_VOTE_REVIEW` | process | weak | 流程时序复核提示，当前未实现完整时序字段 |
| `PROCESS_EMERGENCY_FLOW_EXEMPTED` | process | strong | 《住宅专项维修资金管理办法》第二十四条；《上海市商品住宅维修基金管理办法》第十四条；沪房管物〔2011〕326号第二条至第四条 |
| `PROCESS_EMERGENCY_TRACE_REVIEW_REQUIRED` | process | strong | 沪房管物〔2011〕326号第二条至第四条 |
| `PROCESS_PROPERTY_VALUE_UNSUPPORTED` | process | weak | 字段映射层输入校验，不作为法规结论 |
| `AMOUNT_BUDGET_DISPLAY` | amount | none | 不绑定法规，仅展示 |
| `AMOUNT_CONTRACT_DISPLAY` | amount | none | 不绑定法规，仅展示 |
| `AMOUNT_INFO_MISSING` | amount | none | 不绑定法规，仅展示 |

当前无法匹配明确法规的 code：`ENTITY_IN_WARRANTY`、`ENTITY_OBJECT_UNKNOWN_MANUAL_REVIEW`、`ENTITY_FIELD_CONFLICT_MANUAL_REVIEW`、trace 类 code、`PROCESS_NORMAL_CONSTRUCTION_BEFORE_VOTE_REVIEW`、`PROCESS_PROPERTY_VALUE_UNSUPPORTED`。这些均为 weak 提示，不作为直接违法结论。

`reason_code_basis_registry.json` 还包含：

- `reserved_entries`：后续规则预留 code，如 `EMERGENCY_SCOPE_ALLOWED`、`VOTE_NOT_LEGAL`、`TRACE_MISSING_ACCEPTANCE_TRACE`、`AMOUNT_INFO_PRESENT`。
- `legacy_deprecated_entries`：旧版 code，如 `IN_SCOPE_COMMON_PART`、`MISSING_VOTE`，当前四层审计不再直接发出。
