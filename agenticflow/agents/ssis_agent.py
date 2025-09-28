"""SSIS Analysis Agent for complex DTSX file processing and analysis."""

import os
import json
import sqlite3
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Annotated, List, Optional, Dict, Any, Tuple
from langchain_core.tools import tool
from langchain_core.embeddings import Embeddings
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
import chromadb
from ..core.flow import Agent

class SSISAnalysisAgent(Agent):
    """Agent specialized in SSIS DTSX file analysis and data flow understanding."""
    
    def __init__(self, name: str = "ssis_agent", description: str = "SSIS DTSX file analysis specialist", 
                 vector_backend: str = "chroma", persistent: bool = False):
        tools = self._create_tools()
        super().__init__(name, tools=tools, description=description)
        self._vector_store = None
        self._embeddings = None
        self._vector_backend = vector_backend  # "chroma", "sqlite", or "none"
        self._persistent = persistent
        self._db_path = "examples/artifacts/ssis_vectors.db" if persistent else ":memory:"
        self._initialize_embeddings()
    
    def _initialize_embeddings(self):
        """Initialize embeddings for vector store."""
        if self._vector_backend == "none":
            self._embeddings = None
            return
            
        try:
            if self._vector_backend == "chroma":
                # Use a lightweight model for embeddings
                self._embeddings = HuggingFaceEmbeddings(
                    model_name="all-MiniLM-L6-v2",
                    model_kwargs={'device': 'cpu'}
                )
            elif self._vector_backend == "sqlite":
                # For SQLite, we'll use simple text similarity
                self._embeddings = None
                self._init_sqlite_db()
        except Exception as e:
            print(f"Warning: Could not initialize embeddings: {e}")
            self._embeddings = None
    
    def _init_sqlite_db(self):
        """Initialize SQLite database for text storage and similarity search."""
        try:
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ssis_elements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filepath TEXT,
                    element_tag TEXT,
                    element_text TEXT,
                    attributes TEXT,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Warning: Could not initialize SQLite database: {e}")
    
    def _create_tools(self) -> List:
        """Create SSIS analysis tools."""
        return [
            self._parse_dtsx_file,
            self._extract_data_flows,
            self._extract_connections,
            self._extract_tasks,
            self._extract_variables,
            self._analyze_package_structure,
            self._find_data_sources,
            self._find_data_destinations,
            self._trace_data_lineage,
            self._validate_package,
            self._create_package_summary,
            self._search_package_content,
            self._index_package_for_search,
            self._query_package_semantic,
            self._export_package_analysis,
            self._compare_packages,
            self._extract_error_handling,
            self._analyze_performance_implications
        ]
    
    @tool
    def _parse_dtsx_file(
        self,
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
    def _extract_data_flows(
        self,
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
    def _extract_connections(
        self,
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
    def _extract_tasks(
        self,
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
    def _extract_variables(
        self,
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
    def _analyze_package_structure(
        self,
        filepath: Annotated[str, "Path to the DTSX file"],
        directory: Annotated[str, "Directory containing the file (default: examples/artifacts)"] = "examples/artifacts"
    ) -> str:
        """Analyze the overall structure of the SSIS package."""
        try:
            full_path = os.path.join(directory, filepath)
            tree = ET.parse(full_path)
            root = tree.getroot()
            
            structure = {
                "package_name": filepath,
                "root_element": root.tag,
                "total_elements": len(list(root.iter())),
                "element_hierarchy": {},
                "element_counts": {}
            }
            
            # Build element hierarchy
            def build_hierarchy(element, level=0):
                if level > 5:  # Limit depth to avoid too much detail
                    return
                
                tag_name = element.tag.split('}')[-1] if '}' in element.tag else element.tag
                if tag_name not in structure["element_hierarchy"]:
                    structure["element_hierarchy"][tag_name] = {
                        "count": 0,
                        "level": level,
                        "attributes": list(element.attrib.keys()) if element.attrib else []
                    }
                
                structure["element_hierarchy"][tag_name]["count"] += 1
                structure["element_counts"][tag_name] = structure["element_counts"].get(tag_name, 0) + 1
                
                for child in element:
                    build_hierarchy(child, level + 1)
            
            build_hierarchy(root)
            
            return f"✅ Package structure analysis:\n{json.dumps(structure, indent=2)}"
        except Exception as e:
            return f"❌ Error analyzing package structure: {e}"
    
    @tool
    def _find_data_sources(
        self,
        filepath: Annotated[str, "Path to the DTSX file"],
        directory: Annotated[str, "Directory containing the file (default: examples/artifacts)"] = "examples/artifacts"
    ) -> str:
        """Find all data sources in the SSIS package."""
        try:
            full_path = os.path.join(directory, filepath)
            tree = ET.parse(full_path)
            root = tree.getroot()
            
            data_sources = []
            
            # Look for source components
            for element in root.iter():
                if any(keyword in element.tag.lower() for keyword in ['source', 'input', 'extract']):
                    source_info = {
                        "element_type": element.tag,
                        "attributes": dict(element.attrib),
                        "properties": {}
                    }
                    
                    # Extract source properties
                    for prop in element.iter():
                        if 'Property' in prop.tag or 'property' in prop.tag.lower():
                            if 'Name' in prop.attrib and 'Value' in prop.attrib:
                                source_info["properties"][prop.attrib['Name']] = prop.attrib['Value']
                    
                    data_sources.append(source_info)
            
            return f"✅ Found {len(data_sources)} data sources:\n{json.dumps(data_sources, indent=2)}"
        except Exception as e:
            return f"❌ Error finding data sources: {e}"
    
    @tool
    def _find_data_destinations(
        self,
        filepath: Annotated[str, "Path to the DTSX file"],
        directory: Annotated[str, "Directory containing the file (default: examples/artifacts)"] = "examples/artifacts"
    ) -> str:
        """Find all data destinations in the SSIS package."""
        try:
            full_path = os.path.join(directory, filepath)
            tree = ET.parse(full_path)
            root = tree.getroot()
            
            data_destinations = []
            
            # Look for destination components
            for element in root.iter():
                if any(keyword in element.tag.lower() for keyword in ['destination', 'output', 'load', 'insert', 'update']):
                    dest_info = {
                        "element_type": element.tag,
                        "attributes": dict(element.attrib),
                        "properties": {}
                    }
                    
                    # Extract destination properties
                    for prop in element.iter():
                        if 'Property' in prop.tag or 'property' in prop.tag.lower():
                            if 'Name' in prop.attrib and 'Value' in prop.attrib:
                                dest_info["properties"][prop.attrib['Name']] = prop.attrib['Value']
                    
                    data_destinations.append(dest_info)
            
            return f"✅ Found {len(data_destinations)} data destinations:\n{json.dumps(data_destinations, indent=2)}"
        except Exception as e:
            return f"❌ Error finding data destinations: {e}"
    
    @tool
    def _trace_data_lineage(
        self,
        filepath: Annotated[str, "Path to the DTSX file"],
        directory: Annotated[str, "Directory containing the file (default: examples/artifacts)"] = "examples/artifacts"
    ) -> str:
        """Trace data lineage through the SSIS package."""
        try:
            full_path = os.path.join(directory, filepath)
            tree = ET.parse(full_path)
            root = tree.getroot()
            
            lineage = {
                "sources": [],
                "transformations": [],
                "destinations": [],
                "connections": []
            }
            
            # Extract data flow lineage
            for element in root.iter():
                tag_lower = element.tag.lower()
                
                if any(keyword in tag_lower for keyword in ['source', 'input', 'extract']):
                    lineage["sources"].append({
                        "element": element.tag,
                        "attributes": dict(element.attrib)
                    })
                elif any(keyword in tag_lower for keyword in ['transform', 'convert', 'lookup', 'merge']):
                    lineage["transformations"].append({
                        "element": element.tag,
                        "attributes": dict(element.attrib)
                    })
                elif any(keyword in tag_lower for keyword in ['destination', 'output', 'load']):
                    lineage["destinations"].append({
                        "element": element.tag,
                        "attributes": dict(element.attrib)
                    })
                elif 'connection' in tag_lower:
                    lineage["connections"].append({
                        "element": element.tag,
                        "attributes": dict(element.attrib)
                    })
            
            return f"✅ Data lineage trace:\n{json.dumps(lineage, indent=2)}"
        except Exception as e:
            return f"❌ Error tracing data lineage: {e}"
    
    @tool
    def _validate_package(
        self,
        filepath: Annotated[str, "Path to the DTSX file"],
        directory: Annotated[str, "Directory containing the file (default: examples/artifacts)"] = "examples/artifacts"
    ) -> str:
        """Validate the SSIS package for common issues."""
        try:
            full_path = os.path.join(directory, filepath)
            tree = ET.parse(full_path)
            root = tree.getroot()
            
            validation_results = {
                "is_valid_xml": True,
                "has_connections": False,
                "has_tasks": False,
                "has_variables": False,
                "warnings": [],
                "errors": []
            }
            
            # Check for connections
            for element in root.iter():
                if 'Connection' in element.tag:
                    validation_results["has_connections"] = True
                    break
            
            # Check for tasks
            for element in root.iter():
                if 'Task' in element.tag and 'Task' != element.tag:
                    validation_results["has_tasks"] = True
                    break
            
            # Check for variables
            for element in root.iter():
                if 'Variable' in element.tag:
                    validation_results["has_variables"] = True
                    break
            
            # Add warnings
            if not validation_results["has_connections"]:
                validation_results["warnings"].append("No connections found in package")
            if not validation_results["has_tasks"]:
                validation_results["warnings"].append("No tasks found in package")
            
            return f"✅ Package validation results:\n{json.dumps(validation_results, indent=2)}"
        except ET.ParseError as e:
            return f"❌ XML Validation Error: {e}"
        except Exception as e:
            return f"❌ Error validating package: {e}"
    
    @tool
    def _create_package_summary(
        self,
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
    def _search_package_content(
        self,
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
    
    @tool
    def _index_package_for_search(
        self,
        filepath: Annotated[str, "Path to the DTSX file"],
        directory: Annotated[str, "Directory containing the file (default: examples/artifacts)"] = "examples/artifacts"
    ) -> str:
        """Index the package content for semantic search."""
        try:
            full_path = os.path.join(directory, filepath)
            tree = ET.parse(full_path)
            root = tree.getroot()
            
            if self._vector_backend == "chroma":
                if not self._embeddings:
                    return "❌ Embeddings not initialized. Cannot create vector index."
                
                # Extract text content for indexing
                documents = []
                metadatas = []
                
                for i, element in enumerate(root.iter()):
                    # Create document text
                    doc_text = f"Element: {element.tag}"
                    if element.attrib:
                        doc_text += f" Attributes: {element.attrib}"
                    if element.text and element.text.strip():
                        doc_text += f" Content: {element.text.strip()}"
                    
                    documents.append(doc_text)
                    metadatas.append({
                        "element_type": element.tag,
                        "file": filepath,
                        "element_id": i
                    })
                
                # Create vector store
                self._vector_store = Chroma.from_texts(
                    texts=documents,
                    metadatas=metadatas,
                    embedding=self._embeddings,
                    collection_name=f"ssis_{filepath.replace('.', '_')}"
                )
                
                return f"✅ Indexed {len(documents)} elements in ChromaDB for semantic search"
                
            elif self._vector_backend == "sqlite":
                # Store in SQLite for text-based search
                conn = sqlite3.connect(self._db_path)
                cursor = conn.cursor()
                
                # Clear existing data for this file
                cursor.execute("DELETE FROM ssis_elements WHERE filepath = ?", (filepath,))
                
                indexed_count = 0
                for i, element in enumerate(root.iter()):
                    # Create document text
                    doc_text = f"Element: {element.tag}"
                    if element.attrib:
                        doc_text += f" Attributes: {element.attrib}"
                    if element.text and element.text.strip():
                        doc_text += f" Content: {element.text.strip()}"
                    
                    cursor.execute('''
                        INSERT INTO ssis_elements (filepath, element_tag, element_text, attributes, metadata)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (
                        filepath,
                        element.tag,
                        element.text.strip() if element.text else "",
                        json.dumps(element.attrib),
                        json.dumps({"element_id": i, "element_type": element.tag})
                    ))
                    indexed_count += 1
                
                conn.commit()
                conn.close()
                
                return f"✅ Indexed {indexed_count} elements in SQLite for text search"
                
            else:
                return "❌ No vector backend configured. Set vector_backend to 'chroma' or 'sqlite'."
                
        except Exception as e:
            return f"❌ Error indexing package: {e}"
    
    @tool
    def _query_package_semantic(
        self,
        query: Annotated[str, "Semantic query to search the package"],
        filepath: Annotated[str, "Path to the DTSX file"],
        directory: Annotated[str, "Directory containing the file (default: examples/artifacts)"] = "examples/artifacts"
    ) -> str:
        """Query the package using semantic search."""
        try:
            if self._vector_backend == "chroma":
                if not self._vector_store:
                    return "❌ Package not indexed. Please run index_package_for_search first."
                
                # Perform semantic search
                results = self._vector_store.similarity_search(query, k=5)
                
                search_results = []
                for doc in results:
                    search_results.append({
                        "content": doc.page_content,
                        "metadata": doc.metadata
                    })
                
                return f"✅ ChromaDB semantic search results for '{query}':\n{json.dumps(search_results, indent=2)}"
                
            elif self._vector_backend == "sqlite":
                # Perform text-based search in SQLite
                conn = sqlite3.connect(self._db_path)
                cursor = conn.cursor()
                
                # Search in element text and attributes
                cursor.execute('''
                    SELECT element_tag, element_text, attributes, metadata
                    FROM ssis_elements 
                    WHERE filepath = ? 
                    AND (element_text LIKE ? OR attributes LIKE ? OR element_tag LIKE ?)
                    ORDER BY 
                        CASE 
                            WHEN element_text LIKE ? THEN 1
                            WHEN attributes LIKE ? THEN 2
                            WHEN element_tag LIKE ? THEN 3
                            ELSE 4
                        END
                    LIMIT 5
                ''', (
                    filepath,
                    f'%{query}%', f'%{query}%', f'%{query}%',
                    f'%{query}%', f'%{query}%', f'%{query}%'
                ))
                
                results = cursor.fetchall()
                conn.close()
                
                search_results = []
                for row in results:
                    element_tag, element_text, attributes, metadata = row
                    search_results.append({
                        "element_tag": element_tag,
                        "element_text": element_text,
                        "attributes": json.loads(attributes) if attributes else {},
                        "metadata": json.loads(metadata) if metadata else {}
                    })
                
                return f"✅ SQLite text search results for '{query}':\n{json.dumps(search_results, indent=2)}"
                
            else:
                return "❌ No vector backend configured. Set vector_backend to 'chroma' or 'sqlite'."
                
        except Exception as e:
            return f"❌ Error performing semantic search: {e}"
    
    @tool
    def _export_package_analysis(
        self,
        filepath: Annotated[str, "Path to the DTSX file"],
        output_filename: Annotated[str, "Name of the output analysis file"],
        directory: Annotated[str, "Directory containing the file (default: examples/artifacts)"] = "examples/artifacts"
    ) -> str:
        """Export comprehensive package analysis to a file."""
        try:
            full_path = os.path.join(directory, filepath)
            tree = ET.parse(full_path)
            root = tree.getroot()
            
            analysis = {
                "package_name": filepath,
                "analysis_timestamp": str(Path().cwd()),
                "file_size": os.path.getsize(full_path),
                "structure": {},
                "data_flows": [],
                "connections": [],
                "tasks": [],
                "variables": []
            }
            
            # Extract all components
            for element in root.iter():
                tag_lower = element.tag.lower()
                
                element_info = {
                    "tag": element.tag,
                    "attributes": dict(element.attrib),
                    "text_content": element.text.strip() if element.text else None
                }
                
                if 'dataflow' in tag_lower:
                    analysis["data_flows"].append(element_info)
                elif 'connection' in tag_lower:
                    analysis["connections"].append(element_info)
                elif 'task' in tag_lower and 'task' != tag_lower:
                    analysis["tasks"].append(element_info)
                elif 'variable' in tag_lower:
                    analysis["variables"].append(element_info)
            
            # Write analysis to file
            output_path = os.path.join(directory, output_filename)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(analysis, f, indent=2, ensure_ascii=False)
            
            return f"✅ Exported analysis to '{output_filename}' with {len(analysis)} sections"
        except Exception as e:
            return f"❌ Error exporting analysis: {e}"
    
    @tool
    def _compare_packages(
        self,
        filepath1: Annotated[str, "Path to the first DTSX file"],
        filepath2: Annotated[str, "Path to the second DTSX file"],
        directory: Annotated[str, "Directory containing the files (default: examples/artifacts)"] = "examples/artifacts"
    ) -> str:
        """Compare two SSIS packages."""
        try:
            def analyze_package(filepath):
                full_path = os.path.join(directory, filepath)
                tree = ET.parse(full_path)
                root = tree.getroot()
                
                return {
                    "filename": filepath,
                    "total_elements": len(list(root.iter())),
                    "element_types": {},
                    "has_data_flows": False,
                    "has_connections": False,
                    "has_tasks": False
                }
            
            pkg1 = analyze_package(filepath1)
            pkg2 = analyze_package(filepath2)
            
            comparison = {
                "package1": pkg1,
                "package2": pkg2,
                "differences": []
            }
            
            # Compare element counts
            if pkg1["total_elements"] != pkg2["total_elements"]:
                comparison["differences"].append(f"Element count: {pkg1['total_elements']} vs {pkg2['total_elements']}")
            
            return f"✅ Package comparison:\n{json.dumps(comparison, indent=2)}"
        except Exception as e:
            return f"❌ Error comparing packages: {e}"
    
    @tool
    def _extract_error_handling(
        self,
        filepath: Annotated[str, "Path to the DTSX file"],
        directory: Annotated[str, "Directory containing the file (default: examples/artifacts)"] = "examples/artifacts"
    ) -> str:
        """Extract error handling configuration from the package."""
        try:
            full_path = os.path.join(directory, filepath)
            tree = ET.parse(full_path)
            root = tree.getroot()
            
            error_handling = {
                "error_handlers": [],
                "event_handlers": [],
                "logging_configurations": []
            }
            
            # Look for error handling elements
            for element in root.iter():
                tag_lower = element.tag.lower()
                
                if any(keyword in tag_lower for keyword in ['error', 'exception', 'fail']):
                    error_info = {
                        "element": element.tag,
                        "attributes": dict(element.attrib),
                        "properties": {}
                    }
                    
                    # Extract error properties
                    for prop in element.iter():
                        if 'Property' in prop.tag or 'property' in prop.tag.lower():
                            if 'Name' in prop.attrib and 'Value' in prop.attrib:
                                error_info["properties"][prop.attrib['Name']] = prop.attrib['Value']
                    
                    error_handling["error_handlers"].append(error_info)
                
                elif 'event' in tag_lower and 'handler' in tag_lower:
                    error_handling["event_handlers"].append({
                        "element": element.tag,
                        "attributes": dict(element.attrib)
                    })
                
                elif 'log' in tag_lower:
                    error_handling["logging_configurations"].append({
                        "element": element.tag,
                        "attributes": dict(element.attrib)
                    })
            
            return f"✅ Error handling analysis:\n{json.dumps(error_handling, indent=2)}"
        except Exception as e:
            return f"❌ Error extracting error handling: {e}"
    
    @tool
    def _analyze_performance_implications(
        self,
        filepath: Annotated[str, "Path to the DTSX file"],
        directory: Annotated[str, "Directory containing the file (default: examples/artifacts)"] = "examples/artifacts"
    ) -> str:
        """Analyze potential performance implications of the package."""
        try:
            full_path = os.path.join(directory, filepath)
            tree = ET.parse(full_path)
            root = tree.getroot()
            
            performance_analysis = {
                "complexity_score": 0,
                "data_flow_count": 0,
                "transformation_count": 0,
                "connection_count": 0,
                "potential_bottlenecks": [],
                "recommendations": []
            }
            
            # Count components
            for element in root.iter():
                tag_lower = element.tag.lower()
                
                if 'dataflow' in tag_lower:
                    performance_analysis["data_flow_count"] += 1
                    performance_analysis["complexity_score"] += 10
                
                elif any(keyword in tag_lower for keyword in ['transform', 'convert', 'lookup', 'merge', 'join']):
                    performance_analysis["transformation_count"] += 1
                    performance_analysis["complexity_score"] += 5
                
                elif 'connection' in tag_lower:
                    performance_analysis["connection_count"] += 1
                    performance_analysis["complexity_score"] += 2
            
            # Add recommendations based on analysis
            if performance_analysis["data_flow_count"] > 5:
                performance_analysis["potential_bottlenecks"].append("High number of data flows may cause memory issues")
                performance_analysis["recommendations"].append("Consider breaking into smaller packages")
            
            if performance_analysis["transformation_count"] > 20:
                performance_analysis["potential_bottlenecks"].append("Many transformations may slow execution")
                performance_analysis["recommendations"].append("Review transformation logic for optimization")
            
            if performance_analysis["connection_count"] > 10:
                performance_analysis["potential_bottlenecks"].append("Many connections may cause connection pool issues")
                performance_analysis["recommendations"].append("Review connection management strategy")
            
            return f"✅ Performance analysis:\n{json.dumps(performance_analysis, indent=2)}"
        except Exception as e:
            return f"❌ Error analyzing performance: {e}"
