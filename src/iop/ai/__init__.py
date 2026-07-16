"""Packaged AI guidance and project installer for IoP applications."""

from .installer import AgentGuidanceConflictError, InstallResult, install_agent_guidance

__all__ = [
    "AgentGuidanceConflictError",
    "InstallResult",
    "install_agent_guidance",
]
