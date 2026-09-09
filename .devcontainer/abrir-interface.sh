#!/usr/bin/env bash
# Abre a interface no desktop remoto assim que o servidor grafico responder.
# Roda a cada conexao ao Codespaces e sai na hora, sem travar a inicializacao.
set -u

export DISPLAY=:1
PROJETO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# O desktop-lite leva alguns segundos para subir a tela virtual.
pronto=0
for _ in $(seq 1 60); do
  if xdpyinfo -display "$DISPLAY" >/dev/null 2>&1; then
    pronto=1
    break
  fi
  sleep 1
done

if [ "$pronto" -eq 0 ]; then
  echo "O desktop remoto nao respondeu. Abra a porta 6080 e rode manualmente:"
  echo "  DISPLAY=:1 python3 python/interface.py"
  exit 0
fi

# Uma janela so, mesmo que o Codespaces seja reconectado varias vezes.
pkill -f "python3 .*interface\.py" >/dev/null 2>&1 || true

cd "$PROJETO"
nohup python3 python/interface.py > /tmp/farmtech-interface.log 2>&1 &

echo "Interface aberta no desktop remoto."
echo "Abra a porta 6080 (aba Ports) e use a senha: farmtech"
