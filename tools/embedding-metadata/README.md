# Preparar títulos y resúmenes para embeddings

Use [prepare-embedding-metadata](../../docs/EMBEDDING_METADATA.md) for the Java-to-Python workflow and the combined input contract. The rest of this guide describes the original training and evaluation pilot.

Este piloto lee paquetes JSONL completos de los perfiles `classification-embeddings` 2.0 y `bibliographic-roles` 1.0. Clasifica cada ocurrencia con fastText en CPU. La entrada mínima comprende `manifest.json`, `mapping.json` y las partes JSONL correspondientes. Comprueba el SHA-256 de las partes y reconcilia las filas con el manifiesto.

## Ejecución

Probado con Python 3.12. La descarga del modelo de idioma se realiza una sola vez. El modelo `lid.176.ftz` de fastText usa la licencia Creative Commons Attribution-ShareAlike 3.0. [Documentación y atribución del modelo](https://fasttext.cc/docs/en/language-identification.html)

```sh
python3.12 -m venv .venv
.venv/bin/pip install numpy==1.26.4 fasttext==0.9.3
curl -fL https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.ftz -o lid.176.ftz

.venv/bin/python tools/embedding-metadata/train.py /exports/exp-AR /exports/exp-UY --output modelos-piloto
.venv/bin/python tools/embedding-metadata/postprocess.py /exports/exp-AR /exports/exp-UY \
  --language-model lid.176.ftz --role-model modelos-piloto/role.bin --output resultados
```

Para otra exportación se pueden reutilizar los dos modelos. Cada ejecución entrega un JSONL comprimido y un resumen por exportación. El resumen registra conteos de ocurrencias, tiempos locales, umbrales y hashes del mapeo de entrada, los modelos, el programa y el archivo entregado.

## Criterio de cobertura

El título es el único contenido bibliográfico imprescindible. El resumen del posproceso cuenta cada registro una sola vez en `counts["records.title"]`: `present` si al menos un título contiene texto tras quitar los espacios exteriores, o `missing` en caso contrario. Un título corto o de idioma indeterminado cumple el criterio. Los resúmenes, las afiliaciones, los financiadores, los tipos documentales y los idiomas son opcionales. Los registros sin título se conservan para su revisión mediante el identificador del catálogo.

## Qué contiene cada fila

Se conservan `exportId`, `network`, `catalogId`, `identifier` y `metadataHash`. Los arrays `titles` y `descriptions` mantienen el orden, los valores y los atributos de origen. Cada ocurrencia añade `detectedLanguage` con `es`, `en`, `pt`, `fr`, `other` o `und`. Para `other` también se conserva el código concreto. El idioma requiere al menos tres palabras con letras, puntuación de 0,75 y ventaja de 0,20 sobre la segunda opción.

Cada descripción conserva la decisión inicial en `decision`, con `abstract`, `non_abstract` o `uncertain`. El modelo exige una puntuación de 0,90 para aceptar cualquiera de las dos clases y al menos 12 palabras para aceptar un resumen. Son umbrales experimentales. El modelo evalúa el texto completo como una unidad y una traducción dentro de la misma ocurrencia puede pasar inadvertida.

Si el registro ya tiene uno o más resúmenes clasificados, se usan todos. Si carece de resumen en cualquier idioma, se elige una sola descripción de rol `uncertain` con texto. Entre varias se toma la de más caracteres tras la limpieza y, en caso de empate, la primera en el orden de origen. La ocurrencia seleccionada recibe `role: "abstract"` y `abstractSelection: "uncertain_fallback"`, conserva `decision: "uncertain"`, su literal y su índice. El resumen de ejecución cuenta los registros en `counts["records.abstract"]` como `classified`, `uncertain_fallback` o `missing`.

`embeddingGroups` agrupa dentro del registro los índices desde cero de títulos y resúmenes seleccionados con idioma determinado. Por ejemplo, `{"pt":{"titles":[],"descriptions":[0]}}` permite usar el primer resumen portugués aunque falte un título en ese idioma. Un resumen seleccionado de idioma `und` se consulta en `descriptions`.

## Entrenamiento y alcance de las métricas

El entrenamiento usa etiquetas débiles. Toma hasta 2.000 registros por parte. Obtiene ejemplos positivos de las marcas de resumen y ejemplos negativos de filiaciones, procedencia, patrocinio, índice y URI. Conserva hasta 2.000 textos distintos por autoridad OAI y clase, elimina conflictos dentro de cada partición y equilibra las clases de entrenamiento. La prueba reserva un subconjunto de autoridades OAI por hash y excluye coincidencias exactas con el conjunto de entrenamiento muestreado. La autoridad OAI es una aproximación al repositorio.

Los dos modelos fastText evalúan el contenido. Después se aplican las reglas de función bibliográfica descritas a continuación. La limpieza retira las marcas iniciales explícitas `Fil:`, `Resumen:`, `Abstract:` y `Resumo:`. El modelo de función textual aprende palabras y pares de palabras. La evaluación en `training.json` mide acuerdo con etiquetas débiles de los repositorios reservados. La prosa narrativa, las introducciones, los textos breves y los OCR requieren revisión independiente.


## Afiliaciones, financiadores y tipos documentales

Para incluir los campos declarados de la fuente, usar [el perfil bibliográfico](../../config/exports/bibliographic-roles-v1.json) con `export-metadata --mapping`. Conserva los selectores amplios para títulos, descripciones y palabras clave e incorpora los valores de `dc.type`, `oaire.funderName` / `oaire.fundername` y `dc.contributor.affiliation`, incluidos sus descendientes. Los paquetes anteriores permiten analizar el texto disponible.

- Cada descripción conserva la decisión gruesa y añade `role` con `abstract`, `affiliation`, `funding`, `document_type`, `other` o `uncertain`. El modelo de resúmenes se complementa con señales textuales y, si están presentes, calificadores específicos. Un resumen puede mencionar financiación y seguir siendo elegible para embeddings.
- El array `affiliations` apunta al texto declarado o a la descripción institucional. El campo opcional `literal` conserva la institución o cadena institucional reconocida. Un valor con autor y varias instituciones puede conservarlas juntas.
- El array `funders` contiene nombres literales y su evidencia. `declared` procede del campo explícito de financiador, `funding_statement` de una declaración de apoyo y `sponsorship_field` de una descripción calificada. `agency_mention` identifica una mención ambigua. Para contar financiadores con evidencia de financiación, excluir esta última clase. Los literales y las siglas se conservan tal como aparecen, sin conciliación de entidades.
- `documentTypes` recoge tipos reconocidos, por ejemplo `article`, `masterThesis`, `doctoralThesis` o `bookPart`. Las referencias a `types` señalan valores declarados. Cuando falta un tipo declarado reconocible se pueden usar notas de grado explícitas, con referencia a `descriptions`. Un array vacío significa que faltó evidencia reconocible. Las declaraciones múltiples se conservan. El piloto retiene todos los valores de `types`, incluidos URI desconocidos y valores de versión, para inspección.
- Cada referencia identifica el array de origen mediante `field` y la posición desde cero mediante `index`. El registro conserva el identificador de exportación, el identificador del catálogo y el hash de metadata.
- Las métricas incluyen el hash de las reglas y del modelo aprendido. Los umbrales de fastText se aplican a la predicción estadística. Las reglas, los calificadores y los tipos declarados aportan evidencia separada; una mención de universidad o de agencia por sí sola puede ser ambigua.
