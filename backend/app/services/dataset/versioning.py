import json
from datetime import datetime

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.questionnaire import Questionnaire, QuestionnaireVersion
from app.schemas.dataset import QuestionnaireCreate, QuestionnaireUpdate
from app.schemas.rubric import QuestionItem


async def create_questionnaire(
    payload: QuestionnaireCreate,
    session: AsyncSession,
) -> Questionnaire:
    """Create a new questionnaire with its initial version."""
    questionnaire = Questionnaire(
        name=payload.name,
        description=payload.description,
        source_material_id=payload.source_material_id,
        current_version=1,
    )
    session.add(questionnaire)
    await session.flush()

    version = QuestionnaireVersion(
        questionnaire_id=questionnaire.id,
        version_number=1,
        questions_json=json.dumps([q.model_dump() for q in payload.questions]),
        change_summary="Initial version",
    )
    session.add(version)
    await session.commit()
    await session.refresh(questionnaire)
    return questionnaire


async def update_questionnaire(
    questionnaire_id: int,
    payload: QuestionnaireUpdate,
    session: AsyncSession,
) -> Questionnaire:
    """Append a new version to an existing questionnaire."""
    result = await session.exec(
        select(Questionnaire).where(Questionnaire.id == questionnaire_id)
    )
    questionnaire = result.one()

    new_version_number = questionnaire.current_version + 1
    version = QuestionnaireVersion(
        questionnaire_id=questionnaire_id,
        version_number=new_version_number,
        questions_json=json.dumps([q.model_dump() for q in payload.questions]),
        change_summary=payload.change_summary,
    )
    session.add(version)

    questionnaire.current_version = new_version_number
    questionnaire.updated_at = datetime.utcnow()
    session.add(questionnaire)

    await session.commit()
    await session.refresh(questionnaire)
    return questionnaire


async def get_version_questions(
    questionnaire_id: int,
    version_number: int,
    session: AsyncSession,
) -> list[QuestionItem]:
    """Retrieve and deserialize questions for a specific questionnaire version."""
    result = await session.exec(
        select(QuestionnaireVersion).where(
            QuestionnaireVersion.questionnaire_id == questionnaire_id,
            QuestionnaireVersion.version_number == version_number,
        )
    )
    version = result.one()
    raw = json.loads(version.questions_json)
    return [QuestionItem(**item) for item in raw]
