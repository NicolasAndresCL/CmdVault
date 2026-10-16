---
name: n8n
description: >
  Estándares de Nicolás Cano Leal para automatización con n8n: cuándo usarlo
  en vez de escribir código, diseño de workflows con webhooks/nodos,
  manejo de errores y credenciales. USAR SIEMPRE que se plantee un flujo de
  integración entre servicios (Slack, Sheets, email, APIs), una automatización
  "de una vez" o glue desechable, o se dude entre n8n y un script propio.
---

# n8n — estándares de Nicolás Cano Leal

> n8n es la herramienta para **glue e integraciones desechables**, no para
> lógica de negocio central del producto (skill §7.4: herramienta adecuada al
> costo de la tarea). Si el flujo va a crecer en complejidad de negocio o
> necesita testearse como el resto del sistema, migra a [[python-backend]].

## Cuándo usar n8n vs. código propio

**Usar n8n cuando:**
- Es integración entre servicios ya existentes (Sheets → Slack, webhook →
  email, cron → API externa → BD) sin lógica de negocio profunda.
- Es una automatización desechable o de vida corta: un reporte semanal, un
  aviso puntual, un puente entre dos SaaS que no van a hablar directo.
- El costo de mantener un workflow visual es menor que el de un servicio con
  su propio deploy, tests y CI.

**Usar código propio (Python/Django) cuando:**
- La lógica tiene reglas de negocio no triviales (cálculos, validaciones,
  excepciones de dominio) — eso necesita ser testeable con pytest sin abrir
  n8n.
- El flujo necesita versionarse con el resto del producto y pasar por el
  mismo pipeline de CI.
- Hay estado compartido complejo o necesita transacciones — n8n no maneja
  bien invariantes de negocio.

Regla de oro: **si el workflow necesitaría un test unitario para confiar en
él, no es un workflow — es lógica de negocio, y va en código.**

## Diseño de workflows

1. **Webhooks con validación de origen.** Nunca un webhook público sin al
   menos un secreto compartido (header o query param) o autenticación básica
   — cualquiera que adivine la URL puede disparar el flujo.
2. **Nodo de error explícito (`Error Trigger` / rama `catch`)** en todo
   workflow con efectos externos (envío de correo, escritura en BD/Sheets).
   Un workflow que falla en silencio y nadie se entera es peor que uno que no
   existe — aplica la misma regla de "fallar ruidosamente, no silenciosamente"
   de la sección 2.5 del playbook general.
3. **Reintentos con backoff en nodos HTTP** hacia servicios externos
   inestables (`Retry On Fail` con `maxTries` razonable, no infinito). Un
   servicio caído no debe convertirse en un loop de reintentos que satura la
   instancia de n8n.
4. **Credenciales SIEMPRE en el credential store de n8n**, nunca hardcodeadas
   en un nodo `Set` o pegadas en una URL dentro del workflow. Rotar
   credenciales expuestas si alguna vez quedaron en un export JSON compartido.
5. **Idempotencia**: si el trigger puede dispararse dos veces para el mismo
   evento (reintento de webhook, doble ejecución de cron), el workflow no debe
   duplicar el efecto (doble correo, doble fila). Verificar existencia antes
   de crear, o usar una clave de deduplicación.
6. **Nombrar nodos con lo que hacen**, no dejarlos con el nombre por defecto
   del tipo (`HTTP Request1`, `HTTP Request2`) — un workflow de 15 nodos sin
   nombres propios es indepurable a los 3 meses.
7. **Exportar y versionar el JSON del workflow** en el repo del proyecto que
   lo usa (o en un repo de infraestructura), aunque n8n lo persista en su
   propia BD — es la única forma de tener historial de cambios y rollback.

## Trampas conocidas

- **Loops sin límite** sobre un nodo `Split In Batches` mal cerrado dejan la
  ejecución corriendo indefinidamente y consumen memoria del worker.
- **Timeouts por defecto de nodos HTTP** suelen ser generosos — para
  integraciones críticas, bajar el timeout explícito y manejar el error en
  vez de dejar que el workflow completo se cuelgue esperando un servicio
  caído.
- **Datos sensibles en logs de ejecución de n8n**: si el workflow procesa
  PII, revisar la retención de logs de ejecución de la instancia — n8n guarda
  el payload completo de cada nodo por defecto.
- **Un solo workflow gigante haciendo demasiado**: preferir varios workflows
  chicos conectados por webhook/subworkflow (`Execute Workflow`) sobre uno
  monolítico — más fácil de testear en aislado y de depurar cuando falla un
  tramo.

## Ver también
[[automatizacion]] para cuándo el glue debe ser un script Python en vez de un
workflow visual · [[python-backend]] para migrar lógica que creció más allá de
lo que n8n debería sostener.
