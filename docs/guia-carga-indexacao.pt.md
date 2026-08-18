# Guia de Carga e Indexacao de Entidades

Este guia descreve um fluxo simples de ponta a ponta para compilar a
plataforma, configurar o `lareferencia-shell`, carregar o modelo de entidades e
os dados, executar a consolidacao/deduplicacao, e indexar as entidades finais.

## 1. Fazer o Build da Plataforma

Execute o build a partir da raiz do repositorio pai,
`lareferencia-platform`.

Escolha o profile do ambiente:

```bash
./build.sh ibict
```

Outros profiles comuns:

```bash
./build.sh lareferencia
./build.sh rcaap
./build.sh lite
```

Os profiles `ibict`, `lareferencia` e `rcaap` incluem
`lareferencia-shell-entity-plugin`, que adiciona os comandos de carga e
indexacao de entidades.

## 2. Configurar o lareferencia-shell

Edite:

```text
lareferencia-platform/lareferencia-shell/config/application.properties
```

Aponte o shell para o banco PostgreSQL onde os dados serao carregados:

```properties
spring.datasource.url=jdbc:postgresql://localhost:5432/nome_do_banco
```

Substitua `nome_do_banco` pelo nome real do banco.

Confira tambem o restante da configuracao do ambiente:

- `spring.datasource.username`
- `spring.datasource.password`
- Propriedades de Elasticsearch/OpenSearch, quando a indexacao for feita no
  Elasticsearch
- Propriedades de metadata, entidades ou contexto custom exigidas pelo profile
  selecionado

## 3. Baixar ou Preparar o Modelo de Entidades

Por exemplo, para usar o modelo BrCris/Ibict do GitHub:

```bash
git clone https://github.com/brcris-ibict/brcris-model.git
```

Identifique o arquivo XML do modelo dentro do repositorio clonado, por exemplo:

```text
/path/to/brcris-model/modelo_brcris.xml
```

Prepare tambem o diretorio ou arquivo XML com os dados de entidades:

```text
/path/to/entity-data
```

`load_data` pode receber um unico arquivo XML ou um diretorio. Quando recebe um
diretorio, carrega recursivamente todos os arquivos `.xml`.

## 4. Executar o Shell

A partir do diretorio `lareferencia-shell`:

```bash
cd lareferencia-shell
./lareferencia-shell.jar
```

Se precisar usar outro diretorio de configuracao:

```bash
JAVA_OPTS="-Dapp.config.dir=/path/to/config" ./lareferencia-shell.jar
```

## 5. Preparar o Banco de Dados

Dentro do shell, execute:

```bash
database_migrate
```

Se a intencao for recriar um banco vazio, limpe o banco primeiro:

```bash
database_clean --confirm true
database_migrate
```

Aviso: `database_clean --confirm true` remove os objetos e dados do banco
gerenciados pelo Flyway. Use somente quando voce realmente quiser reiniciar o
banco.

## 6. Carregar o Modelo de Entidades

Carregue o XML do metamodelo de entidades:

```bash
load_model /path/to/modelo.xml
```

## 7. Carregar os Dados de Entidades

Passo recomendado: execute primeiro um dry run para validar o caminho e os XMLs
sem persistir dados.

```bash
load_data --path /path/to/entity-data --dryRun true
```

Depois execute a carga real:

```bash
load_data --path /path/to/entity-data
```

Quando o `load_data` termina, os dados ficam carregados em estruturas fonte ou
dirty. Eles ainda precisam ser consolidados antes da indexacao.

## 8. Consolidar Entidades Dirty

Execute o processo de merge:

```bash
merge_dirty_entities
```

Este passo consolida os dados carregados nas tabelas finais de entidades e
relacoes usadas pela indexacao.

## 9. Indexar Entidades

Liste os indexadores disponiveis na configuracao atual:

```bash
list-indexers
```

Execute a indexacao com o arquivo de configuracao, tipo de entidade, tamanho de
pagina e indexador desejados.

Exemplo:

```bash
index-entities \
  --configFileFullPath /path/to/entity-indexing-config.xml \
  --indexerName entityIndexerElastic \
  --entityTypeName Person \
  --pageSize 1000
```

Filtros opcionais uteis:

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

Quando `provenance` é informado, `lastUpdate` é ignorado.

## 10. Checklist Rapido

- A plataforma foi compilada com um profile que inclui o plugin de entidades.
- `spring.datasource.url` aponta para o banco PostgreSQL correto.
- As migracoes do banco foram executadas.
- O modelo de entidades foi carregado com `load_model`.
- Os dados foram carregados com `load_data --path`.
- `merge_dirty_entities` terminou corretamente.
- `list-indexers` mostra o indexador esperado.
- `index-entities` terminou e gerou o relatorio de indexacao.
