"""Controller HTTP para a API de triagem de bugs."""
from fastapi import APIRouter, Depends, status
from app.adapters.inbound.http.schemas import TriageRequest, TriageResponse, ErrorResponse
from app.adapters.inbound.http.dependencies import get_triage_use_case, get_request_trace_id
from app.application.ports.inbound import TriageUseCase
from app.domain.models import BugReport

router = APIRouter(prefix="/api/v1", tags=["Triage"])


@router.post(
    "/triage",
    response_model=TriageResponse,
    status_code=status.HTTP_200_OK,
    responses={
        422: {"model": ErrorResponse, "description": "Dados da requisição inválidos ou conteúdo excede o limite"},
        502: {"model": ErrorResponse, "description": "Falha na resposta do modelo ou upstream indisponível"},
        504: {"model": ErrorResponse, "description": "Timeout na comunicação com o LLM"},
    },
    summary="Triagem e classificação inteligente de bugs a partir de logs",
)
async def triage_log(
    request_dto: TriageRequest,
    use_case: TriageUseCase = Depends(get_triage_use_case),
    trace_id: str = Depends(get_request_trace_id),
) -> TriageResponse:
    report = BugReport(
        project_name=request_dto.project_name,
        service=request_dto.service,
        timestamp=request_dto.timestamp,
        content=request_dto.content,
    )

    result = await use_case.execute(report=report, trace_id=trace_id)

    return TriageResponse(
        trace_id=result.trace_id,
        complexity=result.complexity.value,
        reasoning=result.reasoning,
        priority=result.priority.value,
        timestamp=result.timestamp,
    )
