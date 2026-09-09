# -*- coding: utf-8 -*-
"""
FarmTech Solutions - Interface visual
Camada gráfica em Tkinter sobre a aplicação de terminal.

Nada é recalculado aqui: os vetores, os cálculos, a gravação do CSV e a
chamada dos scripts em R vêm todos do farmtech.py, que continua funcionando
pelo terminal exatamente como antes.

Uso:
    python python/interface.py
"""

import re
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, scrolledtext, ttk

# A interface fica na mesma pasta do farmtech.py justamente para poder
# importá-lo direto, sem transformar o projeto em pacote.
sys.path.insert(0, str(Path(__file__).resolve().parent))

import farmtech  # noqa: E402

# Mesmo par cultura/manejo definido no ler_cultura() do farmtech.py.
CULTURAS = (
    ("Soja", "Fosfato líquido"),
    ("Milho", "Adubo nitrogenado líquido"),
)

# Paleta: verde escuro como cor principal, verde claro nos estados de destaque
# e neutros frios para o texto, os campos e a tabela.
FUNDO = "#eef2ee"
VERDE = "#1d6b38"
VERDE_ESCURO = "#14512c"
VERDE_MEDIO = "#2f8b4c"
VERDE_CLARO = "#7fbe90"
VERDE_SUAVE = "#e6f0e8"
VERDE_ZEBRA = "#f4f9f5"
VERDE_BORDA = "#c5dbca"
BRANCO = "#ffffff"
TEXTO = "#1f2b22"
TEXTO_SUAVE = "#5d6f62"
CONSOLE_FUNDO = "#12241a"
CONSOLE_TEXTO = "#d5ecda"

FONTE = ("Segoe UI", 10)
FONTE_TITULO = ("Segoe UI", 19, "bold")
FONTE_ROTULO = ("Segoe UI Semibold", 9)
FONTE_SECAO = ("Segoe UI Semibold", 10)

LADO_CANVAS = 190

COLUNAS_TABELA = (
    ("posicao", "Pos.", 45),
    ("cidade", "Cidade", 120),
    ("cultura", "Cultura", 70),
    ("manejo", "Manejo", 175),
    ("lado", "Lado (m)", 80),
    ("ruas", "Ruas", 55),
    ("dose", "Dose (mL/m)", 90),
    ("area", "Área (m²)", 95),
    ("insumo", "Insumo (L)", 90),
)


def manejo_da_cultura(cultura):
    """Devolve o insumo correspondente à cultura escolhida."""
    for nome, manejo in CULTURAS:
        if nome == cultura:
            return manejo
    return ""


def ler_numero(texto, rotulo, inteiro=False):
    """Mesma regra do terminal: número maior que zero, com vírgula ou ponto."""
    texto = texto.strip().replace(",", ".")
    if not texto:
        raise ValueError(f"Informe o campo \"{rotulo}\".")

    try:
        valor = int(texto) if inteiro else float(texto)
    except ValueError:
        tipo = "um número inteiro" if inteiro else "um número"
        raise ValueError(f"{rotulo}: digite {tipo}.")

    if valor <= 0:
        raise ValueError(f"{rotulo}: o valor deve ser maior que zero.")

    return valor


def executar_r(script, *argumentos):
    """Roda um script em R e devolve (código de saída, texto da saída).

    O rodar_script_r() do farmtech.py joga a saída no terminal, que aqui não
    existe, então a interface faz a própria chamada reaproveitando o
    localizador de Rscript e os caminhos dos scripts.
    """
    rscript = farmtech.encontrar_rscript()
    if rscript is None:
        return None, (
            "O R não foi encontrado no computador.\n\n"
            "Instale o R e abra a interface de novo para usar as análises.\n"
        )

    extras = {}
    if hasattr(subprocess, "CREATE_NO_WINDOW"):
        # Evita a janela preta do console piscando na frente da interface.
        extras["creationflags"] = subprocess.CREATE_NO_WINDOW

    try:
        processo = subprocess.run(
            [rscript, str(script), *argumentos],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            **extras,
        )
    except OSError as erro:
        return None, f"Não foi possível executar o Rscript.\n\n{erro}\n"

    return processo.returncode, (processo.stdout or "") + (processo.stderr or "")


def resumo_do_clima(saida):
    """Resumo de uma linha para o cabeçalho, tirado da saída real do clima.R.

    Só entra no resumo o que o R de fato imprimiu. Quando a API não informa um
    dado, o clima.R escreve "não informado pela API" no lugar do número, e aí a
    medida fica de fora em vez de virar um valor inventado.
    """
    medidas = (
        (r"^Local: (.+?)\s*$", "{}"),
        (r"^Temperatura: (-?[\d.]+) °C\s*$", "{} °C"),
        (r"^Umidade relativa: (-?[\d.]+) %\s*$", "umidade {}%"),
    )

    partes = []
    for padrao, formato in medidas:
        achado = re.search(padrao, saida, re.MULTILINE)
        if achado:
            partes.append(formato.format(achado.group(1)))

    return "  ·  ".join(partes)


class Interface(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("FarmTech Solutions - Agricultura Digital")
        self.minsize(1040, 640)
        self.configure(bg=FUNDO)

        self.var_cultura = tk.StringVar(value=CULTURAS[0][0])
        self.var_manejo = tk.StringVar()
        self.var_lado = tk.StringVar()
        self.var_ruas = tk.StringVar()
        self.var_dose = tk.StringVar()
        self.var_area_previa = tk.StringVar()
        self.var_insumo_previa = tk.StringVar()
        self.var_cidade = tk.StringVar(value=farmtech.cidade_atual)
        self.var_clima = tk.StringVar()
        self.var_status = tk.StringVar()
        self.botoes_r = []

        self._estilo()
        self._montar_topo()
        self._montar_corpo()
        self._montar_rodape()

        for variavel in (self.var_cultura, self.var_lado, self.var_ruas, self.var_dose):
            variavel.trace_add("write", lambda *_: self._atualizar_previa())

        self.recarregar(inicial=True)

        # O respiro entre os campos pede mais altura que antes, então a janela
        # abre no tamanho que o conteúdo pede, sem passar da borda da tela.
        self.update_idletasks()
        largura = max(1180, self.winfo_reqwidth())
        altura = min(self.winfo_reqheight(), self.winfo_screenheight() - 90)
        # Encostada no topo, para a barra de tarefas não cobrir o rodapé.
        lateral = max((self.winfo_screenwidth() - largura) // 2, 0)
        self.geometry(f"{largura}x{altura}+{lateral}+10")

    # ------------------------------------------------------------------
    # Montagem da janela
    # ------------------------------------------------------------------
    def _estilo(self):
        estilo = ttk.Style(self)
        if "clam" in estilo.theme_names():
            estilo.theme_use("clam")

        estilo.configure(".", font=FONTE, background=FUNDO, foreground=TEXTO)
        estilo.configure("TFrame", background=FUNDO)

        # Rótulos com leve destaque em verde escuro; as duas variações abaixo
        # cuidam da dica de manejo e dos números da prévia.
        estilo.configure("TLabel", background=FUNDO, foreground=VERDE_ESCURO,
                         font=FONTE_ROTULO)
        estilo.configure("Previa.TLabel", font=("Segoe UI", 13, "bold"),
                         foreground=VERDE_ESCURO)
        estilo.configure("Dica.TLabel", foreground=TEXTO_SUAVE, font=("Segoe UI", 9))

        estilo.configure("TLabelframe", background=FUNDO, borderwidth=1, relief="solid",
                         bordercolor=VERDE_BORDA, lightcolor=VERDE_BORDA,
                         darkcolor=VERDE_BORDA)
        estilo.configure("TLabelframe.Label", background=FUNDO, foreground=VERDE_ESCURO,
                         font=FONTE_SECAO)
        estilo.configure("TSeparator", background=VERDE_BORDA)

        estilo.configure("TRadiobutton", background=FUNDO, foreground=TEXTO,
                         font=FONTE, indicatorcolor=BRANCO, focuscolor=VERDE_CLARO,
                         padding=(0, 2))
        estilo.map("TRadiobutton",
                   foreground=[("active", VERDE_ESCURO)],
                   indicatorcolor=[("selected", VERDE), ("active", VERDE_SUAVE)])

        # Botão secundário: verde bem claro com contorno; o principal é sólido.
        estilo.configure("TButton", padding=(13, 7), font=FONTE_ROTULO, borderwidth=0,
                         relief="flat", background=VERDE_SUAVE, foreground=VERDE_ESCURO,
                         focuscolor=VERDE_CLARO)
        estilo.map("TButton",
                   background=[("pressed", VERDE_CLARO), ("active", "#d8ebdc"),
                               ("disabled", "#e7ebe7")],
                   foreground=[("disabled", "#9aa89d")])
        estilo.configure("Verde.TButton", padding=(13, 8), font=("Segoe UI Semibold", 10),
                         background=VERDE_ESCURO, foreground=BRANCO)
        estilo.map("Verde.TButton",
                   background=[("pressed", VERDE), ("active", VERDE_MEDIO),
                               ("disabled", "#b9cdbe")],
                   foreground=[("disabled", "#eef2ee")])

        estilo.configure("TEntry", padding=(8, 4), fieldbackground=BRANCO,
                         foreground=TEXTO, insertcolor=VERDE_ESCURO, borderwidth=0,
                         relief="flat", selectbackground=VERDE_CLARO,
                         selectforeground=VERDE_ESCURO)

        estilo.configure("Treeview", rowheight=27, font=("Segoe UI", 9),
                         background=BRANCO, fieldbackground=BRANCO, foreground=TEXTO,
                         borderwidth=0)
        estilo.configure("Treeview.Heading", font=("Segoe UI Semibold", 9),
                         background=VERDE_ESCURO, foreground=BRANCO, relief="flat",
                         borderwidth=0, padding=(6, 8))
        estilo.map("Treeview.Heading", background=[("active", VERDE)])
        estilo.map("Treeview", background=[("selected", VERDE_MEDIO)],
                   foreground=[("selected", BRANCO)])
        # Sem a moldura em relevo do clam, a tabela encosta na borda do painel.
        estilo.layout("Treeview", [("Treeview.treearea", {"sticky": "nsew"})])

        estilo.configure("Vertical.TScrollbar", background=VERDE_SUAVE, troughcolor=FUNDO,
                         bordercolor=FUNDO, arrowcolor=VERDE_ESCURO,
                         lightcolor=VERDE_SUAVE, darkcolor=VERDE_SUAVE, borderwidth=0)
        estilo.map("Vertical.TScrollbar", background=[("active", VERDE_CLARO)])

        self._arredondar(estilo)

    def _arredondar(self, estilo):
        """Cantos arredondados nos botões e nos campos.

        O tema clam não tem raio de borda, então o contorno vem de imagens
        9-slice desenhadas na hora. Se o Tk recusar os elementos, o visual
        chapado configurado acima continua valendo.
        """
        # As imagens precisam de referência viva ou o Tk descarta o desenho.
        self._imagens_estilo = []

        def recuo(linha, altura, raio):
            """Quanto a linha entra na horizontal para formar a curva."""
            if linha < raio:
                distancia = raio - 1 - linha
            elif linha >= altura - raio:
                distancia = linha - (altura - raio)
            else:
                return 0
            return raio - int(round((raio ** 2 - distancia ** 2) ** 0.5))

        def arredondado(cor, cor_borda=None, raio=9):
            lado = raio * 2 + 3
            imagem = tk.PhotoImage(master=self, width=lado, height=lado)
            # O canto vazado recebe a cor do painel, o que dispensa transparência.
            imagem.put(FUNDO, to=(0, 0, lado, lado))

            for linha in range(lado):
                inicio = recuo(linha, lado, raio)
                imagem.put(cor_borda or cor, to=(inicio, linha, lado - inicio, linha + 1))

            if cor_borda is not None:
                for linha in range(1, lado - 1):
                    inicio = 1 + recuo(linha - 1, lado - 2, raio - 1)
                    imagem.put(cor, to=(inicio, linha, lado - inicio, linha + 1))

            self._imagens_estilo.append(imagem)
            return imagem

        def aplicar(nome, estilo_alvo, recheio):
            """Troca o fundo do estilo pela imagem, preservando o conteúdo."""
            elemento = recheio.split(".")[0]
            estilo.layout(estilo_alvo, [
                (nome, {"sticky": "nsew", "children": [
                    (f"{elemento}.padding", {"sticky": "nsew", "children": [
                        (recheio, {"sticky": "nsew"})]})]})])

        try:
            estilo.element_create(
                "Secundario.fundo", "image",
                arredondado(VERDE_SUAVE, VERDE_BORDA),
                ("pressed", arredondado(VERDE_CLARO, VERDE_MEDIO)),
                ("active", arredondado("#d8ebdc", VERDE_CLARO)),
                ("disabled", arredondado("#e7ebe7", "#dde3de")),
                # Sem padding=0 o Tk repetiria a borda como espaço interno.
                border=9, padding=0, sticky="nsew")
            aplicar("Secundario.fundo", "TButton", "Button.label")

            estilo.element_create(
                "Principal.fundo", "image",
                arredondado(VERDE_ESCURO),
                ("pressed", arredondado(VERDE)),
                ("active", arredondado(VERDE_MEDIO)),
                ("disabled", arredondado("#b9cdbe")),
                border=9, padding=0, sticky="nsew")
            aplicar("Principal.fundo", "Verde.TButton", "Button.label")

            estilo.element_create(
                "Campo.fundo", "image",
                arredondado(BRANCO, VERDE_BORDA, raio=7),
                ("focus", arredondado(BRANCO, VERDE_MEDIO, raio=7)),
                ("disabled", arredondado("#f1f4f1", "#dde3de", raio=7)),
                border=7, padding=0, sticky="nsew")
            aplicar("Campo.fundo", "TEntry", "Entry.textarea")
        except tk.TclError:
            pass

    def _montar_topo(self):
        # Canvas em vez de Frame só para desenhar o filete de destaque na base
        # sem precisar de um widget a mais; os rótulos seguem sendo filhos dele
        # e são desenhados por cima do traço.
        topo = tk.Canvas(self, highlightthickness=0, borderwidth=0, bg=VERDE_ESCURO)
        topo.pack(fill="x")

        def filete(_evento=None):
            # A altura vem do próprio cabeçalho, que continua se ajustando aos
            # rótulos como antes, em vez de ficar presa a um valor fixo.
            topo.delete("filete")
            largura = max(topo.winfo_width(), 1)
            base = max(topo.winfo_height(), 6)
            topo.create_line(0, base - 2, largura, base - 2, fill=VERDE_MEDIO,
                             width=3, tags="filete")
            topo.create_line(0, base - 2, largura * 0.28, base - 2, fill=VERDE_CLARO,
                             width=3, tags="filete")

        topo.bind("<Configure>", filete)

        tk.Label(topo, text="FarmTech Solutions", font=FONTE_TITULO,
                 bg=VERDE_ESCURO, fg="white").pack(side="left", padx=(22, 12), pady=(0, 6))
        tk.Label(topo, text="cadastro de talhões, cálculo de insumos e análises em R",
                 font=("Segoe UI", 9), bg=VERDE_ESCURO,
                 fg="#bcdcc4").pack(side="left", pady=(8, 0))

        # A cidade fica em cima e o resumo do clima embaixo, que só aparece
        # depois de uma consulta bem-sucedida ao clima.R.
        canto = tk.Frame(topo, bg=VERDE_ESCURO)
        canto.pack(side="right", padx=22)

        self.rotulo_cidade = tk.Label(canto, font=("Segoe UI Semibold", 9), bg=VERDE_ESCURO,
                                      fg="#cfe6d5", anchor="e")
        self.rotulo_cidade.pack(anchor="e")

        tk.Label(canto, textvariable=self.var_clima, font=("Segoe UI", 9),
                 bg=VERDE_ESCURO, fg=VERDE_CLARO, anchor="e").pack(anchor="e")

    def _montar_corpo(self):
        corpo = ttk.Frame(self, padding=16)
        corpo.pack(fill="both", expand=True)
        corpo.columnconfigure(1, weight=1)
        corpo.rowconfigure(0, weight=1)

        self._montar_formulario(corpo)

        direita = ttk.Frame(corpo)
        direita.grid(row=0, column=1, sticky="nsew", padx=(16, 0))
        direita.columnconfigure(0, weight=1)
        direita.rowconfigure(0, weight=3)
        direita.rowconfigure(1, weight=2)

        self._montar_tabela(direita)
        self._montar_analises(direita)

    def _montar_formulario(self, pai):
        caixa = ttk.Labelframe(pai, text=" Talhão quadrado ", padding=(16, 6, 16, 10))
        caixa.grid(row=0, column=0, sticky="nsew")

        ttk.Label(caixa, text="Cultura").grid(row=0, column=0, columnspan=2, sticky="w")

        linha_culturas = ttk.Frame(caixa)
        linha_culturas.grid(row=1, column=0, columnspan=2, sticky="w", pady=(4, 0))
        for coluna, (nome, _) in enumerate(CULTURAS):
            ttk.Radiobutton(linha_culturas, text=nome, value=nome,
                            variable=self.var_cultura).grid(row=0, column=coluna, padx=(0, 18))

        ttk.Label(caixa, textvariable=self.var_manejo, style="Dica.TLabel").grid(
            row=2, column=0, columnspan=2, sticky="w", pady=(3, 10))

        campos = (
            ("Lado do talhão (metros)", self.var_lado),
            ("Quantidade de ruas", self.var_ruas),
            ("Dose do insumo (mL por metro)", self.var_dose),
        )
        for indice, (rotulo, variavel) in enumerate(campos):
            linha = 3 + indice * 2
            ttk.Label(caixa, text=rotulo).grid(row=linha, column=0, columnspan=2, sticky="w")
            entrada = ttk.Entry(caixa, textvariable=variavel, width=26)
            entrada.grid(row=linha + 1, column=0, columnspan=2, sticky="ew", pady=(2, 7))
            if indice == 0:
                self.primeiro_campo = entrada

        ttk.Separator(caixa).grid(row=9, column=0, columnspan=2, sticky="ew", pady=(3, 8))

        ttk.Label(caixa, text="Área calculada").grid(row=10, column=0, sticky="w")
        ttk.Label(caixa, textvariable=self.var_area_previa, style="Previa.TLabel").grid(
            row=10, column=1, sticky="e")
        ttk.Label(caixa, text="Total de insumo").grid(row=11, column=0, sticky="w")
        ttk.Label(caixa, textvariable=self.var_insumo_previa, style="Previa.TLabel").grid(
            row=11, column=1, sticky="e")

        self.canvas_talhao = tk.Canvas(caixa, width=LADO_CANVAS, height=LADO_CANVAS,
                                       bg=BRANCO, highlightthickness=1,
                                       highlightbackground=VERDE_BORDA)
        self.canvas_talhao.grid(row=12, column=0, columnspan=2, pady=9)

        ttk.Button(caixa, text="Cadastrar talhão", style="Verde.TButton",
                   command=self.cadastrar).grid(row=13, column=0, columnspan=2,
                                                sticky="ew", pady=(0, 6))
        ttk.Button(caixa, text="Atualizar selecionado",
                   command=self.atualizar).grid(row=14, column=0, columnspan=2,
                                                sticky="ew", pady=(0, 6))
        ttk.Button(caixa, text="Limpar campos",
                   command=self.limpar).grid(row=15, column=0, columnspan=2, sticky="ew")

        caixa.columnconfigure(0, weight=1)
        caixa.columnconfigure(1, weight=1)

    def _montar_tabela(self, pai):
        caixa = ttk.Labelframe(pai, text=" Registros dos vetores ", padding=(12, 8, 12, 12))
        caixa.grid(row=0, column=0, sticky="nsew")
        caixa.columnconfigure(0, weight=1)
        caixa.rowconfigure(0, weight=1)

        self.tabela = ttk.Treeview(caixa, columns=[c[0] for c in COLUNAS_TABELA],
                                   show="headings", selectmode="browse")
        for chave, titulo, largura in COLUNAS_TABELA:
            self.tabela.heading(chave, text=titulo)
            alinhamento = "w" if chave in ("cidade", "cultura", "manejo") else "e"
            self.tabela.column(chave, width=largura, anchor=alinhamento,
                               stretch=chave == "manejo")
        # Linhas zebradas: as etiquetas são aplicadas no _preencher_tabela().
        self.tabela.tag_configure("par", background=BRANCO)
        self.tabela.tag_configure("impar", background=VERDE_ZEBRA)
        self.tabela.grid(row=0, column=0, sticky="nsew")
        self.tabela.bind("<Double-1>", lambda _evento: self.carregar_no_formulario())

        barra = ttk.Scrollbar(caixa, orient="vertical", command=self.tabela.yview)
        self.tabela.configure(yscrollcommand=barra.set)
        barra.grid(row=0, column=1, sticky="ns")

        acoes = ttk.Frame(caixa)
        acoes.grid(row=1, column=0, columnspan=2, sticky="w", pady=(12, 0))
        ttk.Button(acoes, text="Editar no formulário",
                   command=self.carregar_no_formulario).grid(row=0, column=0, padx=(0, 8))
        ttk.Button(acoes, text="Deletar selecionado",
                   command=self.deletar).grid(row=0, column=1, padx=(0, 8))
        ttk.Button(acoes, text="Recarregar do CSV",
                   command=self.recarregar).grid(row=0, column=2)

    def _montar_analises(self, pai):
        caixa = ttk.Labelframe(pai, text=" Análises em R ", padding=(12, 8, 12, 12))
        caixa.grid(row=1, column=0, sticky="nsew", pady=(16, 0))
        caixa.columnconfigure(1, weight=1)
        caixa.rowconfigure(1, weight=1)

        controles = ttk.Frame(caixa)
        controles.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 11))

        botao_estatisticas = ttk.Button(controles, text="Média e desvio padrão",
                                        command=self.consultar_estatisticas)
        botao_estatisticas.grid(row=0, column=0, padx=(0, 18))

        ttk.Label(controles, text="Cidade:").grid(row=0, column=1, padx=(0, 6))
        ttk.Entry(controles, textvariable=self.var_cidade, width=22).grid(row=0, column=2,
                                                                         padx=(0, 8))
        botao_clima = ttk.Button(controles, text="Consultar clima",
                                 command=self.consultar_clima)
        botao_clima.grid(row=0, column=3)

        self.botoes_r = [botao_estatisticas, botao_clima]

        self.saida_r = scrolledtext.ScrolledText(caixa, height=10, wrap="word",
                                                 font=("Consolas", 9), bg=CONSOLE_FUNDO,
                                                 fg=CONSOLE_TEXTO,
                                                 insertbackground=CONSOLE_TEXTO,
                                                 relief="flat", state="disabled",
                                                 borderwidth=0, highlightthickness=1,
                                                 highlightbackground=VERDE_BORDA,
                                                 selectbackground=VERDE_MEDIO,
                                                 selectforeground=BRANCO,
                                                 padx=14, pady=10)
        self.saida_r.grid(row=1, column=0, columnspan=3, sticky="nsew")

    def _montar_rodape(self):
        rodape = tk.Frame(self, bg=VERDE_SUAVE, highlightthickness=1,
                          highlightbackground=VERDE_BORDA)
        rodape.pack(fill="x")
        tk.Label(rodape, textvariable=self.var_status, bg=VERDE_SUAVE, fg=VERDE_ESCURO,
                 font=("Segoe UI", 9), anchor="w").pack(fill="x", padx=18, pady=7)

    # ------------------------------------------------------------------
    # Prévia e desenho
    # ------------------------------------------------------------------
    def _valores_do_formulario(self, silencioso=False):
        """Lê e valida os três campos. Devolve None quando algo está errado."""
        try:
            lado = ler_numero(self.var_lado.get(), "Lado do talhão")
            quantidade_ruas = ler_numero(self.var_ruas.get(), "Quantidade de ruas", inteiro=True)
            dose = ler_numero(self.var_dose.get(), "Dose do insumo")
        except ValueError as erro:
            if not silencioso:
                messagebox.showwarning("Dados incompletos", str(erro), parent=self)
            return None

        return lado, quantidade_ruas, dose

    def _atualizar_previa(self):
        self.var_manejo.set(f"Manejo: {manejo_da_cultura(self.var_cultura.get())}")

        valores = self._valores_do_formulario(silencioso=True)
        if valores is None:
            self.var_area_previa.set("—")
            self.var_insumo_previa.set("—")
            self._desenhar_talhao()
            return

        lado, quantidade_ruas, dose = valores
        self.var_area_previa.set(f"{farmtech.calcular_area(lado):.2f} m²")
        self.var_insumo_previa.set(
            f"{farmtech.calcular_insumo(lado, quantidade_ruas, dose):.2f} L")
        self._desenhar_talhao(lado, quantidade_ruas)

    def _desenhar_talhao(self, lado=None, quantidade_ruas=None):
        """Representação do talhão: o quadrado e as ruas dentro dele."""
        canvas = self.canvas_talhao
        canvas.delete("all")

        margem = 28
        x0 = y0 = margem
        x1 = y1 = LADO_CANVAS - margem
        canvas.create_rectangle(x0, y0, x1, y1, outline=VERDE, width=2, fill=VERDE_SUAVE)

        if quantidade_ruas:
            # Acima de 24 ruas o desenho viraria um borrão: mostra só a amostra.
            visiveis = min(int(quantidade_ruas), 24)
            passo = (x1 - x0) / (visiveis + 1)
            for indice in range(1, visiveis + 1):
                x = x0 + passo * indice
                canvas.create_line(x, y0 + 4, x, y1 - 4, fill=VERDE_CLARO)

        medida = f"{lado:.2f} m" if lado else "lado"
        centro = (x0 + x1) / 2
        canvas.create_text(centro, y1 + 14, text=medida, fill=TEXTO_SUAVE,
                           font=("Segoe UI", 8))
        canvas.create_text(x0 - 14, centro, text=medida, fill=TEXTO_SUAVE,
                           font=("Segoe UI", 8), angle=90)

        if quantidade_ruas:
            canvas.create_text(centro, y0 - 14, text=f"{int(quantidade_ruas)} rua(s)",
                               fill=VERDE, font=("Segoe UI Semibold", 8))

    # ------------------------------------------------------------------
    # Tabela e estado
    # ------------------------------------------------------------------
    def _posicao_selecionada(self, acao):
        selecao = self.tabela.selection()
        if not selecao:
            messagebox.showinfo("Nenhum registro selecionado",
                                f"Selecione na tabela o registro que deseja {acao}.",
                                parent=self)
            return None
        return int(selecao[0])

    def _preencher_tabela(self, selecionar=None):
        self.tabela.delete(*self.tabela.get_children())

        for posicao in range(len(farmtech.culturas)):
            lado = farmtech.lados[posicao]
            quantidade_ruas = farmtech.ruas[posicao]
            dose = farmtech.doses[posicao]
            self.tabela.insert("", "end", iid=str(posicao),
                               tags=("par" if posicao % 2 == 0 else "impar",), values=(
                posicao,
                farmtech.cidades[posicao],
                farmtech.culturas[posicao],
                farmtech.manejos[posicao],
                f"{lado:.2f}",
                quantidade_ruas,
                f"{dose:.2f}",
                f"{farmtech.calcular_area(lado):.2f}",
                f"{farmtech.calcular_insumo(lado, quantidade_ruas, dose):.2f}",
            ))

        if selecionar is not None and 0 <= selecionar < len(farmtech.culturas):
            chave = str(selecionar)
            self.tabela.selection_set(chave)
            self.tabela.see(chave)

    def _atualizar_status(self, mensagem=""):
        self.rotulo_cidade.configure(text=f"Cidade dos próximos cadastros: {farmtech.cidade_atual}")

        total = len(farmtech.culturas)
        if total:
            area = sum(farmtech.calcular_area(lado) for lado in farmtech.lados)
            insumo = sum(
                farmtech.calcular_insumo(farmtech.lados[i], farmtech.ruas[i], farmtech.doses[i])
                for i in range(total)
            )
            resumo = (f"{total} registro(s)  |  área total {area:.2f} m²  |  "
                      f"insumo total {insumo:.2f} L")
        else:
            resumo = "Nenhum registro cadastrado."

        self.var_status.set(f"{resumo}   {mensagem}".rstrip())

    def _escrever_saida(self, texto):
        self.saida_r.configure(state="normal")
        self.saida_r.delete("1.0", "end")
        self.saida_r.insert("1.0", texto.strip() or "(o R não devolveu nenhuma saída)")
        self.saida_r.configure(state="disabled")

    # ------------------------------------------------------------------
    # Operações sobre os vetores (as mesmas do menu de terminal)
    # ------------------------------------------------------------------
    def recarregar(self, inicial=False):
        """Relê o CSV para os vetores do farmtech.py.

        O carregar_csv() só faz append, então os vetores precisam ser
        esvaziados antes ou os registros apareceriam duplicados.
        """
        for vetor in (farmtech.culturas, farmtech.manejos, farmtech.lados,
                      farmtech.ruas, farmtech.doses, farmtech.cidades):
            vetor.clear()

        farmtech.carregar_csv()
        self._preencher_tabela()
        self._atualizar_previa()

        if inicial:
            self._atualizar_status(f"Dados lidos de {farmtech.ARQUIVO_CSV.name}.")
        else:
            self._atualizar_status("Dados recarregados do CSV.")

    def cadastrar(self):
        valores = self._valores_do_formulario()
        if valores is None:
            return

        lado, quantidade_ruas, dose = valores
        cultura = self.var_cultura.get()

        farmtech.cidades.append(farmtech.cidade_atual)
        farmtech.culturas.append(cultura)
        farmtech.manejos.append(manejo_da_cultura(cultura))
        farmtech.lados.append(lado)
        farmtech.ruas.append(quantidade_ruas)
        farmtech.doses.append(dose)
        farmtech.salvar_csv()

        posicao = len(farmtech.culturas) - 1
        self._preencher_tabela(selecionar=posicao)
        self._atualizar_status(f"Talhão cadastrado na posição {posicao}.")
        self.limpar()

    def atualizar(self):
        posicao = self._posicao_selecionada("atualizar")
        if posicao is None:
            return

        valores = self._valores_do_formulario()
        if valores is None:
            return

        lado, quantidade_ruas, dose = valores
        cultura = self.var_cultura.get()

        farmtech.culturas[posicao] = cultura
        farmtech.manejos[posicao] = manejo_da_cultura(cultura)
        farmtech.lados[posicao] = lado
        farmtech.ruas[posicao] = quantidade_ruas
        farmtech.doses[posicao] = dose
        # O menu de terminal também regrava a cidade atual ao atualizar.
        farmtech.cidades[posicao] = farmtech.cidade_atual
        farmtech.salvar_csv()

        self._preencher_tabela(selecionar=posicao)
        self._atualizar_status(f"Posição {posicao} atualizada.")

    def deletar(self):
        posicao = self._posicao_selecionada("deletar")
        if posicao is None:
            return

        resumo = (f"{farmtech.culturas[posicao]} de "
                  f"{farmtech.lados[posicao]:.2f} m em {farmtech.cidades[posicao]}")
        if not messagebox.askyesno("Confirmar exclusão",
                                   f"Excluir o registro da posição {posicao}?\n\n{resumo}",
                                   parent=self):
            self._atualizar_status("Exclusão cancelada.")
            return

        # Remove a mesma posição dos seis vetores para não perder a sincronia.
        for vetor in (farmtech.culturas, farmtech.manejos, farmtech.lados,
                      farmtech.ruas, farmtech.doses, farmtech.cidades):
            vetor.pop(posicao)
        farmtech.salvar_csv()

        self._preencher_tabela()
        self._atualizar_status(f"Registro da posição {posicao} removido.")

    def carregar_no_formulario(self):
        posicao = self._posicao_selecionada("editar")
        if posicao is None:
            return

        self.var_cultura.set(farmtech.culturas[posicao])
        self.var_lado.set(f"{farmtech.lados[posicao]:g}")
        self.var_ruas.set(str(farmtech.ruas[posicao]))
        self.var_dose.set(f"{farmtech.doses[posicao]:g}")
        self._atualizar_status(f"Posição {posicao} carregada. Edite e use "
                               f"\"Atualizar selecionado\".")

    def limpar(self):
        self.var_lado.set("")
        self.var_ruas.set("")
        self.var_dose.set("")
        self.primeiro_campo.focus_set()

    # ------------------------------------------------------------------
    # Chamadas do R, em thread para a janela não congelar
    # ------------------------------------------------------------------
    def _rodar_em_thread(self, script, argumentos, aviso, ao_terminar=None):
        for botao in self.botoes_r:
            botao.state(["disabled"])
        self._escrever_saida(aviso)

        def trabalho():
            resultado = executar_r(script, *argumentos)
            self.after(0, lambda: concluir(resultado))

        def concluir(resultado):
            codigo, saida = resultado
            self._escrever_saida(saida)
            for botao in self.botoes_r:
                botao.state(["!disabled"])
            if ao_terminar is not None:
                ao_terminar(codigo, saida)

        threading.Thread(target=trabalho, daemon=True).start()

    def consultar_estatisticas(self):
        if not farmtech.culturas:
            self._escrever_saida("Cadastre pelo menos um talhão para calcular "
                                 "as estatísticas.")
            return

        self._atualizar_status("Calculando as estatísticas no R...")
        self._rodar_em_thread(
            farmtech.SCRIPT_ESTATISTICAS, (),
            "Calculando média e desvio padrão no R...",
            lambda _codigo, _saida: self._atualizar_status("Estatísticas calculadas pelo R."),
        )

    def consultar_clima(self):
        escolhida = self.var_cidade.get().strip() or farmtech.cidade_atual
        self.var_cidade.set(escolhida)

        # O clima.R usa o local padrão quando não recebe argumento nenhum.
        argumentos = () if escolhida == farmtech.CIDADE_PADRAO else (escolhida,)

        def concluir(codigo, saida):
            if codigo != 0:
                self.var_cidade.set(farmtech.cidade_atual)
                self._atualizar_status(f"A cidade continua sendo {farmtech.cidade_atual}.")
                return

            self.var_clima.set(resumo_do_clima(saida))

            # A troca só vale se o R encontrou a cidade, como no terminal.
            if escolhida != farmtech.cidade_atual:
                farmtech.cidade_atual = escolhida
                self._atualizar_status(f"Cidade alterada para {escolhida}.")
            else:
                self._atualizar_status("Clima consultado pelo R.")

        self._atualizar_status(f"Consultando o clima de {escolhida}...")
        self._rodar_em_thread(farmtech.SCRIPT_CLIMA, argumentos,
                              f"Consultando a Open-Meteo para {escolhida}...", concluir)


def main():
    Interface().mainloop()


if __name__ == "__main__":
    main()
