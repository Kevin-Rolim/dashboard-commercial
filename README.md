# dashboard-commercial

Dashboard Streamlit para acompanhamento comercial de prospeccao.

## Rodar no Streamlit Community Cloud

O app carrega `dashboard_prospeccao_base.csv` automaticamente quando abre. Nao existe upload lateral nem selecao manual de fonte de dados.

Arquivos que precisam estar no GitHub:

- `app.py`
- `requirements.txt`
- `dashboard_prospeccao_base.csv`

No Streamlit Community Cloud:

1. Acesse https://share.streamlit.io.
2. Crie ou edite o app apontando para este repositorio.
3. Use a branch `main`.
4. Use `app.py` como main file path.
5. Faca o deploy ou reboot do app.

Se a tela publicada ainda mostrar upload lateral, ela esta usando uma versao antiga do repositorio. Confirme se o commit mais recente chegou no GitHub e clique em **Manage app** > **Reboot app** no Streamlit.

## Rodar localmente

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

No Windows, ative o ambiente com:

```powershell
.venv\Scripts\Activate.ps1
```

## Base de dados

O arquivo principal e `dashboard_prospeccao_base.csv`. Outros CSVs continuam ignorados para evitar subir bases extras por acidente.

Se a base tiver informacao sensivel, mantenha o repositorio privado.
