from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from agentic_self_learning.orchestrator import SelfLearningPipeline


class AgentRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed_url = urlparse(self.path)
        if parsed_url.path == "/":
            self._send_html(self._index_html())
            return
        if parsed_url.path == "/health":
            self._send_json({"status": "ok"})
            return
        if parsed_url.path != "/ask":
            self._send_json({"error": "Use /ask?question=..."}, status=404)
            return

        params = parse_qs(parsed_url.query)
        question = self._first(params, "question")
        language = self._first(params, "language", "es")
        source = self._first(params, "source", "wikipedia")

        if not question:
            self._send_json({"error": "Missing required query parameter: question"}, status=400)
            return

        try:
            pipeline = SelfLearningPipeline(source=source, wikipedia_language=language)
            result = pipeline.answer_existing_question(question)
            self._send_json(
                {
                    "question": result.answer.question,
                    "answer": self._strip_answer_tag(result.answer.answer),
                    "evaluation": {
                        "conclusion": result.evaluation.conclusion,
                        "score": result.evaluation.score,
                        "reason": result.evaluation.reason,
                        "question_is_solvable": result.evaluation.question_is_solvable,
                    },
                    "evidence": [
                        {
                            "id": item.document.id,
                            "score": item.score,
                            "title": item.document.metadata.get("title"),
                            "url": item.document.metadata.get("url"),
                            "source": item.document.metadata.get("source", source),
                            "content": item.document.contents,
                        }
                        for item in result.answer.evidence
                    ],
                }
            )
        except Exception as error:
            self._send_json({"error": str(error)}, status=500)

    def log_message(self, format: str, *args) -> None:
        return

    def _send_json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, html: str, status: int = 200) -> None:
        body = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    @staticmethod
    def _first(params: dict[str, list[str]], key: str, default: str = "") -> str:
        values = params.get(key)
        return values[0].strip() if values and values[0].strip() else default

    @staticmethod
    def _strip_answer_tag(text: str) -> str:
        return text.replace("<answer>", "").replace("</answer>", "").strip()

    @staticmethod
    def _index_html() -> str:
        return """<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Agentic Self-Learning</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f7f8fb;
      --panel: #ffffff;
      --text: #1d2433;
      --muted: #667085;
      --line: #d8dee9;
      --accent: #1463ff;
      --accent-dark: #0b4fd0;
      --ok: #087443;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      min-height: 100vh;
      font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: var(--bg);
      color: var(--text);
    }
    main {
      width: min(920px, calc(100% - 32px));
      margin: 0 auto;
      padding: 40px 0;
    }
    header {
      margin-bottom: 24px;
    }
    h1 {
      margin: 0 0 8px;
      font-size: clamp(28px, 4vw, 42px);
      line-height: 1.05;
      letter-spacing: 0;
    }
    p {
      margin: 0;
      color: var(--muted);
      line-height: 1.55;
    }
    .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 20px;
      box-shadow: 0 12px 30px rgba(23, 30, 47, 0.08);
    }
    form {
      display: grid;
      gap: 14px;
    }
    label {
      display: grid;
      gap: 8px;
      font-weight: 650;
    }
    textarea, select {
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px;
      font: inherit;
      color: var(--text);
      background: #fff;
    }
    textarea {
      min-height: 112px;
      resize: vertical;
    }
    .controls {
      display: grid;
      grid-template-columns: 1fr 1fr auto;
      gap: 12px;
      align-items: end;
    }
    button {
      min-height: 46px;
      border: 0;
      border-radius: 8px;
      padding: 0 18px;
      font: inherit;
      font-weight: 700;
      color: #fff;
      background: var(--accent);
      cursor: pointer;
    }
    button:hover { background: var(--accent-dark); }
    button:disabled {
      background: #98a2b3;
      cursor: wait;
    }
    .result {
      margin-top: 18px;
      display: grid;
      gap: 14px;
    }
    .answer {
      font-size: 28px;
      font-weight: 750;
      line-height: 1.2;
      color: var(--ok);
    }
    .evidence {
      display: grid;
      gap: 10px;
    }
    .source {
      border-top: 1px solid var(--line);
      padding-top: 10px;
    }
    .source a {
      color: var(--accent);
      font-weight: 650;
      text-decoration: none;
    }
    .source p {
      margin-top: 6px;
      display: -webkit-box;
      -webkit-line-clamp: 4;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }
    .status {
      min-height: 24px;
      color: var(--muted);
    }
    @media (max-width: 720px) {
      main { padding: 24px 0; }
      .controls { grid-template-columns: 1fr; }
      button { width: 100%; }
    }
  </style>
</head>
<body>
  <main>
    <header>
      <h1>Agentic Self-Learning</h1>
      <p>Haz una pregunta factual y los agentes buscaran evidencia en Wikipedia para responder y evaluar la respuesta.</p>
    </header>

    <section class="panel">
      <form id="ask-form">
        <label>
          Pregunta
          <textarea id="question" name="question" placeholder="Ejemplo: Cual es la capital de Colombia?" required></textarea>
        </label>
        <div class="controls">
          <label>
            Fuente
            <select id="source" name="source">
              <option value="wikipedia" selected>Wikipedia</option>
              <option value="local">Local</option>
            </select>
          </label>
          <label>
            Idioma
            <select id="language" name="language">
              <option value="es" selected>Español</option>
              <option value="en">Ingles</option>
            </select>
          </label>
          <button id="submit" type="submit">Preguntar</button>
        </div>
      </form>

      <div id="status" class="status"></div>
      <div id="result" class="result" hidden></div>
    </section>
  </main>

  <script>
    const form = document.getElementById("ask-form");
    const result = document.getElementById("result");
    const status = document.getElementById("status");
    const submit = document.getElementById("submit");

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const params = new URLSearchParams(new FormData(form));
      status.textContent = "Buscando evidencia...";
      result.hidden = true;
      result.innerHTML = "";
      submit.disabled = true;

      try {
        const response = await fetch(`/ask?${params.toString()}`);
        const data = await response.json();
        if (!response.ok || data.error) {
          throw new Error(data.error || "No se pudo responder la pregunta.");
        }
        status.textContent = data.evaluation?.conclusion
          ? `Evaluacion: ${data.evaluation.conclusion}`
          : "";
        result.innerHTML = renderResult(data);
        result.hidden = false;
      } catch (error) {
        status.textContent = error.message;
      } finally {
        submit.disabled = false;
      }
    });

    function renderResult(data) {
      const evidence = (data.evidence || []).map((item) => `
        <article class="source">
          ${item.url ? `<a href="${escapeHtml(item.url)}" target="_blank" rel="noreferrer">${escapeHtml(item.title || item.id)}</a>` : `<strong>${escapeHtml(item.title || item.id)}</strong>`}
          <p>${escapeHtml(item.content || "")}</p>
        </article>
      `).join("");

      return `
        <div>
          <p>Respuesta</p>
          <div class="answer">${escapeHtml(data.answer || "Sin respuesta")}</div>
        </div>
        <div>
          <p>${escapeHtml(data.evaluation?.reason || "")}</p>
        </div>
        <div class="evidence">
          ${evidence}
        </div>
      `;
    }

    function escapeHtml(value) {
      return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
    }
  </script>
</body>
</html>"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Agentic Self-Learning HTTP API")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), AgentRequestHandler)
    print(f"Serving Agentic Self-Learning API on http://{args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
