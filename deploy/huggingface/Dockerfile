# Contêiner que roda a interface Tkinter do projeto e transmite a janela
# para o navegador. O código do projeto não é alterado nem copiado com
# mudanças: ele é clonado do repositório público e executado como está.
FROM debian:bookworm-slim

# python3-tk    -> Tkinter, usado pela interface
# r-base-core   -> Rscript, procurado pelo farmtech.py no PATH
# r-cran-jsonlite -> única dependência do clima.R
# xvfb          -> tela virtual, já que o contêiner não tem monitor
# x11vnc        -> publica essa tela como servidor VNC
# fluxbox       -> barra de título, permite mover e fechar a janela
# novnc/websockify -> cliente VNC que roda dentro do navegador
RUN apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates \
      git \
      python3 \
      python3-tk \
      r-base-core \
      r-cran-jsonlite \
      xvfb \
      x11vnc \
      fluxbox \
      novnc \
      websockify \
    && rm -rf /var/lib/apt/lists/*

# O pacote novnc do Debian traz vnc.html, mas não index.html, então a raiz do
# site cairia em 404. Este redirect entra direto na tela, sem pedir para
# clicar em "Connect", e o resize=scale encaixa o desktop na janela do
# navegador de quem estiver acessando.
RUN printf '%s\n' \
  '<!doctype html>' \
  '<title>FarmTech Solutions</title>' \
  '<meta http-equiv="refresh" content="0; url=vnc.html?autoconnect=true&resize=scale&reconnect=true">' \
  > /usr/share/novnc/index.html

# O Hugging Face Spaces executa o contêiner com o usuário de UID 1000.
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    DISPLAY=:1 \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8
WORKDIR $HOME/app

# Aumente o VERSAO para forçar um clone novo quando o repositório mudar,
# senão o build reaproveita esta camada do cache e traz o código antigo.
ARG VERSAO=1
RUN git clone --depth 1 \
      https://github.com/henricofernandes/FarmTech-Solutions.git .

COPY --chown=user:user iniciar.sh $HOME/iniciar.sh
RUN chmod +x $HOME/iniciar.sh

EXPOSE 7860
CMD ["/home/user/iniciar.sh"]
