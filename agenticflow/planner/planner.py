"""Planner agent that generates a DAG of tasks with dependencies."""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage
from agenticflow.core.models import get_chat_model


class PlanTask(BaseModel):
    id: str
    description: str
    priority: int = 1
    dependencies: List[str] = Field(default_factory=list)
    # Optional suggestions from the planner
    agent: Optional[str] = None
    capabilities: List[str] = Field(default_factory=list)


class Plan(BaseModel):
    tasks: List[PlanTask] = Field(default_factory=list)


class Planner:
    """LLM-backed planner that returns a structured DAG of tasks."""

    def __init__(self, model_name: Optional[str] = None, temperature: float = 0.0):
        self.llm = get_chat_model(model_name=model_name, temperature=temperature)

    async def aplan(self, user_request: str, agent_catalog: Optional[List[Dict[str, Any]]] = None) -> Plan:
        prompt_template = """
Produce a plan as STRICT JSON only, with the schema:
{{
  "tasks": [
    {{
      "id": "task_1",
      "description": "...",
      "priority": 1,
      "dependencies": [],
      "agent": "fs_agent",
      "capabilities": ["file_write", "file_read"]
    }}
  ]
}}
Guidelines:
- Break the request into MINIMAL atomic steps (one action per task).
- Prefer concise descriptions.
- Include dependencies to enable parallel execution where safe.
- If reasonable, suggest an agent name and capability hints per task.
- Output ONLY valid JSON (no commentary, no code fences).

Available agents (JSON):
{agent_catalog}

User request: {user_request}
"""
        import json as _json
        prompt = prompt_template.format(user_request=user_request, agent_catalog=_json.dumps(agent_catalog or [], ensure_ascii=False))
        try:
            msg = await self.llm.ainvoke([HumanMessage(content=prompt)])
            content = msg.content if isinstance(msg.content, str) else str(msg.content)
            plan_dict = self._extract_json(content)
            plan = Plan(**plan_dict)
            if not plan.tasks:
                # fallback single task
                plan = Plan(tasks=[PlanTask(id="task_1", description=user_request, priority=1, dependencies=[])])
            return plan
        except Exception:
            # conservative fallback
            return Plan(tasks=[PlanTask(id="task_1", description=user_request, priority=1, dependencies=[])])

    def _extract_json(self, text: str) -> Dict[str, Any]:
        # If it's pure JSON
        try:
            return json.loads(text)
        except Exception:
            pass
        # Try to find a JSON object in the text
        m = re.search(r"\{[\s\S]*\}", text)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                pass
        return {"tasks": []}