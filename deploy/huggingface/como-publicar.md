# Como publicar o link público

O que esta pasta contém sobe para um **Space** do Hugging Face, que hospeda contêineres
de graça e dá um endereço público. O resultado é um link que qualquer pessoa abre no
navegador, sem conta e sem instalar nada, e já vê a interface do projeto rodando.

Só a criação do Space precisa de você, porque exige estar logado numa conta. Depois
disso o link é permanente.

## Passo a passo

1. Se ainda não tiver, crie uma conta gratuita em https://huggingface.co/join
2. Abra https://huggingface.co/new-space
3. Preencha:
   - **Space name**: `farmtech-solutions`
   - **Select the Space SDK**: **Docker** e, no template, **Blank**
   - **Space hardware**: `CPU basic` (a opção gratuita)
   - **Visibility**: **Public**
4. Clique em **Create Space**.
5. Na página do Space, vá em **Files** → **Add file** → **Upload files** e arraste os
   três arquivos desta pasta: `Dockerfile`, `iniciar.sh` e `README.md`.

   Confirme a substituição do `README.md` que o Hugging Face criou sozinho — o daqui já
   traz `sdk: docker` e `app_port: 7860`, que é a porta onde a página é publicada.

   Prefira arrastar os arquivos em vez de copiar e colar o conteúdo: o `iniciar.sh` é um
   script de shell e precisa manter o fim de linha original.
6. O build começa sozinho. **A primeira vez leva alguns minutos**, porque é quando o R e
   as bibliotecas gráficas são instalados. Acompanhe em **Logs**.
7. Quando o topo da página mudar para **Running**, o endereço do Space é o link público.
   Ele tem o formato `https://huggingface.co/spaces/SEU-USUARIO/farmtech-solutions`.

## Se preferir pelo git

```bash
git clone https://huggingface.co/spaces/SEU-USUARIO/farmtech-solutions
cd farmtech-solutions
# copie Dockerfile, iniciar.sh e README.md desta pasta para cá
git add . && git commit -m "Interface do FarmTech no navegador" && git push
```

## Quando o projeto mudar

O `Dockerfile` clona o código do repositório público do GitHub, então ele não guarda uma
cópia editada do projeto. Como o Hugging Face reaproveita o cache do build, um `git push`
novo no GitHub não chega sozinho ao Space. Para atualizar, use **Settings** →
**Factory rebuild**, ou troque o valor de `VERSAO` no `Dockerfile`.

## Limites do plano gratuito

O Space hiberna depois de um tempo sem acesso e acorda na próxima visita, levando alguns
segundos. Ao acordar ele volta com os dados originais do repositório, então talhões
cadastrados por lá não permanecem.

E existe **uma única janela compartilhada** entre todos os visitantes: duas pessoas ao
mesmo tempo disputam o mesmo mouse. Para o grupo revezando, funciona bem.
