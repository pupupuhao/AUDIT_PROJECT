import json
import re
from pathlib import Path

from langchain_text_splitters import MarkdownHeaderTextSplitter


headers_to_split_on = [
    ("##", "law_name"),
    ("###", "clause_title"),
]

markdown_splitter = MarkdownHeaderTextSplitter(
    headers_to_split_on=headers_to_split_on,
    strip_headers=False,
)


def extract_label(title: str) -> str:
    standard = re.search(r'第[一二三四五六七八九十百千万\d]+条', title)
    if standard:
        return standard.group()

    major = re.search(r'^[一二三四五六七八九十百千万\d]+[、.]', title.strip())
    if major:
        return major.group()[:-1]

    sub = re.search(r'[（(][一二三四五六七八九十百千万\d]+[）)]', title.strip())
    if sub:
        return sub.group()

    return ""


def clean_text(text: str) -> str:
    text = re.sub(r"#{1,6}\s*", "", text)
    text = re.sub(r"\n+", " ", text)
    return text.strip()


def split_sub_clauses(text: str):
    parts = re.split(r'(?=[（(][一二三四五六七八九十百千万\d]+[）)])', text)
    return [part.strip() for part in parts if part.strip()]


def extract_keywords(text: str):
    words = re.findall(r"[\u4e00-\u9fa5]{2,}", text)
    deduped = []
    for word in words:
        if word not in deduped:
            deduped.append(word)
    return deduped[:5]


def default_logic_rules() -> dict:
    return {
        "action": "",
        "target": [],
        "condition": [],
        "forbidden": [],
        "responsibility": "",
        "threshold": None,
        "required_docs": [],
        "is_emergency": False,
    }


input_file = Path(r"D:\audit-project\backend\data\raw\law_policy.md")
output_path = Path(r"D:\audit-project\backend\data\chunks\rules_db.json")

with input_file.open("r", encoding="utf-8") as f:
    md_content = f.read()

md_header_splits = markdown_splitter.split_text(md_content)

structured_data = []
rule_counter = 0

for split in md_header_splits:
    raw_law = split.metadata.get("law_name", "")
    clean_law = raw_law.replace("#", "").strip()

    full_title = split.metadata.get("clause_title", "").strip()
    clause_label = extract_label(full_title)

    raw_content = split.page_content.strip()
    parent_context = clean_text(split.page_content)
    sub_parts = split_sub_clauses(raw_content)

    for sub in sub_parts:
        unique_id = f"RULE_{str(rule_counter).zfill(3)}"
        cleaned = clean_text(sub)

        chunk = {
            "id": unique_id,
            "law_name": clean_law,
            "clause_label": clause_label,
            "full_title": full_title,
            "content": cleaned,
            "parent_context": parent_context,
            "keywords": extract_keywords(cleaned),
            "sub_clause": extract_label(sub),
            "index": rule_counter,
            "logic_rules": default_logic_rules(),
        }

        structured_data.append(chunk)
        rule_counter += 1

with output_path.open("w", encoding="utf-8") as f:
    json.dump(structured_data, f, ensure_ascii=False, indent=2)

print(f"处理完成，共生成 {len(structured_data)} 条 chunk")
