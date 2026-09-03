# Política de Segurança

## Modelo de uso previsto

Esta aplicação foi feita para rodar **localmente**, em um computador da rede
interna de um escritório, servindo os demais micros dessa mesma rede. Ela
**não tem autenticação de usuário** e **não deve ser exposta à internet
pública** nem a redes não confiáveis.

## Como os dados sensíveis são tratados

- As **senhas dos certificados** são gravadas cifradas (Fernet) no banco. A
  chave fica em `data/.secret.key`, gerada localmente e fora do controle de
  versão.
- A criptografia protege contra leitura casual do arquivo `.db` (backup, cópia
  perdida), **não** contra quem tem acesso ao computador onde a aplicação roda —
  a chave está no mesmo disco.
- A pasta `data/` inteira (banco, arquivos `.pfx`, chave) é sensível. Faça
  backup dela em local seguro e restrinja o acesso ao computador.

## Recomendações de implantação

- Use apenas em rede cabeada/Wi-Fi confiável do escritório.
- Libere a porta `8501` no firewall **apenas** para a faixa de IP da rede local.
- Mantenha o sistema operacional do PC-servidor atualizado e com tela bloqueada.
- Considere criptografia de disco (BitLocker / FileVault / LUKS) no PC-servidor.

## Reportando uma vulnerabilidade

Não abra issue pública para falhas de segurança. Use a aba **Security →
Report a vulnerability** do repositório no GitHub (GitHub Security Advisories),
ou entre em contato em privado com o mantenedor.

Descreva o problema, o impacto e, se possível, um passo a passo mínimo de
reprodução. Evite incluir dados reais de clientes.
