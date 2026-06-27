"""Session 7 intelligent workflow package."""

from .analytics import ModelBundle, load_campaign_data, train_discount_model
from .contracts import (
    FollowUpAnswer,
    RandomForestConfig,
    WorkflowRequest,
    WorkflowResult,
)
from .workflow import IntelligentWorkflow, LocalOllamaLLM

__all__ = [
    "FollowUpAnswer",
    "IntelligentWorkflow",
    "LocalOllamaLLM",
    "ModelBundle",
    "RandomForestConfig",
    "WorkflowRequest",
    "WorkflowResult",
    "load_campaign_data",
    "train_discount_model",
]
