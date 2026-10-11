"""Enums de domínio para classificação de bugs."""
from enum import Enum


class Complexity(str, Enum):
    ALTA = "alta"
    MEDIA = "média"
    BAIXA = "baixa"


class Priority(str, Enum):
    ALTA = "alta"
    MEDIA = "média"
    BAIXA = "baixa"


class ModelTier(str, Enum):
    LOW = "tier-low"
    MEDIUM = "tier-medium"
    HIGH = "tier-high"
