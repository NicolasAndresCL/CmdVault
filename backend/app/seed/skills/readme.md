---
name: readme
description: >
  Formato obligatorio de los README de Nicolás Cano Leal (patrón de PyDual): título con tagline, badges
  de CI/versión/Python, tabla Versión/Fecha/Autor, arquitectura en árbol comentado, tablas de servicios,
  endpoints, errores y variables, verificación, decisiones de diseño y bloque de Autor con pie de versión.
  USAR SIEMPRE que se cree un README nuevo, se reescriba uno existente o se le agreguen secciones
  principales, en cualquier proyecto — aunque no se pida explícitamente "con mi formato".
---

# README — formato de Nicolás Cano Leal

> Referencia viva: <https://github.com/NicolasAndresCL/PyDual> (README v2.0.0) y
> <https://github.com/NicolasAndresCL/CmdVault>. Ante la duda, copiar la estructura de esos dos.

## Reglas no negociables

1. **Título con tagline**: `# Nombre — qué es en una frase corta`. Nunca solo el nombre.
2. **Badges en este orden**, debajo del título:
   ```markdown
   [![CI](https://github.com/NicolasAndresCL/<repo>/actions/workflows/ci.yml/badge.svg)](https://github.com/NicolasAndresCL/<repo>/actions/workflows/ci.yml)
   ![Versión](https://img.shields.io/badge/versi%C3%B3n-1.0.0-blue)
   ![Python](https://img.shields.io/badge/python-3.14-3776AB)
   ```
   El badge de CI es obligatorio: todo repo nace con CI (ver [[github-actions]]). Cambiar el badge de
   lenguaje si el proyecto no es Python (Java, Node…), manteniendo el estilo de shields.io.
3. **Tabla de metadatos sin cabecera**, justo después de los badges:
   ```markdown
   | | |
   |---|---|
   | **Versión** | 1.0.0 |
   | **Fecha** | 16 de octubre de 2026 |
   | **Autor** | [Nicolás Andrés Cano Leal](#autor) |
   ```
   - Fecha **en palabras y en español** ("15 de octubre de 2026"), no ISO.
   - El autor **enlaza al ancla `#autor`** del final.
4. **Versión y fecha coherentes en los tres lugares**: badge, tabla y pie final. Si se sube la versión,
   se cambian los tres a la vez.
5. **Bloque de Autor al final, idéntico siempre**:
   ```markdown
   ## Autor

   **Nicolás Andrés Cano Leal**\
   Backend Engineer → SRE | Python · Django · Kubernetes · Terraform · CI/CD

   - LinkedIn: [linkedin.com/in/nicolasandrescl](https://www.linkedin.com/in/nicolasandrescl/)
   - Portafolio: [nicolasandrescl.github.io](https://nicolasandrescl.github.io/)
   - Correo: [nicolas.cano.leal@gmail.com](mailto:nicolas.cano.leal@gmail.com)

   <Proyecto> v1.0.0 · 16 de octubre de 2026
   ```
   Nota la barra invertida final tras el nombre (salto de línea en Markdown) y el pie
   `Proyecto vX.Y.Z · fecha` como última línea del archivo.

## Estructura de secciones (en este orden; omitir solo las que no apliquen)

1. **Presentación** (sin encabezado, tras la tabla): qué es y para qué, en 1–2 párrafos con lo esencial en
   **negrita**; lista corta de stack (Frontend / Backend / Persistencia / "Todo dockerizado") y cuál es la
   fuente de verdad de los datos.
2. **`## Arquitectura`**: árbol de carpetas en bloque de código **con un comentario por línea**
   (`# multi-stage, no-root, HEALTHCHECK a /healthz`), seguido de una línea de **Flujo:**
   `navegador → ui → HTTP → api → db` y qué capa no toca qué.
3. **`## Levantar con Docker`**: comandos copiables (`cp .env.example .env`, cómo generar secretos,
   `docker compose up -d --build --wait`), **tabla de Servicio | URL**, qué conserva `down` y qué borra
   `down -v`, y cómo bajar el stack al terminar.
4. **`## Correr en local sin Docker`**: versión de Python requerida y probada, venv, variables y arranque
   de cada servicio.
5. **`## Endpoints`** (si hay API): prefijo, tabla Método | Ruta | Qué hace; contrato JSON de errores en
   bloque de código y tabla Código | HTTP | Cuándo.
6. **`## La interfaz`** (si hay UI): viñetas con lo que se puede hacer y cómo degrada si la API cae.
7. **`## Variables de entorno`**: tabla Variable | Servicio | Por defecto | Para qué; marcar en **negrita**
   las obligatorias.
8. **`## Verificación`**: `scripts/verificar.sh` y la lista numerada de jobs del CI que reproduce, con
   umbrales de cobertura y números reales.
9. **`## Decisiones de diseño`**: viñetas con **lema en negrita + porqué**. Es la sección que más vale en
   una entrevista: explica trade-offs, no repite la arquitectura.
10. **`## Autor`** + pie (regla 5).

## Estilo

- Español de Chile con tildes correctas; términos técnicos e identificadores en su forma original.
- **Cifras reales y verificadas** (tests, cobertura, conteos): las mismas en todo el documento y en
  `memory.md`. Antes de escribir un número, sacarlo de la herramienta, no de memoria.
- Tablas para todo lo enumerable (servicios, endpoints, errores, variables); prosa solo para el porqué.
- Comandos siempre copiables y probados; si un comando borra datos, decirlo en **negrita**.
- Nada de secretos reales en ejemplos: placeholders o `secrets.token_urlsafe(32)`.

## Antes de dar el README por terminado

- [ ] Cada ruta, variable, puerto y comando del README existe en el código (grep, no memoria).
- [ ] Versión y fecha iguales en badge, tabla y pie.
- [ ] El badge de CI apunta al repo y workflow correctos (`NicolasAndresCL/<repo>`, `ci.yml`).
- [ ] Bloque de Autor idéntico al de esta skill.

## Ver también
[[github-actions]] para el workflow que respalda el badge · [[docker]] para la sección de Docker ·
[[cierre-de-tarea]] para cuándo se actualiza el README.
