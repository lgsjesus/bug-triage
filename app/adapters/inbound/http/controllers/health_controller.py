"""Controller HTTP para a API de health check."""
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from app.adapters.inbound.http.schemas import HealthResponse
from app.adapters.inbound.http.dependencies import get_health_use_case, get_request_trace_id
from app.application.ports.inbound import HealthUseCase

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"model": HealthResponse, "description": "Serviço e dependências saudáveis"},
        503: {"model": HealthResponse, "description": "Serviço degradado ou LiteLLM inacessível"},
    },
    summary="Verificação de integridade da API e LiteLLM Proxy",
)
async def health_check(
    use_case: HealthUseCase = Depends(get_health_use_case),
    trace_id: str = Depends(get_request_trace_id),
):
    health_data = await use_case.check_health(trace_id=trace_id)

    if health_data.get("status") != "ok":
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=health_data,
        )

    return health_data
