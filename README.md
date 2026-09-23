# Ejemplo 01: de Django clásico a una API

Base de trabajo para retomar una aplicación Django renderizada en el servidor y, durante la clase, hacerla evolucionar hacia una API consumida desde React.

El repositorio comienza con dos aplicaciones independientes:

- `backend/`: Django, el modelo `Activity`, SQLite y una vista HTML clásica.
- `frontend/`: Vite + React + TypeScript recién inicializado, todavía sin integración con Django.

## Puesta en marcha local

### 1. Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py seed_activities
python manage.py runserver
```

Abrir <http://127.0.0.1:8000/>.

### 2. Frontend

En otra terminal:

```bash
cd frontend
pnpm install
pnpm dev
```

Abrir <http://127.0.0.1:5173/>.

## Puesta en marcha con Docker Compose

Los entornos Docker usan `compose.yaml` como configuración base y un archivo adicional según el entorno. Ejecutar los comandos desde la raíz del repositorio.

### Desarrollo

Inicia PostgreSQL, Django con recarga automática y Astro con los directorios del proyecto montados como volúmenes:

```bash
docker compose -f compose.yaml -f compose.dev.yaml up --build
```

Abrir el frontend en <http://127.0.0.1:4321/> y el backend en <http://127.0.0.1:8000/>. Los cambios en el código se reflejan sin reconstruir las imágenes.

Para detenerlo:

```bash
docker compose -f compose.yaml -f compose.dev.yaml down
```

### Producción

Construye las imágenes de producción, ejecuta Django con Gunicorn y expone la aplicación mediante Nginx:

```bash
docker compose -f compose.yaml -f compose.prod.yaml up --build
```

Abrir la aplicación en <http://127.0.0.1:8081/>. En este entorno no se publican directamente los puertos del frontend ni del backend.

Para detenerlo:

```bash
docker compose -f compose.yaml -f compose.prod.yaml down
```

## Verificación rápida

```bash
cd backend
python manage.py test

cd ../frontend
pnpm build
```
