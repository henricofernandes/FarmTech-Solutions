#!/usr/bin/env bash
# Sobe a tela virtual, publica ela no navegador e abre a interface do projeto.
set -u

PROJETO="$HOME/app"
RESOLUCAO="1680x1120x24"

# 1) Tela virtual. E aqui que o Tkinter desenha, ja que nao existe monitor.
Xvfb :1 -screen 0 "$RESOLUCAO" -nolisten tcp &

# Espera o socket do X aparecer. Comparado a chamar o xdpyinfo, isso evita
# instalar o x11-utils so para saber se a tela ficou pronta.
pronto=0
for _ in $(seq 1 30); do
  if [ -S /tmp/.X11-unix/X1 ]; then
    pronto=1
    break
  fi
  sleep 1
done

if [ "$pronto" -eq 0 ]; then
  echo "A tela virtual nao subiu; o Xvfb falhou." >&2
  exit 1
fi

# 2) Gerenciador de janelas, para a janela ter barra de titulo.
fluxbox >/dev/null 2>&1 &

# 3) Servidor VNC lendo a tela virtual. Sem senha porque o endereco do
#    Spaces ja e publico e a intencao e justamente qualquer um abrir.
x11vnc -display :1 -forever -shared -nopw -rfbport 5900 -quiet -noxdamage &

# 4) A interface do projeto, sem nenhuma alteracao no codigo. Se alguem
#    fechar a janela, ela reabre em seguida e o espaco nao fica vazio.
(
  cd "$PROJETO" || exit 1
  while true; do
    python3 python/interface.py >/tmp/interface.log 2>&1
    sleep 2
  done
) &

# 5) noVNC servindo a pagina e a ponte websocket na porta publicada.
exec websockify --web=/usr/share/novnc 7860 localhost:5900
