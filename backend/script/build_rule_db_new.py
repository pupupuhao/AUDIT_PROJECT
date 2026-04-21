import json
import re
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))


INPUT_PATH = BASE_DIR / "data" / "raw" / "law_policy(new).md"
OUTPUT_PATH = BASE_DIR / "data" / "chunks" / "rule_db(new).json"
PURE_OUTPUT_PATH = BASE_DIR / "data" / "chunks" / "rule_db_pure(new).json"


def default_logic_rules() -> dict:
    return {
        "rule_nature": "",
        "audit_stage": "",
        "audit_dimension": "",
        "apply_scope": {
            "project_types": [],
            "repair_modes": [],
            "applicable_objects": [],
        },
        "judgement_mode": "",
        "required_fields": [],
        "required_documents": [],
        "field_expectations": [],
        "risk_points": [],
        "output_hint": {
            "conclusion_type": "",
            "risk_level": "",
            "message_template": "",
        },
    }


def normalize_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text or "")
    return text.strip()


def normalize_paragraphs(lines: list[str]) -> str:
    cleaned = [line.strip() for line in lines if line.strip()]
    return normalize_text(" ".join(cleaned))


def extract_label(text: str) -> str:
    raw = (text or "").strip()
    patterns = [
        r"^(第[一二三四五六七八九十百千万零两\d]+条)",
        r"^([一二三四五六七八九十百千万零两\d]+、)",
        r"^([（(][一二三四五六七八九十百千万零两\d]+[)）])",
        r"^(\d+[、.])",
    ]
    for pattern in patterns:
        match = re.match(pattern, raw)
        if match:
            return match.group(1)
    return ""


def strip_label(text: str, label: str) -> str:
    raw = (text or "").strip()
    if not label:
        return raw
    stripped = raw[len(label):].strip()
    return stripped.lstrip(":： ").strip()


def derive_title_text(level: int, full_title: str, label: str) -> str:
    title = strip_label(full_title, label)
    if level == 5 and title:
        head = re.split(r"[:：]", title, maxsplit=1)[0]
        return head.strip()
    return title


def path_from_node(node: dict) -> list[str]:
    parts = [node["law_name"]]
    for key in ("clause_label", "item_label", "subitem_label"):
        value = node.get(key, "")
        if value:
            parts.append(value)
    return parts


def build_self_context(full_title: str, display_text: str) -> str:
    full_title = normalize_text(full_title)
    display_text = normalize_text(display_text)
    if not full_title:
        return display_text
    if not display_text or display_text == full_title:
        return full_title
    return normalize_text(f"{full_title} {display_text}")


def parse_markdown(markdown: str) -> list[dict]:
    nodes: list[dict] = []
    stack: dict[int, dict] = {}
    doc_counter = 0
    rule_counter = 0
    current_law_name = ""
    current_doc_id = ""

    for raw_line in markdown.splitlines():
        stripped = raw_line.strip()
        if not stripped:
            current = stack.get(5) or stack.get(4) or stack.get(3)
            if current and current["body_lines"] and current["body_lines"][-1] != "":
                current["body_lines"].append("")
            continue

        if stripped.startswith("## "):
            current_law_name = stripped[3:].strip()
            doc_counter += 1
            current_doc_id = f"DOC_{doc_counter:03d}"
            stack = {}
            continue

        heading_level = None
        if stripped.startswith("##### "):
            heading_level = 5
        elif stripped.startswith("#### "):
            heading_level = 4
        elif stripped.startswith("### "):
            heading_level = 3

        if heading_level is not None:
            title = stripped[heading_level + 1 :].strip()
            parent_level = heading_level - 1 if heading_level > 3 else None
            parent = stack.get(parent_level) if parent_level else None

            clause_label = parent.get("clause_label", "") if parent else ""
            item_label = parent.get("item_label", "") if parent else ""
            subitem_label = ""

            current_label = extract_label(title)
            if heading_level == 3:
                clause_label = current_label
            elif heading_level == 4:
                item_label = current_label
            elif heading_level == 5:
                subitem_label = current_label

            rule_id = f"RULE_{rule_counter:04d}"
            rule_counter += 1

            node = {
                "id": rule_id,
                "doc_id": current_doc_id,
                "parent_id": parent["id"] if parent else None,
                "law_name": current_law_name,
                "node_level": heading_level - 1,
                "node_type": {
                    3: "clause",
                    4: "item",
                    5: "subitem",
                }[heading_level],
                "clause_label": clause_label,
                "item_label": item_label,
                "subitem_label": subitem_label,
                "full_title": title,
                "title_text": derive_title_text(heading_level, title, current_label),
                "body_lines": [],
                "index": len(nodes),
            }
            nodes.append(node)

            stack[heading_level] = node
            for level in tuple(stack.keys()):
                if level > heading_level:
                    del stack[level]
            continue

        current = stack.get(5) or stack.get(4) or stack.get(3)
        if current:
            current["body_lines"].append(stripped)

    return nodes


def finalize_nodes(nodes: list[dict]) -> list[dict]:
    finalized: list[dict] = []
    context_by_id: dict[str, str] = {}

    for node in nodes:
        display_text = normalize_paragraphs(node.pop("body_lines", [])) or normalize_text(node["full_title"])
        parent_context = context_by_id.get(node["parent_id"], "")
        current_context = build_self_context(node["full_title"], display_text)
        embedding_text = normalize_text(" ".join([
            node["law_name"],
            parent_context,
            current_context,
        ]))

        finalized_node = {
            "id": node["id"],
            "doc_id": node["doc_id"],
            "parent_id": node["parent_id"],
            "law_name": node["law_name"],
            "node_level": node["node_level"],
            "node_type": node["node_type"],
            "clause_label": node["clause_label"],
            "item_label": node["item_label"],
            "subitem_label": node["subitem_label"],
            "sub_clause": node["subitem_label"] or node["item_label"] or node["clause_label"],
            "full_title": node["full_title"],
            "title_text": node["title_text"],
            "display_text": display_text,
            "content": display_text,
            "embedding_text": embedding_text,
            "clean_text": embedding_text,
            "parent_context": parent_context,
            "path": path_from_node(node),
            "index": node["index"],
            "category": "",
            "logic_rules": default_logic_rules(),
        }
        finalized.append(finalized_node)
        context_by_id[finalized_node["id"]] = normalize_text(" ".join([
            parent_context,
            current_context,
        ]))

    return finalized


def filter_rule_nodes(nodes: list[dict]) -> list[dict]:
    parent_ids = {node["parent_id"] for node in nodes if node.get("parent_id")}
    return [node for node in nodes if node["id"] not in parent_ids]


def run() -> None:
    markdown = INPUT_PATH.read_text(encoding="utf-8")
    parsed_nodes = parse_markdown(markdown)
    rule_db = finalize_nodes(parsed_nodes)
    pure_rule_db = filter_rule_nodes(rule_db)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as file:
        json.dump(rule_db, file, ensure_ascii=False, indent=2)
    with PURE_OUTPUT_PATH.open("w", encoding="utf-8") as file:
        json.dump(pure_rule_db, file, ensure_ascii=False, indent=2)

    print(
        f"处理完成：全量结构节点 {len(rule_db)} 条，纯规则节点 {len(pure_rule_db)} 条，"
        f"输出文件: {OUTPUT_PATH} / {PURE_OUTPUT_PATH}"
    )


if __name__ == "__main__":
    run()
