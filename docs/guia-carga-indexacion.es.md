# Guia de Carga e Indexacion de Entidades

Esta guia describe un flujo simple de punta a punta para compilar la
plataforma, configurar `lareferencia-shell`, cargar el modelo de entidades y
los datos, ejecutar la consolidacion/deduplicacion, e indexar las entidades
finales.

## 1. Compilar la Plataforma

Ejecutar la compilacion desde la raiz del repositorio padre,
`lareferencia-platform`.

Elegir el perfil del despliegue:

```bash
./build.sh ibict
```

Otros perfiles comunes:

```bash
./build.sh lareferencia
./build.sh rcaap
./build.sh lite
```

Los perfiles `ibict`, `lareferencia` y `rcaap` incluyen
`lareferencia-shell-entity-plugin`, que agrega los comandos de carga e
indexacion de entidades.

## 2. Configurar lareferencia-shell

Editar:

```text
lareferencia-platform/lareferencia-shell/config/application.properties
```

Apuntar el shell a la base PostgreSQL donde se cargaran los datos:

```properties
spring.datasource.url=jdbc:postgresql://localhost:5432/nombre_de_la_base
```

Reemplazar `nombre_de_la_base` por el nombre real de la base.

Verificar tambien el resto de la configuracion del ambiente:

- `spring.datasource.username`
- `spring.datasource.password`
- Propiedades de Elasticsearch/OpenSearch, cuando se indexa en Elasticsearch
- Propiedades de metadata, entidades o contexto custom requeridas por el perfil
  seleccionado

## 3. Descargar o Preparar el Modelo de Entidades

Por ejemplo, para usar el modelo BrCris/Ibict desde GitHub:

```bash
git clone https://github.com/brcris-ibict/brcris-model.git
```

Identificar el archivo XML del modelo dentro del repositorio clonado, por
ejemplo:

```text
/path/to/brcris-model/modelo_brcris.xml
```

Preparar tambien el directorio o archivo XML con los datos de entidades:

```text
/path/to/entity-data
```

`load_data` puede recibir un unico archivo XML o un directorio. Cuando recibe
un directorio, carga recursivamente todos los archivos `.xml`.

## 4. Ejecutar el Shell

Desde el directorio `lareferencia-shell`:

```bash
cd lareferencia-shell
./lareferencia-shell.jar
```

Si se necesita usar otro directorio de configuracion:

```bash
JAVA_OPTS="-Dapp.config.dir=/path/to/config" ./lareferencia-shell.jar
```

## 5. Preparar la Base de Datos

Dentro del shell, ejecutar:

```bash
database_migrate
```

Si la intencion es recrear una base vacia, limpiarla primero:

```bash
database_clean --confirm true
database_migrate
```

Advertencia: `database_clean --confirm true` elimina los objetos y datos de la
base gestionados por Flyway. Usarlo solamente cuando realmente se quiere
reiniciar la base.

## 6. Cargar el Modelo de Entidades

Cargar el XML del metamodelo de entidades:

```bash
load_model /path/to/modelo.xml
```

## 7. Cargar los Datos de Entidades

Paso recomendado: ejecutar primero un dry run para validar la ruta y los XML
sin persistir datos.

```bash
load_data --path /path/to/entity-data --dryRun true
```

Luego ejecutar la carga real:

```bash
load_data --path /path/to/entity-data
```

Cuando termina `load_data`, los datos quedan cargados en estructuras fuente o
dirty. Todavia deben ser consolidados antes de indexar.

## 8. Consolidar Entidades Dirty

Ejecutar el proceso de merge:

```bash
merge_dirty_entities
```

Este paso consolida los datos cargados en las tablas finales de entidades y
relaciones usadas por la indexacion.

## 9. Indexar Entidades

Listar los indexadores disponibles en la configuracion actual:

```bash
list-indexers
```

Ejecutar la indexacion con el archivo de configuracion, tipo de entidad, tamano
de pagina e indexador deseados.

Ejemplo:

```bash
index-entities \
  --configFileFullPath /path/to/entity-indexing-config.xml \
  --indexerName entityIndexerElastic \
  --entityTypeName Person \
  --pageSize 1000
```

Filtros opcionales utiles:

```bash
index-entities \
  --configFileFullPath /path/to/entity-indexing-config.xml \
  --indexerName entityIndexerElastic \
  --entityTypeName Person \
  --lastUpdate 2026-08-01T00:00:00 \
  --pageSize 1000
```

```bash
index-entities \
  --configFileFullPath /path/to/entity-indexing-config.xml \
  --indexerName entityIndexerElastic \
  --entityTypeName Person \
  --provenance brc \
  --pageSize 1000
```

Cuando se informa `provenance`, `lastUpdate` es ignorado.

## 10. Checklist Rapido

- La plataforma fue compilada con un perfil que incluye el plugin de entidades.
- `spring.datasource.url` apunta a la base PostgreSQL correcta.
- Las migraciones de base fueron ejecutadas.
- El modelo de entidades fue cargado con `load_model`.
- Los datos fueron cargados con `load_data --path`.
- `merge_dirty_entities` termino correctamente.
- `list-indexers` muestra el indexador esperado.
- `index-entities` termino y genero el reporte de indexacion.
