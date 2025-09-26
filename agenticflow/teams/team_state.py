"""
Team State Management

Centralized state for hierarchical agent teams based on LangGraph patterns.
"""
from typing import Dict, List, Any, Optional
from pydantic import BaseModel


class TeamState(BaseModel):
    """Shared state for hierarchical agent teams."""

    # Core task information
    current_task: str = ""
    messages: List[Dict[str, str]] = []

    # Team coordination
    next_worker: str = ""
    completed_workers: List[str] = []

    # Results and context
    worker_results: Dict[str, Any] = {}
    global_context: Dict[str, Any] = {}

    # Execution tracking
    is_complete: bool = False
    requires_human_input: bool = False
    error_message: str = ""
    execution_count: int = 0

    def add_message(self, role: str, content: str) -> None:
        """Add a message to the conversation history."""
        self.messages.append({"role": role, "content": content})

    def set_worker_result(self, worker_name: str, result: Any) -> None:
        """Store result from a worker agent."""
        self.worker_results[worker_name] = result
        if worker_name not in self.completed_workers:
            self.completed_workers.append(worker_name)

    def get_worker_result(self, worker_name: str) -> Optional[Any]:
        """Get result from a specific worker."""
        return self.worker_results.get(worker_name)

    def update_context(self, key: str, value: Any) -> None:
        """Update global context."""
        self.global_context[key] = value

    def get_context(self, key: str) -> Optional[Any]:
        """Get value from global context."""
        return self.global_context.get(key)

    def mark_complete(self) -> None:
        """Mark the team task as complete."""
        self.is_complete = True
        self.add_message("system", "Team task completed successfully")

    def mark_error(self, error: str) -> None:
        """Mark the team task as failed."""
        self.error_message = error
        self.add_message("system", f"Team task failed: {error}")

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the team execution."""
        return {
            "task": self.current_task,
            "completed_workers": self.completed_workers,
            "total_messages": len(self.messages),
            "is_complete": self.is_complete,
            "has_error": bool(self.error_message)
        }