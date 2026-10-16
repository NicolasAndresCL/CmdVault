---
name: automatizacion
description: >
  Estándares de Nicolás Cano Leal para automatización con Python: Selenium
  headless resiliente, scraping que no se cae con el sitio, ETL idempotente
  con pandas, y watchdogs/heartbeats para procesos de larga duración. USAR
  SIEMPRE que se escriba scraping, un script de automatización de navegador,
  un pipeline ETL, o cualquier proceso que corra desatendido y deba sobrevivir
  a fallos externos.
---

# Automatización — estándares de Nicolás Cano Leal

> Principio rector (skill §2.5): **resiliencia como requisito, no como
> extra.** Un script de automatización que corre desatendido debe asumir el
> fallo desde el diseño — la red cae, el sitio cambia el DOM, el driver se
> desincroniza. El trabajo del script es sobrevivir a eso, no asumir un mundo
> feliz.

## Selenium — scraping resiliente

- **Headless por defecto**, perfil de navegador clonado (no el perfil real del
  usuario) para no arrastrar sesión ni cookies personales al proceso
  automatizado.
- **Resolución offline del driver**: no depender de que `chromedriver`
  se descargue en cada arranque contra internet — cachearlo localmente y
  auto-repararlo si falta o no matchea la versión del navegador instalado
  (skill §2.5: "auto-reparación de dependencias").
- **Esperas explícitas (`WebDriverWait` + `expected_conditions`), nunca
  `time.sleep()` fijo.** Un sleep fijo es o muy corto (falla en máquinas
  lentas) o muy largo (desperdicia tiempo en las rápidas).
- **Selectores robustos a cambios de layout**: preferir `data-testid`/`id`
  estables sobre XPath posicional o clases CSS generadas (`.css-a1b2c3`) que
  cambian con cada build del sitio.
- **Centinela de sesión que falla ruidoso**: si el login falla o la sesión
  expira a mitad de un scraping largo, el script debe detectarlo y **fallar
  visiblemente** (log de error + alerta), nunca seguir corriendo silencioso
  contra una sesión rota devolviendo datos vacíos o corruptos.
- **Reintentos acotados con backoff** ante fallos transitorios de red
  (`requests`/Selenium `TimeoutException`), nunca reintento infinito ni
  reintento inmediato sin backoff que reintenta contra un servicio que
  todavía no se recuperó.

```python
def esperar_elemento(driver, by, valor, timeout=10):
    """Espera explícita — nunca time.sleep() fijo."""
    return WebDriverWait(driver, timeout).until(EC.presence_of_element_located((by, valor)))


def con_reintentos(func, intentos=3, backoff_base=2):
    for intento in range(intentos):
        try:
            return func()
        except (TimeoutException, ConnectionError) as exc:
            if intento == intentos - 1:
                logger.exception("Agotados los reintentos: %s", exc)
                raise
            time.sleep(backoff_base**intento)
```

## ETL con pandas — idempotencia primero

- **Todo script de carga debe poder correrse dos veces sin duplicar datos.**
  Usar `upsert`/`merge` sobre una clave natural, o truncar-y-recargar el rango
  afectado, nunca un `INSERT` ciego que asume que el script corre una sola
  vez.
- **Lectura por estado canónico, no por variantes de string** (skill §3):
  normalizar antes de filtrar (`"Pagado"`, `"pagado"`, `"PAGADO "` deben
  colapsar a un solo valor antes de cualquier `groupby`/`filter`), o se
  pierden filas silenciosamente por inconsistencia de mayúsculas/espacios.
- **Validar el shape de los datos de entrada antes de procesarlos**: columnas
  esperadas presentes, tipos coherentes. Un Excel con una columna renombrada
  a mano debe fallar temprano y explícito, no producir un DataFrame con
  `NaN` silenciosos tres pasos después.
- **Separar lectura (I/O) de transformación (pura)**: la función que
  transforma un DataFrame no debe abrir el archivo ni escribir el resultado —
  así se testea con un DataFrame de fixture, sin tocar disco ni red.

## Watchdogs, heartbeats y procesos de larga duración

- **Outer try/except en todo loop de background.** Un hilo/proceso que corre
  desatendido nunca debe morir por una excepción no capturada — logea y
  continúa el ciclo siguiente.
- **Heartbeat en una fuente compartida** (archivo, fila de BD, endpoint) que
  otro proceso pueda vigilar — permite detectar "el proceso sigue vivo pero
  dejó de progresar" (colgado) y no solo "el proceso murió".
- **Anti-duplicidad entre operadores/instancias**: si dos instancias del
  mismo script pueden correr a la vez (cron solapado, redeploy sin apagar la
  instancia vieja), usar un lock atómico (archivo lock, fila con
  `SELECT ... FOR UPDATE`, o TTL en cache compartida) para que no compitan por
  el mismo trabajo ni lo dupliquen.
- **Locks non-blocking** cuando el objetivo es "no encolar ciclos que se
  pisan" — si el ciclo anterior sigue corriendo, saltar el disparo actual en
  vez de esperar en cola.

## Trampas conocidas

- **Cooldowns de plataforma mal diagnosticados como lentitud del código**
  (skill §7.1): medir antes de optimizar — un scraping "lento" puede ser el
  rate-limit del sitio, no el parseo. Perfilar con timestamps por etapa antes
  de asumir dónde está el cuello de botella.
- **Múltiples llamadas redundantes a una API/Sheets** cuando un singleton con
  TTL cache resolvía el mismo dato en una sola llamada — de 21 llamadas a 1 es
  el tipo de ganancia que aparece al perfilar, no al adivinar.
- **Scripts que no distinguen "no hay datos nuevos" de "la fuente está
  caída"**: ambos casos pueden devolver una lista vacía si no se valida
  explícitamente el código de respuesta/estado de la fuente antes de
  interpretar el resultado como "nada que hacer".

## Ver también
[[n8n]] para cuándo el glue debe ser un workflow visual en vez de un script ·
[[python-backend]] para cuando la automatización necesita persistir estado en
un backend real con API y auditoría.
