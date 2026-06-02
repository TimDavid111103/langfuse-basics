"""
Load a questionnaire JSON file into the database.

If a questionnaire with the same name already exists a new version is created.
The source_material_name field is optional; if provided the questionnaire is
linked to the matching SourceMaterial row.

Questionnaire JSON format:
{
  "name": "Chapter 8 — Fluids",
  "description": "...",
  "source_material_name": "Chapter 8 - Fluids",   // optional
  "questions": [
    {
      "index": 0,
      "text": "...",
      "topic_hint": "...",
      "expected_concepts": ["...", "..."]
    }
  ]
}

Usage:
    # Load all JSON files in data/questionnaires/
    uv run python scripts/load_questionnaire.py

    # Load specific file(s)
    uv run python scripts/load_questionnaire.py data/questionnaires/fluids.json

Run from the backend/ directory.
"""
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlmodel import select

from app.database import AsyncSessionLocal, create_db_and_tables
from app.models.questionnaire import Questionnaire, QuestionnaireVersion
from app.models.source_material import SourceMaterial

QUESTIONNAIRES_DIR = Path(__file__).parent.parent / "data" / "questionnaires"


async def load_file(file_path: Path) -> None:
    """Load a single questionnaire JSON file into the database."""
    data = json.loads(file_path.read_text())

    name: str = data["name"]
    description: str = data["description"]
    source_material_name: str | None = data.get("source_material_name")
    questions: list[dict] = data["questions"]

    async with AsyncSessionLocal() as session:
        source_material_id: int | None = None
        if source_material_name:
            sm_result = await session.exec(
                select(SourceMaterial).where(SourceMaterial.name == source_material_name)
            )
            sm = sm_result.first()
            if sm is None:
                print(f"  warn  source material '{source_material_name}' not found — linking skipped")
            else:
                source_material_id = sm.id

        existing_result = await session.exec(
            select(Questionnaire).where(Questionnaire.name == name)
        )
        questionnaire = existing_result.first()

        questions_json = json.dumps(questions)

        if questionnaire is None:
            questionnaire = Questionnaire(
                name=name,
                description=description,
                source_material_id=source_material_id,
                current_version=1,
            )
            session.add(questionnaire)
            await session.flush()

            version = QuestionnaireVersion(
                questionnaire_id=questionnaire.id,
                version_number=1,
                questions_json=questions_json,
                change_summary="Initial version",
            )
            session.add(version)
            await session.commit()
            print(f"  created  '{name}'  v1  ({len(questions)} questions, id={questionnaire.id})")
        else:
            new_version = questionnaire.current_version + 1
            version = QuestionnaireVersion(
                questionnaire_id=questionnaire.id,
                version_number=new_version,
                questions_json=questions_json,
                change_summary=f"Loaded from {file_path.name}",
            )
            session.add(version)
            questionnaire.current_version = new_version
            questionnaire.updated_at = datetime.utcnow()
            if source_material_id:
                questionnaire.source_material_id = source_material_id
            session.add(questionnaire)
            await session.commit()
            print(f"  updated  '{name}'  v{new_version}  ({len(questions)} questions, id={questionnaire.id})")


async def main(paths: list[Path]) -> None:
    """Load all given questionnaire JSON files into the database."""
    await create_db_and_tables()
    for path in paths:
        print(f"loading {path.name} ...")
        await load_file(path)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        targets = [Path(p) for p in sys.argv[1:]]
    else:
        targets = sorted(QUESTIONNAIRES_DIR.glob("*.json"))
        if not targets:
            print(f"No JSON files found in {QUESTIONNAIRES_DIR}")
            sys.exit(0)

    asyncio.run(main(targets))
