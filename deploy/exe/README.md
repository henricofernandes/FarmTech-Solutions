# Executável para Windows

Gera um `FarmTech.exe` único, de cerca de 10 MB, que qualquer pessoa baixa e abre com
dois cliques — sem instalar Python e sem usar o terminal.

Na primeira execução ele cria as pastas `dados/` e `r/` ao lado de si mesmo e passa a
trabalhar com esses arquivos. Os scripts em R precisam existir em disco de verdade,
porque quem os executa é o `Rscript`, e ficam lado a lado com `dados/` porque é assim
que o `estatisticas.R` encontra o CSV: ele sobe dois níveis a partir do próprio caminho.
Arquivo que já existe não é sobrescrito, então reabrir o programa não apaga cadastros.

O `lancador.py` existe só para isso. Dentro de um executável empacotado, o
`Path(__file__).resolve().parent.parent` do `farmtech.py` deixa de apontar para a pasta
do projeto, então o lançador reaponta as variáveis de caminho antes de a janela abrir.
Nenhuma linha do `farmtech.py` ou do `interface.py` é alterada.

## Gerar

Em um ambiente separado, para não instalar o PyInstaller no Python do sistema:

```powershell
python -m venv .venv-exe
.venv-exe\Scripts\python.exe -m pip install pyinstaller

.venv-exe\Scripts\python.exe -m PyInstaller `
  --noconfirm --onefile --windowed `
  --name FarmTech `
  --add-data "$PWD\dados;dados_padrao" `
  --add-data "$PWD\r;r_padrao" `
  --paths "$PWD\python" `
  --hidden-import farmtech `
  --hidden-import interface `
  deploy\exe\lancador.py
```

O resultado sai em `dist\FarmTech.exe`.

Os caminhos do `--add-data` têm que ser absolutos: o PyInstaller resolve caminho
relativo a partir da pasta do arquivo `.spec`, não da pasta onde o comando rodou.

## Publicar o link de download

1. Abra https://github.com/henricofernandes/FarmTech-Solutions/releases/new
2. Em **Choose a tag**, digite `v1.0` e clique em **Create new tag**.
3. Em **Release title**, escreva `FarmTech Solutions v1.0`.
4. Arraste o `FarmTech.exe` para a área **Attach binaries**.
5. Clique em **Publish release**.

O endereço de download direto passa a ser:

```
https://github.com/henricofernandes/FarmTech-Solutions/releases/latest/download/FarmTech.exe
```

Clicar nesse link baixa o programa na hora, sem abrir página nenhuma. E ele continua
valendo nas próximas versões, porque aponta sempre para a Release mais recente.

## O que avisar para quem for abrir

O executável não tem assinatura digital, então o Windows normalmente mostra o aviso
**"O Windows protegeu o computador"**. É preciso clicar em **Mais informações** e depois
em **Executar assim mesmo**. Alguns antivírus também reclamam de programas empacotados
com PyInstaller — é falso positivo comum nesse tipo de empacotamento, mas vale avisar o
grupo antes para ninguém se assustar.

As análises em R exigem o R instalado na máquina. Sem ele, o cadastro e os cálculos
funcionam normalmente e a interface avisa que não encontrou o R.
