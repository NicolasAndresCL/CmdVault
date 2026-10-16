import httpx
import pytest

from app.api_client import ApiClient


def _client(handler):
    return ApiClient("http://api", "k" * 16, transport=httpx.MockTransport(handler))


@pytest.mark.anyio
async def test_lectura_envia_api_key_y_omite_params_vacios():
    seen = {}

    def handler(req: httpx.Request):
        seen["key"] = req.headers["X-API-Key"]
        seen["params"] = dict(req.url.params)
        return httpx.Response(200, json={"items": [], "total": 0})

    c = _client(handler)
    await c.commands(q="ls", section="", topic=None, limit=5)
    assert seen == {"key": "k" * 16, "params": {"q": "ls", "limit": "5"}}


@pytest.mark.anyio
async def test_lectura_nunca_lanza_si_backend_cae():
    def handler(req):
        raise httpx.ConnectError("caído")

    c = _client(handler)
    assert await c.categories() == []
    assert await c.commands() == {"items": [], "total": 0}
    assert await c.healthy() is False


@pytest.mark.anyio
async def test_escritura_devuelve_detalle_de_error():
    def handler(req):
        return httpx.Response(409, json={"error": "conflict", "detail": "Ya existe"})

    ok, detail = await _client(handler).create_command({})
    assert (ok, detail) == (False, "Ya existe")


@pytest.mark.anyio
async def test_escritura_aplana_errores_422():
    def handler(req):
        return httpx.Response(422, json={"detail": [{"loc": ["body", "title"], "msg": "muy corto"}]})

    ok, detail = await _client(handler).create_command({})
    assert not ok and detail == "title: muy corto"


@pytest.mark.anyio
async def test_delete_204_sin_cuerpo():
    ok, data = await _client(lambda r: httpx.Response(204)).delete_command(1)
    assert (ok, data) == (True, None)


@pytest.fixture
def anyio_backend():
    return "asyncio"
