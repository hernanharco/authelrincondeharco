# pending-request-insight

Fecha y ubicación de la solicitud en la cola de aprobación, y aviso por correo a los
administradores cuando entra una solicitud nueva.
Backend (captura + persistencia + notificación) y frontend (`/dashboard/pending`).

## Specs

S1 — Fecha de la solicitud
Texto del usuario: "cuando aparezca un usuario que diga desde que dia pidio autorizacion".
El dashboard muestra, por cada usuario pendiente, la fecha en que solicitó la
autorización, formateada en `es-ES` y zona `Europe/Madrid`. Se deriva de `created_at`
(no hace falta columna nueva). Si el valor no es parseable, se muestra "sin fecha" y
la tarjeta se sigue renderizando.

S2 — Ubicación de la solicitud
Texto del usuario: "seria genial que mostrara de que ciudad esta pidiendo la autorizacion
o por lo menos el pais".
Se muestra ciudad y país cuando el CDN entrega ambos; sólo el país cuando entrega país; y
"sin ubicación" cuando no hay dato. Nunca se aproxima ni se inventa.
Origen del dato: cabeceras de Cloudflare (`CF-IPCountry`, `CF-IPCity`, `CF-Region`) con
fallback a Vercel (`X-Vercel-IP-Country`, `X-Vercel-IP-City`). `CF-IPCountry` viene activa
por defecto en todos los planes; ciudad/región requieren la Managed Transform
"Add visitor location headers" (gratis). Con sólo país activo, S2 se cumple igual.
Se persiste junto a la IP del cliente al crear el usuario pendiente: la ubicación de la
solicitud es un hecho histórico y no se recalcula.

S3 — Aviso por correo a los administradores
Texto del usuario: "que cuando haya alguien pidiendo una acturizacion me llegue un correo
a hernan.harco para que me informe de esto".
Cuando entra una solicitud de autorización nueva se envía un correo vía Resend con nombre,
email, origen, fecha y ubicación de cada solicitud pendiente, y un enlace al dashboard.

S4 — Agrupación por intervalo
Texto del usuario: "me gusta la opcion de agrupacion pero puedes ser por intervalo de 1 hra".
Como máximo un correo por hora: el correo lista todas las solicitudes aún no notificadas.
Una ráfaga de N solicitudes dentro de la misma hora produce un único correo. La ventana se
evalúa tanto al entrar una solicitud como en un chequeo periódico interno, para que la
última solicitud de una ráfaga nunca quede sin avisar.

S5 — Destinatarios resueltos por rol
Texto del usuario: "hernan.harco@gmail.com, o mejor aun debe revisar aquellos que tenga el
rol de Suparadmin".
Texto del usuario: "bueno tambien incluier los admin porque en un futuro puede haber
colaboradores y pues me imagino que colocarlos superadmin no seria lo correcto".
Destinatarios: usuarios con `role` SUPERADMIN o ADMIN y `is_active = true`, resueltos desde
la tabla en cada envío (sin lista hardcodeada ni variable de entorno). Sin destinatarios: se
loguea y no se envía.

S6 — Fail-open
Un fallo de Resend, de base de datos o de cabeceras nunca cambia la respuesta al solicitante:
el callback de Google sigue devolviendo `PENDING_APPROVAL`. Las solicitudes no notificadas
por un fallo se reintentan en la siguiente ventana.

## Tasks

- [x] T1 (S1, S2) Captura y persistencia de la ubicación + campos en `UserResponse` — commit 2e46792
- [x] T2 (S3, S4, S5, S6) Correo de aviso a administradores con agrupación de 1 h — commit 41c9d35 (+ plantilla 14143bb)
- [x] T3 (S1, S2) Fecha y ubicación en la tarjeta de `/dashboard/pending` — commit 1de7aec
- [x] T4 (S1-S6) Verificación: tests + suite completa

## Log

L1 (original): "en authcore en /dashboard/pending debemos agregar dos cosas 1. cuando
aparezca un usuario que diga desde que dia pidio autorizacion y seria genial que mostrara
de que ciudad esta pidiendo la autorizacion o por lo menos el pais 2. que cuando haya
alguien pidiendo una acturizacion me llegue un correo a hernan.harco para que me informe
de esto"

L2 (decisión, elección del usuario): geolocalización por cabeceras del CDN
(Cloudflare/Vercel), no lookup por IP. Verificado en el repo que `main.py:82` ya monta
`ProxyHeadersMiddleware` declarando Cloudflare/Dokploy.

L3 (corrección del usuario): agrupación por intervalo de 1 hora en lugar de un correo por
solicitud.

L4 (decisión del usuario): destinatario `hernan.harco@gmail.com`, y mejor todavía resolver
los destinatarios desde los roles.

L5 (corrección del usuario): incluir también el rol ADMIN, no sólo SUPERADMIN, para no
degradar colaboradores futuros a superadmin.

L6: el usuario pregunta la opinión sobre el diseño ("o que opinas"). Respuesta y ajustes:
(a) ventana de 1 h con doble disparador porque un agrupador sólo por evento deja la última
solicitud de una ráfaga sin avisar; (b) país siempre disponible con `CF-IPCountry`, ciudad
cuando se active la Managed Transform; (c) los pendientes existentes mostrarán "sin
ubicación": no hay IP histórica y no se aproxima.

L7 (verificación): suite completa del backend en verde con cobertura 88% (gates 80%).
`astro build` compila la página. Defecto encontrado y corregido por sus tests: un mapping
de cabeceras vacío se trataba como "sin request" y perdía también la IP del cliente.
Incidente de método: dos runs de pytest en paralelo comparten `backend/test.db` y sus
fixtures borran tablas por test, así que producen errores fantasma; los runs van en serie.

L8 (slices): 6 commits en `feat/pending-request-insight`, todos ≤ 400 líneas cambiadas.
Límite de slice de PR en ~400 líneas (AGENTS.md) ya superado por la rama completa, así que
la entrega va como dos PRs encadenados: fecha/ubicación (2e46792, 12e2ffc, 1de7aec) y aviso
por correo (14143bb, 41c9d35, 1e59cbf).

L9 (entrega): el usuario eligió publicar como **6 PRs encadenados**, uno por commit salvo el
último (frontend + evidencia ODD), para respetar el tope de 400 líneas por PR de AGENTS.md.
La entrega sale **sin veredicto de la revisión nativa**: el proveedor rechazó el slot del
reviewer (`json: unknown field "evidence"`) y `review.status` respondió después
`capture-route-registration-rejected: selector-mismatch` con `automatic_retry: false`, sin
continuación soportada. Decisión explícita del usuario, no un pase implícito; el defecto queda
documentado en `odd/reports/gentle-ai-review-capture-defect.md` y la autoridad del lineage
`review-863481b50e6db9bd` queda intacta y sin consumir.

L10 (verificación en producción, pendiente al escribir esto): logs de arranque con
"Columnas agregadas a users: ..."; las 4 columnas presentes en `information_schema.columns`;
un pendiente real mostrando fecha + país; el correo llegando a las casillas de SUPERADMIN/ADMIN
y un único correo cuando entran dos solicitudes en la misma hora. Rollback seguro: las columnas
son aditivas y nullable, el código anterior las ignora.
