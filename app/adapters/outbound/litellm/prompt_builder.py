"""Construtor de prompts para classificação de bugs."""
from typing import List, Dict
from app.domain.models import BugReport

SYSTEM_PROMPT = """Você é um engenheiro sênior especialista em triagem, confiabilidade e análise de logs de produção.
Sua tarefa é analisar o relato de bug/log informado e classificar a severidade e impacto.

Regras estritas de resposta:
1. Responda ESTRITAMENTE em formato JSON puro, sem marcação markdown e sem blocos ```json.
2. O JSON deve conter EXATAMENTE estas 3 chaves:
   - "complexity": "alta", "média" ou "baixa"
   - "reasoning": justificativa técnica da conclusão simplificada em no MÁXIMO 3 parágrafos explicativos.
   - "priority": "alta", "média" ou "baixa"
3. Seja conciso, técnico e objetivo.
"""


class PromptBuilder:
    """Traduz o modelo de domínio em mensagens compatíveis com chat completion."""

    @staticmethod
    def build_messages(report: BugReport) -> List[Dict[str, str]]:
        user_content = (
            f"Projeto: {report.project_name}\n"
            f"Serviço: {report.service}\n"
            f"Data/Hora do Evento: {report.timestamp}\n"
            f"Log/Conteúdo do Erro:\n{report.content}\n\n"
            "Analise e retorne o JSON com complexity, reasoning (máx 3 parágrafos) e priority."
        )

        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]
