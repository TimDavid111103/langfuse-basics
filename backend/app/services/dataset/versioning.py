import json

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.questionnaire import QuestionnaireVersion
from app.schemas.rubric import QuestionItem


async def get_version_questions(
    questionnaire_id: int,
    version_number: int,
    session: AsyncSession,
) -> list[QuestionItem]:
    """Retrieve and deserialise the questions for a specific questionnaire version."""
    result = await session.exec(
        select(QuestionnaireVersion).where(
            QuestionnaireVersion.questionnaire_id == questionnaire_id,
            QuestionnaireVersion.version_number == version_number,
        )
    )
    version = result.one()
    raw = json.loads(version.questions_json)
    return [QuestionItem(**item) for item in raw]
