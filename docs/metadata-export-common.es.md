# Perfil común de metadata completa

El mismo [`common-full-metadata-v1.json`](../config/exports/common-full-metadata-v1.json),
guardado en `config/exports/` del shell, puede usarse con UY y AREANDINA.
El esquema de salida es `common-full-metadata-v1.schema.json`, en los recursos
`export/` de core-lib. El envoltorio conserva el contrato compacto v2.

## Familias comunes

Todos los registros contienen las mismas familias, siempre como arrays:
`titles`, `creators`, `contributors`, `keywords`, `descriptions`, `publishers`,
`dates`, `types`, `formats`, `identifiers`, `sources`, `languages`, `relations`,
`coverage`, `rights`, `others`, `repository`, `bundles` y `additionalMetadata`.
Si no hay ocurrencias, la familia es `[]`.

Cada ocurrencia bibliográfica contiene `value` y, cuando existen,
`language` y `qualifier`. El perfil común 1.1 omite `schema`: las familias y el
perfil guardado en el paquete ya definen su procedencia. El calificador `none` se omite; no se infiere un idioma.

```json
{
  "titles": [
    {"value": "Título principal", "language": "spa"},
    {"value": "Otro título", "qualifier": "alternative"}
  ],
  "creators": [
    {"value": "Persona autora", "qualifier": "author"}
  ],
  "contributors": [
    {"value": "Persona asesora", "qualifier": "advisor"}
  ]
}
```

`dc.creator.none` y `dc.contributor.author` se reúnen en `creators`. El resto
de `dc.contributor` se exporta en `contributors`, preservando el rol en
`qualifier`. Las restantes familias bibliográficas reúnen las variantes del
campo DC correspondiente. `descriptions` conserva resúmenes, notas y cualquier
otra descripción; `qualifier` distingue `abstract`, `tableofcontents`, etc.
Las fechas se conservan como strings, distinguidas por su calificador.

Los campos de extensión (DCTERMS, LOM, DSpace, OAIre, `dc.audience` y `dc.thesis`)
se conservan en `additionalMetadata` con `path` para identificar su ruta exacta.
Allí se omiten `schema` y `qualifier`, pues ambos están contenidos en `path`:

```json
{
  "additionalMetadata": [
    {"value": "Publication", "path": "dspace.entity.type"},
    {"value": "Texto adicional", "path": "dcterms.abstract.none"}
  ]
}
```

`others` y `repository` conservan sus campos técnicos como arrays dentro de cada
objeto. `bundles` conserva los contenedores vacíos observados. Los valores vacíos,
espacios y duplicados permanecen intactos. No se inventan idiomas ni se recortan textos.

## Extensiones del mapeador

`forEach` admite un selector o un array de selectores. El array selecciona su
unión en el orden del documento XML. Un elemento que coincide con más de un
selector solo se procesa una vez. Un array vacío o con selectores repetidos es
un error de configuración.

`includeContext` permite incluir `schema`, `qualifier` y `path` a partir del
elemento XOAI original, antes de separar sus ocurrencias. `schema` es el primer
componente del camino; `qualifier` es el resto a partir del tercer componente,
omitiendo `none`; `path` conserva el camino completo. El perfil común usa únicamente `qualifier` en familias bibliográficas y `path`
en extensiones; la capacidad genérica de incluir `schema` sigue disponible para
otros perfiles. Los campos de contexto no pueden colisionar con
los campos declarados en `fields`. Se mantiene `occurrenceStart: "value"` para
asociar a cada texto los campos que le siguen.

```text
export-mapping-validate --mapping /config/exports/common-full-metadata-v1.json
export-metadata --networks UY,AREANDINA --variant processed --format jsonl --mapping /config/exports/common-full-metadata-v1.json --output /exports
```

El perfil cubre la unión de rutas observadas en los snapshots estudiados de
ambas fuentes. La estructura común no garantiza cobertura automática de nuevas
rutas: si aparecen, hay que inventariarlas y versionar el perfil. No se redefine
el significado de calificadores, vocabularios ni idiomas entre repositorios.

## Verificación

El perfil 1.1 generó el paquete `exp-213561cc-7716-4eb4-b14c-972a9d2d3c42` y exportó conjuntamente
22.700 registros de UY y 4.000 de AREANDINA: estado `COMPLETE`, cero errores.
Todos contienen las mismas 19 familias. Se compararon sus 1.006.015 valores
(737.971 de UY y 268.044 de AREANDINA) con los XML usados, conservando texto,
idiomas, orden por ruta/campo, vacíos y repeticiones. Se comprobaron además los
localizadores SQLite y los hashes de los archivos del paquete.

Los ejemplos [UY](examples/common-uy.json) y
[AREANDINA](examples/common-areandina.json) cumplen el mismo esquema JSON.
Las 25 pruebas del exportador pasan; incluyen selectores combinados, orden del
XML, deduplicación de coincidencias entre selectores, calificadores, esquemas,
asociación de idioma, roles de autor/asesor y rechazo de configuraciones inválidas.

Se comprobó la ausencia de `schema` en todas las ocurrencias, y que las extensiones
conservan únicamente `path` como contexto. El esquema JSON rechaza tanto `schema`
como `qualifier` en extensiones. Los ejemplos corresponden al perfil 1.1.
