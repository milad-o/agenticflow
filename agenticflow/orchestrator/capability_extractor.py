"""LLM-based capability extractor for tasks."""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional
from langchain_core.messages import HumanMessage
from agenticflow.core.models import get_chat_model


class CapabilityExtractor:
    def __init__(self, model_name: Optional[str] = None, temperature: float = 0.0):
        self.llm = get_chat_model(model_name=model_name, temperature=temperature)

    async def aextract(self, task_description: str, agents_summary: List[Dict[str, Any]]) -> Dict[str, Any]:
        prompt = f"""
Analyze the task and propose required capabilities and helpful tools.
STRICT JSON ONLY with fields:
{{
  "capabilities": ["file_write", "file_read", "shell"],
  "tools": ["mkdir", "write_file", "read_file", "list_dir"],
  "notes": "..."
}}
Task: {task_description}
Agents: {json.dumps(agents_summary)}
Rules:
- Only return valid JSON. No extra text.
- capabilities: short keywords like file_write, file_read, shell, general.
- tools: pick from agent-exposed tools when possible.
"""
        try:
            rsp = await self.llm.ainvoke([HumanMessage(content=prompt)])
            data = json.loads(rsp.content) if isinstance(rsp.content, str) else {}
            # sanity defaults
            data.setdefault("capabilities", ["general"])
            data.setdefault("tools", [])
            data.setdefault("notes", "")
            return data
        except Exception:
            return {"capabilities": ["general"], "tools": [], "notes": "fallback"}
