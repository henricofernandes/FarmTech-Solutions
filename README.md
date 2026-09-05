# FarmTech Solutions — Agricultura Digital

Projeto da fase 1 da FIAP. Uma aplicação de terminal em **Python** cadastra talhões de
soja e milho, calcula a área plantada e o insumo necessário, e grava tudo em CSV. Duas
aplicações em **R** consomem esses dados: uma calcula estatísticas e a outra consulta
uma API meteorológica pública.

## Integrantes do grupo

| Nome | RM |
|---|---|
| Henrico Fernandes | PREENCHER_RM |
| PREENCHER_NOME | PREENCHER_RM |
| PREENCHER_NOME | PREENCHER_RM |
| PREENCHER_NOME | PREENCHER_RM |

## Estrutura

```
FarmTech-Solutions/
├── python/farmtech.py               aplicação principal (menu, vetores, cálculos, CSV)
├── r/estatisticas.R                 média e desvio padrão a partir do CSV
├── r/clima.R                        clima em tempo real pela API Open-Meteo
├── dados/dados_agricultura.csv      registros gerados pelo Python
├── dados/cidades.csv                cidade de cada talhão (arquivo auxiliar)
├── docs/                            documentação detalhada de cada parte
├── formacao-social/link-artigo.txt  artigo da Embrapa escolhido e a formatação exigida
└── video/link-video.txt             link do vídeo de demonstração
```

## Pré-requisitos

| Ferramenta | Uso | Observação |
|---|---|---|
| Python 3 | aplicação principal | só biblioteca padrão (`csv`, `pathlib`, `shutil`, `subprocess`, `sys`) |
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
Rodando pelo menu do Python isso não é necessário: ele procura o `Rscript` no PATH e,
se não achar, nas pastas de instalação do R em `C:\Program Files\R`.

Os caminhos são resolvidos a partir da localização dos próprios scripts, então os
comandos funcionam mesmo se você estiver em outra pasta.

## Como as três partes se conversam

O CSV é o único ponto de troca de dados entre Python e R. Não há banco de dados nem API
entre eles: o Python escreve o arquivo, o R lê.

```
Python (vetores) ──> dados/dados_agricultura.csv ──> R (estatísticas)
                                                     R (clima) ──> API Open-Meteo
```

A cada cadastro, atualização ou deleção, o Python reescreve o CSV inteiro a partir dos
vetores. É o que garante que o arquivo seja sempre um espelho exato do que está na
memória, inclusive depois de uma deleção que muda as posições de todos os registros.

Quem dispara as análises é o menu do Python, que chama o `Rscript` como um programa
externo: a opção 2 roda o `estatisticas.R` logo depois de listar os registros, e a
opção 5 roda o `clima.R` passando a cidade como argumento. O cálculo estatístico e o
acesso à internet acontecem sempre do lado do R.

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

Pendentes: publicar no GitHub — o versionamento local já está feito, falta criar o
repositório remoto e enviar os commits; escrever o resumo de Formação Social, já que o
artigo está escolhido em `formacao-social/link-artigo.txt` mas o `resumo-artigo.pdf`
ainda não existe; e gravar o vídeo, cujo link continua em branco no
`video/link-video.txt`. Há também um ponto em aberto no cálculo de área — as duas
culturas usam a mesma figura geométrica (quadrado), e o enunciado pode estar pedindo
uma figura diferente para cada cultura.
