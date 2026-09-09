#!/usr/bin/env bash
# Instala o que o projeto precisa dentro do Codespaces: o Python com Tkinter
# e o R com o jsonlite. Roda uma unica vez, na criacao do ambiente.
set -euo pipefail

export DEBIAN_FRONTEND=noninteractive

sudo apt-get update

# python3-tk traz o Tkinter, que nao vem na imagem base.
# r-base-core traz o Rscript que o farmtech.py procura no PATH.
# x11-utils traz o xdpyinfo, usado para saber quando a tela ficou pronta.
sudo apt-get install -y --no-install-recommends \
  python3 \
  python3-tk \
  r-base-core \
  x11-utils

# O jsonlite e a unica dependencia do clima.R. O pacote do Debian instala
# pronto; se o nome nao existir na distribuicao, compila do CRAN.
if ! sudo apt-get install -y --no-install-recommends r-cran-jsonlite; then
  echo "Pacote do Debian indisponivel, instalando o jsonlite pelo CRAN..."
  sudo Rscript -e 'install.packages("jsonlite", repos = "https://cloud.r-project.org")'
fi

sudo rm -rf /var/lib/apt/lists/*

# Falha agora, com mensagem clara, em vez de deixar a interface abrir quebrada.
python3 -c "import tkinter; print('Tkinter', tkinter.TkVersion, 'ok')"
Rscript -e 'cat("R", as.character(getRversion()), "ok\n")'
Rscript -e 'stopifnot(requireNamespace("jsonlite", quietly = TRUE)); cat("jsonlite ok\n")'

echo "Ambiente pronto."
