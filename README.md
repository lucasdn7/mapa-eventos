# mapa-eventos

Mapa interativo dos eventos de veículos antigos em Santa Catarina em 2026.

## O que foi criado

- `requirements-geospatial.txt` declara o GeoPandas e dependências geoespaciais do projeto.
- `data/events_sc_2026.csv` contém a lista estruturada dos 23 eventos informados, com coordenadas do município/cidade.
- `data/santa_catarina_boundary.geojson` mantém apenas o contorno de Santa Catarina para o mapa estático.
- `scripts/prepare_santa_catarina_boundary.py` filtra uma malha geográfica maior e salva somente Santa Catarina usando GeoPandas.
- `scripts/generate_interactive_map.py` gera o HTML interativo em `santa_catarina_eventos_2026.html` e mantém uma cópia em `public/santa_catarina_eventos_2026.html`.

## Instalação

```bash
python -m pip install -r requirements-geospatial.txt
```

> Observação: no ambiente atual, a instalação via PyPI foi bloqueada por erro de túnel `403 Forbidden`. O repositório já está preparado com as dependências declaradas para instalação em um ambiente com acesso liberado.

## Selecionar somente Santa Catarina com GeoPandas

Quando você tiver uma malha oficial do Brasil/UFs em GeoJSON, Shapefile ou GeoPackage, rode:

```bash
python scripts/prepare_santa_catarina_boundary.py caminho/para/malha_brasil.geojson data/santa_catarina_boundary.geojson
```

O script procura códigos e nomes comuns da UF, como `42`, `4200000`, `SC` e `Santa Catarina`, e salva o resultado em EPSG:4326.


## Deploy no Vercel

Este projeto é um site estático: o Vercel deve publicar `index.html` e `santa_catarina_eventos_2026.html`, sem tentar criar uma função Python.

A configuração está em `vercel.json` e desativa instalação/build Python no deploy. As dependências geoespaciais ficam em `requirements-geospatial.txt`, fora do nome padrão `requirements.txt`, para o Vercel não detectar o projeto como runtime Python.

Depois do deploy, abra a URL pública gerada pelo Vercel. A raiz (`/`) redireciona para o mapa interativo.

## Ver o mapa sem Python e sem servidor local

Abra o arquivo `index.html` na raiz do repositório com duplo clique. Ele redireciona automaticamente para o mapa interativo gerado em `santa_catarina_eventos_2026.html`.

Se o projeto estiver publicado no Vercel, o link público será a URL do deploy apontando para `index.html`.

## Gerar o mapa interativo

```bash
python scripts/generate_interactive_map.py
```

Abra o arquivo gerado:

```text
santa_catarina_eventos_2026.html
```

## Notas dos dados

A lista fornecida informa cidade, data e contato, mas não informa endereço específico de venue. Por isso, os marcadores usam as coordenadas centrais dos municípios/cidades. A rota começa no primeiro evento informado, Florianópolis, e conecta sempre o evento geograficamente mais próximo ainda não visitado, até chegar aos eventos mais distantes.
