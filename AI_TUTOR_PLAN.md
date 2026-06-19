# Tutor AI Para Patrones De Velas

Implementado como primera version local:

- Boton `Analizar con ChatGPT`.
- Backend local `pattern_ai_server.py`; no hay llamadas directas desde el HTML.
- `OPENAI_API_KEY` vive en `.env`, nunca en el navegador.
- La API recibe datos estructurados del patron:
  - tipo de patron
  - direccion
  - velas OHLC
  - indice de inicio y confirmacion
  - reglas detectadas
- Panel `Tutor AI` con:
  - lectura del patron
  - psicologia del mercado
  - calidad de la confirmacion
  - que lo fortalece
  - que lo debilita
  - pregunta de estudio
- Preguntas de seguimiento usando el mismo contexto del patron actual.
- Tono educativo: no dar senales de compra/venta.

Mejoras futuras:

- Streaming de respuesta.
- Selector de nivel: principiante, intermedio, avanzado.
- Comparacion con patron ideal.
- Soporte para analizar capturas del canvas ademas de OHLC.
