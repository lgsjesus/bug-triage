"""Contrato de dados esperado na resposta gerada pelo LLM."""
from pydantic import BaseModel, Field


class LLMRawTriageResponse(BaseModel):
    """Schema para validação do payload JSON retornado pelo modelo."""
    complexity: str = Field(description="alta, média ou baixa")
    reasoning: str = Field(description="Justificativa concisa em até 3 parágrafos")
    priority: str = Field(description="alta, média ou baixa")
