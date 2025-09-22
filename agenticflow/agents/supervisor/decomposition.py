from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ...tools.external.llm import LLMClient, LLMResult
from ...orchestration.core.orchestrator import WorkflowDefinition
from ...orchestration.tasks.graph import TaskNode
from ..capabilities.matcher import CapabilityMatcher
from .llm_schema import parse_plan


@dataclass
class LLMTaskDecomposer:
    llm: LLMClient
    matcher: CapabilityMatcher

    async def decompose(self, query: str, context: Dict[str, Any]) -> WorkflowDefinition:
        prompt = self._build_prompt(query, context)
        result: LLMResult = await self.llm.generate(prompt)
        try:
            # Prefer robust schema parsing
            wf = await parse_plan(result.text, matcher=self.matcher, default_agent=context.get("default_agent", "analyst"))
            return wf
        except Exception:
            # Fallback to single noop task if LLM output invalid
            return WorkflowDefinition(tasks=[TaskNode(task_id="t1", agent_id=context.get("default_agent", "analyst"), task_type="noop", params={"query": query})])

    def _build_prompt(self, query: str, context: Dict[str, Any]) -> str:
        return (
            "You are a planner. Given a user query, return a JSON object with a 'tasks' array. "
            "Each task has: id (string), type (string), capability (string), params (object), deps (array of ids). "
            f"Query: {query}\n"
        )
