"""SSIS-specific tools for DTSX file analysis."""

import os
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Annotated, List, Optional, Dict, Any
from langchain_core.tools import tool

@tool
def parse_dtsx_file(
    filepath: Annotated[str, "Path to the DTSX file to parse"],
    directory: Annotated[str, "Directory containing the file (default: examples/artifacts)"] = "examples/artifacts"
) -> str:
    """Parse a DTSX file and extract basic structure."""
    try:
        full_path = os.path.join(directory, filepath)
        if not os.path.exists(full_path):
            return f"❌ File not found: {full_path}"
        
        # Parse XML
        tree = ET.parse(full_path)
        root = tree.getroot()
        
        # Extract basic package information
        package_info = {
            "filename": filepath,
            "root_tag": root.tag,
            "namespace": root.tag.split('}')[0] + '}' if '}' in root.tag else '',
            "attributes": dict(root.attrib),
            "child_elements": [child.tag for child in root],
            "file_size": os.path.getsize(full_path)
        }
        
        return f"✅ Parsed DTSX file '{filepath}':\n{json.dumps(package_info, indent=2)}"
    except ET.ParseError as e:
        return f"❌ XML Parse Error: {e}"
    except Exception as e:
        return f"❌ Error parsing DTSX file: {e}"

@tool
def extract_data_flows(
    filepath: Annotated[str, "Path to the DTSX file"],
    directory: Annotated[str, "Directory containing the file (default: examples/artifacts)"] = "examples/artifacts"
) -> str:
    """Extract data flow information from DTSX file."""
    try:
        full_path = os.path.join(directory, filepath)
        tree = ET.parse(full_path)
        root = tree.getroot()
        
        data_flows = []
        
        # Find all DataFlow elements
        for dataflow in root.iter():
            if 'DataFlow' in dataflow.tag or 'dataflow' in dataflow.tag.lower():
                flow_info = {
                    "element": dataflow.tag,
                    "attributes": dict(dataflow.attrib),
                    "children": [child.tag for child in dataflow]
                }
                data_flows.append(flow_info)
        
        # Find data flow tasks
        for task in root.iter():
            if 'DataFlowTask' in task.tag or 'dataflowtask' in task.tag.lower():
                task_info = {
                    "task_type": "DataFlowTask",
                    "attributes": dict(task.attrib),
                    "children": [child.tag for child in task]
                }
                data_flows.append(task_info)
        
        return f"✅ Found {len(data_flows)} data flow elements:\n{json.dumps(data_flows, indent=2)}"
    except Exception as e:
        return f"❌ Error extracting data flows: {e}"

@tool
def extract_connections(
    filepath: Annotated[str, "Path to the DTSX file"],
    directory: Annotated[str, "Directory containing the file (default: examples/artifacts)"] = "examples/artifacts"
) -> str:
    """Extract connection information from DTSX file."""
    try:
        full_path = os.path.join(directory, filepath)
        tree = ET.parse(full_path)
        root = tree.getroot()
        
        connections = []
        
        # Find connection managers
        for conn in root.iter():
            if 'ConnectionManager' in conn.tag or 'connectionmanager' in conn.tag.lower():
                conn_info = {
                    "type": "ConnectionManager",
                    "attributes": dict(conn.attrib),
                    "properties": {}
                }
                
                # Extract connection properties
                for prop in conn.iter():
                    if 'Property' in prop.tag or 'property' in prop.tag.lower():
                        if 'Name' in prop.attrib and 'Value' in prop.attrib:
                            conn_info["properties"][prop.attrib['Name']] = prop.attrib['Value']
                
                connections.append(conn_info)
        
        # Find OLE DB connections
        for ole_conn in root.iter():
            if 'OleDbConnection' in ole_conn.tag or 'oledbconnection' in ole_conn.tag.lower():
                conn_info = {
                    "type": "OLE DB Connection",
                    "attributes": dict(ole_conn.attrib),
                    "properties": {}
                }
                
                for prop in ole_conn.iter():
                    if 'Property' in prop.tag or 'property' in prop.tag.lower():
                        if 'Name' in prop.attrib and 'Value' in prop.attrib:
                            conn_info["properties"][prop.attrib['Name']] = prop.attrib['Value']
                
                connections.append(conn_info)
        
        return f"✅ Found {len(connections)} connections:\n{json.dumps(connections, indent=2)}"
    except Exception as e:
        return f"❌ Error extracting connections: {e}"

@tool
def extract_tasks(
    filepath: Annotated[str, "Path to the DTSX file"],
    directory: Annotated[str, "Directory containing the file (default: examples/artifacts)"] = "examples/artifacts"
) -> str:
    """Extract all tasks from DTSX file."""
    try:
        full_path = os.path.join(directory, filepath)
        tree = ET.parse(full_path)
        root = tree.getroot()
        
        tasks = []
        
        # Find all task elements
        for task in root.iter():
            if 'Task' in task.tag and 'Task' != task.tag:
                task_info = {
                    "task_type": task.tag,
                    "attributes": dict(task.attrib),
                    "children": [child.tag for child in task],
                    "properties": {}
                }
                
                # Extract task properties
                for prop in task.iter():
                    if 'Property' in prop.tag or 'property' in prop.tag.lower():
                        if 'Name' in prop.attrib and 'Value' in prop.attrib:
                            task_info["properties"][prop.attrib['Name']] = prop.attrib['Value']
                
                tasks.append(task_info)
        
        return f"✅ Found {len(tasks)} tasks:\n{json.dumps(tasks, indent=2)}"
    except Exception as e:
        return f"❌ Error extracting tasks: {e}"

@tool
def extract_variables(
    filepath: Annotated[str, "Path to the DTSX file"],
    directory: Annotated[str, "Directory containing the file (default: examples/artifacts)"] = "examples/artifacts"
) -> str:
    """Extract variables from DTSX file."""
    try:
        full_path = os.path.join(directory, filepath)
        tree = ET.parse(full_path)
        root = tree.getroot()
        
        variables = []
        
        # Find variable elements
        for var in root.iter():
            if 'Variable' in var.tag or 'variable' in var.tag.lower():
                var_info = {
                    "attributes": dict(var.attrib),
                    "properties": {}
                }
                
                # Extract variable properties
                for prop in var.iter():
                    if 'Property' in prop.tag or 'property' in prop.tag.lower():
                        if 'Name' in prop.attrib and 'Value' in prop.attrib:
                            var_info["properties"][prop.attrib['Name']] = prop.attrib['Value']
                
                variables.append(var_info)
        
        return f"✅ Found {len(variables)} variables:\n{json.dumps(variables, indent=2)}"
    except Exception as e:
        return f"❌ Error extracting variables: {e}"

@tool
def create_package_summary(
    filepath: Annotated[str, "Path to the DTSX file"],
    directory: Annotated[str, "Directory containing the file (default: examples/artifacts)"] = "examples/artifacts"
) -> str:
    """Create a comprehensive summary of the SSIS package."""
    try:
        full_path = os.path.join(directory, filepath)
        tree = ET.parse(full_path)
        root = tree.getroot()
        
        summary = {
            "package_name": filepath,
            "file_size_bytes": os.path.getsize(full_path),
            "total_elements": len(list(root.iter())),
            "element_types": {},
            "has_data_flows": False,
            "has_connections": False,
            "has_tasks": False,
            "has_variables": False
        }
        
        # Count element types
        for element in root.iter():
            tag_name = element.tag.split('}')[-1] if '}' in element.tag else element.tag
            summary["element_types"][tag_name] = summary["element_types"].get(tag_name, 0) + 1
            
            # Check for specific components
            if 'DataFlow' in element.tag:
                summary["has_data_flows"] = True
            if 'Connection' in element.tag:
                summary["has_connections"] = True
            if 'Task' in element.tag and 'Task' != element.tag:
                summary["has_tasks"] = True
            if 'Variable' in element.tag:
                summary["has_variables"] = True
        
        return f"✅ Package summary:\n{json.dumps(summary, indent=2)}"
    except Exception as e:
        return f"❌ Error creating package summary: {e}"

@tool
def search_package_content(
    filepath: Annotated[str, "Path to the DTSX file"],
    search_term: Annotated[str, "Term to search for in the package"],
    directory: Annotated[str, "Directory containing the file (default: examples/artifacts)"] = "examples/artifacts"
) -> str:
    """Search for specific content within the SSIS package."""
    try:
        full_path = os.path.join(directory, filepath)
        tree = ET.parse(full_path)
        root = tree.getroot()
        
        matches = []
        search_lower = search_term.lower()
        
        # Search through all elements
        for element in root.iter():
            # Search in element tag
            if search_lower in element.tag.lower():
                matches.append({
                    "type": "element_tag",
                    "element": element.tag,
                    "attributes": dict(element.attrib),
                    "context": "Element tag match"
                })
            
            # Search in attributes
            for attr_name, attr_value in element.attrib.items():
                if search_lower in attr_value.lower():
                    matches.append({
                        "type": "attribute_value",
                        "element": element.tag,
                        "attribute": attr_name,
                        "value": attr_value,
                        "context": f"Attribute '{attr_name}' match"
                    })
            
            # Search in text content
            if element.text and search_lower in element.text.lower():
                matches.append({
                    "type": "text_content",
                    "element": element.tag,
                    "text": element.text.strip(),
                    "context": "Text content match"
                })
        
        return f"✅ Found {len(matches)} matches for '{search_term}':\n{json.dumps(matches, indent=2)}"
    except Exception as e:
        return f"❌ Error searching package content: {e}"
