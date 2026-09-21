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

Docker Compose queda preparado para uso futuro; no es necesario para seguir la primera clase.

```bash
docker compose up --build
```

El backend queda disponible en <http://127.0.0.1:8000/> y el frontend en <http://127.0.0.1:5173/>. El comando del backend aplica las migraciones y carga los datos de muestra antes de iniciar el servidor.

Para detener ambos servicios:

```bash
docker compose down
```

## Verificación rápida

```bash
cd backend
python manage.py test

cd ../frontend
pnpm build
```

## Punto de partida didáctico

En este corte todavía no hay una API JSON ni comunicación entre ambos proyectos. Django consulta SQLite y produce el HTML completo. La evolución hacia `GET /activities` y el consumo con `fetch` se realiza a partir de esta base.

## Entorno de desarrollo con Docker

El proyecto dispone de un entorno de desarrollo completamente dockerizado mediante Docker Compose.

Este entorno ejecuta tres servicios:

- **Frontend:** Astro + React, utilizando el servidor de desarrollo de Astro.
- **Backend:** Django, utilizando `runserver`.
- **Base de datos:** PostgreSQL, con persistencia mediante un volumen de Docker.

El código fuente del frontend y del backend se monta dentro de sus respectivos contenedores mediante bind mounts. Esto permite que los cambios realizados durante el desarrollo se reflejen sin necesidad de reconstruir las imágenes.

### 1. Requisitos previos

Para ejecutar el proyecto es necesario contar con:

- Docker Engine o Docker Desktop.
- Docker Compose V2.
- Git.

No es necesario instalar Python, Node.js ni PostgreSQL directamente en el sistema anfitrión, ya que sus entornos de ejecución se encuentran dentro de los contenedores.

### 2. Clonar el repositorio

```bash
git clone <URL_DEL_REPOSITORIO>
cd actividad_2-Arquitecturas_Web
```

Reemplazar `<URL_DEL_REPOSITORIO>` por la dirección del repositorio correspondiente.

### 3. Configurar las variables de entorno

Crear un archivo `.env` en la raíz del proyecto con las variables necesarias para PostgreSQL:

```dotenv
DB_NAME=activities_db
DB_USER=activities_user
DB_PASSWORD=contraseña_local
```

Los valores de `DB_NAME`, `DB_USER` y `DB_PASSWORD` deben coincidir con los utilizados por los servicios `db` y `backend` en `compose.yaml`.

El backend utiliza el nombre del servicio `db` como host de PostgreSQL y se conecta al puerto interno `5432`.

No es necesario publicar el puerto de PostgreSQL en el sistema anfitrión.

### 4. Construir e iniciar los servicios

Desde la raíz del proyecto, ejecutar:

```bash
docker compose -f compose.yaml -f compose.dev.yaml up -d --build
```

Docker Compose combina ambos archivos de configuración, construye las imágenes necesarias y crea e inicia los contenedores del frontend, backend y base de datos.

La opción `-d` permite ejecutar los servicios en segundo plano.

### 5. Aplicar las migraciones de Django

Una vez que PostgreSQL esté disponible, ejecutar:

```bash
docker compose -f compose.yaml -f compose.dev.yaml exec backend python manage.py migrate
```

Este comando aplica las migraciones de Django sobre la base de datos PostgreSQL.

### 6. Cargar los datos iniciales

Para cargar las actividades, participantes e inscripciones de prueba:

```bash
docker compose -f compose.yaml -f compose.dev.yaml exec backend python manage.py seed_activities
```

Este comando carga los datos iniciales definidos por el proyecto.

### 7. Acceder a la aplicación

Una vez iniciados los servicios, se puede acceder a ellos mediante las siguientes direcciones:

| Servicio           | Dirección                                |
| ------------------ | ---------------------------------------- |
| Frontend Astro     | http://localhost:4321                    |
| Backend Django     | http://localhost:8000                    |
| API de actividades | http://localhost:8000/api/v2/activities/ |

PostgreSQL no se encuentra publicado en el sistema anfitrión. El backend se comunica con la base de datos mediante la red interna de Docker Compose.

### 8. Consultar el estado y los registros

Para comprobar el estado de los servicios:

```bash
docker compose -f compose.yaml -f compose.dev.yaml ps
```

Para consultar los registros de todos los servicios:

```bash
docker compose -f compose.yaml -f compose.dev.yaml logs -f
```

Para consultar únicamente los registros del frontend:

```bash
docker compose -f compose.yaml -f compose.dev.yaml logs -f frontend
```

Para consultar los registros del backend:

```bash
docker compose -f compose.yaml -f compose.dev.yaml logs -f backend
```

La opción `-f` permite seguir los registros en tiempo real. Para dejar de visualizarlos, presionar `Ctrl+C`. Esto no detiene los contenedores.

### 9. Desarrollo y recarga automática

Los directorios del frontend y del backend se montan dentro de sus respectivos contenedores mediante bind mounts.

Esto permite modificar el código fuente desde el editor y reflejar los cambios en los contenedores.

Astro proporciona recarga automática durante el desarrollo del frontend, mientras que Django utiliza el mecanismo de recarga de `runserver`.

No es necesario reconstruir las imágenes después de cada modificación del código fuente.

Cuando se modifican dependencias, Dockerfiles u otros elementos que forman parte de la construcción de las imágenes, puede ser necesario reconstruir los servicios afectados.

### 10. Detener el entorno

Para detener y eliminar los contenedores y la red creada por Compose:

```bash
docker compose -f compose.yaml -f compose.dev.yaml down
```

Este comando conserva los volúmenes de Docker, por lo que los datos almacenados en PostgreSQL no se eliminan.

Para volver a iniciar el entorno:

```bash
docker compose -f compose.yaml -f compose.dev.yaml up -d
```

**Advertencia:** no utilizar `docker compose down -v` si se desea conservar la información almacenada en los volúmenes de PostgreSQL.
