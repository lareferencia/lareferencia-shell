# Perfiles de exportación de metadata

Estos son los perfiles de ejemplo mantenidos en el repositorio del shell.

| Archivo | Versión | Contenido |
| --- | --- | --- |
| `publications-v1.json` | 1.0 | Ejemplo inicial: identificadores, dark, títulos y abstracts. |
| `common-full-metadata-v1.json` | 1.1 | Metadata completa de UY y AREANDINA en 19 familias comunes. Calificadores opcionales y extensiones identificadas por `path`. |
| `classification-embeddings-v1.json` | 2.0 | Títulos, descripciones y keywords de todas las variantes de Dublin Core. |
| `bibliographic-roles-v1.json` | 1.0 | Títulos, descripciones, keywords, tipos, afiliaciones y financiadores para el preparador de metadata de embeddings. |
| `subjects-ford-v1.json` | 1.0 | Registros con una materia cuyo valor empieza por una URI FORD de BECyT o de Perú. Exporta títulos, descripciones y todas las materias. |
| `licenses-v1.json` | 1.1 | Valores de `dc.rights.*` de hasta 300 puntos de código Unicode. Excluye las URI de `info:eu-repo` y COAR. |

Los perfiles se leen desde archivos mediante `--mapping`. Se pueden editar o
versionar independientemente del JAR. Al instalar el shell, copiar este directorio
a `exports/` dentro del directorio de configuración usado en esa instalación.
Por ejemplo, si la configuración está en `/config`, los archivos quedan en
`/config/exports/`. No se copian automáticamente a otros volúmenes de configuración.

Desde el shell, ejecutado en la raíz de este repositorio:

```text
export-mapping-list
export-mapping-list --directory config/exports
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

`classification-embeddings-v1.json` exporta `titles`, `descriptions` y
`keywords` a partir de `dc.title.*`, `dc.description.*` y `dc.subject.*`.
Cada array conserva las ocurrencias con su `value`, `language` y `qualifier`
cuando estos últimos están presentes. Las descripciones pueden incluir
resúmenes, notas o afiliaciones.

El export conserva `network`, `catalogId`, `identifier` y `metadataHash`.
El preparador Python recibe el directorio `exp-…` completo y clasifica las
descripciones antes de componer los textos de entrada. Para incluir campos
dedicados de tipos, afiliaciones y financiadores, usar
`bibliographic-roles-v1.json`. [Preparar metadata para embeddings](https://github.com/LA-Referencia-IOI/lareferencia-metadata-tools/blob/main/docs/EMBEDDING_METADATA.md).

```text
export-mapping-validate --mapping config/exports/classification-embeddings-v1.json
export-metadata-preview --network AREANDINA --mapping config/exports/classification-embeddings-v1.json --limit 3
export-metadata --networks UY,AREANDINA --variant processed --format jsonl --mapping config/exports/classification-embeddings-v1.json --compression gzip --output /exports
```
