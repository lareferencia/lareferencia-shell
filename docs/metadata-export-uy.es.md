# Perfil completo de UY

> Análisis histórico: el perfil específico usado para estos ejemplos se retiró.
> Para nuevas exportaciones usar `common-full-metadata-v1.json`; su estructura
> se describe en [el contrato común](metadata-export-common.es.md).

Perfil vigente: `lareferencia-shell/config/exports/common-full-metadata-v1.json`.

Se analizaron los 22.700 XML referenciados por la exportación de UY
`exp-2fa482bc-7e14-4a8d-8425-7b177c688e66`. En esos registros el hash original
coincide con el procesado. La cobertura declarada corresponde a este conjunto;
el acrónimo UY es el de la instalación de desarrollo, cuyos registros incluyen
repositorios de Costa Rica. No se infiere país a partir del acrónimo.

El [XML representativo](examples/uy-full-metadata.xml) y su
[JSON completo](examples/uy-full-metadata.json) permiten revisar el mapeo lado a lado.

## Estructura observada

Todos los campos bibliográficos tienen la forma `dc.<campo>.none:value`.
No aparecen calificadores como `abstract`, `issued` o `author`, ni atributos
por valor como `language`, `scheme` o `uri`. El idioma del recurso está en
`dc.language.none`; no se atribuye ese idioma a títulos o descripciones concretos.
Los textos y fechas se mantienen como strings: no se infieren roles ni tipos de fecha.

| Ruta XOAI | Campo JSON | Valores observados |
| --- | --- | ---: |
| `dc.contributor.none:value` | `contributors` | 3028 |
| `dc.coverage.none:value` | `coverage` | 117 |
| `dc.creator.none:value` | `creators` | 51516 |
| `dc.date.none:value` | `dates` | 55095 |
| `dc.description.none:value` | `descriptions` | 51181 |
| `dc.format.none:value` | `formats` | 12067 |
| `dc.identifier.none:value` | `identifiers` | 52350 |
| `dc.language.none:value` | `languages` | 22344 |
| `dc.publisher.none:value` | `publishers` | 13830 |
| `dc.relation.none:value` | `relations` | 14016 |
| `dc.rights.none:value` | `rights` | 32282 |
| `dc.source.none:value` | `sources` | 116882 |
| `dc.subject.none:value` | `keywords` | 129547 |
| `dc.title.none:value` | `titles` | 29841 |
| `dc.type.none:value` | `types` | 40375 |

Cada campo bibliográfico es un array de objetos `{"value": "..."}`. Cada
`value` inicia una ocurrencia. Se preservan repeticiones, strings vacíos, espacios
y orden dentro de cada campo: no hay normalización ni deduplicación.

`descriptions` incluye todas las descripciones, que pueden ser resúmenes,
notas o afiliaciones. `creators` y `contributors` conservan la distinción del XML.
`identifiers` contiene los identificadores bibliográficos; el `identifier` del
envoltorio sigue siendo el identificador del catálogo original.

También se exportan todos los campos técnicos observados:

- `others`: `handle`, `identifier`, `lastModifyDate`.
- `repository`: `mail`, `name`.
- `bundles`: conserva las ocurrencias del contenedor vacío como objetos vacíos.

Los bloques técnicos son arrays de objetos agrupados por elemento. Sus campos
son arrays de strings, incluso cuando están vacíos (`[""]` para un field vacío).
Una ausencia produce `[]`, diferente de un field presente con texto vacío.

## Uso

```text
export-mapping-validate --mapping /config/exports/common-full-metadata-v1.json
export-metadata-preview --network UY --variant processed --mapping /config/exports/common-full-metadata-v1.json --limit 3
export-metadata --network UY --variant processed --format jsonl --mapping /config/exports/common-full-metadata-v1.json --compression gzip --output /exports
```

Este perfil enumera rutas exactas para conservar su significado. Si aparecen
nuevos calificadores, campos, atributos o contenido en `bundles`, habrá que
inventariarlos y versionar el perfil. No es una captura genérica de cualquier XOAI.
La exportación conserva todos los valores observados, pero no pretende reconstruir
la serialización XML (prefijos, namespaces declarados, espaciado estructural u orden
entre familias). Para recuperar el XML exacto se mantiene `metadataHash` y el almacén.

## Verificación contra los XML

Se generó el paquete `exp-a66754a6-f84a-4567-bf2f-89426133c3e3`, con estado
`COMPLETE`: 22.700 registros exportados, cero errores y tres archivos JSONL GZIP.
Se compararon los 737.971 valores de campos exportados con los XML seleccionados
por `metadataHash`, conservando texto, vacíos, repeticiones y orden por ruta/campo.
Se comprobó también la presencia de los 22.700 contenedores `bundles` vacíos,
los localizadores en `records.sqlite` y los checksums de todos los archivos.
Esta comprobación cubre los XML de este snapshot y no garantiza campos futuros.
