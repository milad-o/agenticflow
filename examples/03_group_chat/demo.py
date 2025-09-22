import argparse
import asyncio
import os
from pathlib import Path
import shutil
import subprocess

from agenticflow.agents.base.agent import Agent
from agenticflow.agents.supervisor.group_chat import GroupChatSupervisor
from agenticflow.orchestration.core.orchestrator import Orchestrator
from agenticflow.observability.graph import mermaid_from_definition
from agenticflow.observability.system_viz import mermaid_system, dot_system
from agenticflow.agents.tool_agent import ToolAgent
from agenticflow.agents.tools.builtin import FSReadTool, HttpFetchTool


class ChatAgent(Agent):
    async def perform_task(self, task_type, params):
        if task_type != "chat":
            return {"ok": False}
        # Minimalistic local response; can be replaced with an LLM
        topic = params.get("topic", "")
        rnd = params.get("round", 0)
        return {"ok": True, "message": f"[{self.agent_id} r{rnd}] {topic}"}


class ChatToolAgent(ToolAgent):
    async def perform_task(self, task_type, params):
        if task_type == "chat":
            topic = params.get("topic", "")
            rnd = params.get("round", 0)
            return {"ok": True, "message": f"[{self.agent_id} r{rnd}] {topic}"}
        return await super().perform_task(task_type, params)


def try_write_svg(dot_text: str, out_svg: Path):
    """Attempt to render DOT to SVG using Graphviz dot if available."""
    if not shutil.which("dot"):
        return False
    p = subprocess.Popen(["dot", "-Tsvg", "-o", str(out_svg)], stdin=subprocess.PIPE, text=True)
    p.communicate(dot_text)
    return p.returncode == 0


async def main_async(participants: list[str], rounds: int, topic: str, store: str, db_path: str | None, outdir: str, with_tools: bool):
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)

    # Build DAG
    sup = GroupChatSupervisor(agent_task_type="chat")
    wf = sup.build_workflow(participants=participants, rounds=rounds, topic=topic)

    # Orchestrator (local agents)
    if store == "sqlite":
        from agenticflow.adapters.store.sqlite import SQLiteEventStore
        es = SQLiteEventStore(db_path or (out / "events.sqlite3"))
    else:
        from agenticflow.adapters.store.memory import InMemoryEventStore
        es = InMemoryEventStore()
    orch = Orchestrator(event_store=es, emit_workflow_started=True, emit_workflow_lifecycle=True, max_parallelism=4, per_agent_concurrency=1)

    # Register local agents
    for a in participants:
        if with_tools:
            roots = [str(Path.cwd())]
            tools = {
                "fs_read": FSReadTool(roots=roots),
                "http_fetch": HttpFetchTool(allow_patterns=[r"^https?://"]),
            }
            orch.register_agent(ChatToolAgent(a, tools=tools))
        else:
            orch.register_agent(ChatAgent(a))

    wf_id = await orch.execute_workflow(wf)
    print("Started:", wf_id)

    # Render workflow diagram (Mermaid)
    (out / "workflow.mmd").write_text(mermaid_from_definition(wf))

    # Render system diagram (agents + task types)
    # Introspect tools if ToolAgents registered
    tools_by_agent = {}
    for a in participants:
        ag = orch._agents.get(a)
        if isinstance(ag, ToolAgent):
            tools_by_agent[a] = list(getattr(ag, "tools", {}).keys())
    task_types = {a: ["chat"] for a in participants}
    sys_mmd = mermaid_system(participants, tools_by_agent=tools_by_agent, task_types_by_agent=task_types)
    (out / "system.mmd").write_text(sys_mmd)

    sys_dot = dot_system(participants, tools_by_agent=tools_by_agent, task_types_by_agent=task_types)
    (out / "system.dot").write_text(sys_dot)
    if try_write_svg(sys_dot, out / "system.svg"):
        print("Wrote:", out / "system.svg")
    else:
        print("Graphviz not available; wrote DOT and Mermaid instead.")


def main():
    ap = argparse.ArgumentParser(description="Local multi-agent group chat demo")
    ap.add_argument("--participants", nargs="+", required=True)
    ap.add_argument("--rounds", type=int, default=2)
    ap.add_argument("--topic", default="Discuss topic")
    ap.add_argument("--store", choices=["memory","sqlite"], default="memory")
    ap.add_argument("--db-path", default=None)
    ap.add_argument("--outdir", default="examples/03_group_chat/artifacts")
    ap.add_argument("--with-tools", action="store_true", help="Register ChatToolAgent with fs_read and http_fetch")
    args = ap.parse_args()
    asyncio.run(main_async(args.participants, args.rounds, args.topic, args.store, args.db_path, args.outdir, args.with_tools))


if __name__ == "__main__":
    main()