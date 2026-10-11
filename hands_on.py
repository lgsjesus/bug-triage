"""Script hands-on interativo para testar os endpoints da Bug Triage API.

Permite testar requisições reais contra a API em execução (localmente ou via Docker).
Uso:
    python hands_on.py
"""
import sys
import json
import time
from datetime import datetime, timezone

try:
    import httpx
except ImportError:
    print("ERRO: Pacote 'httpx' não encontrado. Instale com: pip install httpx")
    sys.exit(1)

BASE_URL = "http://localhost:8000"


def print_header(title: str):
    print("\n" + "=" * 70)
    print(f"🔹 {title}")
    print("=" * 70)


def print_response(response: httpx.Response):
    print(f"Status Code : {response.status_code}")
    print(f"Header Trace: {response.headers.get('X-Trace-Id', 'Nenhum')}")
    try:
        data = response.json()
        print("Corpo da Resposta:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
    except Exception:
        print(f"Corpo bruto: {response.text}")


def test_health(client: httpx.Client):
    print_header("1. Testando Health Check (GET /health)")
    try:
        res = client.get(f"{BASE_URL}/health")
        print_response(res)
    except httpx.ConnectError:
        print(f"❌ Não foi possível conectar a {BASE_URL}.")
        print("Certifique-se de que a API está rodando:")
        print("  - Local: uvicorn app.main:app --port 8000 --reload")
        print("  - Docker: docker compose up -d")


def test_triage_low(client: httpx.Client):
    print_header("2. Testando Triagem: Bug Leve (UI / Typo / Baixa complexidade)")
    payload = {
        "project_name": "portal-web",
        "service": "frontend-app",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "content": "Botão de login desalinhado no menu superior direito após ajuste de CSS no header."
    }
    print(f"Enviando payload para {BASE_URL}/api/v1/triage...")
    try:
        res = client.post(f"{BASE_URL}/api/v1/triage", json=payload)
        print_response(res)
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")


def test_triage_medium(client: httpx.Client):
    print_header("3. Testando Triagem: Bug Médio (Log longo > 300 caracteres)")
    long_log = (
        "ERROR 2026-10-10 16:30:12.441 [http-nio-8080-exec-1] OrderProcessingService: "
        "Failed to validate payment voucher for customer id 99421. "
        "java.lang.IllegalArgumentException: Voucher token validation timed out after 3000ms. "
        "at com.store.payment.VoucherClient.apply(VoucherClient.java:142) "
        "at com.store.order.OrderProcessingService.checkout(OrderProcessingService.java:88) "
        "at com.store.order.OrderController.submitOrder(OrderController.java:55) "
        "Nested exception: Connection reset by peer while waiting for response."
    )
    payload = {
        "project_name": "ecommerce",
        "service": "order-service",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "content": long_log
    }
    print(f"Enviando payload ({len(long_log)} chars) para {BASE_URL}/api/v1/triage...")
    try:
        res = client.post(f"{BASE_URL}/api/v1/triage", json=payload)
        print_response(res)
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")


def test_triage_high(client: httpx.Client):
    print_header("4. Testando Triagem: Bug Crítico (Termo crítico: 'deadlock')")
    payload = {
        "project_name": "billing-core",
        "service": "transaction-worker",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "content": "CRITICAL: Database connection pool locked up. Deadlock detected between thread-41 and thread-88 while attempting to acquire lock on ledger table."
    }
    print(f"Enviando payload para {BASE_URL}/api/v1/triage...")
    try:
        res = client.post(f"{BASE_URL}/api/v1/triage", json=payload)
        print_response(res)
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")


def test_validation_error(client: httpx.Client):
    print_header("5. Testando Tratamento de Erro 422 (Timestamp inválido)")
    payload = {
        "project_name": "analytics",
        "service": "collector",
        "timestamp": "data-e-hora-invalida",
        "content": "Erro qualquer no coletor"
    }
    print(f"Enviando payload inválido para {BASE_URL}/api/v1/triage...")
    try:
        res = client.post(f"{BASE_URL}/api/v1/triage", json=payload)
        print_response(res)
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")


def main():
    print("=" * 70)
    print("🧪 ROTEIRO HANDS-ON: TESTE INTERATIVO DA BUG TRIAGE API")
    print(f"Alvo: {BASE_URL}")
    print("=" * 70)

    with httpx.Client(timeout=40.0) as client:
        test_health(client)
        time.sleep(1)
        test_triage_low(client)
        time.sleep(1)
        test_triage_medium(client)
        time.sleep(1)
        test_triage_high(client)
        time.sleep(1)
        test_validation_error(client)

    print("\n" + "=" * 70)
    print("✅ Roteiro hands-on concluído!")
    print("Observe o terminal onde a API está rodando para conferir as linhas de")
    print("log em JSON estruturado com 'trace_id', latência e tokens gastos.")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
