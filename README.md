# Arquitecturas Web - UNTDF - Hito 2

Sistema de actividades e inscripciones con autenticación JWT. El frontend activo es **Astro con componentes React**; el backend es **Django + Django REST Framework**, con **PostgreSQL**. Docker Compose integra los servicios y el entorno de entrega usa **Nginx** como entrada y **Gunicorn** como servidor de Django.

- Repositorio: <https://github.com/jeretamargo/actividad_2-Arquitecturas_Web>
- [Informe PDF: arquitectura, autenticación, decisiones y límites](output/pdf/informe-hito-2.pdf).
- [Diagrama de componentes](docs/diagrama-componentes.svg) y [fuente Mermaid editable](docs/diagrama-componentes.mmd).
- La interfaz utiliza `/api/v2/`. `frontend/` corresponde al frontend anterior; el proyecto activo está en `frontend-astro/`.

## Ejecutar desde una copia limpia

### Requisitos y configuración

Instalar Git y Docker con Docker Compose v2. En Windows, iniciar Docker Desktop con contenedores Linux y la integración WSL habilitada si se trabaja desde Ubuntu. No hace falta instalar Python, Node ni PostgreSQL en el equipo.

```bash
git clone https://github.com/jeretamargo/actividad_2-Arquitecturas_Web.git
cd actividad_2-Arquitecturas_Web
cp .env.example .env
```

En PowerShell, reemplazar el último comando por `Copy-Item .env.example .env`. Si ya existe `.env`, conservarlo en lugar de sobrescribirlo.

`.env.example` contiene valores públicos de evaluación para `DB_NAME`, `DB_USER` y `DB_PASSWORD`. Compose los pasa a PostgreSQL y Django; dentro de Docker configura `DB_HOST=db` y `DB_PORT=5432`. Los archivos `.env.development` locales no son necesarios para estos comandos. Las credenciales y la clave Django/JWT del código son exclusivamente de demostración local.

### Entorno de entrega: Nginx + Gunicorn

Ejecutar **desde la raíz del repositorio** y en este orden. `-p hito2` mantiene un volumen y una red propios para este entorno.

```bash
# 1. Construir las imágenes e iniciar PostgreSQL.
docker compose -p hito2 -f compose.yaml -f compose.prod.yaml build
docker compose -p hito2 -f compose.yaml -f compose.prod.yaml up -d db

# 2. Crear el esquema y cargar los datos iniciales.
docker compose -p hito2 -f compose.yaml -f compose.prod.yaml run --rm backend python manage.py migrate
docker compose -p hito2 -f compose.yaml -f compose.prod.yaml run --rm backend python manage.py seed_activities
docker compose -p hito2 -f compose.yaml -f compose.prod.yaml run --rm backend python manage.py seed_users

# 3. Iniciar el conjunto completo.
docker compose -p hito2 -f compose.yaml -f compose.prod.yaml up -d
docker compose -p hito2 -f compose.yaml -f compose.prod.yaml ps
```

Abrir <http://127.0.0.1:8081/>. Login: <http://127.0.0.1:8081/login/>. Inscripciones propias: <http://127.0.0.1:8081/enrollments/>. Nginx es el único servicio publicado: `/api/` va a Django y el resto a Astro. Mantener el mismo hostname durante la prueba; las cookies de `localhost` y `127.0.0.1` son distintas.

Las migraciones incluidas crean las tablas del dominio, la relación usuario-participante (`0004`) y la lista de refresh tokens revocados (`0005`). No es necesario ejecutar `makemigrations`. Compose no aplica migraciones ni semillas automáticamente: los comandos anteriores son parte del arranque inicial.

Después de detenerlo, para volver a usar los mismos datos alcanza con `up -d`. Para consultar problemas de arranque y detener el entorno:

```bash
docker compose -p hito2 -f compose.yaml -f compose.prod.yaml logs --tail=100
docker compose -p hito2 -f compose.yaml -f compose.prod.yaml down
```

`down` conserva PostgreSQL. No usar `down -v` para detenerlo: elimina los datos persistentes. Para comprobar otra instalación vacía sin tocar la anterior se puede repetir **todos** los comandos con otro nombre después de `-p`, dejando libre el puerto 8081.

### Entorno de desarrollo

Usa Django con recarga y Astro con proxy de `/api/`. No incluye Nginx/Gunicorn, por lo que la comprobación de entrega debe realizarse con el entorno anterior. El nombre `hito2-dev` usa una base separada de `hito2`.

```bash
docker compose -p hito2-dev -f compose.yaml -f compose.dev.yaml build
docker compose -p hito2-dev -f compose.yaml -f compose.dev.yaml up -d db
docker compose -p hito2-dev -f compose.yaml -f compose.dev.yaml run --rm backend python manage.py migrate
docker compose -p hito2-dev -f compose.yaml -f compose.dev.yaml run --rm backend python manage.py seed_activities
docker compose -p hito2-dev -f compose.yaml -f compose.dev.yaml run --rm backend python manage.py seed_users
docker compose -p hito2-dev -f compose.yaml -f compose.dev.yaml up -d
```

Frontend: <http://127.0.0.1:4321/>. API: <http://127.0.0.1:8000/api/v2/activities/>. Los puertos 4321 y 8000 deben estar libres. Para detener: `docker compose -p hito2-dev -f compose.yaml -f compose.dev.yaml down`.

## Usuarios y datos de evaluación

Estas cuentas son públicas, locales y exclusivas para evaluar el TP. No tienen permisos administrativos.

| Usuario | Contraseña | Participante | Inscripciones iniciales |
| --- | --- | --- | --- |
| `maria` | `MariaTP2026!` | María López | 2 |
| `jorge` | `JorgeTP2026!` | Jorge Fernández | 1 |

`seed_activities` restaura 4 actividades, 5 participantes y 8 inscripciones. **Es un reinicio del escenario de muestra**: elimina actividades, participantes e inscripciones ajenas a ese conjunto y restaura los cupos originales. Ejecutarlo al preparar la evaluación, no para conservar cambios realizados durante las pruebas.

`seed_users` crea o restaura las dos cuentas y las vincula por los UUID estables de sus participantes. Puede repetirse sin duplicarlas ni alterar inscripciones. Si cambió una contraseña de muestra o se desactivó una cuenta, restaura la contraseña documentada y la activa. No cambia el hash cuando la contraseña ya coincide. Puede crear los dos participantes incluso sin `seed_activities`, aunque para el escenario completo se deben ejecutar ambos comandos en el orden indicado.

Ante una cuenta administrativa con esos nombres o un vínculo usuario-participante incompatible, `seed_users` se detiene y revierte toda la operación: no reasigna identidades existentes. Las contraseñas se guardan mediante el sistema de hashes de Django.

## Autenticación y contrato de la API v2

Se utiliza **PyJWT**, sin SimpleJWT. El usuario se valida con `authenticate()` de Django; `sub` identifica su cuenta y el backend obtiene `request.user.participant`. En los endpoints protegidos, enviar un UUID en el cuerpo o `X-Participant-ID` no permite seleccionar a otro participante.

| Método y ruta | Acceso y resultado esperado |
| --- | --- |
| `GET /api/v2/activities/` | Público: lista de actividades y disponibilidad. |
| `GET /api/v2/activities/{activity_id}/` | Público: detalle o `404`. |
| `GET /api/v2/me/enrollments/` | Bearer access: inscripciones del participante autenticado. |
| `PUT /api/v2/me/enrollments/create/{activity_id}/` | Bearer access, sin body: `201` nueva; `200` si ya existe; `409` sin cupo; `404` actividad inexistente. |
| `DELETE /api/v2/me/enrollments/delete/{activity_id}/` | Bearer access: `204`, incluso si ya estaba cancelada; `404` actividad inexistente. |
| `GET /api/v2/auth/csrf/` | Devuelve `csrf_token` y prepara la cookie CSRF. |
| `POST /api/v2/auth/login/` | JSON `username`/`password`: access en JSON y refresh en cookie; `401` credenciales incorrectas; `403` sin participante. |
| `POST /api/v2/auth/refresh/` | Cookie refresh válida y no revocada: nuevo access. Refresh faltante, vencido, inválido o revocado: `401`. |
| `POST /api/v2/auth/logout/` | Revoca el `jti` del refresh recibido, borra su cookie y responde `204`. Repetirlo también devuelve `204`. |

Los tres POST de autenticación requieren CSRF: primero consultar `/auth/csrf/`, conservar las cookies y enviar el valor JSON como `X-CSRFToken`. Esto también aplica a Yaak o herramientas similares. Sin protección CSRF válida se recibe `403` antes de validar las credenciales. El frontend ya realiza ese intercambio.

El access dura **10 minutos**, incluye `sub`, `username`, `type=access`, `iat`, `exp` y se envía como `Authorization: Bearer <token>`. El refresh dura **7 días**, incluye `sub`, `type=refresh`, `jti`, `iat`, `exp` y se guarda en cookie **HttpOnly**, `SameSite=Lax`, con `Path=/api/v2/auth/`. Para la evaluación por HTTP local, `Secure=False`.

En el navegador, el access queda únicamente en memoria del módulo de autenticación: no se guarda en localStorage, sessionStorage ni cookies. Al recargar o navegar entre páginas Astro, la memoria se reconstruye y el frontend recupera un access usando la cookie refresh. Ante un `401` protegido intenta renovar y reintenta una sola vez. El logout limpia el estado privado y espera la respuesta del servidor; un fallo de red se muestra para permitir reintentar.

### Decisiones y límites

- **Separación de credenciales:** el access breve autoriza las operaciones y el refresh permite recuperar la sesión sin exponer su valor al JavaScript del navegador. HttpOnly no evita que un script malicioso actúe como el usuario mientras está ejecutándose; no reemplaza la prevención de XSS.
- **Revocación persistente:** `RevokedToken(jti, revoked_at)` se guarda en PostgreSQL. Reiniciar Django no borra las revocaciones. El logout afecta al refresh presentado, no a todas las sesiones del usuario.
- **Access después del logout:** el servidor no agrega el access a una lista de revocación. Una copia ya emitida sigue siendo aceptada hasta su vencimiento original, como máximo el tiempo restante de los 10 minutos, siempre que el usuario continúe activo y vinculado. El navegador descarta su copia, pero eso no invalida una copia externa.
- **Refresh:** se reutiliza hasta sus 7 días originales; no hay rotación, detección de reutilización ni extensión de su vencimiento. La tabla de revocados no tiene limpieza automática.
- **Alcance local:** no hay HTTPS, limitación de intentos de login, recuperación de contraseña ni gestión de sesiones por dispositivo. La clave Django/JWT está fija en el código y las credenciales son públicas: esta configuración es de evaluación, no un despliegue público seguro.
- **Compatibilidad heredada:** `/api/v1/` sigue disponible con su comportamiento anterior, sin la autenticación JWT de v2. No se considera una API protegida y su permanencia impide afirmar que todas las rutas del sistema exigen autenticación. La interfaz actual usa v2.
- **Cupo e idempotencia:** se conservan los resultados secuenciales del Hito 1 y la restricción única actividad-participante. El conteo de cupos y la creación no usan bloqueo transaccional; solicitudes simultáneas pueden superar el cupo y una carrera por la misma inscripción puede producir un error. No se afirma garantía bajo concurrencia.
- **Dependencias:** el frontend usa `npm ci` con su lockfile; las imágenes base y parte de las dependencias Python usan etiquetas/rangos. Se reproduce el procedimiento y los datos de evaluación, sin prometer imágenes idénticas bit a bit en fechas distintas.

## Comprobaciones

### Pruebas automatizadas

Con el entorno de entrega iniciado:

```bash
docker compose -p hito2 -f compose.yaml -f compose.prod.yaml exec -T backend python manage.py test --noinput
docker compose -p hito2 -f compose.yaml -f compose.prod.yaml exec -T backend python manage.py makemigrations --check --dry-run
```

Django crea y elimina una base de pruebas independiente; no carga las semillas en la base de trabajo. Las pruebas comprueban el listado público y su método HTTP, el arranque de las semillas desde cero, login con CSRF y cookie HttpOnly, identidad propia aunque se envíe otro participante, repetición sin duplicados, restauración de credenciales y rollback ante conflictos.

Puede aparecer la advertencia previa `urls.W005` por el namespace `activities` compartido entre v1/v2. No impide estas pruebas, que usan las rutas explícitas documentadas.

Las pruebas del frontend se ejecutan en desarrollo, porque la imagen final de Astro contiene sólo los artefactos de ejecución:

```bash
docker compose -p hito2-dev -f compose.yaml -f compose.dev.yaml run --rm --no-deps frontend npm test
```

Son pruebas del cliente con respuestas HTTP simuladas. El build de producción ya se ejecuta durante `docker compose ... build`. Si se prueba fuera de Docker, usar Node >=22.12, `cd frontend-astro`, `npm ci`, `npm test` y `npm run build`.

### Instalación aislada verificada

Se construyó el entorno de entrega con `.env.example` y un volumen PostgreSQL nuevo, bajo el proyecto separado `hito2-repro-check`. Se aplicaron las migraciones, ambas semillas y una segunda ejecución de `seed_users`. Pasaron las 6 pruebas de Django, la comprobación de migraciones y 24 verificaciones HTTP reales por Nginx: páginas SSR, credenciales correctas/incorrectas, CSRF, ausencia de access, inscripciones propias, inscripción/cancelación repetidas, cupo agotado, refresh, logout, revocación y vigencia del access anterior al logout. Para comprobar `409` con sólo dos usuarios se creó una actividad temporal de capacidad 1 en esa base aislada; no se modificó el escenario de desarrollo. Se corrigió el proxy para conservar el puerto externo en `Host`, necesario para que la validación CSRF coincida con `Origin`.

### Recorrido manual de evaluación

1. Sin sesión: consultar actividades; intentar inscribirse o ver inscripciones propias y comprobar que se requiere login.
2. Probar una contraseña incorrecta y luego ingresar como María. Ver sus dos inscripciones iniciales; ingresar como Jorge muestra una distinta.
3. En el taller de capacidad 2, inscribir a María. Repetir el PUT con su access en Yaak: `200`, sin otra fila. Inscribir a Jorge: ocupa el segundo lugar. Para comprobar `409` desde otra identidad, usar una cuenta adicional local vinculada a otro participante; las dos cuentas provistas ya ocupan ese taller.
4. Cancelar una inscripción y repetir DELETE: ambos `204`. Confirmar que se libera el cupo.
5. Recargar una página: el access se recupera mediante refresh. Esperar el vencimiento del access y comprobar la renovación.
6. Cerrar sesión: desaparece la información privada. Conservar previamente, sólo para la prueba en Yaak, copias de ambos tokens: el refresh revocado devuelve `401`, mientras el access previo puede seguir funcionando hasta vencer. Mantener cookies y CSRF válidos al comprobar el rechazo del refresh.

Los recorridos modifican los datos del escenario. Para volver al punto inicial ejecutar `seed_activities` y luego `seed_users`, teniendo presente el reinicio de datos que realiza el primero.

## Estructura

```text
backend/                 Django, API, modelos, migraciones, semillas y pruebas
frontend-astro/          Astro SSR, componentes React y autenticación en memoria
nginx/                   Rutas de entrada del entorno de entrega
compose*.yaml            Servicios y variantes desarrollo/entrega
.env.example             Configuración local de ejemplo
docs/                    Diagrama y generador del informe
output/pdf/              Informe de la entrega
```
