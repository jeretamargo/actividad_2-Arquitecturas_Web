# Backend Django

Django + Django REST Framework con PostgreSQL y JWT mediante PyJWT. El frontend activo consume `/api/v2/`.

La guía completa de configuración, ejecución con Docker Compose, migraciones, credenciales de prueba y verificaciones está en el [README principal](../README.md). El [informe](../output/pdf/informe-hito-2.pdf) explica la arquitectura y sus límites.

## Datos iniciales

Dentro del contenedor backend, después de `python manage.py migrate`:

```bash
python manage.py seed_activities
python manage.py seed_users
```

`seed_activities` **restaura** el escenario de muestra (4 actividades, 5 participantes y 8 inscripciones), eliminando datos de actividades/participantes/inscripciones fuera de ese conjunto. No es una importación para una base con datos que se quieran preservar.

`seed_users` crea o restaura las cuentas locales `maria` y `jorge` y las vincula a sus participantes. No cambia actividades ni inscripciones; puede repetirse sin duplicar cuentas. Las credenciales públicas de evaluación están en el README principal. Ante vínculos incompatibles o cuentas administrativas con esos nombres, revierte la operación y muestra un error.

## Estructura relevante

- `activities/models.py`: Activity, Participant, Enrollment y RevokedToken.
- `activities/authentication.py`: validación de access y decodificación de refresh.
- `activities/api/v2/`: endpoints públicos, inscripciones propias y autenticación.
- `activities/migrations/`: esquema y relación usuario-participante.
- `activities/management/commands/`: semillas de dominio y usuarios.
- `activities/test_seed_users.py`: reproducción, login, identidad e idempotencia de las cuentas.
- `config/settings.py`: PostgreSQL, duración de tokens y configuración local.

## Verificación

Ejecutar dentro del contenedor backend:

```bash
python manage.py test --noinput
python manage.py makemigrations --check --dry-run
```

Las pruebas usan una base independiente. No ejecutar `flush` ni eliminar el volumen de PostgreSQL para correrlas.
