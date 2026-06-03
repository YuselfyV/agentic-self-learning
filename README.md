# Agentic Self-Learning Lite

Replica ligera inspirada en `Towards-Agentic-Self-Learning`.

Esta version conserva la idea principal del repositorio original sin exigir servidores de recuperacion, GPUs ni entrenamiento PPO:

1. Un agente genera una pregunta factual.
2. Un agente responde usando una herramienta `retrieve`.
3. Un agente evalua si la pregunta y la respuesta son validas.

## Estructura

```text
agentic_self_learning/
  agents/
    question_agent.py
    answer_agent.py
    evaluator_agent.py
  tools/
    retrieval.py
  orchestrator.py
  schemas.py
  cli.py
data/
  knowledge_base.jsonl
tests/
```

## Uso rapido

```bash
python -m agentic_self_learning.cli --topic "capitales"
```

Tambien puedes pasar una pregunta propia:

```bash
python -m agentic_self_learning.cli --question "What is the capital of Colombia?"
```

## Usar Wikipedia como fuente online

La replica puede investigar en Wikipedia usando la API publica de MediaWiki:

```bash
python -m agentic_self_learning.cli \
  --source wikipedia \
  --wikipedia-language en \
  --question "What is the capital of Colombia?"
```

Para Wikipedia en espanol:

```bash
python -m agentic_self_learning.cli \
  --source wikipedia \
  --wikipedia-language es \
  --question "Cual es la capital de Colombia?"
```

Puedes hacer preguntas en espanol si usas `--wikipedia-language es`. Tambien puedes hacer preguntas en ingles con `--wikipedia-language en`.

Importante: este proyecto responde con recuperacion de evidencia. Puede recibir cualquier pregunta, pero funciona mejor con preguntas factuales que tengan una respuesta concreta y aparezcan en Wikipedia.

## Usarlo sin tenerlo localmente

Hay dos caminos sencillos:

1. GitHub Codespaces: abre el repositorio en Codespaces y ejecuta los comandos desde el navegador.
2. Despliegue como API: publica el proyecto en un servicio como Render, Railway, Fly.io, Hugging Face Spaces o una maquina virtual.

El proyecto incluye un servidor HTTP minimo:

```bash
python3 -m agentic_self_learning.server --host 0.0.0.0 --port 8000
```

Luego abre esta direccion en el navegador para usar la interfaz:

```text
http://localhost:8000/
```

La API sigue disponible para otras aplicaciones:

```text
http://localhost:8000/ask?source=wikipedia&language=es&question=Cual%20es%20la%20capital%20de%20Colombia
```

O desde otra aplicacion:

```bash
curl "http://localhost:8000/ask?source=wikipedia&language=es&question=Cual%20es%20la%20capital%20de%20Colombia"
```

### Despliegue sugerido en Render

1. Sube este proyecto a GitHub.
2. En Render, crea un nuevo Web Service desde el repositorio.
3. Usa Python como entorno.
4. En Start Command coloca:

   ```bash
   python3 -m agentic_self_learning.server --host 0.0.0.0 --port $PORT
   ```

5. Cuando Render entregue una URL publica, consulta:

   ```text
   https://TU-URL.onrender.com/ask?source=wikipedia&language=es&question=Cual%20es%20la%20capital%20de%20Colombia
   ```

### Paso a paso

1. Verifica que Python este disponible:

   ```bash
   python3 --version
   ```

2. Entra a la carpeta del proyecto:

   ```bash
   cd /Users/yuselfymichel/Documents/agentic-self-learning
   ```

3. Ejecuta el flujo local para comprobar que todo funciona:

   ```bash
   python3 -m agentic_self_learning.cli --topic capitales
   ```

4. Ejecuta el flujo online con Wikipedia:

   ```bash
   python3 -m agentic_self_learning.cli --source wikipedia --question "What is Mars known as?"
   ```

5. Cambia el idioma cuando lo necesites:

   ```bash
   python3 -m agentic_self_learning.cli --source wikipedia --wikipedia-language es --question "Que planeta es conocido como el planeta rojo?"
   ```

## Formas online posibles

- Wikipedia / MediaWiki API: opcion actual. Es abierta, gratuita y buena para investigacion enciclopedica.
- Wikipedia REST API: alternativa moderna para busquedas y paginas concretas.
- Wikidata API: mejor cuando necesitas entidades estructuradas, propiedades y relaciones.
- Buscadores externos: utiles para web abierta, pero suelen requerir API key.
- Retriever propio remoto: replica mas cercana al proyecto original; montas un servidor `/retrieve` y los agentes lo consultan por HTTP.

## Relacion con el repositorio original

El repositorio original usa un flujo agentico con etiquetas como `<tool_call>`, `<tool_response>`, `<question>` y `<answer>`, ademas de una herramienta de recuperacion local. Esta replica mantiene ese patron, pero lo implementa con una base de conocimiento local en JSONL para que sea facil de estudiar y extender.

## Siguiente paso recomendado

Para acercarlo mas al proyecto original, cambia `LocalRetrievalTool` por un cliente HTTP que consulte un servidor de recuperacion externo compatible con `/retrieve`.
