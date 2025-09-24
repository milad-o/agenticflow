#!/usr/bin/env python3
"""
Run Flow with Planner and CapabilityExtractor using local Ollama.
"""
import asyncio
from agenticflow import Flow
from agenticflow.agent import Agent
from agenticflow.core.config import AgentConfig
from agenticflow.planner.planner import Planner
from agenticflow.orchestrator.capability_extractor import CapabilityExtractor

async def main():
    flow = Flow()

    file_mgr = Agent(AgentConfig(name="file_mgr", model="", temperature=0.0), [])
    file_mgr.discover_tools_by_names(flow.tool_registry, ["read_file", "write_file"])

    sys_admin = Agent(AgentConfig(name="sys_admin", model="", temperature=0.0), [])
    sys_admin.discover_tools_by_names(flow.tool_registry, ["shell", "list_dir", "mkdir"]) 

    flow.add_agent("file_mgr", file_mgr)
    flow.add_agent("sys_admin", sys_admin)

    flow.set_planner(Planner())
    flow.set_capability_extractor(CapabilityExtractor())

    flow.start()

    request = (
        "Create a new workspace folder named 'demo_out'. Inside it: "
        "(1) create 'data/customers.csv' with headers id,name,tier and rows 1,Alice,Gold; 2,Bob,Silver; 3,Chad,Bronze. "
        "(2) create 'scripts/count_customers.txt' containing the text 'Customers: 3'. "
        "(3) list the contents of 'demo_out'. "
        "(4) append a new customer 4,Dina,Gold to customers.csv. "
        "(5) read back customers.csv and summarize how many Gold vs Silver vs Bronze into a 'README.md' in the workspace root. "
        "(6) finally print the absolute path of 'demo_out' and list its contents."
    )

    result = await flow.arun(request)
    print("Final:", result.get("final_response"))
    flow.stop()

if __name__ == "__main__":
    asyncio.run(main())
