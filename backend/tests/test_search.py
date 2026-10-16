from app.search import escape_like, parse_query
from app.seed.loader import parse_frontmatter, slugify


def test_parse_query_vacia():
    assert parse_query(None).empty
    assert parse_query("   ").empty


def test_parse_query_terminos_y_filtros():
    pq = parse_query('cat:docker tag:Redes "port forward" logs')
    assert pq.filters == {"cat": "docker", "tag": "redes"}
    assert pq.terms == ["port forward", "logs"]


def test_parse_query_comillas_sin_cerrar_no_revienta():
    pq = parse_query('"sin cerrar')
    assert pq.terms == ['"sin', "cerrar"]


def test_escape_like():
    assert escape_like("50%_a\\b") == "50\\%\\_a\\\\b"


def test_slugify_estable_y_sin_tildes():
    assert slugify("Abrir puerto en firewalld (AlmaLinux)") == "abrir-puerto-en-firewalld-almalinux"
    assert slugify("Configuración rápida ñandú") == "configuracion-rapida-nandu"


def test_frontmatter_plegado():
    meta = parse_frontmatter("name: x\ndescription: >\n  línea uno\n  línea dos\nother: y")
    assert meta == {"name": "x", "description": "línea uno línea dos", "other": "y"}
