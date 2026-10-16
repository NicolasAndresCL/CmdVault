"""Lógica pura de búsqueda: sin BD, testeable de forma aislada."""

from __future__ import annotations

import re
import shlex
from dataclasses import dataclass, field

_FILTRO = re.compile(r"^(tag|level|section|topic|cat):(.+)$", re.IGNORECASE)


@dataclass
class ParsedQuery:
    """Consulta del buscador ya descompuesta.

    Soporta texto libre, frases entre comillas y filtros ``tag:x``, ``level:x``,
    ``section:x``, ``topic:x`` y ``cat:x`` (p. ej. ``cat:docker tag:redes "port forward"``).
    """

    terms: list[str] = field(default_factory=list)
    filters: dict[str, str] = field(default_factory=dict)

    @property
    def empty(self) -> bool:
        return not self.terms and not self.filters


def parse_query(raw: str | None) -> ParsedQuery:
    pq = ParsedQuery()
    if not raw or not raw.strip():
        return pq
    try:
        tokens = shlex.split(raw)
    except ValueError:  # comillas sin cerrar: se degrada a split simple
        tokens = raw.split()
    for tok in tokens:
        m = _FILTRO.match(tok)
        if m:
            pq.filters[m.group(1).lower()] = m.group(2).strip().lower()
        elif tok.strip():
            pq.terms.append(tok.strip().lower())
    return pq


def escape_like(term: str) -> str:
    """Escapa comodines de LIKE para que ``50%`` o ``a_b`` se busquen literal."""
    return term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
