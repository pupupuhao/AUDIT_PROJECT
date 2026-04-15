# 审计导入模板 Excel（V1 设计稿）

## 目标
本稿仅用于记录 V1 模板字段与映射策略，不包含解析实现代码。

## 三层结构
1. Excel 原始字段层：保持来源字段原名，不重命名。
2. 映射层：将原始字段映射到审计语义字段，独立维护。
3. 审计字段层：沿用当前 rule_engine 的既有字段。

## V1 模板固定列（建议）
- `wsname`
- `need_vote`
- `is_voted`
- `need_record`
- `agree_hou`
- `agree_hou_rate`
- `agree_area`
- `bo_tot_amt`
- `orgn_amt`
- `code`
- `name`
- `work_org`
- `startup_date`
- `finish_date`

## 映射策略（仅设计）
- 稳定直映：
  - `wsname -> project_name`
  - `is_voted -> has_vote`（布尔标准化）
  - `startup_date -> construction_start_date`
  - `finish_date -> construction_end_date`
- 延迟映射（口径待确认）：
  - `bo_tot_amt -> excel_amount_raw`
  - `orgn_amt -> excel_approved_amount_raw`

## 当前约束
- 本阶段不做 Excel 上传/解析实现。
- 不新增前端上传按钮，不新增解析函数。
- 金额字段先保留源语义，不直接固化到 `amount/approved_amount`。
