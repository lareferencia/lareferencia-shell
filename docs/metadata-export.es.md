# Exportación de metadata para enriquecimientos externos

Los comandos `export-metadata`, `export-mapping-validate` y
`export-metadata-preview` exportan entradas trazables para procesos externos.
El servicio reutilizable está en `org.lareferencia.core.export`, en core-lib.
Esta versión define también el contrato de retorno; la importación de resultados
y los transformadores que los aplicarán se desarrollarán posteriormente.

## Preparación y comandos

Usar la misma base PostgreSQL, `store.basepath` y `metadata.store.type` que el
cosechador. El shell necesita leer los catálogos, bases de validación y metadata.
No requiere migraciones nuevas. Los comandos anteriores
`export-all-lgk-metadata` y `export-all-lgk-identifiers-mapping` conservan su sintaxis
y sus formatos.

Los perfiles de ejemplo están en `lareferencia-shell/config/exports/`, junto
con su [README de uso](../config/exports/README.md). Los esquemas permanecen en
`lareferencia-core-lib/src/main/resources/export/` y en el JAR de core-lib.
Copiar `publications-v1.json` al directorio de configuración deseado y ajustarlo
al XOAI real de las fuentes. Este ejemplo no define un estándar bibliográfico
universal: cada perfil define su propio contrato en `data`.

Desde el shell interactivo:

```text
export-mapping-validate --mapping /config/exports/publications-v1.json
export-metadata-preview --network RCAAP --variant processed --mapping /config/exports/publications-v1.json --limit 5
export-metadata --networks RCAAP,IBICT --variant processed --format jsonl --mapping /config/exports/publications-v1.json --partition-by network --max-records 10000 --max-bytes 128MiB --compression gzip --output /exports
export-metadata --all-networks --variant original --format xml --output /exports
export-metadata --network RCAAP --variant original --format xml --layout per-record --compression none --output /exports
```

También se pueden pasar los comandos al ejecutable del shell. Usar
`help export-metadata` para consultar las opciones del build instalado.

| Opción | Comportamiento |
| --- | --- |
| `--network`, `--networks`, `--all-networks` | Exactamente una selección. Acrónimos exactos y sensibles a mayúsculas; la lista usa comas, sin espacios. Duplicados y desconocidos son errores. |
| `--variant original\|processed` | Predeterminado `processed`. Original es el XML almacenado antes de las transformaciones de validación; puede haber sido convertido a XOAI durante la cosecha. Procesada usa `published_metadata_hash`, incluso si coincide con el original. |
| `--valid-only` | Predeterminado `false`: incluye activos válidos e inválidos. Activarlo requiere validación. Las bajas se excluyen siempre. |
| `--format xml\|json\|jsonl` | Predeterminado `jsonl`. JSON es un array por archivo; JSONL es un objeto por línea. Ambos requieren `--mapping`; XML lo rechaza. |
| `--layout collection\|per-record` | Solo XML, predeterminado `collection`. Individual escribe el XML almacenado y localiza su identidad en `records.sqlite`; colección envuelve cada XML con `source` e `input`. |
| `--partition-by network\|none` | Predeterminado `network`. `none` combina fuentes bajo `data/`. |
| `--max-records`, `--max-bytes` | Predeterminados 10000 y 128MiB. Bytes UTF-8 sin comprimir, incluyendo separadores y envoltorios. Acepta bytes enteros, B, KiB, MiB o GiB. No se admiten límites explícitos para XML individual. |
| `--compression none\|gzip` | Predeterminado `gzip`. El límite no se refiere al tamaño comprimido. |
| `--output` | Directorio padre; cada ejecución crea un nuevo `exp-<uuid>`. |

Solo se seleccionan LGK: snapshots válidos, completados y no eliminados. La
selección se fija al comenzar, aunque aparezca después un LGK más reciente.
Una fuente sin LGK se registra como omitida; si la selección explícita no tiene
ningún LGK, el comando falla. Todas las fuentes sin LGK pueden producir un paquete
vacío completo usando `--all-networks`.

El recorrido es por acrónimo y luego ID del catálogo. Nunca se corta un registro
entre archivos: si supera el máximo ocupa un archivo propio y se incrementa
`warnings.oversizedRecords`. Los números de archivo avanzan en toda la ejecución.
Los nombres de directorio se sanitizan; la identidad conserva el acrónimo exacto.
Las colisiones de nombres sanitizados se rechazan antes de exportar.

## Mapeos XOAI

`mapping-v1.schema.json` describe la especificación. El comando de validación
comprueba propiedades, tipos y selectores antes de abrir los catálogos. También
rechaza claves JSON duplicadas y contenido adicional después del objeto.

```json
{
  "specVersion": 1,
  "name": "publications",
  "version": "1.0",
  "inputSchema": "xoai",
  "fields": {
    "identifiers": {
      "select": "dc.identifier.*",
      "type": "string",
      "normalize": ["trim"],
      "unique": true
    },
    "titles": {
      "forEach": "dc.title.*",
      "occurrenceStart": "value",
      "fields": {
        "value": {"select": ":value", "type": "string", "many": false},
        "language": {"select": ":language", "type": "string", "many": false}
      }
    }
  }
}
```

`dc.identifier.dark` navega por `element/@name` y termina en `field name="value"`.
`dc.identifier.dark:value` expresa ese campo explícitamente. `:language` selecciona
el campo del elemento actual. Cada `forEach` produce un array de objetos y evalúa
sus campos relativos a cada ocurrencia; puede anidarse.

`*` conserva la semántica recursiva del helper de validación: selecciona elementos
descendientes y excluye el elemento padre. Por ello `dc.identifier.*` no extrae el
`value` situado directamente en `dc.identifier`; ese valor necesita su propio
selector `dc.identifier`. Las rutas no son XPath libre. No se admiten predicados,
funciones, ni el marcador legacy `$`; `forEach` ya selecciona elementos.

Se admiten strings, enteros de precisión arbitraria y booleanos literales
`true`/`false`. Un string conserva sus espacios salvo `normalize: ["trim"]`.
No se descartan cadenas vacías. Las listas (`many: true`, predeterminado) vacías
son `[]`; los escalares ausentes se omiten. Múltiples valores para un escalar
producen error. `unique` conserva la primera ocurrencia, después de normalizar y
convertir. Un selector ausente es diferente de un error de evaluación o conversión.

Con `occurrenceStart: "value"` en una regla `forEach`, cada campo directo `value`
inicia una ocurrencia; los campos hermanos siguientes pertenecen a ella hasta el
próximo `value`. Por ejemplo, `value=Hola, language=spa, value=Hello, language=eng`
produce dos objetos con `value` y `language` escalares. Otros atributos, como
`scheme` o `uri`, se declaran mediante selectores `:scheme` o `:uri`.
Solo se admiten selectores directos `:field` dentro de esta agrupación. Los campos
ausentes se omiten cuando son escalares; los atributos repetidos requieren listas
explícitas. Un campo anterior al primer `value` es un error de agrupación. Nunca
se emparejan arrays por posición ni se propaga un idioma a otras ocurrencias.
Si el orden del XML no expresa la asociación (por ejemplo, todos los valores y
luego todos los idiomas), usar el agrupamiento por elemento sin `occurrenceStart`
y campos `many: true` para conservar el grupo original sin inventar asociaciones.

La previsualización no crea paquetes; `--limit` limita filas intentadas, incluyendo
filtradas y erróneas. Muestra registros proyectados y errores. La previsualización no tiene `exportId` y no sirve como entrada final.

## Paquete e identidad

```text
exp-<uuid>/
  manifest.json
  mapping.json
  records.sqlite
  errors.jsonl
  RCAAP/
    part-000001.jsonl.gz
```

`mapping.json` solo se incluye para JSON. La identidad es obligatoria y queda fuera
del mapeo bibliográfico:

```json
{
  "network": "RCAAP",
  "catalogId": "0123456789abcdef0123456789abcdef",
  "identifier": "oai:repositorio:12345",
  "metadataHash": "...",
  "data": {"titles": [{"value": "Título", "language": "es"}]}
}
```

La clave del registro es `(network, catalogId)`. Ambos componentes se conservan
separados; `catalogId` e `identifier` siempre provienen del catálogo original.
Un identifier puede aparecer en varias fuentes. No se recalcula el ID almacenado.
`metadataHash` identifica el XML elegido. No se emite `payloadHash`, `recordKey`,
`source`, `input` ni `exportId` en los registros JSON/JSONL. El paquete conserva
`exportId`, variante y snapshots una sola vez en el manifiesto. No consumir líneas
sueltas sin conservar su paquete de procedencia.

El contrato JSON compacto es la versión 2. Las colecciones XML mantienen su
envoltorio de identidad y los XML individuales conservan el contenido almacenado.

El manifiesto contiene `contractVersion: 2`, las opciones, la copia lógica del
mapeo y su hash canónico, fuentes omitidas, y las referencias exactas de snapshots.
Cada fuente conserva el ID interno del snapshot como evidencia técnica, fechas
UTC, estado y archivos de procedencia disponibles con su hash. Los IDs internos de
redes no se utilizan para seleccionar ni vincular registros.

`records.sqlite` contiene la tabla `records`: `record_key`, `export_id`, `network`,
`catalog_id`, `identifier`, `snapshot_ref`, `original_metadata_hash`, `variant`,
`metadata_hash`, `datestamp`, `is_valid`, `is_transformed`, `status`,
`file`, `position`, `error`. Incluye filas `EXPORTED`, `FILTERED` y `ERROR`.
`is_valid` e `is_transformed` pueden ser NULL si no hay información de validación.

Los localizadores son relativos al paquete. `position` es línea desde 1 para
JSONL, índice desde 0 para JSON y colecciones XML, o NULL para XML individual.
Después de descomprimir un archivo se utiliza esa posición. Los XML individuales
se nombran con acrónimo sanitizado e ID del catálogo; no se usa el identifier como
nombre de archivo. El índice se entrega cerrado en journal DELETE, sin WAL externo.

Ejemplo de búsqueda de una entrada desde un resultado externo:

```sql
SELECT network, catalog_id, identifier, snapshot_ref,
       metadata_hash, file, position
FROM records
WHERE export_id = ? AND network = ? AND catalog_id = ? AND status = 'EXPORTED';
```

El manifiesto resuelve `snapshot_ref` al snapshot original. Para consultar aquel
catálogo se busca `oai_record.id = catalog_id` y se contrasta el `identifier`.
Los paquetes JSON guardan únicamente referencias a XML: conservar el almacén de
metadata y la referencia al snapshot para reconstruir posteriormente los originales.
El índice contiene los datos necesarios para remapear aunque se limpien las bases
históricas; recuperar su XML sigue dependiendo de la retención del almacén.

## Consistencia, errores y ejecución por lotes

El lector usa conexiones SQLite propias `mode=ro` y `query_only`, con validación
vinculada por `identifier_hash`. No ejecuta migraciones ni checkpoints del origen.
Las bases legacy sin columna `deleted` de validación se leen sin modificar su
esquema. No se cambia el hash seleccionado ni se sustituye una validación ausente
por metadata original. Los XML se procesan uno por uno y el parser rechaza DTD y
entidades externas. La memoria de los registros está acotada por el registro más
grande, no por el número total de registros.

Se comprueban estado, manifiestos y atributos de archivos DB/WAL antes y después
de la lectura y al finalizar. Un cambio detectado invalida el paquete. Esto no es
un bloqueo global del cosechador: evitar revalidar o limpiar esos snapshots durante
la exportación. La creación de un LGK nuevo no cambia las referencias fijadas.

El manifiesto empieza como `RUNNING`, y finaliza `COMPLETE`, `PARTIAL` (errores por
registro) o `FAILED` (infraestructura/cambio de origen). En ejecuciones terminadas
sin fallo de infraestructura, `attempted = exported + filtered + errors`.
Los errores por registro se guardan en `errors.jsonl` con identidad. Los errores
fatales conservan la evidencia que pudo escribirse; si hay fallo de disco puede
quedar un manifiesto `RUNNING` o archivos `.tmp`, que no deben consumirse.

Los archivos de datos se publican al completarse, mediante renombrado. El
manifiesto enumera tamaños y SHA-256 de todos los archivos entregados salvo él
mismo; excluye temporales y journals. Antes de procesar un paquete comprobar su
estado y los checksums. No consumir como completo un paquete parcial o fallido.

En modo no interactivo, una exportación parcial o fallida produce error del shell
y salida no exitosa. Interactivamente se muestra el resumen o error y se mantiene
la sesión. Una interrupción controlada puede registrar `FAILED`; una terminación
abrupta deja `RUNNING`. Esta versión no reanuda ejecuciones.

## Contrato de retorno de enriquecimientos

`enrichment-return-v2.schema.json` describe un resultado del contrato compacto.
Copiar `network`, `catalogId`, `identifier` y `metadataHash` desde el registro,
añadir `exportId` desde el manifiesto del paquete y el bloque siguiente. El esquema
v1 se conserva únicamente para paquetes anteriores:

```json
{
  "enrichment": {
    "id": "enr-<uuid>",
    "type": "subject-classification",
    "schemaVersion": "1",
    "runId": "run-<uuid>",
    "generatedAt": "2026-11-05T12:00:00Z",
    "values": {"subjects": ["Tema de ejemplo"]}
  }
}
```

Un manifiesto externo por `runId` debe registrar procesador, versión, configuración
completa y hash, fechas, estado, archivos y checksums, y las versiones o referencias
inmutables de modelo, prompt, vocabularios y otras dependencias empleadas. Conservar
también los fallos y casos sin resultado para reconciliar la ejecución con el paquete.

La vinculación de retorno es `(exportId, network, catalogId)`. Los futuros transformadores
deberán contrastar identidad y hashes, aplicar de manera idempotente, y registrar
qué enriquecimiento cambió qué campos, snapshot de destino y hashes antes/después.
Un cambio de XML debe requerir una política explícita de compatibilidad; la primera
política será coincidencia estricta de entrada. No basta con que coincida el ID.
La compatibilidad se comprueba con `metadataHash`, sin hash adicional del JSON.

La configuración del transformador deberá incorporar el hash inmutable de la
colección de enriquecimientos al fingerprint del pipeline. Una ruta de archivo
sin versión/hash no permite detectar nuevos resultados durante la reutilización
incremental. La sustitución o retirada de enriquecimientos deberá preservar valores
que procedan del repositorio y registrar su propia auditoría.

## Perfil común para varias fuentes

`common-full-metadata-v1.json` normaliza UY y AREANDINA a las mismas familias.
Consultar [el contrato común, ejemplos y límites](metadata-export-common.es.md).

Los perfiles disponibles son `publications-v1.json` (ejemplo bibliográfico inicial),
`common-full-metadata-v1.json` (formato común completo) y
`classification-embeddings-v1.json` (títulos, posibles resúmenes y keywords). Los perfiles
intermedios de texto y los específicos de UY/AREANDINA se retiraron. Los análisis
por fuente se conservan como antecedentes del perfil común.
