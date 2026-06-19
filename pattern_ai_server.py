import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


HOST = "127.0.0.1"
PORT = int(os.getenv("PORT", "8010"))
ROOT = Path(__file__).resolve().parent
HTML_FILE = ROOT / "candle_patterns.html"
OPENAI_URL = "https://api.openai.com/v1/responses"
DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")


def load_env(path=ROOT / ".env"):
    if not path.exists():
        return

    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def selected_candles_summary(context):
    pattern = context.get("pattern", {})
    candles = context.get("candles", [])
    start = pattern.get("start_index", 0)
    end = pattern.get("end_index", 0)
    return [
        candle for candle in candles
        if start <= candle.get("index", 0) - 1 <= end
    ]


def build_prompt(mode, context, question, messages):
    pattern = context.get("pattern", {})
    candles = context.get("candles", [])
    selected = selected_candles_summary(context)

    system = (
        "Eres un mentor experto en price action, swing trading y supply & demand. "
        "Tu objetivo es enseñar patrones de velas de confirmación de forma educativa. "
        "No des recomendaciones financieras, señales de compra/venta, objetivos de precio "
        "ni instrucciones operativas. Explica con claridad, usando las velas OHLC dadas."
    )

    base_context = {
        "pattern": pattern,
        "selected_candles": selected,
        "full_sequence": candles,
    }

    if mode == "followup":
        previous = [
            {"role": msg.get("role"), "content": msg.get("content")}
            for msg in messages[-8:]
            if msg.get("role") in {"user", "assistant"}
        ]
        user = (
            "Responde la pregunta de seguimiento sobre el patrón actual. "
            "Mantén el enfoque educativo y referencia velas específicas cuando ayude.\n\n"
            f"Contexto JSON:\n{json.dumps(base_context, ensure_ascii=False)}\n\n"
            f"Historial reciente:\n{json.dumps(previous, ensure_ascii=False)}\n\n"
            f"Pregunta:\n{question}"
        )
    else:
        user = (
            "Analiza este patrón detectado. Devuelve una explicación en español con estas secciones:\n"
            "1. Lectura del patrón\n"
            "2. Psicología del mercado\n"
            "3. Calidad de la confirmación\n"
            "4. Qué lo fortalece\n"
            "5. Qué lo debilita\n"
            "6. Pregunta de estudio\n\n"
            "Usa frases breves y concretas. No des señal de entrada.\n\n"
            f"Contexto JSON:\n{json.dumps(base_context, ensure_ascii=False)}"
        )

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def extract_output_text(payload):
    if "output_text" in payload and payload["output_text"]:
        return payload["output_text"]

    chunks = []
    for item in payload.get("output", []):
        for content in item.get("content", []):
            text = content.get("text")
            if text:
                chunks.append(text)
    return "\n".join(chunks).strip()


def call_openai(mode, context, question, messages):
    load_env()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Falta OPENAI_API_KEY en .env o en variables de entorno.")

    model = os.getenv("OPENAI_MODEL", DEFAULT_MODEL)
    body = {
        "model": model,
        "input": build_prompt(mode, context, question, messages),
        "temperature": 0.35,
        "max_output_tokens": 900,
    }

    request = Request(
        OPENAI_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=45) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenAI API error {exc.code}: {details}") from exc
    except URLError as exc:
        raise RuntimeError(f"No se pudo conectar con OpenAI: {exc.reason}") from exc

    text = extract_output_text(payload)
    if not text:
        raise RuntimeError("OpenAI no devolvió texto analizable.")
    return text


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlparse(self.path).path
        if path in {"/", "/candle_patterns.html"}:
            self.send_file(HTML_FILE, "text/html; charset=utf-8")
            return
        self.send_error(404, "Not found")

    def do_POST(self):
        path = urlparse(self.path).path
        if path == "/api/analyze-pattern":
            self.handle_analyze()
            return
        self.send_error(404, "Not found")

    def handle_analyze(self):
        try:
            payload = self.read_json()
            analysis = call_openai(
                mode=payload.get("mode", "initial"),
                context=payload.get("context", {}),
                question=payload.get("question", ""),
                messages=payload.get("messages", []),
            )
            self.send_json({"analysis": analysis})
        except Exception as exc:
            self.send_json({"error": str(exc)}, status=500)

    def read_json(self):
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length)
        return json.loads(raw.decode("utf-8")) if raw else {}

    def send_file(self, path, content_type):
        if not path.exists():
            self.send_error(404, "File not found")
            return
        body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        return


def main():
    if not HTML_FILE.exists():
        print(f"No existe {HTML_FILE}", file=sys.stderr)
        sys.exit(1)

    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Candle trainer listo en http://{HOST}:{PORT}")
    print("Usa Ctrl+C para detener.")
    server.serve_forever()


if __name__ == "__main__":
    main()
