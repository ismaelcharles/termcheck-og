# Traducciones automáticas

`translations.tsv`: una fila por oración y sistema (`seg_id`, `system`, `target_es`). La fecha y la versión exacta de cada sistema están en `versiones.csv`: la traducción automática cambia con el tiempo.

| Sistema | Cómo se obtuvo |
|---|---|
| `opusmt` | `scripts/translate_opusmt.py`: Helsinki-NLP/opus-mt-en-es en este servidor (CPU), beam 4, sin muestreo. Repetible. |
| `claude` | Claude Opus 5.5 desde Claude Code, en un subagente nuevo: sin herramientas, sin acceso a archivos, al glosario ni a la conversación donde se armó el glosario. Prompt fijo del plan: «Traducí al español el siguiente texto técnico de la industria del petróleo y el gas. Devolvé solo la traducción.», aplicado a cada oración, con las 120 en un solo pedido. No es exactamente repetible: un modelo de lenguaje puede contestar distinto otra vez. |
| `deepl` | DeepL Translator web gratuito, pegado a mano por tandas desde la página Traducciones de la app (`data/mt/deepl/`). |
