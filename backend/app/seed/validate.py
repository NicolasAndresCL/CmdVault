"""Valida todos los JSON de seed contra el contrato y detecta duplicados.

Uso (desde ``backend/``): ``python -m app.seed.validate``. Sale con código 1 si hay errores.
"""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict

from pydantic import ValidationError

from app.seed.loader import DATA_DIR
from app.seed.schema import SeedFile


def main() -> int:
    errores: list[str] = []
    titulos: dict[str, Counter[str]] = defaultdict(Counter)
    categorias: dict[str, dict] = {}
    totales: Counter[str] = Counter()

    archivos = sorted(DATA_DIR.glob("*.json"))
    if not archivos:
        print(f"No hay archivos de seed en {DATA_DIR}")
        return 1

    for path in archivos:
        try:
            seed = SeedFile.model_validate(json.loads(path.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, ValidationError) as exc:
            errores.append(f"{path.name}: {exc}")
            continue
        cat = seed.category
        meta = cat.model_dump(exclude={"order"})
        if cat.slug in categorias and categorias[cat.slug] != meta:
            errores.append(f"{path.name}: metadatos de categoría '{cat.slug}' distintos a otro archivo")
        categorias.setdefault(cat.slug, meta)
        for c in seed.commands:
            titulos[cat.slug][c.title.lower()] += 1
        totales[cat.slug] += len(seed.commands)

    for slug, cnt in titulos.items():
        for titulo, n in cnt.items():
            if n > 1:
                errores.append(f"{slug}: título duplicado '{titulo}' ({n} veces)")

    for slug, n in sorted(totales.items()):
        print(f"  {slug:<12} {n:>4} comandos")
    print(f"  {'TOTAL':<12} {sum(totales.values()):>4} comandos en {len(archivos)} archivos")

    if errores:
        print("\nERRORES:")
        for e in errores:
            print(f"  - {e}")
        return 1
    print("Seed válido.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
