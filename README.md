# FarmTech Solutions — Agricultura Digital

Projeto da fase 1 da FIAP. Uma aplicação de terminal em **Python** cadastra talhões de
soja e milho, calcula a área plantada e o insumo necessário, e grava tudo em CSV. Duas
aplicações em **R** consomem esses dados: uma calcula estatísticas e a outra consulta
uma API meteorológica pública.

## Estrutura

```
FarmTech-Solutions/
├── python/farmtech.py          aplicação principal (menu, vetores, cálculos, CSV)
├── r/estatisticas.R            média e desvio padrão a partir do CSV
├── r/clima.R                   clima em tempo real pela API Open-Meteo
├── dados/dados_agricultura.csv registros gerados pelo Python
├── dados/cidades.csv           cidade de cada talhão (arquivo auxiliar)
├── docs/                       documentação detalhada de cada parte
├── formacao-social/            resumo do artigo da Embrapa
└── video/                      link do vídeo de demonstração
```

## Pré-requisitos

| Ferramenta | Uso | Observação |
|---|---|---|
| Python 3 | aplicação principal | só biblioteca padrão (`csv`, `pathlib`, `subprocess`) |
| R | estatísticas e clima | necessário para as opções de análise |
| Pacote `jsonlite` | ler o JSON da API | instale com `install.packages("jsonlite")` |

## Como executar

Abra o terminal na pasta do projeto.

```powershell
python python/farmtech.py     # aplicação principal
Rscript r/estatisticas.R      # média e desvio padrão dos talhões
Rscript r/clima.R             # clima do local padrão (Sorriso - MT)
Rscript r/clima.R Rio Verde   # clima de outra cidade
```

Se o terminal responder que `Rscript` não é reconhecido, o R não está no PATH. Use o
caminho completo, por exemplo `& "C:\Program Files\R\R-4.6.1\bin\Rscript.exe" r/clima.R`.

Os caminhos são resolvidos a partir da localização dos próprios scripts, então os
comandos funcionam mesmo se você estiver em outra pasta.

## Como as três partes se conversam

O CSV é o único ponto de contato entre Python e R. Não há banco de dados nem API entre
eles: o Python escreve o arquivo, o R lê.

```
Python (vetores) ──> dados/dados_agricultura.csv ──> R (estatísticas)
                                                     R (clima) ──> API Open-Meteo
```

A cada cadastro, atualização ou deleção, o Python reescreve o CSV inteiro a partir dos
vetores. É o que garante que o arquivo seja sempre um espelho exato do que está na
memória, inclusive depois de uma deleção que muda as posições de todos os registros.

O clima é o caminho inverso: o menu do Python chama o `Rscript` como um programa
externo e passa a cidade como argumento. Quem acessa a internet é sempre o R.

## Documentação detalhada

| Documento | Conteúdo |
|---|---|
| [docs/python.md](docs/python.md) | menu, vetores, cálculos, validações e persistência |
| [docs/r.md](docs/r.md) | os dois scripts em R, estatísticas e API meteorológica |
| [docs/dados.md](docs/dados.md) | formato dos arquivos CSV e regras dos dados |

## Situação dos requisitos

Atendidos: duas culturas (soja e milho), cálculo de área, manejo de insumos, dados em
vetores, menu com entrada, saída, atualização por posição, deleção e sair, rotinas de
loop e decisão, estatísticas em R, e o "ir além" com a API meteorológica pelo R.

Pendentes: versionamento no GitHub, o resumo de Formação Social e o vídeo de
demonstração. Há também um ponto em aberto no cálculo de área — as duas culturas usam
a mesma figura geométrica (quadrado), e o enunciado pode estar pedindo uma figura
diferente para cada cultura.
