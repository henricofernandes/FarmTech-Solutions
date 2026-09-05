# -*- coding: utf-8 -*-
"""
FarmTech Solutions - Agricultura Digital
Cálculo de área e de insumos de talhões quadrados.

Soja  -> Fosfato líquido
Milho -> Adubo nitrogenado líquido

Os registros ficam em vetores na memória e são gravados em
dados/dados_agricultura.csv, que é lido pela aplicação em R.
"""

import csv
import shutil
import subprocess
import sys
from pathlib import Path

# Vetores paralelos: a mesma posição em todas as listas é o mesmo talhão.
culturas = []   # Soja ou Milho
manejos = []    # insumo da cultura
lados = []      # lado do talhão (metros)
ruas = []       # quantidade de ruas
doses = []      # dose do insumo (mL por metro)
cidades = []    # cidade em que o talhão foi cadastrado

# Caminho relativo ao arquivo .py, então funciona de qualquer pasta de execução.
PASTA_DADOS = Path(__file__).resolve().parent.parent / "dados"
ARQUIVO_CSV = PASTA_DADOS / "dados_agricultura.csv"
COLUNAS_CSV = ["cultura", "manejo", "lado", "ruas", "dose", "area", "total_insumo_litros"]

# A cidade fica num arquivo à parte para o CSV principal manter exatamente as
# colunas previstas no projeto. As duas listas seguem sempre a mesma ordem.
ARQUIVO_CIDADES = PASTA_DADOS / "cidades.csv"
CIDADE_DESCONHECIDA = "não informada"

# As análises são feitas em R; o Python apenas chama os scripts quando precisa.
PASTA_R = Path(__file__).resolve().parent.parent / "r"
SCRIPT_CLIMA = PASTA_R / "clima.R"
SCRIPT_ESTATISTICAS = PASTA_R / "estatisticas.R"
CIDADE_PADRAO = "Sorriso - MT"  # o mesmo local padrão definido no clima.R

# Vale para os próximos cadastros e volta ao padrão sempre que o programa abre.
cidade_atual = CIDADE_PADRAO


def calcular_area(lado):
    """Área do talhão quadrado, em m²."""
    return lado * lado


def calcular_insumo(lado, quantidade_ruas, dose):
    """Total de insumo em litros (o cálculo em mL é dividido por 1000)."""
    return lado * quantidade_ruas * dose / 1000


def sem_zero_a_toa(valor):
    """Grava 100 no lugar de 100.0, mas mantém as casas decimais quando existem."""
    return int(valor) if valor == int(valor) else valor


def carregar_cidades(quantidade):
    """Lê as cidades salvas. Devolve 'não informada' quando não dá para usar."""
    if not ARQUIVO_CIDADES.exists():
        return [CIDADE_DESCONHECIDA] * quantidade

    with open(ARQUIVO_CIDADES, newline="", encoding="utf-8") as arquivo:
        salvas = [linha["cidade"] for linha in csv.DictReader(arquivo) if "cidade" in linha]

    # Se os dois arquivos estiverem fora de sincronia, o vínculo por posição
    # não é confiável, então é melhor não afirmar a cidade de ninguém.
    if len(salvas) != quantidade:
        return [CIDADE_DESCONHECIDA] * quantidade

    return salvas


def carregar_csv():
    """Coloca nos vetores o que já estava salvo no CSV, ao abrir o programa."""
    if not ARQUIVO_CSV.exists():
        return

    with open(ARQUIVO_CSV, newline="", encoding="utf-8") as arquivo:
        registros = list(csv.DictReader(arquivo))

    try:
        for linha in registros:
            culturas.append(linha["cultura"])
            manejos.append(linha["manejo"])
            lados.append(float(linha["lado"]))
            ruas.append(int(linha["ruas"]))
            doses.append(float(linha["dose"]))
    except (KeyError, TypeError, ValueError):
        # Vetores pela metade seriam pior que vetores vazios: começa do zero.
        for vetor in (culturas, manejos, lados, ruas, doses, cidades):
            vetor.clear()
        print("Aviso: o CSV está fora do formato esperado e não foi carregado.")
        return

    cidades.extend(carregar_cidades(len(culturas)))


def salvar_csv():
    """Reescreve o CSV inteiro a partir dos vetores, mantendo os dois iguais."""
    PASTA_DADOS.mkdir(parents=True, exist_ok=True)

    with open(ARQUIVO_CSV, "w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.writer(arquivo)
        escritor.writerow(COLUNAS_CSV)

        for posicao in range(len(culturas)):
            lado = lados[posicao]
            escritor.writerow([
                culturas[posicao],
                manejos[posicao],
                sem_zero_a_toa(lado),
                ruas[posicao],
                sem_zero_a_toa(doses[posicao]),
                sem_zero_a_toa(calcular_area(lado)),
                sem_zero_a_toa(calcular_insumo(lado, ruas[posicao], doses[posicao])),
            ])

    with open(ARQUIVO_CIDADES, "w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.writer(arquivo)
        escritor.writerow(["cidade"])
        for cidade in cidades:
            escritor.writerow([cidade])


def ler_numero(mensagem, inteiro=False):
    """Lê um número maior que zero, repetindo a pergunta enquanto for inválido."""
    while True:
        texto = input(mensagem).replace(",", ".")
        try:
            valor = int(texto) if inteiro else float(texto)
        except ValueError:
            print("Valor inválido. Digite um número.")
            continue

        if valor <= 0:
            print("O valor deve ser maior que zero.")
            continue

        return valor


def ler_cultura():
    """Pergunta a cultura e devolve a cultura com o manejo correspondente."""
    while True:
        print("\n1 - Soja")
        print("2 - Milho")
        opcao = input("Escolha a cultura: ").strip()

        if opcao == "1":
            return "Soja", "Fosfato líquido"
        if opcao == "2":
            return "Milho", "Adubo nitrogenado líquido"
        print("Opção inválida. Escolha 1 ou 2.")


def ler_talhao():
    """Lê todos os dados de um talhão e devolve na ordem dos vetores."""
    cultura, manejo = ler_cultura()
    lado = ler_numero("Lado do talhão (metros): ")
    quantidade_ruas = ler_numero("Quantidade de ruas: ", inteiro=True)
    dose = ler_numero("Dose do insumo (mL por metro): ")
    return cultura, manejo, lado, quantidade_ruas, dose


def ler_posicao(mensagem):
    """Lê a posição de um registro. Devolve None quando não existe."""
    if not culturas:
        print("Nenhum registro cadastrado.")
        return None

    try:
        posicao = int(input(mensagem))
    except ValueError:
        print("Posição inválida. Digite um número inteiro.")
        return None

    if posicao < 0 or posicao >= len(culturas):
        print(f"Posição inexistente. Registros válidos: 0 a {len(culturas) - 1}.")
        return None

    return posicao


def mostrar(posicao):
    """Mostra um registro com a área e o total de insumo calculados."""
    lado = lados[posicao]
    area = calcular_area(lado)
    total_litros = calcular_insumo(lado, ruas[posicao], doses[posicao])

    print(f"\nPosição: {posicao}")
    print(f"Cidade: {cidades[posicao]}")
    print(f"Cultura: {culturas[posicao]} ({manejos[posicao]})")
    print(f"Lado do talhão: {lado:.2f} m")
    print(f"Quantidade de ruas: {ruas[posicao]}")
    print(f"Dose: {doses[posicao]:.2f} mL/m")
    print(f"Área: {area:.2f} m²")
    print(f"Total de insumo: {total_litros:.2f} L")


def entrada_dados():
    print("\nENTRADA DE DADOS")
    print(f"Cidade do talhão: {cidade_atual}")
    print("(troque a cidade na opção 5 antes de cadastrar, se precisar)")

    cultura, manejo, lado, quantidade_ruas, dose = ler_talhao()

    cidades.append(cidade_atual)
    culturas.append(cultura)
    manejos.append(manejo)
    lados.append(lado)
    ruas.append(quantidade_ruas)
    doses.append(dose)
    salvar_csv()

    print("\nRegistro cadastrado com sucesso.")
    mostrar(len(culturas) - 1)


def saida_dados():
    print("\nSAÍDA DE DADOS")
    if not culturas:
        print("Nenhum registro cadastrado.")
        return

    for posicao in range(len(culturas)):
        mostrar(posicao)

    mostrar_estatisticas()


def atualizar_dados():
    print("\nATUALIZAÇÃO DE DADOS")
    posicao = ler_posicao("Posição do registro que deseja atualizar: ")
    if posicao is None:
        return

    mostrar(posicao)
    print(f"\nInforme os novos dados (cidade atual: {cidade_atual}):")
    culturas[posicao], manejos[posicao], lados[posicao], ruas[posicao], doses[posicao] = ler_talhao()
    cidades[posicao] = cidade_atual
    salvar_csv()

    print("\nRegistro atualizado com sucesso.")
    mostrar(posicao)


def deletar_dados():
    print("\nDELEÇÃO DE DADOS")
    posicao = ler_posicao("Posição do registro que deseja deletar: ")
    if posicao is None:
        return

    mostrar(posicao)
    if input("\nConfirma a exclusão? (s/n): ").strip().lower() != "s":
        print("Exclusão cancelada.")
        return

    # Remove a mesma posição de todos os vetores para não perder a sincronia.
    culturas.pop(posicao)
    manejos.pop(posicao)
    lados.pop(posicao)
    ruas.pop(posicao)
    doses.pop(posicao)
    cidades.pop(posicao)
    salvar_csv()

    print("Registro removido com sucesso.")


def encontrar_rscript():
    """Procura o Rscript no PATH e, se não achar, nas pastas de instalação do R."""
    caminho = shutil.which("Rscript")
    if caminho:
        return caminho

    for pasta in sorted(Path("C:/Program Files/R").glob("R-*/bin/Rscript.exe"), reverse=True):
        return str(pasta)

    return None


def rodar_script_r(rscript, script, *argumentos):
    """Executa um script em R e devolve o código de saída dele."""
    # Sem o flush, o texto já impresso pelo Python pode sair depois do texto do R.
    sys.stdout.flush()
    return subprocess.run([rscript, str(script), *argumentos]).returncode


def mostrar_estatisticas():
    """Média e desvio padrão dos registros, calculados pelo script em R."""
    rscript = encontrar_rscript()
    if rscript is None:
        print("\nO R não foi encontrado, então as estatísticas não foram calculadas.")
        return

    # O R lê o CSV do disco, que já está atualizado a cada cadastro ou exclusão.
    rodar_script_r(rscript, SCRIPT_ESTATISTICAS)


def escolher_cidade():
    """Devolve a cidade a consultar: a que já está em uso ou uma nova."""
    while True:
        print(f"\n1 - Ver o clima de {cidade_atual} (cidade atual)")
        print("2 - Trocar a cidade")
        opcao = input("Escolha uma opção: ").strip()

        if opcao == "1":
            return cidade_atual

        if opcao == "2":
            cidade = input("Nome da cidade: ").strip()
            if cidade:
                return cidade
            print("Você não digitou nenhuma cidade.")
            continue

        print("Opção inválida. Escolha 1 ou 2.")


def consultar_clima():
    global cidade_atual

    print("\nCLIMA DA REGIÃO")

    rscript = encontrar_rscript()
    if rscript is None:
        print("O R não foi encontrado no computador.")
        print("Instale o R e rode o programa de novo para usar esta opção.")
        return

    escolhida = escolher_cidade()

    argumentos = [] if escolhida == CIDADE_PADRAO else [escolhida]

    # A consulta à API acontece dentro do R, que já imprime tudo no terminal.
    codigo = rodar_script_r(rscript, SCRIPT_CLIMA, *argumentos)

    # A troca só vale se o R encontrou a cidade, para não guardar nome errado.
    if codigo != 0:
        print(f"A cidade continua sendo {cidade_atual}.")
        return

    if escolhida != cidade_atual:
        cidade_atual = escolhida
        print(f"\nCidade alterada para {cidade_atual}.")
        print("Os próximos talhões cadastrados ficarão registrados nela.")


def voltar_ao_menu():
    """Pausa após o resultado. Devolve False quando o usuário quer sair."""
    while True:
        print("\n1 - Voltar ao menu")
        print("2 - Sair do programa")
        opcao = input("Escolha uma opção: ").strip()

        if opcao == "1":
            return True
        if opcao == "2":
            return False
        print("Opção inválida. Escolha 1 ou 2.")


def main():
    carregar_csv()
    if culturas:
        print(f"\n{len(culturas)} registro(s) carregado(s) de {ARQUIVO_CSV.name}.")

    while True:
        print("\n" + "=" * 50)
        print("FARMTECH SOLUTIONS")
        print("=" * 50)
        print("1 - Entrada de dados (Cadastrar talhão quadrado)")
        print("2 - Saída de dados (Listar registros dos vetores)")
        print("3 - Atualização de dados (por posição do vetor)")
        print("4 - Deleção de dados (por posição do vetor)")
        print("5 - Clima da região (consulta a API pelo R)")
        print("6 - Sair do programa")
        opcao = input("Escolha uma opção: ").strip()

        if opcao == "1":
            entrada_dados()
        elif opcao == "2":
            saida_dados()
        elif opcao == "3":
            atualizar_dados()
        elif opcao == "4":
            deletar_dados()
        elif opcao == "5":
            consultar_clima()
        elif opcao == "6":
            break
        else:
            print("\nOpção inválida. Escolha um número de 1 a 6.")
            continue

        # Depois do resultado, o usuário decide se volta ao menu ou encerra.
        if not voltar_ao_menu():
            break

    print("\nPrograma encerrado.")


if __name__ == "__main__":
    main()
