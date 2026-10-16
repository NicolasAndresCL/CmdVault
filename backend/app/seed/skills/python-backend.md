---
name: python-backend
description: >
  Estándares de arquitectura backend de Nicolás Cano Leal en Python: Django +
  DRF por capas, excepciones de dominio que viajan como HTTP, permisos a nivel
  de objeto, settings tipados por entorno y testing con pytest. USAR SIEMPRE
  que se diseñe, arranque o refactorice una API/backend Python — vistas,
  serializers, servicios, manejo de errores, permisos, settings o tests —
  aunque no se pida explícitamente "sigue mis estándares".
---

# Python backend — estándares de Nicolás Cano Leal

> Referencia real y probada: `backend/core/` (`exceptions.py`, `events.py`,
> `api/base_views.py`, `api/exception_handler.py`, `api/permissions.py`) y
> `backend/config/settings/` de TienditaMarian.

## Stack por defecto

Python 3.12+ · Django + DRF (ViewSets/router para CRUD puro; clases explícitas
con mixins cuando hay endpoints no-CRUD que no calzan en un router) ·
`pydantic-settings`/`django-environ` para config tipada desde `.env` ·
PostgreSQL en producción (`dj-database-url` + `psycopg` v3), SQLite en tests ·
`gunicorn` + WhiteNoise + `/healthz/` · pytest + `pytest-cov` + `ruff`.

**No hardcodear config ni secretos, nunca.** Todo desde `.env` vía settings
tipados.

## 1. Excepciones de dominio, no `Response` a mano

Las reglas de negocio **lanzan**, no devuelven un `Response` armado en la
vista. Un servicio se prueba con `pytest.raises(MiError)` sin levantar HTTP:

```python
class TienditaError(Exception):
    """Raíz de errores de negocio. Cualquier otra excepción es un bug → 500 ruidoso."""

    codigo: str = "error_tienda"
    http_status: int = status.HTTP_400_BAD_REQUEST
    mensaje: str = "No se pudo completar la operación."

    def __init__(self, mensaje=None):
        self.mensaje = mensaje or self.mensaje
        super().__init__(self.mensaje)

    def detalle(self) -> dict:
        return {}


class StockInsuficienteError(TienditaError):
    codigo = "stock_insuficiente"
    http_status = status.HTTP_409_CONFLICT  # 409, no 400: la petición está
    # bien formada, choca con el estado actual — "alguien se te adelantó",
    # no "te equivocaste al pedir".
```

Un **único** `EXCEPTION_HANDLER` (`core/api/exception_handler.py`) traduce
`TienditaError` a HTTP y normaliza también los errores nativos de DRF al mismo
contrato:

```json
{"error": {"codigo": "stock_insuficiente", "mensaje": "...", "detalle": {...}}}
```

El `codigo` es el identificador estable que consume el frontend — nunca el
texto en español, que puede cambiar. Registrar con `logger.warning` los
errores de negocio (esperables) y con `logger.exception` los que el handler no
reconoce (bugs reales, deben verse ruidosos, nunca tragarse en silencio).

## 2. Vistas base para eliminar duplicación, sin forzar ViewSets

Si el proyecto tiene endpoints no-CRUD (`carrito/add`, `checkout`) que no
calzan en un router, documentar la decisión como ADR en el propio archivo
(ver `core/api/base_views.py`) y centralizar el cableado repetido:

```python
class BaseListCreateView(mixins.ListModelMixin, mixins.CreateModelMixin, GenericAPIView):
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)
```

## 3. Permisos: nivel de objeto + filtro de queryset, las DOS mitades

`IsAuthenticated` solo responde "¿quién eres?", no "¿esto es tuyo?". Hacen
falta las dos mitades o queda un agujero:

- **Filtro de listado** (`PorDuenoMixin.get_queryset`): sin él, el listado
  sigue devolviendo lo ajeno aunque el detalle esté protegido.
- **Permiso de objeto** (`EsDuenoOAdmin.has_object_permission`): protege el
  acceso directo por id.
- **`perform_create` fuerza el dueño desde `request.user`**, nunca desde el
  body — si no, se puede crear un recurso a nombre de otra persona mandando
  `{"usuario": 7}`.

```python
class EsAdminOSoloLectura(BasePermission):
    """Lectura pública, escritura solo staff — el patrón típico de catálogo."""

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_staff)
```

## 4. Eventos de dominio con callbacks inyectables

Cuando una acción dispara efectos secundarios (correo, notificación,
auditoría), no acoplarlos directo en `save()` ni en señales invisibles.
Declarar el evento y suscribir el efecto — la lógica de negocio no sabe quién
escucha, y los tests inyectan un despachador vacío:

```python
class Evento(StrEnum):
    ORDEN_CREADA = "orden_creada"  # nombrado en pasado: ya ocurrió


despachador = Despachador()
despachador.suscribir(Evento.ORDEN_CREADA, enviar_correo_confirmacion)
despachador.emitir(Evento.ORDEN_CREADA, orden)
```

**Regla clave: un suscriptor que falla no tumba la operación.** Cada callback
va en su propio `try/except`; si el correo está caído, la venta ya ocurrió y
debe quedar registrada — el fallo se loguea y la vida sigue. `emitir` nunca
lanza, devuelve la lista de fallos para que quien llama decida.

## 5. Settings por entorno, herencia real (no forks divergentes)

`base.py` (común) ← `dev.py` / `test.py` / `prod.py` heredan con `from .base
import *`. **Nunca** un settings de test autónomo que diverja de producción
(el bug clásico: un `settings_test.py` corriendo sin DRF, con `AllowAny`,
validando una app que no es la que se despliega).

- `test.py` inyecta sus defaults en `os.environ` **antes** de importar
  `base`, para que la suite corra en checkout limpio sin `.env`:
  `SECRET_KEY` insegura de prueba, `DATABASE_URL=sqlite://:memory:` (pero
  cede el paso a un `DATABASE_URL` real si el entorno lo trae — así la misma
  suite corre contra Postgres cuando hace falta probar `select_for_update`).
  Hashing rápido (`MD5PasswordHasher`) y throttling desactivado (`None`, no
  borrado — DRF lanza `ImproperlyConfigured` si una vista referencia un scope
  ausente).
- `prod.py`: objetivo explícito "`check --deploy` sin warnings". Togglear
  `SECURE_SSL_REDIRECT`/`SESSION_COOKIE_SECURE`/`CSRF_COOKIE_SECURE`/HSTS con
  una sola variable (`SECURE_HTTPS`) para poder correr detrás de un proxy sin
  TLS todavía, sin tocar código.
- `ALLOWED_HOSTS` en prod **sin default**: `env.list("ALLOWED_HOSTS")` a
  secas, para que faltar la variable sea un fallo explícito, no un `*`
  silencioso.

## 6. Hardening — checklist antes de "listo para producción"

- [ ] Autenticación real (JWT/Token + `IsAuthenticated` de default), nunca
      `AllowAny`.
- [ ] Rate limiting diferenciado por perfil de riesgo (`anon`/`user`/scope
      propio para login — es el endpoint que se ataca por fuerza bruta).
- [ ] `manage.py check --deploy` limpio.
- [ ] `SECRET_KEY` fuerte, fuera del código.
- [ ] Logging estructurado con loggers por raíz de paquete (`apps`, `core`),
      nivel configurable por `LOG_LEVEL`.

## 7. Testing

- pytest como disciplina: lógica pura sin I/O es lo que se testea primero y
  con más profundidad. `unittest.mock` para aislar BD/archivos, `responses`
  para HTTP cliente.
- Cobertura objetivo ~83%+, **100% en caminos críticos** (serializers, cálculo
  de negocio, checkout).
- `conftest`/`settings.test` fuerza SQLite (o el motor que corresponda) —
  entorno de test aislado de producción siempre.

## Ver también
[[arquitectura-software]] para el diseño (UML, SOLID, patrones) que estas capas
implementan · [[docker]] para empaquetar este backend · [[kubernetes]] para
desplegarlo en un clúster · [[terraform]] para la infraestructura que necesita ·
[[github-actions]] para el pipeline que corre estos tests y valida
`check --deploy`.
