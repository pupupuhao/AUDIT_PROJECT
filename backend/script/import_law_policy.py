import asyncio
import re
import sys
from pathlib import Path

from tortoise import Tortoise


BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from app.core.events import _build_tortoise_db_url
from modules.audit.models.law_clause import LawClauseModel


LAW_POLICY_PATH = BASE_DIR / "data" / "raw" / "law_policy.md"


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def parse_clause_label(title: str) -> str:
    title = normalize_text(title)
    patterns = [
        r"^(第[一二三四五六七八九十百千万零两0-9]+条)",
        r"^([一二三四五六七八九十]+、)",
        r"^([（(][一二三四五六七八九十0-9]+[)）])",
        r"^([0-9]+[、.])",
    ]
    for pattern in patterns:
        match = re.match(pattern, title)
        if match:
            return match.group(1)
    return title[:100]


def parse_markdown(markdown: str) -> list[dict]:
    clauses = []
    current_law = ""
    current_title = ""
    content_lines: list[str] = []

    def flush_current():
        nonlocal current_title, content_lines
        if not current_law or not current_title or not content_lines:
            current_title = ""
            content_lines = []
            return

        full_title = normalize_text(current_title)
        content = "\n".join(line.rstrip() for line in content_lines).strip()
        if content:
            clauses.append(
                {
                    "law_name": normalize_text(current_law),
                    "clause_label": parse_clause_label(full_title),
                    "full_title": full_title,
                    "content": content,
                }
            )
        current_title = ""
        content_lines = []

    for raw_line in markdown.splitlines():
        line = raw_line.strip()
        if line.startswith("## "):
            flush_current()
            current_law = line[3:].strip()
            continue

        if line.startswith("### "):
            flush_current()
            current_title = line[4:].strip()
            continue

        if not line:
            if content_lines and content_lines[-1] != "":
                content_lines.append("")
            continue

        if current_title:
            content_lines.append(line)

    flush_current()
    return clauses


async def run():
    await Tortoise.init(
        db_url=_build_tortoise_db_url(),
        modules={"models": ["modules.system.models", "modules.audit.models"]},
    )
    await Tortoise.generate_schemas()

    markdown = LAW_POLICY_PATH.read_text(encoding="utf-8")
    clauses = parse_markdown(markdown)

    created = 0
    updated = 0

    for item in clauses:
        obj = await LawClauseModel.filter(
            law_name=item["law_name"],
            clause_label=item["clause_label"],
            full_title=item["full_title"],
            status__not=9,
        ).first()

        if obj is None:
            await LawClauseModel.create(**item)
            created += 1
        else:
            obj.content = item["content"]
            await obj.save()
            updated += 1

    total = await LawClauseModel.filter(status__not=9).count()
    await Tortoise.close_connections()
    print(f"导入完成：新增 {created} 条，更新 {updated} 条，当前有效条款 {total} 条。")


if __name__ == "__main__":
    asyncio.run(run())
