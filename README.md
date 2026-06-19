# Candle Confirmation Trainer

Aplicacion web simple para estudiar patrones de velas de confirmacion:

- Bullish/Bearish Engulfing
- Bullish/Bearish Pin Bar
- Bullish/Bearish 3-Candle Reversal

La pagina genera secuencias aleatorias de velas, detecta patrones dentro del grupo y muestra explicaciones educativas.

## Uso

Abre `candle_patterns.html` directamente en el navegador.

## Tutor AI

Para usar el panel `Tutor AI`, abre la pagina desde el servidor local:

1. Crea un archivo `.env`:

```env
OPENAI_API_KEY=tu_api_key_de_openai
OPENAI_MODEL=gpt-4.1-mini
PORT=8010
```

2. Ejecuta:

```bash
python3 pattern_ai_server.py
```

3. Abre:

```text
http://127.0.0.1:8010
```

El API key queda en el backend local y no se expone en el navegador.

## Notas

Esta herramienta es educativa. No genera senales financieras ni recomendaciones de entrada.
