# Contribuindo

Obrigado pelo interesse em contribuir! Este é um projeto pequeno e focado —
as diretrizes abaixo são leves.

## Ambiente de desenvolvimento

```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Linux/macOS
pip install -r requirements.txt
python run.py
```

## Antes de abrir um Pull Request

1. **Nunca** faça commit de dados reais: arquivos `.pfx/.p12`, o banco
   `certificados.db`, `data/.secret.key`, planilhas exportadas ou qualquer
   informação de clientes. O `.gitignore` já cobre isso — confira com
   `git status` mesmo assim.
2. Verifique que a aplicação sobe e as telas principais respondem:

   ```bash
   python -m py_compile run.py webapp/*.py src/*.py
   python run.py   # abra http://localhost:8501 e navegue por Dashboard / Certificados / Mensagens / Configurações
   ```

3. Mantenha o estilo do código existente: nomes e comentários em português,
   funções pequenas, sem dependências novas sem necessidade.
4. Descreva no PR **o que muda** e **como testou**.

## Reportando bugs

Abra uma issue usando o modelo de bug. Inclua passos para reproduzir, o que
esperava e o que aconteceu. **Não cole dados de clientes** em issues.

## Segurança

Vulnerabilidades não devem ser reportadas em issues públicas — veja
[SECURITY.md](SECURITY.md).
