---
title: FarmTech Solutions
emoji: 🌱
colorFrom: green
colorTo: gray
sdk: docker
app_port: 7860
pinned: false
---

# FarmTech Solutions — Agricultura Digital

Interface visual do projeto rodando ao vivo. Cadastre um talhão de soja ou milho, veja
a área e o insumo serem calculados, e dispare as duas análises em **R**: média e desvio
padrão dos talhões, e o clima em tempo real pela API Open-Meteo.

A janela é o programa em **Tkinter** de verdade, executado dentro do contêiner e
transmitido para o navegador via noVNC. O código não foi adaptado para a web: é o mesmo
`python/interface.py` do repositório.

Código-fonte: https://github.com/henricofernandes/FarmTech-Solutions

## Duas observações

Existe **uma única janela compartilhada**. Se duas pessoas abrirem ao mesmo tempo, as
duas controlam o mesmo mouse. Para revezar, funciona bem.

Os cadastros feitos aqui **não são permanentes**: o espaço hiberna quando fica sem uso e
volta com os dados originais do repositório.
