"""A gateway call is persisted and can be summarized by the usage repository."""

from cropcover.config import Settings
from cropcover.db.llm_calls import UsageRepository, make_recorder
from cropcover.db.session import make_engine, make_sessionmaker
from cropcover.llm.gateway import FakeLLM, LLMGateway


async def test_gateway_call_is_recorded_and_summed_per_day(database_url):
    settings_engine = make_engine_from_url(database_url)
    sessions = make_sessionmaker(settings_engine)
    gateway = LLMGateway(
        [FakeLLM("gemini", "gemini-3.8-flash", ["A short answer."])],
        recorder=make_recorder(sessions),
        usd_inr=95,
    )
    result = await gateway.generate([{"role": "user", "content": "Question"}])
    async with sessions() as session:
        rows = await UsageRepository(session).by_day()
    await settings_engine.dispose()
    assert result.provider == "gemini"
    assert rows[0]["calls"] == 1 and rows[0]["tokens_in"] == result.tokens_in
    assert rows[0]["cost_inr"] == round(result.cost_inr, 4)


def make_engine_from_url(database_url):
    settings = Settings(app_env="ci", database_url=database_url, _env_file=None)
    return make_engine(settings)
