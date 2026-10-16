## Qué cambia y por qué

## Tipo
- [ ] Contenido de la biblioteca (seed JSON)
- [ ] Backend
- [ ] Frontend / temas
- [ ] Infra (Docker / CI)

## Verificación
- [ ] `python -m app.seed.validate` en verde (si toca el seed)
- [ ] `pytest` backend y frontend en verde
- [ ] `docker compose up -d --build --wait` + `./scripts/smoke.sh`
- [ ] README / docs actualizados
