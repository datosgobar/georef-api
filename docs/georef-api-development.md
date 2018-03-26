# Georef API - Guía de instalación para entorno de desarrollo

## Dependencias

- [ElasticSearch >=6.2](https://www.elastic.co/guide/en/elasticsearch/reference/current/_installation.html)
- [Python >=3.6.x](https://www.python.org/downloads/)
- [Pip](https://pip.pypa.io/en/stable/installing/)
- [PostgreSQL 9.6](https://www.postgresql.org/download/)
- [PostGis 2.3](http://postgis.net/install/)
- [Virtualenv](https://packaging.python.org/guides/installing-using-pip-and-virtualenv/)
- Wget

## Datos

Los datos de las entidades políticas y vías de circulación deben descargarse del [portal de datos](http://datos.gob.ar/).  

## Base de datos

Crear una base de datos en PostgreSQL con la extensión Postgis.

Ejemplo:

```plsql
-- Creando base de datos
CREATE DATABASE georef_api WITH ENCODING='UTF8';

-- Agregando Postgis a la base de datos creada
CREATE EXTENSION postgis;
```

## Instalación

- Clonar repositorio:

    `$ git clone https://github.com/datosgobar/georef-api.git`
    
- Crear un entorno virtual y activarlo:

    `$ python3.6 -m venv venv`
    
    `$ . venv/bin/activate`
 
- Instalar dependencias con _pip_:
    
    `(venv)$ pip install -r requirements.txt`

- Copiar las variables de entorno:

    `(venv)$ cp environment.example.sh environment.sh`
    
- Completar el archivo `environment.sh` con los valores con los datos correspondientes:

    ```bash
    export GEOREF_API_DB_HOST= # localhost
    export GEOREF_API_DB_NAME= # georef 
    export GEOREF_API_DB_USER= # postgres
    export GEOREF_API_DB_PASS= # postgres   
 
    export ENTIDADES_DATA_DIR= # /directorio/datos/de/entidades
    export VIAS_DATA_DIR= # /directorio/datos/de/vias
 
    export FLASK_APP=service/__init__.py
    export FLASK_DEBUG=1

    export OSM_API_URL='http://nominatim.openstreetmap.org/search'
    ```
- Cargar funciones en PostgreSQL:

    `(venv)$ python scripts/functions_load.py`
 
## ElasticSearch

- Levantar el servicio de ElasticSearch:

    `$ cd directorio/a/elasticsearch/bin/ && ./elasticseach`
  
- Probar el servicio:

    `$ curl -X GET 'http://localhost:9200'`
    
### Generar índices

- Importar variables de entorno:
    
    `(venv)$ . environment.sh`
    
- Generar índices de entidades:

    `(venv)$ python scripts/index_entities.py crear-entidades`
    
- Generar índices de vías de circulación:

    `(venv)$ python scripts/index_entities.py crear-vias`

## Correr API 

- Correr _georef-api_:
    
    `(venv)$ flask run`
    
- Listar otros comandos utiles:

    `(venv)$ python scripts/index_entities.py`

## Pruebas

- Pruebas unitarias:

    `(venv) $ python -m unittest`
  
- Consumir la API mediante la herramienta CURL:

    `$ curl localhost:5000/api/v1.0/direcciones?direccion=cabral+500`
  
    `$ curl localhost:5000/api/v1.0/provincias`