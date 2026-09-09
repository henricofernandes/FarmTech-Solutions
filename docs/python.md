# Aplicação Python — `python/farmtech.py`

Programa de terminal que cadastra talhões quadrados, calcula área e insumo, e mantém
os dados em vetores espelhados num arquivo CSV.

Tudo o que está descrito aqui é a lógica do projeto, e é ela que a interface visual
reaproveita sem duplicar nada. Se você procura a janela, veja
[docs/interface.md](interface.md).

## Menu principal

```
1 - Entrada de dados (Cadastrar talhão quadrado)
2 - Saída de dados (Listar registros dos vetores)
3 - Atualização de dados (por posição do vetor)
4 - Deleção de dados (por posição do vetor)
5 - Clima da região (consulta a API pelo R)
6 - Sair do programa
```

Depois de cada operação o programa pausa e oferece "voltar ao menu" ou "sair", para o
resultado não sumir da tela. O laço principal só termina quando o usuário escolhe sair.

## Os vetores

Seis listas paralelas, onde a mesma posição em todas representa o mesmo talhão:

| Vetor | Conteúdo |
|---|---|
| `culturas` | Soja ou Milho |
| `manejos` | insumo definido automaticamente pela cultura |
| `lados` | lado do talhão, em metros |
| `ruas` | quantidade de ruas |
| `doses` | dose do insumo, em mL por metro |
| `cidades` | cidade em que o talhão foi cadastrado |

Manter listas paralelas exige disciplina: toda operação precisa mexer em todas elas na
mesma posição, senão os dados se desencontram. Por isso a deleção remove a mesma
posição das seis, e o carregamento descarta tudo se encontrar qualquer inconsistência.

## Cálculos

```python
area = lado * lado                              # m²
total_insumo_litros = lado * ruas * dose / 1000 # mL convertidos em litros
```

Os dois valores são derivados dos demais campos, então não ficam guardados em vetores:
são recalculados na hora de exibir e na hora de gravar o CSV. Isso evita ter dado
duplicado que pode ficar desatualizado depois de uma edição.

## Entrada de dados e validações

`ler_numero()` aceita vírgula ou ponto como separador decimal e repete a pergunta
enquanto o valor não for um número maior que zero. A quantidade de ruas usa a mesma
função com `inteiro=True`. A cultura é escolhida por número, e o manejo vem junto: soja
sempre recebe fosfato líquido, milho sempre recebe adubo nitrogenado líquido.

`ler_posicao()` confere se a posição informada existe antes de atualizar ou deletar, e
avisa qual é a faixa válida quando o usuário erra.

## Persistência

`salvar_csv()` é chamada após cadastrar, atualizar e deletar. Ela reescreve os dois
arquivos inteiros a partir dos vetores, em vez de tentar alterar só a linha afetada.

`carregar_csv()` roda na abertura do programa e devolve os registros salvos para os
vetores, então os dados sobrevivem entre execuções. Se o CSV estiver com algum valor
inválido, o programa avisa e começa vazio em vez de quebrar.

## A cidade e a integração com o R

A cidade atual começa em Sorriso - MT toda vez que o programa abre. Ao trocá-la na
opção 5, os talhões cadastrados a partir dali ficam registrados na cidade nova.

A troca só é confirmada se o R encontrar a cidade, para não gravar um nome inexistente.
O Python não acessa a API: ele localiza o `Rscript` (no PATH ou na pasta de instalação
do R), monta o comando e deixa o R imprimir o resultado no terminal.
