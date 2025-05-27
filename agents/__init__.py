"""
RealityPatch Agents Package

This package contains various agents for fact-checking and claim analysis:
- Clarity Agent: Extracts and structures claims from text
- Proof Agent: Searches for evidence to verify claims
- Sage Agent: Provides additional analysis and context
"""

from .agent_clarity import run_clarity_agent
from .agent_proof import run_proof_agent

__all__ = ['run_clarity_agent', 'run_proof_agent'] 