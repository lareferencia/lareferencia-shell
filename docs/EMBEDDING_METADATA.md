# Paquete bibliográfico para embeddings

El comando `prepare-embedding-metadata` materializa registros de metadata clasificada y publica un directorio autónomo por ejecución. El consumidor puede trasladar ese directorio y leer las partes por orden con Python estándar. El perfil `bibliographic-roles` 1.0 incluye todas las familias. El preparador también acepta exportaciones con `classification-embeddings` 2.0, cuya proyección contiene títulos, descripciones y palabras clave.

## Instalación y ejecución

Desde la raíz del repositorio del shell, con Python 3.12, instalar el comando en un entorno virtual. Provisionar en un directorio los archivos aprobados `lid.176.ftz` y `role.bin`. El [procedimiento del piloto](../tools/embedding-metadata/README.md) documenta la obtención del detector de idiomas y el entrenamiento del clasificador de roles. El manifiesto identifica los archivos exactos utilizados mediante SHA-256.

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install ./tools/embedding-metadata
export LR_EMBEDDING_MODELS=/opt/lareferencia/modelos
```

Para ejecutar las pruebas desde la raíz del repositorio después de instalar el paquete:

```sh
.venv/bin/python -m unittest discover -s tools/embedding-metadata
```

Desde el shell de LA Referencia, con el perfil del [catálogo del shell](../config/exports/bibliographic-roles-v1.json) instalado en su directorio de configuración:

```text
export-metadata --network UY --variant original --format jsonl --mapping config/exports/bibliographic-roles-v1.json --compression gzip --output /srv/metadata/exports
```

Desde el sistema operativo, asignar a `EXPORT_DIR` el directorio exacto comunicado por el shell. La ubicación de modelos también puede indicarse con `--models-dir`.

```sh
.venv/bin/prepare-embedding-metadata --input "$EXPORT_DIR" --output /srv/metadata/embedding-inputs
```

El comando comprueba el inventario y el índice del padre. Un error en los datos proyectados de una fila identificada se registra en `errors.jsonl`. Las inconsistencias de integridad, identidad o infraestructura detienen la ejecución. Trabaja en un directorio temporal de la raíz de salida, cierra SQLite, relee las partes para comprobar cada localizador y publica por renombre. Devuelve 0 con `COMPLETE`, 2 con `PARTIAL` o 1 con `FAILED`. En un fallo fatal se comunica el motivo por stderr y se descarta la salida provisional. Un reintento genera un nuevo identificador. Los consumidores automáticos deben exigir `COMPLETE`.

## Contrato annotated-metadata 1

- El manifiesto contiene `packageId`, tipo y versión de contrato, estado, fechas, redes y snapshots, referencia y SHA-256 del manifiesto padre, variante, perfil, modelos, reglas, umbrales y versiones. `parts` contiene la lista ordenada de rutas relativas con datos. `files` inventaría las partes, el índice y los errores con tamaños y hashes.
- Cada parte de entrada genera una parte JSONL GZIP en la misma partición y mantiene el orden de origen. El tamaño en bytes varía al materializar la clasificación. Cada fila contiene `network`, `catalogId`, `identifier`, `metadataHash` y `data`.
- Las siete familias siempre son arrays. `titles` y `abstracts` llevan `value` y el idioma detectado en `language` (código concreto, o `und` si quedó indeterminado). Los resúmenes llevan `selection` con `classified` o `uncertain_fallback`. Se elige un único respaldo cuando falta un resumen en todo el registro. Los índices de origen conservan el orden de las ocurrencias.
- `keywords` conserva las ocurrencias y los atributos del perfil. `affiliations` usa el literal institucional extraído, o la ocurrencia de origen si faltó un literal separable. `funders` conserva el valor y la evidencia. `agency_mention` identifica una mera mención. `documentTypes` contiene tipos normalizados. `otherDescriptions` conserva otras descripciones, incluidas las dudosas restantes, con su idioma y rol.
- Un registro sin título queda disponible y se cuenta en `title.missing`. La ausencia de categorías opcionales es válida. Los conteos concilian entrada = anotados + errores. El manifiesto da la cobertura por red y tipo de selección.
- `records.sqlite` contiene una fila por entrada exportada, identificada por `(network, catalog_id)`. Incluye identificador, hash, snapshot, parte y línea padre, parte y línea de salida y estado. Las líneas comienzan en 1. El JSON en `origins` apunta desde cada ocurrencia entregada a `[campo, índice]` en el `data` del padre, con índices desde 0. En el manifiesto, `parent.exportId` identifica el export original.
- Para recuperar los XML históricos sigue siendo necesario conservar el almacén correspondiente. La preparación de texto para embeddings solo requiere la carpeta entregada.

## Idioma de las palabras clave

Desde la versión 1.1 del preparador, cada elemento de `keywords` contiene el literal original, `language` y `languageSource`. Si la fuente incluía el atributo de idioma, `declaredLanguage` conserva su valor original. La selección sigue este orden.

1. Para un literal con texto, usar el idioma explícito válido, normalizado a su código de idioma base (`pt-BR` → `pt`, `spa` → `es`). La evidencia es `declared`.
2. Buscar el término o frase completos en títulos y resúmenes clasificados de idioma conocido del mismo registro. La comparación normaliza Unicode, mayúsculas y espacios y conserva los acentos. Una coincidencia exclusiva de un idioma da `record_text`. Si aparece en varios idiomas queda `und`.
3. Sin coincidencias, aplicar el detector existente a la keyword. Una frase de al menos tres palabras con puntuación y margen suficientes da `model`. Ante evidencia insuficiente el idioma es `und` y la evidencia es `undetermined`. Los calificadores XOAI se preservan. En UY se observaron términos ingleses y españoles bajo un mismo calificador `es`, por lo que este por sí solo no decide el idioma.

El manifiesto registra `counts.keywordOccurrences` y `counts.keywordsUndetermined` sobre todas las ocurrencias entregadas, incluidas las vacías. El desglose por red distingue idiomas y evidencias.

## Consumidor de ejemplo

[build_inputs.py](../tools/embedding-metadata/examples/build_inputs.py) usa únicamente la biblioteca estándar de Python 3.11+. Ejecutado sobre una copia del paquete, verifica los hashes de las partes y arma textos agrupando títulos y resúmenes por idioma dentro de cada registro con título. Los títulos y resúmenes indeterminados se entregan individualmente. A cada grupo con idioma conocido se añade un último párrafo con sus keywords en orden original, separadas por comas, y los índices se agregan a `fields`. Las keywords indeterminadas o sin grupo de texto en ese idioma quedan en el paquete. Los paquetes anteriores que carecen de `languageSource` conservan el resultado previo de títulos y resúmenes. Cada texto conserva las referencias a sus campos e índices. Para excluir los resúmenes de respaldo, añadir `--classified-only`.

```sh
python3.12 tools/embedding-metadata/examples/build_inputs.py "$PACKAGE_DIR" > entradas.jsonl
```

## Validación de la entrega con UY

El preparador 1.1.0 se probó sobre los 30.752 registros activos de UY del snapshot 4186, con metadata original y el perfil `bibliographic-roles` 1.0. El export `exp-01b83c75-1d65-4883-bd8c-d22fa911f847` produjo el paquete anotado `ann-fc3c9eac-76b1-406c-bd5b-136eb63670cc` en estado `COMPLETE`, con 30.752 filas y cero errores.

| Indicador | Resultado |
| --- | ---: |
| Registros con título | 30.752 |
| Registros con resumen clasificado | 23.869 |
| Registros con descripción dudosa seleccionada como resumen | 2.040 |
| Registros sin resumen | 4.843 |
| Ocurrencias de palabras clave | 177.463 |
| Ocurrencias con idioma indeterminado | 101.239 (57,05 %) |
| Textos preparados para embeddings | 53.737 |
| Textos que incorporaron palabras clave | 29.855 |

El consumidor leyó una copia del paquete anotado y generó los textos por idioma. Se comprobó que los índices de los campos recuperan el texto entregado. En el registro `2650dec7ea16ad480565ad17203e8f5d`, la entrada en español incorpora «heridas» y la inglesa incorpora «wounds». «traumatismos» y «traumatisms» permanecen en el paquete con idioma indeterminado.

La validación cubre exportación, trazabilidad y preparación de textos. Medir la precisión lingüística requiere una muestra etiquetada manualmente. La generación de vectores pertenece a la siguiente etapa.
