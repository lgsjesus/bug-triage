"""Tradutor e normalizador da resposta crua do LLM para o domínio."""
import json
import re
from typing import Tuple, Optional
from app.domain.enums import Complexity, Priority
from app.domain.models import TokenUsage
from app.domain.exceptions import InvalidLLMResponseError
from app.adapters.outbound.litellm.llm_schemas import LLMRawTriageResponse

_COMPLEXITY_MAP = {
    "alta": Complexity.ALTA,
    "alto": Complexity.ALTA,
    "high": Complexity.ALTA,
    "critical": Complexity.ALTA,
    "crítica": Complexity.ALTA,
    "critica": Complexity.ALTA,
    "média": Complexity.MEDIA,
    "media": Complexity.MEDIA,
    "médio": Complexity.MEDIA,
    "medio": Complexity.MEDIA,
    "medium": Complexity.MEDIA,
    "baixa": Complexity.BAIXA,
    "baixo": Complexity.BAIXA,
    "low": Complexity.BAIXA,
}

_PRIORITY_MAP = {
    "alta": Priority.ALTA,
    "alto": Priority.ALTA,
    "high": Priority.ALTA,
    "critical": Priority.ALTA,
    "crítica": Priority.ALTA,
    "critica": Priority.ALTA,
    "urgente": Priority.ALTA,
    "média": Priority.MEDIA,
    "media": Priority.MEDIA,
    "médio": Priority.MEDIA,
    "medio": Priority.MEDIA,
    "medium": Priority.MEDIA,
    "baixa": Priority.BAIXA,
    "baixo": Priority.BAIXA,
    "low": Priority.BAIXA,
}


class ResponseTranslator:
    """Isola a lógica de parsing, higienização e conversão de contratos da IA."""

    @staticmethod
    def clean_json_text(text: str) -> str:
        """Remove cercaduras markdown code fence como ```json ... ``` se presentes."""
        stripped = (text or "").strip()
        # Remove fence ```json ... ``` ou ``` ... ```
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", stripped)
        if match:
            return match.group(1).strip()
        return stripped

    @classmethod
    def parse_and_validate(cls, raw_content: str) -> Tuple[Complexity, str, Priority]:
        """Faz parse do JSON retornado e normaliza para as entidades do domínio."""
        if not raw_content or not raw_content.strip():
            raise InvalidLLMResponseError("O modelo retornou uma resposta vazia.")

        cleaned = cls.clean_json_text(raw_content)

        try:
            parsed_data = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise InvalidLLMResponseError(
                f"Falha ao decodificar JSON retornado pelo modelo: {exc}"
            ) from exc

        try:
            raw_response = LLMRawTriageResponse.model_validate(parsed_data)
        except Exception as exc:
            raise InvalidLLMResponseError(
                f"Estrutura da resposta incompatível com o contrato esperado: {exc}"
            ) from exc

        # Normalização de complexidade
        comp_key = raw_response.complexity.strip().lower()
        complexity = _COMPLEXITY_MAP.get(comp_key)
        if not complexity:
            raise InvalidLLMResponseError(
                f"Complexidade '{raw_response.complexity}' não reconhecida pelo domínio."
            )

        # Normalização de prioridade
        prio_key = raw_response.priority.strip().lower()
        priority = _PRIORITY_MAP.get(prio_key)
        if not priority:
            raise InvalidLLMResponseError(
                f"Prioridade '{raw_response.priority}' não reconhecida pelo domínio."
            )

        # Higienização de parágrafos: garantir no máximo 3 parágrafos
        paragraphs = [p.strip() for p in raw_response.reasoning.split("\n\n") if p.strip()]
        if not paragraphs:
            paragraphs = [p.strip() for p in raw_response.reasoning.split("\n") if p.strip()]

        if len(paragraphs) > 3:
            # Se vier mais que 3, consolida mantendo no máximo 3 parágrafos
            reasoning = "\n\n".join(paragraphs[:2] + [" ".join(paragraphs[2:])])
        elif paragraphs:
            reasoning = "\n\n".join(paragraphs)
        else:
            reasoning = raw_response.reasoning.strip()

        return complexity, reasoning, priority

    @staticmethod
    def extract_token_usage(usage_obj: Optional[object]) -> TokenUsage:
        """Extrai contagem de tokens com segurança contra campos nulos."""
        if not usage_obj:
            return TokenUsage(prompt_tokens=None, completion_tokens=None, total_tokens=None)

        prompt_tokens = getattr(usage_obj, "prompt_tokens", None)
        completion_tokens = getattr(usage_obj, "completion_tokens", None)
        total_tokens = getattr(usage_obj, "total_tokens", None)

        return TokenUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
        )
