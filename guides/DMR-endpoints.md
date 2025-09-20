# Docker Model Runner (DMR) — Endpoints & OpenAI Compatibility

> The one‑stop reference for calling Docker Model Runner directly and via OpenAI‑compatible SDKs.

---

## 1) Base URLs & Networking

DMR exposes endpoints differently depending on where the client runs and how DMR is enabled.

### Docker Desktop (recommended)

* **From containers** → `http://model-runner.docker.internal/`
* **From host processes** → `http://localhost:12434/` *(when TCP host access is enabled on port 12434)*

### Docker Engine (Linux)

* **From containers** → `http://172.17.0.1:12434/` *(host gateway address)*
* **From host processes** → `http://localhost:12434/`

> If `172.17.0.1` isn’t reachable in a Compose project, add:
>
> ```yaml
> services:
>   your-service:
>     extra_hosts:
>       - "model-runner.docker.internal:host-gateway"
> ```
>
> Then call: `http://model-runner.docker.internal:12434/…`

### Via Unix socket (advanced)

* **Socket path**: typically `$HOME/.docker/run/docker.sock` (Desktop) or `/var/run/docker.sock` (Engine)
* **Path prefix**: when using a socket, prefix requests with `/**exp/vDD4.40**`.

  * Example: `localhost/exp/vDD4.40/engines/llama.cpp/v1/chat/completions`

---

## 2) Engine path & versioning

DMR exposes OpenAI‑compatible endpoints under **`/engines/{backend}/v1`**.

* Current backend: `llama.cpp` → `/engines/llama.cpp/v1/...`
* **Shortcut**: you may omit the backend segment and use `/engines/v1/...`.

> Use the engine path that your SDK or tooling prefers. Both forms work as long as DMR is enabled.

---

## 3) DMR (Docker‑style) endpoints

These manage **models as OCI artifacts**—pulling, listing, inspecting, and deleting locally.

| Method | Path                         | Purpose                      |
| :----: | ---------------------------- | ---------------------------- |
|  POST  | `/models/create`             | Pull/create a model locally  |
|   GET  | `/models`                    | List local models            |
|   GET  | `/models/{namespace}/{name}` | Inspect local model metadata |
| DELETE | `/models/{namespace}/{name}` | Remove a local model         |

### Namespace & name

* `namespace` is typically the **account/organization** on your registry (e.g., `ai`, `myorg`).
* `name` is the **repository** (e.g., `gemma3`, `qwen2.5`, `smollm2`).
* A **tag** may be appended: `ai/gemma3:1B-Q4_K_M`.
* Fully‑qualified references include registry: `index.docker.io/ai/qwen2.5:7B-F16` or `ghcr.io/myorg/smollm2:latest`.

---

## 4) OpenAI‑compatible endpoints

Base: **`/engines/llama.cpp/v1`** *(or `/engines/v1`)*

| Method | Path                         | What it does                                 |
| :----: | ---------------------------- | -------------------------------------------- |
|   GET  | `/models`                    | List models available to DMR (OpenAI schema) |
|   GET  | `/models/{namespace}/{name}` | Retrieve a single model (OpenAI schema)      |
|  POST  | `/chat/completions`          | Chat API (messages array)                    |
|  POST  | `/completions`               | Legacy text completions                      |
|  POST  | `/embeddings`                | Embeddings                                   |

### 4.1 Required headers

* `Content-Type: application/json`
* `Authorization: Bearer <any non-empty string>` *(many OpenAI SDKs require it; DMR itself does not use/validate API keys when running locally)*

### 4.2 Chat Completions — request shape (OpenAI‑style)

```json
{
  "model": "ai/gemma3",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Explain context windows in 2 bullets."}
  ],
  "temperature": 0.7,
  "top_p": 1,
  "stream": false
}
```

**Notes**

* Parameters unsupported by the current backend may be ignored.
* Tool/function‑calling support depends on backend/model; for llama.cpp, support is evolving and not guaranteed for every model/build.

### 4.3 Streaming

Use `"stream": true` for SSE streaming if your SDK supports it. Some tool‑calling scenarios may require disabling streaming; prefer non‑streaming for maximum compatibility.

### 4.4 Embeddings — request shape

```json
{
  "model": "ai/all-minilm",
  "input": ["hello world", "bonjour le monde"]
}
```

---

## 5) Example calls

### From another container (Desktop)

```sh
curl http://model-runner.docker.internal/engines/llama.cpp/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer dmr" \
  -d '{
    "model": "ai/smollm2",
    "messages": [
      {"role":"system","content":"You are a helpful assistant."},
      {"role":"user","content":"Write 3 facts about the fall of Rome."}
    ]
  }'
```

### From host via TCP

```sh
# Ensure Desktop TCP access is enabled on 12434
#   docker desktop enable model-runner --tcp 12434

curl http://localhost:12434/engines/llama.cpp/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer dmr" \
  -d '{
    "model": "ai/smollm2",
    "messages": [
      {"role":"system","content":"You are a helpful assistant."},
      {"role":"user","content":"Write 3 facts about the fall of Rome."}
    ]
  }'
```

### Via Unix socket

```sh
curl --unix-socket $HOME/.docker/run/docker.sock \
  localhost/exp/vDD4.40/engines/llama.cpp/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer dmr" \
  -d '{
    "model": "ai/smollm2",
    "messages": [
      {"role":"system","content":"You are a helpful assistant."},
      {"role":"user","content":"Write 3 facts about the fall of Rome."}
    ]
  }'
```

---

## 6) Compose integration (models → env injection)

Compose can define models and inject connection details into your services.

```yaml
services:
  app:
    image: my-app
    models:
      - llm

models:
  llm:
    model: ai/smollm2
    context_size: 4096
    runtime_flags:
      - "--no-prefill-assistant"
```

**Injected env vars (short syntax)**

* `LLM_URL` → base URL for the OpenAI‑compatible endpoints
* `LLM_MODEL` → the model identifier (e.g., `ai/smollm2`)

**Injected env vars (long syntax)**

```yaml
services:
  app:
    image: my-app
    models:
      llm:
        endpoint_var: AI_MODEL_URL
        model_var: AI_MODEL_NAME
```

This yields `AI_MODEL_URL` and `AI_MODEL_NAME` in the app container.

---

## 7) Practical SDK configuration (examples)

### OpenAI Python SDK

```python
from openai import OpenAI
client = OpenAI(
    base_url="http://localhost:12434/engines/v1",  # or model-runner.docker.internal from containers
    api_key="dmr"  # non-empty string to satisfy SDK; DMR does not validate
)

resp = client.chat.completions.create(
    model="ai/gemma3",
    messages=[{"role":"user","content":"Hello!"}]
)
print(resp.choices[0].message.content)
```

### Java (Spring AI)

```java
OpenAiApi api = OpenAiApi.builder()
    .baseUrl("http://localhost:12434/engines")
    .apiKey("dmr")
    .build();
```

---

## 8) Troubleshooting & tips

* **Can’t reach from a container?** Add `extra_hosts: ["model-runner.docker.internal:host-gateway"]` and use that hostname.
* **401 from OpenAI SDK**: Provide any non‑empty API key string (e.g., `dmr`).
* **Tool/function calling**: Prefer non‑streaming (`"stream": false`) unless confirmed supported by your model/backend.
* **Context length**: Match `context_size` to hardware; large contexts need more RAM/VRAM.
* **Model IDs**: Use `ai/<repo>[:tag]` or full registry form.

---

## 9) Quick reference cheatsheet

* **Base (container)**: `http://model-runner.docker.internal/`
* **Base (host TCP)**: `http://localhost:12434/`
* **Socket prefix**: `/exp/vDD4.40`
* **OpenAI base**: `/engines/llama.cpp/v1` *(or `/engines/v1`)*
* **Models mgmt**: `POST /models/create`, `GET /models`, `GET/DELETE /models/{namespace}/{name}`
* **OpenAI APIs**: `GET /models`, `GET /models/{namespace}/{name}`, `POST /chat/completions`, `POST /completions`, `POST /embeddings`
* **Headers**: `Content-Type: application/json`, `Authorization: Bearer dmr`

---

### Appendix: Minimal cURL templates

**List models**

```sh
curl -H "Authorization: Bearer dmr" \
  http://localhost:12434/engines/v1/models
```

**Retrieve model**

```sh
curl -H "Authorization: Bearer dmr" \
  http://localhost:12434/engines/v1/models/ai/gemma3
```

**Embeddings**

```sh
curl http://localhost:12434/engines/v1/embeddings \
  -H "Content-Type: application/json" -H "Authorization: Bearer dmr" \
  -d '{"model":"ai/all-minilm","input":["hello","world"]}'
```
