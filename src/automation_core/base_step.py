"""
Base class for pipeline steps
"""

import logging
from abc import ABC, abstractmethod


class BaseStep(ABC):
    """Abstract base class for all pipeline steps"""

    def __init__(self, step_id: str, step_type: str, version: str):
        self.step_id = step_id
        self.step_type = step_type
        self.version = version
        self.logger = logging.getLogger(f"{__name__}.{step_id}")

    @abstractmethod
    def execute(self, context: dict) -> dict:
        """
        Execute the step logic

        Args:
            context: Dictionary containing pipeline context and step inputs

        Returns:
            Dictionary containing step output and status
        """
        pass
