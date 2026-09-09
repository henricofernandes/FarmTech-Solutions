# -*- coding: utf-8 -*-
"""
Lançador usado só para gerar o executável do FarmTech Solutions.

Ele existe porque o farmtech.py resolve as pastas dados/ e r/ a partir da
localização do próprio arquivo .py, e dentro de um executável empacotado esse
caminho deixa de existir. Aqui as duas pastas são criadas ao lado do .exe na
primeira execução, e as variáveis de caminho do módulo passam a apontar para
elas.

Nenhuma linha do farmtech.py ou do interface.py é alterada: os valores são
reapontados de fora, antes de a janela abrir.
"""

import shutil
import sys
import traceback
from pathlib import Path


def pasta_do_pacote():
    """Pasta temporária onde o PyInstaller extraiu o que foi embutido no .exe."""
    interno = getattr(sys, "_MEIPASS", None)
    return Path(interno) if interno else Path(__file__).resolve().parent


def pasta_de_trabalho():
    """
    Onde ficam os dados e os scripts em R.

    Fica ao lado do .exe, para a pessoa encontrar os arquivos sem procurar. Se
    aquele lugar não aceitar escrita (um pendrive protegido, por exemplo), cai
    para uma pasta na área do usuário.
    """
    if getattr(sys, "frozen", False):
        candidata = Path(sys.executable).resolve().parent
    else:
        candidata = Path(__file__).resolve().parent

    teste = candidata / ".teste-de-escrita"
    try:
        teste.touch()
        teste.unlink()
        return candidata
    except OSError:
        alternativa = Path.home() / "FarmTech-Solutions"
        alternativa.mkdir(parents=True, exist_ok=True)
        return alternativa


def preparar(base):
    """
    Põe no lugar os arquivos que vieram dentro do .exe.

    Os scripts em R precisam existir como arquivos de verdade no disco, porque
    quem os executa é o Rscript. E eles descobrem a pasta do projeto subindo
    dois níveis a partir de si mesmos, então a dupla dados/ e r/ tem que ficar
    lado a lado, igual ao repositório.

    Arquivo que já existe não é sobrescrito, para não apagar os cadastros de
    quem já usou o programa antes.
    """
    pacote = pasta_do_pacote()

    for destino_nome, origem_nome in (("dados", "dados_padrao"), ("r", "r_padrao")):
        destino = base / destino_nome
        destino.mkdir(parents=True, exist_ok=True)

        origem = pacote / origem_nome
        if not origem.is_dir():
            continue

        for arquivo in origem.iterdir():
            if arquivo.is_file() and not (destino / arquivo.name).exists():
                shutil.copy2(arquivo, destino / arquivo.name)


def main():
    base = pasta_de_trabalho()
    preparar(base)

    import farmtech

    farmtech.PASTA_DADOS = base / "dados"
    farmtech.ARQUIVO_CSV = farmtech.PASTA_DADOS / "dados_agricultura.csv"
    farmtech.ARQUIVO_CIDADES = farmtech.PASTA_DADOS / "cidades.csv"
    farmtech.PASTA_R = base / "r"
    farmtech.SCRIPT_CLIMA = farmtech.PASTA_R / "clima.R"
    farmtech.SCRIPT_ESTATISTICAS = farmtech.PASTA_R / "estatisticas.R"

    import interface

    interface.main()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # O executável é gerado sem console, então um erro morreria calado.
        detalhe = traceback.format_exc()
        try:
            import tkinter as tk
            from tkinter import messagebox

            raiz = tk.Tk()
            raiz.withdraw()
            messagebox.showerror("FarmTech Solutions", detalhe)
            raiz.destroy()
        except Exception:
            sys.stderr.write(detalhe)
        sys.exit(1)
