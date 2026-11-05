# Perfiles de exportación de metadata

Estos son los perfiles de ejemplo mantenidos en el repositorio del shell.

| Archivo | Versión | Contenido |
| --- | --- | --- |
| `publications-v1.json` | 1.0 | Ejemplo inicial: identificadores, dark, títulos y abstracts. |
| `common-full-metadata-v1.json` | 1.1 | Metadata completa de UY y AREANDINA en 19 familias comunes. Calificadores opcionales y extensiones identificadas por `path`. |
| `classification-embeddings-v1.json` | 1.0 | Títulos, posibles resúmenes y keywords para clasificación y embeddings. Incluye descripciones sin calificar. |
| `licenses-v1.json` | 1.0 | Licencias de `dc.rights.*` de hasta 300 caracteres; omite textos largos sin truncarlos. |

Los perfiles se leen desde archivos mediante `--mapping`. Se pueden editar o
versionar independientemente del JAR. Al instalar el shell, copiar este directorio
a `exports/` dentro del directorio de configuración usado en esa instalación.
Por ejemplo, si la configuración está en `/config`, los archivos quedan en
`/config/exports/`. No se copian automáticamente a otros volúmenes de configuración.

Desde el shell, ejecutado en la raíz de este repositorio:

```text
export-mapping-validate --mapping config/exports/publications-v1.json
export-mapping-validate --mapping config/exports/common-full-metadata-v1.json
export-metadata-preview --network AREANDINA --variant processed --mapping config/exports/common-full-metadata-v1.json --limit 3
export-metadata --networks UY,AREANDINA --variant processed --format jsonl --mapping config/exports/common-full-metadata-v1.json --output /exports
export-mapping-validate --mapping config/exports/licenses-v1.json
export-metadata-preview --network UY --variant processed --mapping config/exports/licenses-v1.json --limit 3
```

El perfil común se comprobó contra los snapshots estudiados de UY y AREANDINA.
El perfil de clasificación se ejecutó sobre ambas fuentes: 26.700 registros,
estado `COMPLETE` y cero errores (`exp-d90b244f-2766-4b6f-b2b7-24d66a285fda`).
Incluyó 51.181 descripciones sin calificar en UY; pueden ser resúmenes, notas o
afiliaciones. Revisar esta advertencia al construir la entrada para embeddings.
Nuevas rutas o fuentes pueden requerir ampliarlo; no se infiere información ausente.
No repite `schema` por ocurrencia. `qualifier` se conserva cuando existe; en
`additionalMetadata`, la ruta completa en `path` conserva esquema y calificador.

Los JSON Schema de la especificación, la salida común y el contrato de retorno
permanecen en `lareferencia-core-lib/src/main/resources/export/` y en su JAR.

Consultar [la guía de exportación](../../docs/metadata-export.es.md) y
[el formato común](../../docs/metadata-export-common.es.md).

## Perfil para clasificación y embeddings

`classification-embeddings-v1.json` exporta únicamente `titles`, `abstracts` y
`keywords` dentro de `data`. Las tres familias son arrays de ocurrencias con
`value`, `language` opcional y `qualifier` opcional, sin repetir `schema`.
Se mantiene el envoltorio común con `network`, `catalogId`, `identifier` y
`metadataHash` para vincular las clasificaciones con sus registros originales.

- Títulos: las variantes de `dc.title` del perfil común, incluidos alternativos,
  subtítulos y traducciones.
- Resúmenes: `dc.description.abstract`, `abstractenglish`, `resumen` y `none`,
  además de `dcterms.abstract.none`.
- Keywords: todas las variantes de `dc.subject` del perfil común, más
  `dcterms.subject.none` y `dcterms.subject.Lemb`.

Las descripciones sin calificar se incluyen por decisión explícita para aprovechar
UY, donde no se distinguen resúmenes, notas y afiliaciones. Por tanto, `abstracts`
contiene **posibles resúmenes**, no textos garantizados como resúmenes. En ambas
fuentes, los valores sin calificar se reconocen por la ausencia de `qualifier`.
Se excluyen rutas explícitas como `dc.description.notes`, `tableofcontents`,
`program` y `degreename`. Las keywords pueden incluir términos de vocabularios
controlados o códigos, identificables por su calificador.

Se conservan repeticiones, espacios, valores vacíos y orden; un campo ausente es
`[]`. No se infieren idiomas, no se concatenan textos ni se generan embeddings.
Para construir la entrada del modelo, usar los `value` y elegir una política de
idiomas, deduplicación y longitud en el procesamiento externo. El índice y el
manifiesto del paquete conservan la trazabilidad para devolver enriquecimientos.

```text
export-mapping-validate --mapping config/exports/classification-embeddings-v1.json
export-metadata-preview --network AREANDINA --mapping config/exports/classification-embeddings-v1.json --limit 3
export-metadata --networks UY,AREANDINA --variant processed --format jsonl --mapping config/exports/classification-embeddings-v1.json --compression gzip --output /exports
```
