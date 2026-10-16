def test_healthz(client):
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "db": "ok"}


def test_categorias_con_totales(client):
    data = client.get("/api/v1/categories").json()
    assert [(c["slug"], c["total"]) for c in data] == [("linux", 2), ("docker", 2)]


def test_categoria_inexistente_404(client):
    r = client.get("/api/v1/categories/nada")
    assert r.status_code == 404
    assert r.json()["error"] == "not_found"


def test_busqueda_texto_libre(client):
    r = client.get("/api/v1/commands", params={"q": "firewall"}).json()
    assert r["total"] == 1
    assert r["items"][0]["section"] == "AlmaLinux"


def test_busqueda_por_tag_con_tilde(client):
    r = client.get("/api/v1/commands", params={"q": "tag:métricas"}).json()
    assert [c["title"] for c in r["items"]] == ["Ver uso de 50% de CPU"]


def test_busqueda_porcentaje_literal(client):
    assert client.get("/api/v1/commands", params={"q": "50%"}).json()["total"] == 1


def test_filtros_categoria_y_nivel(client):
    r = client.get("/api/v1/commands", params={"category": "linux", "level": "intermedio"}).json()
    assert r["total"] == 1
    r = client.get("/api/v1/commands", params={"q": "cat:docker level:avanzado"}).json()
    assert r["total"] == 1


def test_paginacion(client):
    r = client.get("/api/v1/commands", params={"limit": 1, "offset": 1}).json()
    assert r["total"] == 4 and len(r["items"]) == 1


def test_facets(client):
    f = client.get("/api/v1/categories/linux/facets").json()
    assert {x["value"] for x in f["sections"]} == {"Común", "AlmaLinux"}


def test_escritura_sin_api_key_401(client):
    r = client.post("/api/v1/commands", json={})
    assert r.status_code == 401


def test_crud_comando_propio(client, auth):
    body = {
        "category": "linux",
        "title": "Mi alias favorito",
        "command": "alias ll='ls -lah'",
        "section": "Común",
        "topic": "Shell",
        "description": "Alias para listar rápido.",
        "examples": [{"description": "Persistir", "code": "echo \"alias ll='ls -lah'\" >> ~/.bashrc"}],
        "tags": ["Alias"],
    }
    r = client.post("/api/v1/commands", json=body, headers=auth)
    assert r.status_code == 201, r.text
    cid = r.json()["id"]
    assert r.json()["source"] == "user" and r.json()["tags"] == ["alias"]

    assert client.post("/api/v1/commands", json=body, headers=auth).status_code == 409

    r = client.patch(f"/api/v1/commands/{cid}", json={"level": "intermedio"}, headers=auth)
    assert r.json()["level"] == "intermedio"

    assert client.delete(f"/api/v1/commands/{cid}", headers=auth).status_code == 204
    assert client.get(f"/api/v1/commands/{cid}").status_code == 404


def test_comando_seed_no_editable(client, auth):
    cid = client.get("/api/v1/commands", params={"q": "firewall"}).json()["items"][0]["id"]
    r = client.patch(f"/api/v1/commands/{cid}", json={"level": "avanzado"}, headers=auth)
    assert r.status_code == 409


def test_favoritos(client, auth):
    cid = client.get("/api/v1/commands").json()["items"][0]["id"]
    r = client.put(f"/api/v1/commands/{cid}/favorite", json={"is_favorite": True}, headers=auth)
    assert r.json()["is_favorite"] is True
    assert client.get("/api/v1/commands", params={"favorites": True}).json()["total"] == 1


def test_skills(client):
    lst = client.get("/api/v1/skills").json()
    assert lst == [
        {"slug": "demo-skill", "name": "Demo — estándar de prueba", "summary": "Estándar de prueba en dos líneas."}
    ]
    assert "Contenido" in client.get("/api/v1/skills/demo-skill").json()["content"]


def test_stats(client):
    s = client.get("/api/v1/stats").json()
    assert s["commands"] == 4 and s["categories"] == 2 and s["skills"] == 1
    assert s["examples"] == 4
    assert s["by_level"]["básico"] == 2


def test_reseed_requiere_key(client):
    assert client.post("/api/v1/admin/reseed").status_code == 401
