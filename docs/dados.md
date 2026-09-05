# Dados do projeto

Os dois arquivos da pasta `dados/` são gerados e mantidos automaticamente pelo Python.
Não é preciso preencher nada à mão.

## `dados_agricultura.csv`

Arquivo principal, lido pelo `r/estatisticas.R`. Tem exatamente as sete colunas
previstas no projeto:

```
cultura,manejo,lado,ruas,dose,area,total_insumo_litros
Soja,Fosfato líquido,100,20,500,10000,1000
Milho,Adubo nitrogenado líquido,150,30,400,22500,1800
```

| Coluna | Significado | Unidade |
|---|---|---|
| `cultura` | Soja ou Milho | — |
| `manejo` | insumo definido pela cultura | — |
| `lado` | lado do talhão quadrado | metros |
| `ruas` | quantidade de ruas da lavoura | inteiro |
| `dose` | dose do insumo aplicada | mL por metro |
| `area` | `lado × lado` | m² |
| `total_insumo_litros` | `lado × ruas × dose ÷ 1000` | litros |

As duas últimas colunas são calculadas pelo Python no momento da gravação, a partir das
anteriores. O arquivo é salvo em UTF-8, por causa dos acentos em "Fosfato líquido".

## `cidades.csv`

Arquivo auxiliar com a cidade de cada talhão, uma por linha, na mesma ordem do arquivo
principal:

```
cidade
Sorriso - MT
Rio de Janeiro
```

Ele existe separado porque o arquivo principal precisa manter exatamente as sete
colunas exigidas pelo projeto, e não caberia uma coluna de cidade ali. Os dois são
reescritos juntos pela mesma função, então cadastro, atualização e deleção mantêm as
linhas alinhadas.

Se algum dia os dois ficarem com quantidades diferentes de linhas — por edição manual,
por exemplo — o programa não arrisca associar a cidade errada ao talhão: ele carrega os
dados normalmente e marca todas as cidades como "não informada".

Registros criados antes de a cidade existir no projeto também aparecem como "não
informada", porque de fato não há como saber onde foram cadastrados.

## Regras dos dados

A cultura define o manejo automaticamente, sem o usuário escolher:

| Cultura | Manejo |
|---|---|
| Soja | Fosfato líquido |
| Milho | Adubo nitrogenado líquido |

Lado, ruas e dose precisam ser maiores que zero, e a quantidade de ruas precisa ser um
número inteiro. Vírgula e ponto são aceitos como separador decimal na digitação.

## Sincronia com os vetores

O CSV é sempre um espelho exato dos vetores em memória. A cada cadastro, atualização ou
deleção o arquivo é reescrito por completo, em vez de receber uma alteração pontual.
Isso resolve o caso mais delicado, a deleção, em que todas as posições seguintes mudam.

Ao abrir o programa, o caminho inverso acontece: o CSV é carregado de volta para os
vetores, então os dados de execuções anteriores não se perdem.
