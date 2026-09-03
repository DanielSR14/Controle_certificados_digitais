# Sobre o projeto

**Controle de Certificados Digitais** é uma aplicação web local, feita em
Flask, para escritórios de contabilidade gerenciarem os certificados digitais
`.pfx/.p12` dos seus clientes: cadastro, acompanhamento de vencimento,
renovação e envio dos avisos de vencimento.

## Motivação

Controlar dezenas de certificados de clientes em planilha é trabalhoso e falho:
a validade fica desatualizada, ninguém lembra de avisar o cliente a tempo e a
mesma mensagem de aviso é reescrita toda semana. A ideia aqui é concentrar tudo
em um painel só, rodando na própria rede do escritório, **sem depender de
serviço em nuvem** e sem tirar os arquivos e as senhas de dentro de casa.

## Decisões de projeto

- **Local-first.** Um único processo Flask + SQLite, sem contêiner, sem banco
  externo, sem build de frontend. `python run.py` e está no ar.
- **Offline.** htmx e Chart.js são vendorizados; a interface funciona sem
  internet, o que importa em redes de escritório instáveis.
- **A validade vem do certificado, não do nome do arquivo.** O `.pfx` é sempre
  aberto com `cryptography` para ler emissão, validade e número de série. O
  parsing do nome do arquivo é só uma sugestão de senha na importação em lote.
- **Senhas cifradas em repouso.** Fernet com chave local em `data/.secret.key`,
  fora do controle de versão.
- **Fluxos em dois passos (validar → confirmar).** Upload, renovação e
  importação em lote mostram o que foi lido antes de gravar qualquer coisa.

## Escopo

Ferramenta interna. O código está aberto como referência de um CRUD real em
Flask + htmx, com leitura de certificados X.509 e um fluxo de importação em
lote. Nome do escritório, assinatura e modelo de mensagem são genéricos por
padrão e podem ser trocados em **Configurações**.

Detalhes de uso e instalação no [README](README.md).
