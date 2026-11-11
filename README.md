# TermCheck O&G

Verificador de terminología para traducción automática inglés → español en Oil & Gas upstream (variante técnica de Argentina).

Estado: Fase 0 (arranque). El plan completo está en `docs/plan.md`.

## Instalar (Linux)

```
python3 -m venv --without-pip .venv
python3 -m pip --python .venv/bin/python install pip
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m spacy download en_core_web_sm
.venv/bin/python -m spacy download es_core_news_sm
```

En Google Colab alcanza con `!pip install -r requirements.txt` y las dos líneas de `spacy download`.

## Probar que anda

```
.venv/bin/python scripts/hola_spacy.py
```

Las pruebas automáticas:

```
.venv/bin/python -m pytest -v
```

Revisar el glosario (errores y avisos):

```
PYTHONPATH=src .venv/bin/python -m termcheck.glossary data/glossary/glossary_en_es.csv
```

## App web (planilla del glosario)

```
.venv/bin/streamlit run app/streamlit_app.py
```

Queda en http://127.0.0.1:8501 (para probar sin Google: `TERMCHECK_SIN_LOGIN=1` delante). En el servidor se publica en https://termcheck.aval.site con `sudo bash deploy/termcheck.sh`; se entra con Google y los correos permitidos van en `.streamlit/secrets.toml` (no va a git).
