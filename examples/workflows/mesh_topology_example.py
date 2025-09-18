#!/usr/bin/env python3
"""
MeshTopology Example - Demonstrating Partial Mesh Connectivity

This example showcases the new MeshTopology implementation with different
connectivity strategies for selective agent communication patterns.

Unlike PeerToPeer (full mesh), MeshTopology allows partial connectivity
based on strategies like capability matching, proximity, or custom rules.
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from agenticflow.workflows.topologies import (
    MeshTopology, TopologyType, create_topology
)
from agenticflow.workflows.multi_agent import MultiAgentSystem
from agenticflow.core.agent import Agent
from agenticflow.config.settings import AgentConfig, LLMProviderConfig, LLMProvider


def demonstrate_capability_based_mesh():
    """Demonstrate capability-based mesh connectivity."""
    print("🔗 Capability-Based Mesh Topology")
    print("=" * 50)
    
    # Create mesh with capability-based connections
    mesh = MeshTopology(
        "capability_mesh", 
        max_connections_per_agent=3,
        connectivity_strategy="capability_based"
    )
    
    # Add agents with overlapping capabilities
    agents_config = [
        {
            "id": "data_analyst",
            "name": "Data Analyst", 
            "capabilities": ["data_analysis", "statistics", "visualization"]
        },
        {
            "id": "ml_engineer", 
            "name": "ML Engineer",
            "capabilities": ["machine_learning", "data_analysis", "python"]
        },
        {
            "id": "web_scraper",
            "name": "Web Scraper",
            "capabilities": ["web_scraping", "data_extraction", "python"]
        },
        {
            "id": "database_admin",
            "name": "Database Admin", 
            "capabilities": ["database", "data_extraction", "sql"]
        },
        {
            "id": "data_scientist",
            "name": "Data Scientist",
            "capabilities": ["statistics", "machine_learning", "research"]
        }
    ]
    
    # Add agents to mesh
    for config in agents_config:
        mesh.add_agent(
            config["id"], 
            config["name"],
            capabilities=config["capabilities"],
            role="specialist"
        )
        print(f"✅ Added: {config['name']} with capabilities {config['capabilities']}")
    
    # Show connections based on capability overlap
    print(f"\n🔗 Capability-Based Connections:")
    for agent_id, connections in mesh.connection_matrix.items():
        agent_name = mesh.agents[agent_id].agent_name
        connected_names = [mesh.agents[conn_id].agent_name for conn_id in connections]
        print(f"   {agent_name} -> {connected_names}")
    
    # Show statistics
    stats = mesh.get_connection_stats()
    print(f"\n📊 Network Stats:")
    print(f"   Total connections: {stats['total_connections']}")
    print(f"   Connectivity ratio: {stats['connectivity_ratio']:.2%}")
    print(f"   Average connections per agent: {stats['average_connections_per_agent']:.1f}")
    
    return mesh


def demonstrate_proximity_based_mesh():
    """Demonstrate proximity-based mesh connectivity."""
    print("\n\n📍 Proximity-Based Mesh Topology")
    print("=" * 50)
    
    # Create mesh with proximity-based connections
    mesh = MeshTopology(
        "proximity_mesh",
        max_connections_per_agent=2,
        connectivity_strategy="proximity_based"
    )
    
    # Add agents with location/department metadata
    agents_config = [
        {
            "id": "us_east_analyst",
            "name": "US East Analyst",
            "metadata": {"region": "us-east", "department": "analytics", "timezone": "EST"}
        },
        {
            "id": "us_west_analyst", 
            "name": "US West Analyst",
            "metadata": {"region": "us-west", "department": "analytics", "timezone": "PST"}
        },
        {
            "id": "eu_analyst",
            "name": "EU Analyst", 
            "metadata": {"region": "europe", "department": "analytics", "timezone": "CET"}
        },
        {
            "id": "us_east_ops",
            "name": "US East Operations",
            "metadata": {"region": "us-east", "department": "operations", "timezone": "EST"}
        },
        {
            "id": "eu_ops",
            "name": "EU Operations",
            "metadata": {"region": "europe", "department": "operations", "timezone": "CET"}
        }
    ]
    
    # Add agents to mesh
    for config in agents_config:
        mesh.add_agent(
            config["id"],
            config["name"], 
            metadata=config["metadata"],
            role="regional_agent"
        )
        print(f"✅ Added: {config['name']} in {config['metadata']['region']}/{config['metadata']['department']}")
    
    # Show proximity-based connections
    print(f"\n🔗 Proximity-Based Connections:")
    for agent_id, connections in mesh.connection_matrix.items():
        agent_info = mesh.agents[agent_id]
        connected_info = [
            f"{mesh.agents[conn_id].agent_name} ({mesh.agents[conn_id].metadata.get('region', 'unknown')})"
            for conn_id in connections
        ]
        print(f"   {agent_info.agent_name} ({agent_info.metadata.get('region', 'unknown')}) -> {connected_info}")
    
    stats = mesh.get_connection_stats()
    print(f"\n📊 Network Stats:")
    print(f"   Connectivity ratio: {stats['connectivity_ratio']:.2%}")
    print(f"   Strategy: {stats['connectivity_strategy']}")
    
    return mesh


def demonstrate_different_strategies():
    """Compare different connectivity strategies."""
    print("\n\n⚖️  Comparing Connectivity Strategies")
    print("=" * 50)
    
    strategies = ["capability_based", "round_robin", "proximity_based", "random"]
    
    # Same set of agents for fair comparison
    agents_config = [
        {"id": "agent1", "name": "Agent 1", "capabilities": ["skill_a", "skill_b"]},
        {"id": "agent2", "name": "Agent 2", "capabilities": ["skill_b", "skill_c"]},
        {"id": "agent3", "name": "Agent 3", "capabilities": ["skill_a", "skill_c"]},
        {"id": "agent4", "name": "Agent 4", "capabilities": ["skill_d"]},
        {"id": "agent5", "name": "Agent 5", "capabilities": ["skill_a"]}
    ]
    
    for strategy in strategies:
        print(f"\n📋 {strategy.replace('_', ' ').title()} Strategy:")
        
        mesh = MeshTopology(
            f"compare_{strategy}",
            max_connections_per_agent=2,
            connectivity_strategy=strategy
        )
        
        # Add agents
        for config in agents_config:
            mesh.add_agent(config["id"], config["name"], capabilities=config["capabilities"])
        
        # Show results
        stats = mesh.get_connection_stats()
        print(f"   Connections: {stats['total_connections']}/{stats['max_possible_connections']}")
        print(f"   Connectivity: {stats['connectivity_ratio']:.2%}")
        
        # Show connection pattern
        connections_summary = []
        for agent_id, connections in mesh.connection_matrix.items():
            if connections:
                connections_summary.append(f"{agent_id}->{'|'.join(connections)}")
        print(f"   Pattern: {' '.join(connections_summary)}")


async def demonstrate_mesh_multi_agent_system():
    """Demonstrate MeshTopology in a real multi-agent system."""
    print("\n\n🤖 MeshTopology in Multi-Agent System")
    print("=" * 50)
    
    try:
        # Create mesh topology for specialized agents
        mesh_topology = create_topology(
            TopologyType.MESH, 
            "specialist_mesh",
            max_connections_per_agent=2,
            connectivity_strategy="capability_based"
        )
        
        # Create specialized agents (using simple config for demo)
        agents_config = [
            {
                "name": "research_agent",
                "instructions": "You specialize in research and data gathering.",
                "capabilities": ["research", "data_collection"]
            },
            {
                "name": "analysis_agent", 
                "instructions": "You specialize in data analysis and statistics.",
                "capabilities": ["analysis", "statistics", "data_processing"]
            },
            {
                "name": "writing_agent",
                "instructions": "You specialize in content creation and writing.",
                "capabilities": ["writing", "content_creation"]
            }
        ]
        
        # Create agents
        agents = []
        for config in agents_config:
            agent_config = AgentConfig(
                name=config["name"],
                instructions=config["instructions"],
                llm=LLMProviderConfig(
                    provider=LLMProvider.GROQ,  # Using Groq as it's often free
                    model="llama-3.1-8b-instant"
                )
            )
            agent = Agent(agent_config)
            agents.append(agent)
            
            # Register with mesh topology
            mesh_topology.add_agent(
                config["name"],
                config["name"].replace("_", " ").title(),
                capabilities=config["capabilities"],
                role="specialist"
            )
        
        # Create multi-agent system with mesh topology
        system = MultiAgentSystem(
            agents=agents,
            topology=mesh_topology
        )
        
        print("✅ Created multi-agent system with mesh topology")
        print(f"✅ Agents: {[agent.name for agent in agents]}")
        print(f"✅ Topology: {mesh_topology.topology_type.value}")
        
        # Show the mesh connections
        print(f"\n🔗 Agent Mesh Connections:")
        for agent_id, connections in mesh_topology.connection_matrix.items():
            connected_names = [mesh_topology.agents[conn_id].agent_name for conn_id in connections]
            print(f"   {mesh_topology.agents[agent_id].agent_name} -> {connected_names}")
        
        # Show topology stats
        topo_stats = mesh_topology.get_topology_stats()
        print(f"\n📊 System Statistics:")
        print(f"   Agents: {topo_stats['agents_count']}")
        print(f"   Routes: {topo_stats['routes_count']}")
        print(f"   Network Density: {topo_stats['connectivity']['density']:.2%}")
        
        return system
        
    except Exception as e:
        print(f"⚠️  Multi-agent demo skipped (likely missing API keys): {e}")
        return None


def demonstrate_manual_mesh_management():
    """Demonstrate manual mesh connection management."""
    print("\n\n⚙️  Manual Mesh Management")
    print("=" * 50)
    
    # Create empty mesh 
    mesh = MeshTopology("manual_mesh", max_connections_per_agent=4)
    
    # Add agents
    agent_names = ["coordinator", "worker_a", "worker_b", "specialist", "backup"]
    for name in agent_names:
        mesh.add_agent(name, name.replace("_", " ").title(), role="custom")
        print(f"✅ Added: {name}")
    
    print("\n🔗 Initial automatic connections:")
    for agent_id, connections in mesh.connection_matrix.items():
        print(f"   {agent_id} -> {list(connections)}")
    
    # Manually add strategic connections
    print("\n⚙️  Adding manual connections:")
    
    # Connect coordinator to all workers
    manual_connections = [
        ("coordinator", "worker_a", "Coordinator manages Worker A"),
        ("coordinator", "worker_b", "Coordinator manages Worker B"),
        ("specialist", "backup", "Specialist backed up by Backup"),
    ]
    
    for agent1, agent2, description in manual_connections:
        success = mesh.add_connection(agent1, agent2)
        status = "✅" if success else "❌"
        print(f"   {status} {description}: {agent1} <-> {agent2}")
    
    # Show final network
    print(f"\n🔗 Final mesh connections:")
    for agent_id, connections in mesh.connection_matrix.items():
        print(f"   {agent_id} -> {list(connections)}")
    
    # Show network statistics
    stats = mesh.get_connection_stats()
    print(f"\n📊 Final Network Stats:")
    print(f"   Total connections: {stats['total_connections']}")
    print(f"   Connectivity ratio: {stats['connectivity_ratio']:.2%}")
    print(f"   Average connections per agent: {stats['average_connections_per_agent']:.1f}")
    
    return mesh


async def main():
    """Run all MeshTopology demonstrations."""
    print("🕸️  AgenticFlow MeshTopology Demonstrations")
    print("=" * 60)
    print("Showcasing selective connectivity patterns for multi-agent systems")
    print()
    
    # Run all demonstrations
    mesh1 = demonstrate_capability_based_mesh()
    mesh2 = demonstrate_proximity_based_mesh()
    demonstrate_different_strategies()
    system = await demonstrate_mesh_multi_agent_system()
    mesh3 = demonstrate_manual_mesh_management()
    
    print("\n\n🎉 MeshTopology Demonstrations Complete!")
    print("=" * 60)
    print("✅ MeshTopology provides flexible partial connectivity")
    print("✅ Multiple connectivity strategies available")
    print("✅ Manual connection management supported")  
    print("✅ Integrates seamlessly with MultiAgentSystem")
    print()
    print("🔗 Key Benefits:")
    print("   • Selective connectivity (vs full mesh)")
    print("   • Strategy-based connections (capability, proximity, etc.)")
    print("   • Efficient for large agent networks")
    print("   • Customizable connection limits")
    print("   • Manual override capabilities")


if __name__ == "__main__":
    asyncio.run(main())