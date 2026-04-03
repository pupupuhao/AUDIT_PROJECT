import json
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from pipelines.rule_builder import enhance_rule

# chunk 文件路径
chunk_file = os.path.join(os.path.dirname(
    os.path.dirname(__file__)), "data", "chunks", "rules_db.json")

# 读取 chunk JSON
with open(chunk_file, "r", encoding="utf-8") as f:
    chunks = json.load(f)

# 遍历每条 chunk 进行增强
enhanced_rules = []
for i, rule in enumerate(chunks, 1):
    print(f"\n=== 处理规则 {i}/{len(chunks)} ===")
    result = enhance_rule(rule)
    enhanced_rules.append(result)


# 可选：保存增强后的规则到文件
output_file = os.path.join(os.path.dirname(os.path.dirname(
    __file__)), "data", "rules", "rules_db_with_llm.json")
os.makedirs(os.path.dirname(output_file), exist_ok=True)

with open(output_file, "w", encoding="utf-8") as f:
    json.dump(enhanced_rules, f, ensure_ascii=False, indent=2)

print(f"\n✅ 已生成增强规则，共 {len(enhanced_rules)} 条，保存在：{output_file}")
