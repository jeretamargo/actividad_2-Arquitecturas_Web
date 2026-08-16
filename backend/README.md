# Backend Django

Aplicación Django clásica con persistencia SQLite. La ruta `/` consulta el modelo `Activity` y renderiza en el servidor una tabla HTML con todos sus campos.

## Requisitos

- Python 3.12 o posterior.

## Iniciar el proyecto

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py seed_activities
python manage.py runserver
```

Abrir <http://127.0.0.1:8000/>.

`seed_activities` se puede ejecutar más de una vez: restaura el mismo conjunto de actividades, participantes e inscripciones sin duplicarlos.

## Comandos útiles

```bash
# Ejecutar las pruebas
python manage.py test

# Abrir la consola de Django
python manage.py shell

# Vaciar la base y volver a cargar los datos de muestra
python manage.py flush --noinput
python manage.py seed_activities
```

## Estructura relevante

- `activities/models.py`: modelos `Activity`, `Participant` y `Enrollment`.
- `activities/views.py`: vista clásica que consulta la base.
- `activities/templates/activities/activity_list.html`: documento HTML producido por Django.
- `activities/management/commands/seed_activities.py`: datos reproducibles.

SQLite usa el archivo `db.sqlite3`, creado por `python manage.py migrate` y excluido de Git.
