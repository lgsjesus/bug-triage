# 🧪 Guia Hands-on: Testando a Bug Triage API

Este guia prático contém instruções passo a passo para você subir a aplicação e testar todos os cenários da API, seja via script Python interativo ou diretamente pelo terminal (PowerShell / curl).

---

## Passo 1: Subir a Aplicação

Escolha uma das duas formas:

### Opção A: Via Docker Compose (Mais rápido e completo)
Sobe o LiteLLM Proxy e a API já integrados:
```bash
docker compose up -d --build
```
Para acompanhar os logs estruturados no terminal:
```bash
docker compose logs -f triage-api
```

### Opção B: Via Terminal Local (Python Virtualenv)
```powershell
# Ativar o ambiente virtual
.\venv\Scripts\Activate.ps1

# Subir o servidor FastAPI
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## Passo 2: Executar o Script Automatizado Hands-on

Criamos o script [`hands_on.py`](file:///C:/ai-projects/bug-triage/hands_on.py) que executa todos os cenários automaticamente:

```powershell
.\venv\Scripts\python.exe hands_on.py
```

O script testará:
1. `GET /health` (Verificação de status do serviço e proxy)
2. `POST /api/v1/triage` com **Bug Leve** (Tier Low)
3. `POST /api/v1/triage` com **Bug Médio** (Log longo > 300 caracteres, Tier Medium)
4. `POST /api/v1/triage` com **Bug Crítico** (Termo 'deadlock', Tier High)
5. `POST /api/v1/triage` com **Erro de Validação 422** (Timestamp mal formatado)

---

## Passo 3: Testando Manualmente via Terminal (PowerShell / curl)

Você também pode disparar chamadas pontuais diretamente do terminal:

### 1. Health Check
```powershell
curl.exe -i http://localhost:8000/health
```
**Resposta esperada (200 OK):**
```json
{
  "status": "ok",
  "dependencies": {
    "litellm": "up"
  },
  "trace_id": "90d1f4ba-813d-425f-bc13-ba144fbb8b83",
  "timestamp": "2026-10-10T19:30:00.000000+00:00"
}
```

---

### 2. Triagem de Bug Leve (UI / CSS)
```powershell
curl.exe -X POST http://localhost:8000/api/v1/triage `
  -H "Content-Type: application/json" `
  -d '{
    "project_name": "portal-web",
    "service": "frontend",
    "timestamp": "2026-10-10T16:00:00-03:00",
    "content": "Botão de login com texto desalinhado no menu mobile."
  }'
```

---

### 3. Triagem de Bug Crítico (Deadlock / Alta Prioridade)
```powershell
curl.exe -X POST http://localhost:8000/api/v1/triage `
  -H "Content-Type: application/json" `
  -d '{
    "project_name": "checkout-api",
    "service": "payment-worker",
    "timestamp": "2026-10-10T16:00:00-03:00",
    "content": "Deadlock detectado ao tentar adquirir conexão no pool transacional."
  }'
```

**Resposta esperada:**
```json
{
  "trace_id": "a50db81d-e59e-4c7f-8d96-e2aeb387f311",
  "complexity": "alta",
  "reasoning": "Texto simplificado em até 3 parágrafos...",
  "priority": "alta",
  "timestamp": "2026-10-10T16:00:00-03:00"
}
```

---

### 4. Testando Erro de Validação (422)
Envie um timestamp inválido ou payload incompleto:
```powershell
curl.exe -X POST http://localhost:8000/api/v1/triage `
  -H "Content-Type: application/json" `
  -d '{
    "project_name": "checkout",
    "service": "billing",
    "timestamp": "data-invalida",
    "content": "falha"
  }'
```
**Resposta esperada (HTTP 422):**
```json
{
  "trace_id": "9e1c3a64-2cb6-49f2-8703-9bb6da074492",
  "detail": "Erro de validação dos dados enviados.",
  "errors": [...]
}
```

---

## Passo 4: Como Inspecionar a Telemetria e Logs

Olhe o terminal onde o servidor está rodando. A cada requisição, você verá as linhas JSON geradas:
- `event: "request_received"` (mostra `content_length` para proteger dados sensíveis)
- `event: "tier_selected"` (mostra o tier escolhido e o motivo da heurística)
- `event: "llm_call_started"` (modelo solicitado)
- `event: "llm_call_completed"` (**modelo solicitado**, **modelo efetivo retornado pelo proxy**, **tokens** e **latência em ms**)
- `event: "llm_response_parsed"` (complexidade e prioridade)
- `event: "request_completed"` (status HTTP e latência total da requisição)

Todos os logs compartilham o mesmo `trace_id` da requisição para rastreamento ponta a ponta.
