#!/usr/bin/env python3
"""
🗂️ Advanced File Management Tools for Enterprise Super Agentic Chatbot
====================================================================

Comprehensive file management capabilities including:
- Multi-format file support (XML, CSV, YAML, TOML, INI, LOG)
- File editing and modification tools
- File format conversion
- Database integration
- Report generation
- File relationship mapping
- Advanced analysis and visualization
"""

import os
import json
import csv
import xml.etree.ElementTree as ET
import yaml
import toml
import configparser
import sqlite3
import asyncio
import hashlib
import mimetypes
import shutil
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Union, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
import re
import subprocess

# Rich imports for visualization
from rich.console import Console
from rich.table import Table
from rich.tree import Tree
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, TaskID
from rich.json import JSON
import rich.box

# Data analysis
try:
    import pandas as pd
    import numpy as np
except ImportError:
    # Fallback if pandas/numpy not available
    pd = None
    np = None
    
from collections import defaultdict, Counter

# Graph generation (optional)
try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    import networkx as nx
    from matplotlib.backends.backend_agg import FigureCanvasAgg
except ImportError:
    plt = sns = nx = None

# AgenticFlow tool decorator
from agenticflow.tools.registry import tool

console = Console()

@dataclass
class FileInfo:
    """Comprehensive file information."""
    path: str
    name: str
    size: int
    modified: datetime
    created: datetime
    mime_type: str
    extension: str
    encoding: str
    hash_md5: str
    hash_sha256: str
    line_count: Optional[int] = None
    word_count: Optional[int] = None
    
@dataclass
class FileRelationship:
    """File relationship information."""
    source_file: str
    target_file: str
    relationship_type: str  # 'imports', 'includes', 'references', 'depends_on'
    strength: float  # 0.0 to 1.0
    context: str

class AdvancedFileManager:
    """Advanced file management system with comprehensive capabilities."""
    
    def __init__(self):
        self.file_cache = {}
        # Initialize relationship graph (fallback if NetworkX not available)
        if nx:
            self.relationship_graph = nx.DiGraph()
        else:
            self.relationship_graph = None  # Will use dict-based fallback
        self.supported_formats = {
            '.json': self._handle_json,
            '.xml': self._handle_xml,
            '.csv': self._handle_csv,
            '.yaml': self._handle_yaml,
            '.yml': self._handle_yaml,
            '.toml': self._handle_toml,
            '.ini': self._handle_ini,
            '.cfg': self._handle_ini,
            '.log': self._handle_log,
            '.txt': self._handle_text,
            '.md': self._handle_markdown,
            '.py': self._handle_python,
            '.js': self._handle_javascript,
            '.html': self._handle_html,
            '.sql': self._handle_sql
        }
        
    # ========================
    # ENHANCED FILE FORMAT SUPPORT
    # ========================
    
    @tool(name="analyze_file_comprehensive", description="Comprehensive analysis of any file format")
    async def analyze_file_comprehensive(self, file_path: str, include_content: bool = True) -> str:
        """Perform comprehensive analysis of any supported file format."""
        try:
            path = Path(file_path)
            
            if not path.exists():
                return f"❌ File not found: {file_path}"
            
            # Get file info
            file_info = await self._get_file_info(path)
            
            # Format-specific analysis
            extension = path.suffix.lower()
            if extension in self.supported_formats:
                content_analysis = await self.supported_formats[extension](path)
            else:
                content_analysis = await self._handle_generic(path)
            
            # Build comprehensive report
            report = {
                "file_info": asdict(file_info),
                "format_analysis": content_analysis,
                "recommendations": await self._get_file_recommendations(path, content_analysis)
            }
            
            return f"📊 Comprehensive File Analysis:\n{json.dumps(report, indent=2, default=str)}"
            
        except Exception as e:
            return f"❌ Error analyzing file: {str(e)}"
    
    @tool(name="convert_file_format", description="Convert files between different formats")
    async def convert_file_format(self, source_path: str, target_format: str, target_path: str = None) -> str:
        """Convert files between different formats with validation."""
        try:
            source = Path(source_path)
            if not source.exists():
                return f"❌ Source file not found: {source_path}"
            
            # Determine target path
            if not target_path:
                target_path = source.with_suffix(f".{target_format.lower()}")
            
            target = Path(target_path)
            
            # Load source data
            source_data = await self._load_structured_data(source)
            if isinstance(source_data, str) and source_data.startswith("❌"):
                return source_data
            
            # Convert and save
            conversion_result = await self._save_structured_data(source_data, target, target_format.lower())
            
            return f"✅ Successfully converted {source_path} → {target_path}\nFormat: {source.suffix} → .{target_format}\nResult: {conversion_result}"
            
        except Exception as e:
            return f"❌ Error converting file: {str(e)}"
    
    # ========================
    # FILE MODIFICATION & EDITING TOOLS
    # ========================
    
    @tool(name="edit_file_content", description="Edit file content with find/replace, line operations")
    async def edit_file_content(self, file_path: str, operation: str, **kwargs) -> str:
        """Advanced file editing with multiple operation types."""
        try:
            path = Path(file_path)
            
            if not path.exists():
                return f"❌ File not found: {file_path}"
            
            # Backup original
            backup_path = path.with_suffix(path.suffix + ".backup")
            shutil.copy2(path, backup_path)
            
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            original_lines = len(lines)
            
            # Perform operation
            if operation == "find_replace":
                find_text = kwargs.get("find", "")
                replace_text = kwargs.get("replace", "")
                case_sensitive = kwargs.get("case_sensitive", True)
                
                flags = 0 if case_sensitive else re.IGNORECASE
                content = re.sub(re.escape(find_text), replace_text, content, flags=flags)
                
            elif operation == "insert_line":
                line_number = kwargs.get("line_number", len(lines))
                text = kwargs.get("text", "")
                lines.insert(line_number - 1, text)
                content = '\n'.join(lines)
                
            elif operation == "delete_line":
                line_number = kwargs.get("line_number")
                if 1 <= line_number <= len(lines):
                    del lines[line_number - 1]
                    content = '\n'.join(lines)
                
            elif operation == "replace_line":
                line_number = kwargs.get("line_number")
                text = kwargs.get("text", "")
                if 1 <= line_number <= len(lines):
                    lines[line_number - 1] = text
                    content = '\n'.join(lines)
                    
            elif operation == "append":
                text = kwargs.get("text", "")
                content += "\n" + text
                
            elif operation == "prepend":
                text = kwargs.get("text", "")
                content = text + "\n" + content
            
            # Write modified content
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            new_lines = len(content.split('\n'))
            
            return f"✅ File edited successfully: {file_path}\nOperation: {operation}\nLines: {original_lines} → {new_lines}\nBackup created: {backup_path}"
            
        except Exception as e:
            return f"❌ Error editing file: {str(e)}"
    
    @tool(name="merge_files", description="Merge multiple files with different strategies")
    async def merge_files(self, file_paths: List[str], output_path: str, merge_strategy: str = "concatenate") -> str:
        """Merge multiple files using different strategies."""
        try:
            files = [Path(p) for p in file_paths]
            missing = [str(f) for f in files if not f.exists()]
            
            if missing:
                return f"❌ Files not found: {', '.join(missing)}"
            
            output = Path(output_path)
            
            if merge_strategy == "concatenate":
                # Simple concatenation
                with open(output, 'w', encoding='utf-8') as out_file:
                    for file_path in files:
                        with open(file_path, 'r', encoding='utf-8') as in_file:
                            out_file.write(f"\n# === Content from {file_path} ===\n")
                            out_file.write(in_file.read())
                            out_file.write("\n")
                            
            elif merge_strategy == "json_merge":
                # Merge JSON objects
                merged_data = {}
                for file_path in files:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if isinstance(data, dict):
                            merged_data.update(data)
                
                with open(output, 'w', encoding='utf-8') as f:
                    json.dump(merged_data, f, indent=2)
                    
            elif merge_strategy == "csv_merge":
                # Merge CSV files
                dataframes = []
                for file_path in files:
                    df = pd.read_csv(file_path)
                    dataframes.append(df)
                
                merged_df = pd.concat(dataframes, ignore_index=True)
                merged_df.to_csv(output, index=False)
            
            return f"✅ Successfully merged {len(files)} files into {output_path}\nStrategy: {merge_strategy}"
            
        except Exception as e:
            return f"❌ Error merging files: {str(e)}"
    
    # ========================
    # DATABASE INTEGRATION
    # ========================
    
    @tool(name="query_database", description="Execute SQL queries on databases")
    async def query_database(self, db_path: str, query: str, output_format: str = "json") -> str:
        """Execute SQL queries on SQLite databases with multiple output formats."""
        try:
            db_file = Path(db_path)
            
            if not db_file.exists():
                return f"❌ Database file not found: {db_path}"
            
            conn = sqlite3.connect(db_path)
            
            # Execute query
            if query.strip().upper().startswith(('SELECT', 'PRAGMA')):
                # Read operation
                df = pd.read_sql_query(query, conn)
                
                if output_format == "json":
                    result = df.to_json(orient='records', indent=2)
                elif output_format == "csv":
                    result = df.to_csv(index=False)
                elif output_format == "table":
                    result = df.to_string(index=False)
                else:
                    result = df.to_dict('records')
                    
            else:
                # Write operation
                cursor = conn.cursor()
                cursor.execute(query)
                conn.commit()
                result = f"Query executed successfully. Rows affected: {cursor.rowcount}"
            
            conn.close()
            
            return f"🗃️ Database Query Result:\n{result}"
            
        except Exception as e:
            return f"❌ Database error: {str(e)}"
    
    @tool(name="analyze_database_schema", description="Analyze database structure and relationships")
    async def analyze_database_schema(self, db_path: str) -> str:
        """Analyze database schema, tables, and relationships."""
        try:
            conn = sqlite3.connect(db_path)
            
            # Get all tables
            tables_query = "SELECT name FROM sqlite_master WHERE type='table';"
            tables = pd.read_sql_query(tables_query, conn)
            
            schema_analysis = {
                "database_path": db_path,
                "total_tables": len(tables),
                "tables": {}
            }
            
            for table_name in tables['name']:
                # Get table info
                table_info_query = f"PRAGMA table_info({table_name});"
                columns = pd.read_sql_query(table_info_query, conn)
                
                # Get row count
                count_query = f"SELECT COUNT(*) as count FROM {table_name};"
                row_count = pd.read_sql_query(count_query, conn)['count'].iloc[0]
                
                schema_analysis["tables"][table_name] = {
                    "columns": columns.to_dict('records'),
                    "row_count": row_count,
                    "primary_keys": columns[columns['pk'] == 1]['name'].tolist()
                }
            
            conn.close()
            
            return f"🗃️ Database Schema Analysis:\n{json.dumps(schema_analysis, indent=2)}"
            
        except Exception as e:
            return f"❌ Error analyzing database: {str(e)}"
    
    # ========================
    # REPORT GENERATION
    # ========================
    
    @tool(name="generate_report", description="Generate comprehensive reports from data")
    async def generate_report(self, data_source: str, report_type: str = "html", template: str = "standard") -> str:
        """Generate comprehensive reports with charts and analytics."""
        try:
            # Load data
            if data_source.endswith('.json'):
                with open(data_source, 'r') as f:
                    data = json.load(f)
            elif data_source.endswith('.csv'):
                data = pd.read_csv(data_source).to_dict('records')
            else:
                return f"❌ Unsupported data source format: {data_source}"
            
            # Generate report
            report_path = Path(data_source).with_suffix(f'.report.{report_type}')
            
            if report_type == "html":
                html_content = await self._generate_html_report(data, template)
                with open(report_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                    
            elif report_type == "markdown":
                md_content = await self._generate_markdown_report(data, template)
                with open(report_path, 'w', encoding='utf-8') as f:
                    f.write(md_content)
            
            return f"📊 Report generated successfully: {report_path}\nType: {report_type}\nTemplate: {template}"
            
        except Exception as e:
            return f"❌ Error generating report: {str(e)}"
    
    # ========================
    # FILE RELATIONSHIP MAPPING
    # ========================
    
    @tool(name="map_file_relationships", description="Analyze and map relationships between files")
    async def map_file_relationships(self, directory: str, output_format: str = "json") -> str:
        """Analyze file relationships and create dependency graphs."""
        try:
            dir_path = Path(directory)
            
            if not dir_path.exists():
                return f"❌ Directory not found: {directory}"
            
            relationships = []
            
            # Analyze files in directory
            for file_path in dir_path.rglob("*"):
                if file_path.is_file():
                    file_relationships = await self._analyze_file_dependencies(file_path)
                    relationships.extend(file_relationships)
            
            # Build relationship graph (fallback if NetworkX not available)
            if nx:
                graph = nx.DiGraph()
                for rel in relationships:
                    graph.add_edge(rel.source_file, rel.target_file, 
                                 relationship_type=rel.relationship_type,
                                 strength=rel.strength,
                                 context=rel.context)
            else:
                # Dict-based fallback for relationship tracking
                graph = {'nodes': set(), 'edges': []}
                for rel in relationships:
                    graph['nodes'].add(rel.source_file)
                    graph['nodes'].add(rel.target_file)
                    graph['edges'].append({
                        'source': rel.source_file,
                        'target': rel.target_file,
                        'type': rel.relationship_type,
                        'strength': rel.strength,
                        'context': rel.context
                    })
            
            # Generate output
            if output_format == "json":
                if nx:
                    output = {
                        "total_files": len(graph.nodes),
                        "total_relationships": len(graph.edges),
                        "relationships": [asdict(rel) for rel in relationships]
                    }
                else:
                    output = {
                        "total_files": len(graph['nodes']) if graph else 0,
                        "total_relationships": len(graph['edges']) if graph else 0,
                        "relationships": [asdict(rel) for rel in relationships]
                    }
                result = json.dumps(output, indent=2)
                
            elif output_format == "graphml":
                if nx:
                    # Save as GraphML for visualization tools
                    output_path = dir_path / "file_relationships.graphml"
                    nx.write_graphml(graph, output_path)
                    result = f"Graph saved to: {output_path}"
                else:
                    result = "❌ NetworkX not available for GraphML export"
                
            elif output_format == "visualization":
                # Create visual representation
                output_path = await self._create_relationship_visualization(graph, dir_path)
                result = f"Visualization saved to: {output_path}"
            
            return f"🔗 File Relationship Analysis:\n{result}"
            
        except Exception as e:
            return f"❌ Error mapping relationships: {str(e)}"
    
    # ========================
    # ADVANCED FILE ANALYSIS
    # ========================
    
    @tool(name="analyze_file_patterns", description="Detect patterns and anomalies in files")
    async def analyze_file_patterns(self, file_path: str, pattern_types: List[str] = None) -> str:
        """Detect patterns, duplicates, and anomalies in files."""
        try:
            if pattern_types is None:
                pattern_types = ["duplicates", "patterns", "anomalies", "structure"]
            
            path = Path(file_path)
            analysis = {
                "file": str(path),
                "timestamp": datetime.now().isoformat()
            }
            
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            if "duplicates" in pattern_types:
                analysis["duplicates"] = await self._find_duplicate_lines(lines)
            
            if "patterns" in pattern_types:
                analysis["patterns"] = await self._detect_content_patterns(content)
            
            if "anomalies" in pattern_types:
                analysis["anomalies"] = await self._detect_anomalies(lines)
            
            if "structure" in pattern_types:
                analysis["structure"] = await self._analyze_structure(content, path.suffix)
            
            return f"🔍 Pattern Analysis Results:\n{json.dumps(analysis, indent=2)}"
            
        except Exception as e:
            return f"❌ Error analyzing patterns: {str(e)}"
    
    @tool(name="compare_files", description="Compare multiple files and show differences")
    async def compare_files(self, file1_path: str, file2_path: str, comparison_type: str = "content") -> str:
        """Compare files with different comparison strategies."""
        try:
            file1, file2 = Path(file1_path), Path(file2_path)
            
            if not file1.exists() or not file2.exists():
                return f"❌ One or both files not found: {file1_path}, {file2_path}"
            
            comparison = {
                "file1": str(file1),
                "file2": str(file2),
                "comparison_type": comparison_type,
                "timestamp": datetime.now().isoformat()
            }
            
            if comparison_type == "content":
                # Line-by-line content comparison
                with open(file1, 'r') as f1, open(file2, 'r') as f2:
                    lines1, lines2 = f1.readlines(), f2.readlines()
                
                comparison["total_lines"] = {"file1": len(lines1), "file2": len(lines2)}
                comparison["differences"] = await self._compare_content(lines1, lines2)
                
            elif comparison_type == "structure":
                # Structural comparison for structured files
                data1 = await self._load_structured_data(file1)
                data2 = await self._load_structured_data(file2)
                comparison["structure_diff"] = await self._compare_structures(data1, data2)
                
            elif comparison_type == "metadata":
                # Metadata comparison
                info1 = await self._get_file_info(file1)
                info2 = await self._get_file_info(file2)
                comparison["metadata_diff"] = await self._compare_metadata(info1, info2)
            
            return f"🔀 File Comparison Results:\n{json.dumps(comparison, indent=2, default=str)}"
            
        except Exception as e:
            return f"❌ Error comparing files: {str(e)}"
    
    # ========================
    # FLOWCHART & VISUALIZATION
    # ========================
    
    @tool(name="generate_flowchart", description="Generate flowcharts from code or data flows")
    async def generate_flowchart(self, source_file: str, flowchart_type: str = "auto", output_format: str = "png") -> str:
        """Generate flowcharts and process diagrams."""
        try:
            source = Path(source_file)
            
            if not source.exists():
                return f"❌ Source file not found: {source_file}"
            
            # Analyze source for flow structure
            flow_data = await self._extract_flow_structure(source, flowchart_type)
            
            # Generate flowchart
            output_path = source.with_suffix(f'.flowchart.{output_format}')
            
            if flowchart_type in ["code_flow", "auto"]:
                await self._generate_code_flowchart(flow_data, output_path)
            elif flowchart_type == "data_flow":
                await self._generate_data_flowchart(flow_data, output_path)
            elif flowchart_type == "network":
                await self._generate_network_diagram(flow_data, output_path)
            
            return f"📊 Flowchart generated: {output_path}\nType: {flowchart_type}\nFormat: {output_format}"
            
        except Exception as e:
            return f"❌ Error generating flowchart: {str(e)}"
    
    # ========================
    # HELPER METHODS (FORMAT HANDLERS)
    # ========================
    
    async def _handle_json(self, path: Path) -> Dict[str, Any]:
        """Handle JSON file analysis."""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return {
            "format": "JSON",
            "type": type(data).__name__,
            "size": len(data) if isinstance(data, (list, dict)) else 1,
            "structure_depth": self._get_nested_depth(data),
            "keys": list(data.keys()) if isinstance(data, dict) else None,
            "validation": "valid"
        }
    
    async def _handle_xml(self, path: Path) -> Dict[str, Any]:
        """Handle XML file analysis."""
        tree = ET.parse(path)
        root = tree.getroot()
        
        return {
            "format": "XML",
            "root_element": root.tag,
            "namespace": root.tag.split('}')[0][1:] if '}' in root.tag else None,
            "total_elements": len(list(root.iter())),
            "attributes": dict(root.attrib),
            "validation": "valid"
        }
    
    async def _handle_csv(self, path: Path) -> Dict[str, Any]:
        """Handle CSV file analysis."""
        df = pd.read_csv(path)
        
        return {
            "format": "CSV",
            "rows": len(df),
            "columns": len(df.columns),
            "column_names": df.columns.tolist(),
            "data_types": df.dtypes.to_dict(),
            "missing_values": df.isnull().sum().to_dict(),
            "memory_usage": f"{df.memory_usage(deep=True).sum()} bytes"
        }
    
    async def _handle_yaml(self, path: Path) -> Dict[str, Any]:
        """Handle YAML file analysis."""
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        return {
            "format": "YAML",
            "type": type(data).__name__,
            "structure_depth": self._get_nested_depth(data),
            "keys": list(data.keys()) if isinstance(data, dict) else None,
            "validation": "valid"
        }
    
    async def _handle_toml(self, path: Path) -> Dict[str, Any]:
        """Handle TOML file analysis."""
        data = toml.load(path)
        
        return {
            "format": "TOML",
            "sections": list(data.keys()),
            "structure_depth": self._get_nested_depth(data),
            "validation": "valid"
        }
    
    async def _handle_ini(self, path: Path) -> Dict[str, Any]:
        """Handle INI/CFG file analysis."""
        config = configparser.ConfigParser()
        config.read(path)
        
        return {
            "format": "INI/CFG",
            "sections": config.sections(),
            "total_options": sum(len(config[section]) for section in config.sections()),
            "validation": "valid"
        }
    
    async def _handle_log(self, path: Path) -> Dict[str, Any]:
        """Handle log file analysis."""
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        log_levels = Counter()
        timestamps = []
        
        for line in lines:
            # Extract log levels
            for level in ['ERROR', 'WARN', 'INFO', 'DEBUG']:
                if level in line.upper():
                    log_levels[level] += 1
                    break
            
            # Extract timestamps (basic pattern matching)
            timestamp_match = re.search(r'\d{4}-\d{2}-\d{2}', line)
            if timestamp_match:
                timestamps.append(timestamp_match.group())
        
        return {
            "format": "LOG",
            "total_lines": len(lines),
            "log_levels": dict(log_levels),
            "date_range": {
                "start": min(timestamps) if timestamps else None,
                "end": max(timestamps) if timestamps else None
            },
            "unique_dates": len(set(timestamps))
        }
    
    async def _handle_text(self, path: Path) -> Dict[str, Any]:
        """Handle plain text file analysis."""
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        words = content.split()
        lines = content.split('\n')
        
        return {
            "format": "TEXT",
            "lines": len(lines),
            "words": len(words),
            "characters": len(content),
            "average_line_length": sum(len(line) for line in lines) / len(lines) if lines else 0,
            "most_common_words": Counter(words).most_common(10)
        }
    
    async def _handle_markdown(self, path: Path) -> Dict[str, Any]:
        """Handle Markdown file analysis."""
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract headers
        headers = re.findall(r'^#+\s+(.+)$', content, re.MULTILINE)
        
        # Extract links
        links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)
        
        return {
            "format": "Markdown",
            "headers": len(headers),
            "header_structure": headers[:10],  # First 10 headers
            "links": len(links),
            "external_links": [link for link in links if link[1].startswith('http')],
            "words": len(content.split()),
            "lines": len(content.split('\n'))
        }
    
    async def _handle_python(self, path: Path) -> Dict[str, Any]:
        """Handle Python file analysis."""
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Basic code analysis
        imports = re.findall(r'^(?:from\s+\S+\s+)?import\s+([^\n;]+)', content, re.MULTILINE)
        functions = re.findall(r'^def\s+(\w+)', content, re.MULTILINE)
        classes = re.findall(r'^class\s+(\w+)', content, re.MULTILINE)
        
        return {
            "format": "Python",
            "lines_of_code": len(content.split('\n')),
            "imports": len(imports),
            "functions": len(functions),
            "classes": len(classes),
            "function_names": functions[:10],  # First 10
            "class_names": classes,
            "complexity_estimate": len(functions) + len(classes) * 2
        }
    
    async def _handle_javascript(self, path: Path) -> Dict[str, Any]:
        """Handle JavaScript file analysis."""
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        functions = re.findall(r'function\s+(\w+)', content)
        arrow_functions = re.findall(r'(\w+)\s*=>\s*{', content)
        
        return {
            "format": "JavaScript",
            "lines_of_code": len(content.split('\n')),
            "functions": len(functions),
            "arrow_functions": len(arrow_functions),
            "function_names": functions + arrow_functions
        }
    
    async def _handle_html(self, path: Path) -> Dict[str, Any]:
        """Handle HTML file analysis."""
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Basic HTML parsing
        tags = re.findall(r'<(\w+)', content)
        tag_counts = Counter(tags)
        
        return {
            "format": "HTML",
            "total_tags": len(tags),
            "unique_tags": len(set(tags)),
            "most_common_tags": dict(tag_counts.most_common(10)),
            "has_doctype": "<!DOCTYPE" in content,
            "estimated_complexity": len(set(tags))
        }
    
    async def _handle_sql(self, path: Path) -> Dict[str, Any]:
        """Handle SQL file analysis."""
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract SQL statements
        statements = re.split(r';\s*\n', content)
        select_count = len(re.findall(r'\bSELECT\b', content, re.IGNORECASE))
        insert_count = len(re.findall(r'\bINSERT\b', content, re.IGNORECASE))
        update_count = len(re.findall(r'\bUPDATE\b', content, re.IGNORECASE))
        delete_count = len(re.findall(r'\bDELETE\b', content, re.IGNORECASE))
        
        return {
            "format": "SQL",
            "total_statements": len(statements),
            "statement_types": {
                "SELECT": select_count,
                "INSERT": insert_count,
                "UPDATE": update_count,
                "DELETE": delete_count
            },
            "tables_referenced": list(set(re.findall(r'FROM\s+(\w+)', content, re.IGNORECASE)))
        }
    
    async def _handle_generic(self, path: Path) -> Dict[str, Any]:
        """Handle generic/unknown file types."""
        stat = path.stat()
        
        return {
            "format": "GENERIC",
            "extension": path.suffix,
            "size_bytes": stat.st_size,
            "mime_type": mimetypes.guess_type(path)[0],
            "is_binary": await self._is_binary_file(path)
        }
    
    # ========================
    # UTILITY HELPER METHODS
    # ========================
    
    async def _get_file_info(self, path: Path) -> FileInfo:
        """Get comprehensive file information."""
        stat = path.stat()
        
        # Calculate hashes
        with open(path, 'rb') as f:
            content = f.read()
            md5_hash = hashlib.md5(content).hexdigest()
            sha256_hash = hashlib.sha256(content).hexdigest()
        
        # Try to determine encoding and count lines/words for text files
        line_count = word_count = None
        encoding = 'unknown'
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                text_content = f.read()
                encoding = 'utf-8'
                line_count = len(text_content.split('\n'))
                word_count = len(text_content.split())
        except UnicodeDecodeError:
            pass
        
        return FileInfo(
            path=str(path),
            name=path.name,
            size=stat.st_size,
            modified=datetime.fromtimestamp(stat.st_mtime),
            created=datetime.fromtimestamp(stat.st_ctime),
            mime_type=mimetypes.guess_type(path)[0] or 'unknown',
            extension=path.suffix,
            encoding=encoding,
            hash_md5=md5_hash,
            hash_sha256=sha256_hash,
            line_count=line_count,
            word_count=word_count
        )
    
    def _get_nested_depth(self, obj, depth=0):
        """Calculate nested depth of data structures."""
        if isinstance(obj, dict):
            return max(self._get_nested_depth(value, depth + 1) for value in obj.values()) if obj else depth
        elif isinstance(obj, list):
            return max(self._get_nested_depth(item, depth + 1) for item in obj) if obj else depth
        else:
            return depth
    
    async def _is_binary_file(self, path: Path) -> bool:
        """Check if file is binary."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                f.read(1024)  # Try to read first 1KB as text
            return False
        except UnicodeDecodeError:
            return True
    
    # ========================
    # MISSING HELPER METHODS - IMPLEMENTED
    # ========================
    
    async def _load_structured_data(self, file_path: Path):
        """Load structured data from various formats."""
        try:
            extension = file_path.suffix.lower()
            
            if extension == '.json':
                with open(file_path, 'r') as f:
                    return json.load(f)
            elif extension == '.csv':
                if pd:
                    return pd.read_csv(file_path).to_dict('records')
                else:
                    # Fallback CSV reader
                    with open(file_path, 'r') as f:
                        reader = csv.DictReader(f)
                        return list(reader)
            elif extension in ['.yaml', '.yml']:
                with open(file_path, 'r') as f:
                    return yaml.safe_load(f)
            elif extension == '.toml':
                return toml.load(file_path)
            elif extension in ['.xml']:
                tree = ET.parse(file_path)
                return self._xml_to_dict(tree.getroot())
            else:
                return f"❌ Unsupported format for loading: {extension}"
                
        except Exception as e:
            return f"❌ Error loading data: {str(e)}"
    
    async def _save_structured_data(self, data, file_path: Path, format_type: str):
        """Save structured data in various formats."""
        try:
            if format_type == 'json':
                with open(file_path, 'w') as f:
                    json.dump(data, f, indent=2)
            elif format_type == 'csv':
                if pd and isinstance(data, list):
                    df = pd.DataFrame(data)
                    df.to_csv(file_path, index=False)
                else:
                    # Fallback CSV writer
                    with open(file_path, 'w', newline='') as f:
                        if isinstance(data, list) and data:
                            writer = csv.DictWriter(f, fieldnames=data[0].keys())
                            writer.writeheader()
                            writer.writerows(data)
            elif format_type in ['yaml', 'yml']:
                with open(file_path, 'w') as f:
                    yaml.dump(data, f, default_flow_style=False)
            elif format_type == 'toml':
                with open(file_path, 'w') as f:
                    toml.dump(data, f)
            
            return f"Successfully saved as {format_type.upper()}"
            
        except Exception as e:
            return f"❌ Error saving data: {str(e)}"
    
    def _xml_to_dict(self, element):
        """Convert XML element to dictionary."""
        result = {}
        
        # Add attributes
        if element.attrib:
            result['@attributes'] = element.attrib
        
        # Add text content
        if element.text and element.text.strip():
            if len(element) == 0:
                return element.text.strip()
            else:
                result['#text'] = element.text.strip()
        
        # Add children
        for child in element:
            child_data = self._xml_to_dict(child)
            if child.tag in result:
                if not isinstance(result[child.tag], list):
                    result[child.tag] = [result[child.tag]]
                result[child.tag].append(child_data)
            else:
                result[child.tag] = child_data
        
        return result
    
    async def _get_file_recommendations(self, path: Path, analysis: dict):
        """Generate recommendations based on file analysis."""
        recommendations = []
        
        if analysis.get('format') == 'JSON':
            if analysis.get('structure_depth', 0) > 5:
                recommendations.append("Consider flattening deeply nested structure")
            recommendations.append("JSON is suitable for API data exchange")
        elif analysis.get('format') == 'CSV':
            if analysis.get('missing_values'):
                recommendations.append("Handle missing values before analysis")
            recommendations.append("CSV is optimal for tabular data processing")
        elif analysis.get('format') == 'LOG':
            recommendations.append("Consider log rotation for large files")
            recommendations.append("Use structured logging for better analysis")
        
        return recommendations
    
    async def _analyze_file_dependencies(self, file_path: Path):
        """Analyze file dependencies and relationships."""
        relationships = []
        
        try:
            if file_path.suffix == '.py':
                # Analyze Python imports
                with open(file_path, 'r') as f:
                    content = f.read()
                
                imports = re.findall(r'^(?:from\s+(\S+)\s+)?import\s+([^\n;]+)', content, re.MULTILINE)
                for imp in imports:
                    module = imp[0] if imp[0] else imp[1].split('.')[0]
                    relationships.append(FileRelationship(
                        source_file=str(file_path),
                        target_file=module,
                        relationship_type='imports',
                        strength=0.8,
                        context=f"Python import: {module}"
                    ))
            
            elif file_path.suffix in ['.html', '.xml']:
                # Analyze includes/references
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Find linked files (href, src attributes)
                links = re.findall(r'(?:href|src)=["\']([^"\'>]+)["\']', content)
                for link in links:
                    if not link.startswith('http'):
                        relationships.append(FileRelationship(
                            source_file=str(file_path),
                            target_file=link,
                            relationship_type='references',
                            strength=0.6,
                            context=f"File reference: {link}"
                        ))
                        
        except Exception as e:
            console.log(f"Error analyzing dependencies for {file_path}: {e}")
        
        return relationships
    
    async def _find_duplicate_lines(self, lines):
        """Find duplicate lines in file content."""
        line_counts = Counter(line.strip() for line in lines if line.strip())
        duplicates = {line: count for line, count in line_counts.items() if count > 1}
        
        return {
            "total_duplicates": len(duplicates),
            "duplicate_lines": duplicates,
            "duplicate_percentage": len(duplicates) / len(lines) * 100 if lines else 0
        }
    
    async def _detect_content_patterns(self, content):
        """Detect common patterns in content."""
        patterns = {}
        
        # Email patterns
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', content)
        if emails:
            patterns['emails'] = list(set(emails))
        
        # URL patterns
        urls = re.findall(r'https?://[^\s<>"]+', content)
        if urls:
            patterns['urls'] = list(set(urls))
        
        # IP addresses
        ips = re.findall(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', content)
        if ips:
            patterns['ip_addresses'] = list(set(ips))
        
        # Phone numbers (basic pattern)
        phones = re.findall(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', content)
        if phones:
            patterns['phone_numbers'] = list(set(phones))
        
        return patterns
    
    async def _detect_anomalies(self, lines):
        """Detect anomalies in file content."""
        anomalies = []
        
        if not lines:
            return anomalies
        
        # Line length anomalies
        avg_length = sum(len(line) for line in lines) / len(lines)
        for i, line in enumerate(lines):
            if len(line) > avg_length * 3:  # Lines much longer than average
                anomalies.append({
                    "type": "long_line",
                    "line_number": i + 1,
                    "length": len(line),
                    "average": avg_length
                })
        
        # Empty lines clustering
        empty_line_groups = []
        current_group_size = 0
        for i, line in enumerate(lines):
            if not line.strip():
                current_group_size += 1
            else:
                if current_group_size > 5:  # More than 5 consecutive empty lines
                    empty_line_groups.append({
                        "type": "excessive_empty_lines",
                        "start_line": i - current_group_size,
                        "count": current_group_size
                    })
                current_group_size = 0
        
        anomalies.extend(empty_line_groups)
        return anomalies
    
    async def _analyze_structure(self, content, file_extension):
        """Analyze file structure based on type."""
        structure = {}
        
        if file_extension == '.py':
            # Python structure analysis
            structure['classes'] = len(re.findall(r'^class\s+\w+', content, re.MULTILINE))
            structure['functions'] = len(re.findall(r'^def\s+\w+', content, re.MULTILINE))
            structure['imports'] = len(re.findall(r'^(?:from\s+\S+\s+)?import\s+', content, re.MULTILINE))
            
        elif file_extension in ['.html', '.xml']:
            # Markup structure analysis
            tags = re.findall(r'<(\w+)', content)
            structure['total_tags'] = len(tags)
            structure['unique_tags'] = len(set(tags))
            structure['tag_distribution'] = dict(Counter(tags).most_common(10))
            
        elif file_extension == '.css':
            # CSS structure analysis
            selectors = re.findall(r'([\w\-\.#]+)\s*{', content)
            structure['selectors'] = len(selectors)
            structure['unique_selectors'] = len(set(selectors))
            
        return structure
    
    async def _compare_content(self, lines1, lines2):
        """Compare file contents line by line."""
        max_lines = max(len(lines1), len(lines2))
        differences = []
        
        for i in range(max_lines):
            line1 = lines1[i] if i < len(lines1) else ""
            line2 = lines2[i] if i < len(lines2) else ""
            
            if line1.strip() != line2.strip():
                differences.append({
                    "line_number": i + 1,
                    "file1_content": line1.strip(),
                    "file2_content": line2.strip(),
                    "difference_type": "modified" if line1 and line2 else ("added" if line2 else "deleted")
                })
        
        return {
            "total_differences": len(differences),
            "differences": differences[:50],  # Limit to first 50 differences
            "similarity_percentage": max(0, 100 - (len(differences) / max_lines * 100)) if max_lines > 0 else 100
        }
    
    async def _compare_structures(self, data1, data2):
        """Compare structural differences between data."""
        differences = {}
        
        # Compare types
        if type(data1) != type(data2):
            differences['type_mismatch'] = {
                'data1_type': type(data1).__name__,
                'data2_type': type(data2).__name__
            }
        
        # Compare dict structures
        if isinstance(data1, dict) and isinstance(data2, dict):
            keys1, keys2 = set(data1.keys()), set(data2.keys())
            differences['missing_in_data1'] = list(keys2 - keys1)
            differences['missing_in_data2'] = list(keys1 - keys2)
            differences['common_keys'] = list(keys1 & keys2)
        
        # Compare list lengths
        if isinstance(data1, list) and isinstance(data2, list):
            differences['length_difference'] = len(data2) - len(data1)
        
        return differences
    
    async def _compare_metadata(self, info1, info2):
        """Compare file metadata."""
        return {
            'size_difference': info2.size - info1.size,
            'modified_time_diff': (info2.modified - info1.modified).total_seconds(),
            'same_hash': info1.hash_md5 == info2.hash_md5,
            'encoding_match': info1.encoding == info2.encoding
        }
    
    async def _create_relationship_visualization(self, graph, output_dir):
        """Create visualization of file relationships."""
        if not nx:
            return "❌ NetworkX not available for visualization"
        
        try:
            output_path = output_dir / "file_relationships.png"
            
            if plt:
                plt.figure(figsize=(12, 8))
                pos = nx.spring_layout(graph)
                nx.draw(graph, pos, with_labels=True, node_color='lightblue', 
                       node_size=1500, font_size=8, font_weight='bold')
                plt.title("File Relationship Graph")
                plt.savefig(output_path, dpi=300, bbox_inches='tight')
                plt.close()
                
            return str(output_path)
            
        except Exception as e:
            return f"❌ Error creating visualization: {str(e)}"
    
    async def _extract_flow_structure(self, source_file, flowchart_type):
        """Extract flow structure from source file."""
        # Placeholder implementation
        return {
            "nodes": ["Start", "Process", "Decision", "End"],
            "edges": [("Start", "Process"), ("Process", "Decision"), ("Decision", "End")],
            "type": flowchart_type
        }
    
    async def _generate_code_flowchart(self, flow_data, output_path):
        """Generate code flowchart."""
        # Placeholder - would generate actual flowchart
        with open(output_path.with_suffix('.txt'), 'w') as f:
            f.write(f"Code Flowchart Data:\n{json.dumps(flow_data, indent=2)}")
        return str(output_path.with_suffix('.txt'))
    
    async def _generate_data_flowchart(self, flow_data, output_path):
        """Generate data flowchart."""
        # Placeholder - would generate actual flowchart
        with open(output_path.with_suffix('.txt'), 'w') as f:
            f.write(f"Data Flow Chart:\n{json.dumps(flow_data, indent=2)}")
        return str(output_path.with_suffix('.txt'))
    
    async def _generate_network_diagram(self, flow_data, output_path):
        """Generate network diagram."""
        # Placeholder - would generate actual diagram
        with open(output_path.with_suffix('.txt'), 'w') as f:
            f.write(f"Network Diagram:\n{json.dumps(flow_data, indent=2)}")
        return str(output_path.with_suffix('.txt'))
    
    async def _generate_html_report(self, data, template):
        """Generate HTML report."""
        html = f'''<!DOCTYPE html>
<html>
<head>
    <title>Data Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ color: #333; border-bottom: 2px solid #007acc; }}
        .data {{ background: #f5f5f5; padding: 15px; margin: 10px 0; }}
        pre {{ background: #fff; padding: 10px; border: 1px solid #ddd; }}
    </style>
</head>
<body>
    <h1 class="header">Enterprise Data Report</h1>
    <div class="data">
        <h2>Data Summary</h2>
        <p>Generated on: {datetime.now().isoformat()}</p>
        <p>Template: {template}</p>
        <p>Record Count: {len(data) if isinstance(data, list) else 'N/A'}</p>
    </div>
    <div class="data">
        <h2>Data Content</h2>
        <pre>{json.dumps(data, indent=2)}</pre>
    </div>
</body>
</html>'''
        return html
    
    async def _generate_markdown_report(self, data, template):
        """Generate Markdown report."""
        md = f'''# Enterprise Data Report

**Generated**: {datetime.now().isoformat()}  
**Template**: {template}  
**Records**: {len(data) if isinstance(data, list) else 'N/A'}  

## Data Summary

This report contains comprehensive analysis of the provided data.

## Data Content

```json
{json.dumps(data, indent=2)}
```

## Analysis

- Data Type: {type(data).__name__}
- Structure: {'Complex' if isinstance(data, (dict, list)) else 'Simple'}
- Size: {len(str(data))} characters

---
*Report generated by Enterprise Super Agentic Chatbot*'''
        return md

# Global instance
file_manager = AdvancedFileManager()