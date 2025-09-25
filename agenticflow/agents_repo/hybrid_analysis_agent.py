"""Hybrid RPAVH Analysis Agent - CSV-focused analytics (chunked).

Provides a fast analysis agent that can compute group-wise aggregations over large CSVs
without loading the entire file into memory.
"""
from typing import Optional, Dict, Any
from agenticflow.agent.hybrid_rpavh_agent import HybridRPAVHAgent
from agenticflow.core.config import AgentConfig
from agenticflow.core.roles import AgentRole


class AnalysisAgentRules:
    def get_rules_text(self) -> str:
        return (
            "ANALYSIS AGENT RULES\n\n"
            "- When asked to compute aggregates (average/mean/group by), prefer csv_chunk_aggregate.\n"
            "- Accept file path, group_by column, and numeric value column.\n"
            "- Keep memory usage low; do not read entire file at once.\n"
            "- Output concise, structured results that downstream reporter can tabulate.\n"
        )


def create_hybrid_analysis_agent(
    name: str = "hybrid_analysis",
    max_attempts: int = 2,
    model_name: str = "",
    csv_path: Optional[str] = None,
    group_by: Optional[str] = None,
    value_column: Optional[str] = None,
) -> HybridRPAVHAgent:
    config = AgentConfig(
        name=name,
        model=model_name,
        temperature=0.0,
        role=AgentRole.ANALYST if hasattr(AgentRole, "ANALYST") else AgentRole.REPORTER,
        capabilities=["data_analysis", "csv_aggregate"],
        system_prompt=(
            "You are a fast data analysis agent specialized in CSV analytics.\n"
            "Prefer direct tool execution and avoid unnecessary LLM calls."
        ),
        rules=AnalysisAgentRules(),
    )

    agent = HybridRPAVHAgent(
        config=config,
        max_attempts=max_attempts,
        use_llm_reflection=False,
        use_llm_verification=False,
    )

    agent.static_resources.update(
        {
            "csv_path": csv_path or "",
            "group_by": group_by or "",
            "value_column": value_column or "",
        }
    )

    # Disable auto discovery; demo will adopt tools explicitly
    try:
        setattr(agent, "auto_discover", False)
    except Exception:
        pass
    return agent