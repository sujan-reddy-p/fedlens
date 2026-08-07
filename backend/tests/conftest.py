import pytest

from app.agent.graph import get_graph
from app.config import get_settings


@pytest.fixture(autouse=True)
def isolate_tests_from_external_services(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("APP_ENV", "test")
    get_settings.cache_clear()
    get_graph.cache_clear()
    yield
    get_settings.cache_clear()
    get_graph.cache_clear()
