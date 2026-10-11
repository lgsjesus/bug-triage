"""Testes unitários para regras de domínio e seleção heurística de modelos."""
import pytest
from app.domain.enums import Complexity, Priority, ModelTier
from app.application.services.model_selection_service import ModelSelectionService


def test_log_curto_sem_termos_criticos_seleciona_tier_low():
    selector = ModelSelectionService()
    tier, reason = selector.select_tier("Erro no layout: botão com texto desalinhado no menu")
    assert tier == ModelTier.LOW
    assert "padrão" in reason


def test_log_longo_acima_de_300_caracteres_seleciona_tier_medium():
    selector = ModelSelectionService()
    long_content = "Exception in thread 'main' " + ("x" * 301)
    tier, reason = selector.select_tier(long_content)
    assert tier == ModelTier.MEDIUM
    assert "Log extenso" in reason


def test_log_exatos_300_caracteres_fica_em_tier_low():
    selector = ModelSelectionService()
    exact_300 = "a" * 300
    tier, _ = selector.select_tier(exact_300)
    assert tier == ModelTier.LOW


@pytest.mark.parametrize(
    "termo",
    ["deadlock", "memory leak", "race condition", "segfault", "corruption", "DEADLOCK", "Memory Leak"],
)
def test_termos_criticos_selecionam_tier_high(termo):
    selector = ModelSelectionService()
    content = f"Alerta crítico no cluster: possível {termo} detectado no worker de pagamentos"
    tier, reason = selector.select_tier(content)
    assert tier == ModelTier.HIGH
    assert "Termo crítico" in reason


def test_termo_critico_tem_precedencia_sobre_log_longo():
    selector = ModelSelectionService()
    huge_with_critical = ("stacktrace de 1000 linhas..." * 50) + " deadlock no banco de dados"
    tier, reason = selector.select_tier(huge_with_critical)
    assert tier == ModelTier.HIGH


def test_enums_valores_em_portugues():
    assert Complexity.ALTA.value == "alta"
    assert Complexity.MEDIA.value == "média"
    assert Complexity.BAIXA.value == "baixa"

    assert Priority.ALTA.value == "alta"
    assert Priority.MEDIA.value == "média"
    assert Priority.BAIXA.value == "baixa"
