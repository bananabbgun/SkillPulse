from skillpulse.extraction import SkillExtractor
from skillpulse.schema import ExtractedSkill


def ids(skills):
    return {skill.skill_id for skill in skills}


def test_extracts_bilingual_data_engineering_skills():
    text = "技能需求：Python、SQL、資料管線 data pipeline、Spark、Airflow、資料倉儲。"
    found = SkillExtractor().extract(text)
    assert {"python", "sql", "etl", "spark", "airflow", "data_warehouse"}.issubset(ids(found))


def test_context_required_ai_terms_match_in_requirement_context():
    text = "Requirements: Python, LLM, prompt engineering, RAG, embeddings, vector database."
    found = SkillExtractor().extract(text)
    assert {"llm", "prompt_engineering", "rag", "embeddings", "vector_db"}.issubset(ids(found))
    assert any(skill.ai_era for skill in found)


def test_context_required_ai_terms_do_not_match_boilerplate_only():
    text = "我們是一間生成式 AI 公司，提供員工旅遊與彈性上班。"
    found = SkillExtractor().extract(text)
    assert "llm" not in ids(found)

