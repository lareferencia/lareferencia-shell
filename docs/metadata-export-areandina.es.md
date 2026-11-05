# Exportación completa de AREANDINA

> Análisis histórico: el perfil específico usado para estos ejemplos se retiró.
> Para nuevas exportaciones usar `common-full-metadata-v1.json`; su estructura
> se describe en [el contrato común](metadata-export-common.es.md).

El perfil específico histórico se definió inventariando los XML procesados de 4.000 registros de AREANDINA.
Cubre 149 rutas con campos: DC, DCTERMS, DSpace, LOM, OAIre, `others` y
`repository`. También conserva el contenedor `bundles` vacío.

A diferencia de UY, esta fuente contiene calificadores bibliográficos y campos
`language` asociados a las ocurrencias. Para distinguir todos los calificadores,
las claves de `data` son rutas XOAI exactas, por ejemplo:

```json
{
  "dc.title.none": [{"value": "Título", "language": "spa"}],
  "dc.contributor.author": [{"value": "Nombre del autor"}],
  "dc.description.abstract": [{"value": "Resumen", "language": "spa"}],
  "dc.subject.unesco": [{"value": "Educación"}]
}
```

Cada campo `value` inicia una ocurrencia y conserva los campos siguientes hasta
el próximo `value`. No se deduplican valores ni se recortan textos o espacios.
Se omite `language` cuando no existe. Los bloques técnicos `others` y `repository`
se agrupan por elemento, con arrays para sus campos. Las rutas ausentes producen
arrays vacíos. El campo `dc.language.iso` describe el idioma del recurso y no se
propaga a las demás ocurrencias.

```text
export-metadata --network AREANDINA --variant processed --format jsonl --mapping /config/exports/common-full-metadata-v1.json --output /exports
```

Este perfil cubre las rutas observadas en este conjunto, no cualquier XOAI futuro.
Si aparecen campos o calificadores nuevos habrá que inventariarlos y versionar
el perfil. El XML exacto sigue referenciado por `metadataHash` y el almacén.

La prueba generó el paquete `exp-6a91ee8e-e7af-44da-a04e-4fac6fb62ab5` en estado
`COMPLETE`: 4.000 registros, cero errores, un archivo JSONL GZIP. Se compararon
los 268.044 valores de campos contra sus XML seleccionados por `metadataHash`,
incluidos idiomas, repeticiones y campos vacíos. También se verificaron los
localizadores del índice SQLite, los checksums y los títulos bilingües del
registro `oai:digitk.areandina.edu.co:areandina/4305`.
