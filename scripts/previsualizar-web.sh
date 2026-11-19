#!/usr/bin/env bash
# Ejecuta únicamente la interfaz paralela; Ctrl+C cierra el servidor.
set -Eeuo pipefail
raiz=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
python_web="$raiz/.venv/bin/python"
if [[ ! -x "$python_web" ]]; then
  python_web=/home/ubuntu/termcheck-og/.venv/bin/python
fi
cd "$raiz"
export PYTHONPATH="$raiz/src:$raiz"
exec "$python_web" -m uvicorn web.main:publica --host 127.0.0.1 --port "${TERMCHECK_PUERTO_WEB:-8530}" --no-access-log
