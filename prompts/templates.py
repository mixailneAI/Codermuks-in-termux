# =============================================================================
#  Codermuks in Termux — системные промпты v1.4.0 (фасад)
# =============================================================================
#  Все промпты вынесены в отдельные файлы. Этот модуль просто
#  реэкспортирует их, чтобы старый код мог импортировать как раньше:
#      from prompts.templates import SYSTEM_PLANNER
# =============================================================================

from prompts.project_decider import SYSTEM_PROJECT_DECIDER
from prompts.planner import SYSTEM_PLANNER
from prompts.coder import SYSTEM_CODER
from prompts.fixer import SYSTEM_FIXER
from prompts.researcher import SYSTEM_RESEARCHER
from prompts.analyzer import SYSTEM_ANALYZER
from prompts.reasoning import SYSTEM_REASONING


__all__ = [
    "SYSTEM_PROJECT_DECIDER",
    "SYSTEM_PLANNER",
    "SYSTEM_CODER",
    "SYSTEM_FIXER",
    "SYSTEM_RESEARCHER",
    "SYSTEM_ANALYZER",
    "SYSTEM_REASONING",
]
