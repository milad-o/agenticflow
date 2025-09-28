"""Data agent for JSON, XML, and other data formats."""

import json
import xml.etree.ElementTree as ET
import yaml
import csv
import toml
import configparser
import sqlite3
from pathlib import Path
from typing import Annotated, List, Optional, Dict, Any, Union
from langchain_core.tools import tool
from ..core.flow import Agent

class DataAgent(Agent):
    """Agent specialized in data processing and manipulation."""
    
    def __init__(self, name: str = "data_agent", description: str = "Data processing specialist"):
        tools = self._create_tools()
        super().__init__(name, tools=tools, description=description)
    
    def _create_tools(self) -> List:
        """Create data processing tools."""
        return [
            self._read_json,
            self._write_json,
            self._validate_json,
            self._transform_json,
            self._merge_json,
            self._read_xml,
            self._write_xml,
            self._validate_xml,
            self._transform_xml,
            self._read_yaml,
            self._write_yaml,
            self._read_csv,
            self._write_csv,
            self._read_toml,
            self._write_toml,
            self._read_ini,
            self._write_ini,
            self._create_sqlite,
            self._query_sqlite,
            self._convert_data,
            self._analyze_data,
            self._clean_data,
            self._validate_data
        ]
    
    @tool
    def _read_json(
        self,
        filename: Annotated[str, "Name of the JSON file to read"],
        directory: Annotated[str, "Directory containing the file (default: examples/artifacts)"] = "examples/artifacts"
    ) -> str:
        """Read data from a JSON file."""
        try:
            filepath = os.path.join(directory, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            info = f"📄 JSON file '{filepath}':\n"
            info += f"📏 Size: {len(json.dumps(data))} characters\n"
            info += f"🔢 Type: {type(data).__name__}\n"
            
            if isinstance(data, dict):
                info += f"🔑 Keys: {', '.join(data.keys())}\n"
            elif isinstance(data, list):
                info += f"📊 Items: {len(data)}\n"
            
            info += f"📋 Content:\n{json.dumps(data, indent=2)[:500]}...\n"
            
            return info
        except Exception as e:
            return f"❌ Error reading JSON file: {e}"
    
    @tool
    def _write_json(
        self,
        filename: Annotated[str, "Name of the JSON file to write"],
        data: Annotated[str, "Data to write (JSON string)"],
        directory: Annotated[str, "Directory to write file in (default: examples/artifacts)"] = "examples/artifacts"
    ) -> str:
        """Write data to a JSON file."""
        try:
            os.makedirs(directory, exist_ok=True)
            filepath = os.path.join(directory, filename)
            
            # Parse and validate JSON
            parsed_data = json.loads(data)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(parsed_data, f, indent=2, ensure_ascii=False)
            
            return f"✅ Wrote JSON data to '{filepath}'"
        except json.JSONDecodeError as e:
            return f"❌ Invalid JSON format: {e}"
        except Exception as e:
            return f"❌ Error writing JSON file: {e}"
    
    @tool
    def _validate_json(
        self,
        data: Annotated[str, "JSON data to validate"]
    ) -> str:
        """Validate JSON data format."""
        try:
            parsed_data = json.loads(data)
            return f"✅ JSON is valid\n📊 Type: {type(parsed_data).__name__}\n📏 Size: {len(data)} characters"
        except json.JSONDecodeError as e:
            return f"❌ Invalid JSON: {e}"
        except Exception as e:
            return f"❌ Error validating JSON: {e}"
    
    @tool
    def _transform_json(
        self,
        data: Annotated[str, "JSON data to transform"],
        transformation: Annotated[str, "Transformation to apply (flatten, normalize, etc.)"]
    ) -> str:
        """Transform JSON data."""
        try:
            parsed_data = json.loads(data)
            
            if transformation == "flatten":
                def flatten_dict(d, parent_key='', sep='_'):
                    items = []
                    for k, v in d.items():
                        new_key = f"{parent_key}{sep}{k}" if parent_key else k
                        if isinstance(v, dict):
                            items.extend(flatten_dict(v, new_key, sep=sep).items())
                        else:
                            items.append((new_key, v))
                    return dict(items)
                
                if isinstance(parsed_data, dict):
                    flattened = flatten_dict(parsed_data)
                    return f"✅ Flattened JSON:\n{json.dumps(flattened, indent=2)}"
                else:
                    return "❌ Flattening only works with JSON objects"
            else:
                return f"❌ Unknown transformation: {transformation}"
        except Exception as e:
            return f"❌ Error transforming JSON: {e}"
    
    @tool
    def _merge_json(
        self,
        files: Annotated[str, "Comma-separated list of JSON files to merge"],
        output_filename: Annotated[str, "Name of the output merged file"],
        directory: Annotated[str, "Directory containing the files (default: examples/artifacts)"] = "examples/artifacts"
    ) -> str:
        """Merge multiple JSON files into one."""
        try:
            file_list = [f.strip() for f in files.split(',')]
            merged_data = []
            
            for filename in file_list:
                filepath = os.path.join(directory, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        merged_data.extend(data)
                    else:
                        merged_data.append(data)
            
            output_path = os.path.join(directory, output_filename)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(merged_data, f, indent=2, ensure_ascii=False)
            
            return f"✅ Merged {len(file_list)} JSON files into '{output_filename}' with {len(merged_data)} items"
        except Exception as e:
            return f"❌ Error merging JSON files: {e}"
    
    @tool
    def _read_xml(
        self,
        filename: Annotated[str, "Name of the XML file to read"],
        directory: Annotated[str, "Directory containing the file (default: examples/artifacts)"] = "examples/artifacts"
    ) -> str:
        """Read data from an XML file."""
        try:
            filepath = os.path.join(directory, filename)
            tree = ET.parse(filepath)
            root = tree.getroot()
            
            info = f"📄 XML file '{filepath}':\n"
            info += f"🏷️ Root tag: {root.tag}\n"
            info += f"📏 Attributes: {len(root.attrib)}\n"
            info += f"👶 Children: {len(list(root))}\n"
            
            # Get all unique tags
            tags = set()
            for elem in root.iter():
                tags.add(elem.tag)
            info += f"🏷️ All tags: {', '.join(sorted(tags))}\n"
            
            return info
        except Exception as e:
            return f"❌ Error reading XML file: {e}"
    
    @tool
    def _write_xml(
        self,
        filename: Annotated[str, "Name of the XML file to write"],
        root_tag: Annotated[str, "Root tag name"],
        data: Annotated[str, "Data to write (JSON format)"],
        directory: Annotated[str, "Directory to write file in (default: examples/artifacts)"] = "examples/artifacts"
    ) -> str:
        """Write data to an XML file."""
        try:
            os.makedirs(directory, exist_ok=True)
            filepath = os.path.join(directory, filename)
            
            # Parse JSON data
            parsed_data = json.loads(data)
            
            # Create XML structure
            root = ET.Element(root_tag)
            
            def dict_to_xml(parent, data):
                if isinstance(data, dict):
                    for key, value in data.items():
                        child = ET.SubElement(parent, key)
                        dict_to_xml(child, value)
                elif isinstance(data, list):
                    for item in data:
                        dict_to_xml(parent, item)
                else:
                    parent.text = str(data)
            
            dict_to_xml(root, parsed_data)
            
            # Write XML
            tree = ET.ElementTree(root)
            tree.write(filepath, encoding='utf-8', xml_declaration=True)
            
            return f"✅ Wrote XML data to '{filepath}'"
        except Exception as e:
            return f"❌ Error writing XML file: {e}"
    
    @tool
    def _validate_xml(
        self,
        data: Annotated[str, "XML data to validate"]
    ) -> str:
        """Validate XML data format."""
        try:
            root = ET.fromstring(data)
            return f"✅ XML is valid\n🏷️ Root tag: {root.tag}\n👶 Children: {len(list(root))}"
        except ET.ParseError as e:
            return f"❌ Invalid XML: {e}"
        except Exception as e:
            return f"❌ Error validating XML: {e}"
    
    @tool
    def _transform_xml(
        self,
        data: Annotated[str, "XML data to transform"],
        transformation: Annotated[str, "Transformation to apply (to_json, to_html, etc.)"]
    ) -> str:
        """Transform XML data."""
        try:
            root = ET.fromstring(data)
            
            if transformation == "to_json":
                def xml_to_dict(element):
                    result = {}
                    if element.text and element.text.strip():
                        result['text'] = element.text.strip()
                    if element.attrib:
                        result['attributes'] = element.attrib
                    if list(element):
                        result['children'] = [xml_to_dict(child) for child in element]
                    return result
                
                json_data = xml_to_dict(root)
                return f"✅ Converted XML to JSON:\n{json.dumps(json_data, indent=2)}"
            else:
                return f"❌ Unknown transformation: {transformation}"
        except Exception as e:
            return f"❌ Error transforming XML: {e}"
    
    @tool
    def _read_yaml(
        self,
        filename: Annotated[str, "Name of the YAML file to read"],
        directory: Annotated[str, "Directory containing the file (default: examples/artifacts)"] = "examples/artifacts"
    ) -> str:
        """Read data from a YAML file."""
        try:
            filepath = os.path.join(directory, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            info = f"📄 YAML file '{filepath}':\n"
            info += f"📏 Size: {len(yaml.dump(data))} characters\n"
            info += f"🔢 Type: {type(data).__name__}\n"
            
            if isinstance(data, dict):
                info += f"🔑 Keys: {', '.join(data.keys())}\n"
            elif isinstance(data, list):
                info += f"📊 Items: {len(data)}\n"
            
            info += f"📋 Content:\n{yaml.dump(data, default_flow_style=False)[:500]}...\n"
            
            return info
        except Exception as e:
            return f"❌ Error reading YAML file: {e}"
    
    @tool
    def _write_yaml(
        self,
        filename: Annotated[str, "Name of the YAML file to write"],
        data: Annotated[str, "Data to write (JSON string)"],
        directory: Annotated[str, "Directory to write file in (default: examples/artifacts)"] = "examples/artifacts"
    ) -> str:
        """Write data to a YAML file."""
        try:
            os.makedirs(directory, exist_ok=True)
            filepath = os.path.join(directory, filename)
            
            # Parse JSON data
            parsed_data = json.loads(data)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                yaml.dump(parsed_data, f, default_flow_style=False, allow_unicode=True)
            
            return f"✅ Wrote YAML data to '{filepath}'"
        except Exception as e:
            return f"❌ Error writing YAML file: {e}"
    
    @tool
    def _read_csv(
        self,
        filename: Annotated[str, "Name of the CSV file to read"],
        directory: Annotated[str, "Directory containing the file (default: examples/artifacts)"] = "examples/artifacts"
    ) -> str:
        """Read data from a CSV file."""
        try:
            filepath = os.path.join(directory, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            info = f"📄 CSV file '{filepath}':\n"
            info += f"📏 Rows: {len(rows)}\n"
            if rows:
                info += f"📋 Columns: {', '.join(rows[0].keys())}\n"
                info += f"📊 First row: {rows[0]}\n"
            
            return info
        except Exception as e:
            return f"❌ Error reading CSV file: {e}"
    
    @tool
    def _write_csv(
        self,
        filename: Annotated[str, "Name of the CSV file to write"],
        data: Annotated[str, "Data to write (JSON array format)"],
        directory: Annotated[str, "Directory to write file in (default: examples/artifacts)"] = "examples/artifacts"
    ) -> str:
        """Write data to a CSV file."""
        try:
            os.makedirs(directory, exist_ok=True)
            filepath = os.path.join(directory, filename)
            
            # Parse JSON data
            parsed_data = json.loads(data)
            
            if not parsed_data:
                return "❌ No data to write"
            
            # Write CSV
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=parsed_data[0].keys())
                writer.writeheader()
                writer.writerows(parsed_data)
            
            return f"✅ Wrote {len(parsed_data)} rows to '{filepath}'"
        except Exception as e:
            return f"❌ Error writing CSV file: {e}"
    
    @tool
    def _read_toml(
        self,
        filename: Annotated[str, "Name of the TOML file to read"],
        directory: Annotated[str, "Directory containing the file (default: examples/artifacts)"] = "examples/artifacts"
    ) -> str:
        """Read data from a TOML file."""
        try:
            filepath = os.path.join(directory, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                data = toml.load(f)
            
            info = f"📄 TOML file '{filepath}':\n"
            info += f"📏 Size: {len(toml.dumps(data))} characters\n"
            info += f"🔢 Type: {type(data).__name__}\n"
            
            if isinstance(data, dict):
                info += f"🔑 Keys: {', '.join(data.keys())}\n"
            
            info += f"📋 Content:\n{toml.dumps(data)[:500]}...\n"
            
            return info
        except Exception as e:
            return f"❌ Error reading TOML file: {e}"
    
    @tool
    def _write_toml(
        self,
        filename: Annotated[str, "Name of the TOML file to write"],
        data: Annotated[str, "Data to write (JSON string)"],
        directory: Annotated[str, "Directory to write file in (default: examples/artifacts)"] = "examples/artifacts"
    ) -> str:
        """Write data to a TOML file."""
        try:
            os.makedirs(directory, exist_ok=True)
            filepath = os.path.join(directory, filename)
            
            # Parse JSON data
            parsed_data = json.loads(data)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                toml.dump(parsed_data, f)
            
            return f"✅ Wrote TOML data to '{filepath}'"
        except Exception as e:
            return f"❌ Error writing TOML file: {e}"
    
    @tool
    def _read_ini(
        self,
        filename: Annotated[str, "Name of the INI file to read"],
        directory: Annotated[str, "Directory containing the file (default: examples/artifacts)"] = "examples/artifacts"
    ) -> str:
        """Read data from an INI file."""
        try:
            filepath = os.path.join(directory, filename)
            config = configparser.ConfigParser()
            config.read(filepath)
            
            info = f"📄 INI file '{filepath}':\n"
            info += f"📋 Sections: {', '.join(config.sections())}\n"
            
            for section in config.sections():
                info += f"🔧 [{section}]: {', '.join(config[section].keys())}\n"
            
            return info
        except Exception as e:
            return f"❌ Error reading INI file: {e}"
    
    @tool
    def _write_ini(
        self,
        filename: Annotated[str, "Name of the INI file to write"],
        data: Annotated[str, "Data to write (JSON format with sections)"],
        directory: Annotated[str, "Directory to write file in (default: examples/artifacts)"] = "examples/artifacts"
    ) -> str:
        """Write data to an INI file."""
        try:
            os.makedirs(directory, exist_ok=True)
            filepath = os.path.join(directory, filename)
            
            # Parse JSON data
            parsed_data = json.loads(data)
            
            config = configparser.ConfigParser()
            for section, options in parsed_data.items():
                config[section] = options
            
            with open(filepath, 'w', encoding='utf-8') as f:
                config.write(f)
            
            return f"✅ Wrote INI data to '{filepath}'"
        except Exception as e:
            return f"❌ Error writing INI file: {e}"
    
    @tool
    def _create_sqlite(
        self,
        filename: Annotated[str, "Name of the SQLite database to create"],
        sql_schema: Annotated[str, "Database schema (SQL CREATE TABLE statements)"],
        directory: Annotated[str, "Directory to create database in (default: examples/artifacts)"] = "examples/artifacts"
    ) -> str:
        """Create a SQLite database with schema."""
        try:
            os.makedirs(directory, exist_ok=True)
            filepath = os.path.join(directory, filename)
            
            conn = sqlite3.connect(filepath)
            cursor = conn.cursor()
            
            # Execute schema
            cursor.executescript(sql_schema)
            conn.commit()
            conn.close()
            
            return f"✅ Created SQLite database '{filepath}' with schema"
        except Exception as e:
            return f"❌ Error creating SQLite database: {e}"
    
    @tool
    def _query_sqlite(
        self,
        filename: Annotated[str, "Name of the SQLite database to query"],
        query: Annotated[str, "SQL query to execute"],
        directory: Annotated[str, "Directory containing the database (default: examples/artifacts)"] = "examples/artifacts"
    ) -> str:
        """Execute a query on a SQLite database."""
        try:
            filepath = os.path.join(directory, filename)
            conn = sqlite3.connect(filepath)
            cursor = conn.cursor()
            
            cursor.execute(query)
            results = cursor.fetchall()
            
            conn.close()
            
            return f"✅ Query executed successfully\n📊 Results: {len(results)} rows\n📋 Data: {results[:10]}"
        except Exception as e:
            return f"❌ Error executing query: {e}"
    
    @tool
    def _convert_data(
        self,
        filename: Annotated[str, "Name of the file to convert"],
        source_format: Annotated[str, "Source format (json, xml, yaml, csv, toml, ini)"],
        target_format: Annotated[str, "Target format (json, xml, yaml, csv, toml, ini)"],
        output_filename: Annotated[str, "Name of the output file"],
        directory: Annotated[str, "Directory containing the file (default: examples/artifacts)"] = "examples/artifacts"
    ) -> str:
        """Convert data from one format to another."""
        try:
            filepath = os.path.join(directory, filename)
            output_path = os.path.join(directory, output_filename)
            
            # Read data based on source format
            if source_format.lower() == 'json':
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            elif source_format.lower() == 'yaml':
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
            elif source_format.lower() == 'csv':
                with open(filepath, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    data = list(reader)
            else:
                return f"❌ Unsupported source format: {source_format}"
            
            # Write data based on target format
            if target_format.lower() == 'json':
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            elif target_format.lower() == 'yaml':
                with open(output_path, 'w', encoding='utf-8') as f:
                    yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
            elif target_format.lower() == 'csv':
                with open(output_path, 'w', newline='', encoding='utf-8') as f:
                    if data and isinstance(data, list):
                        writer = csv.DictWriter(f, fieldnames=data[0].keys())
                        writer.writeheader()
                        writer.writerows(data)
            else:
                return f"❌ Unsupported target format: {target_format}"
            
            return f"✅ Converted '{filename}' from {source_format.upper()} to {target_format.upper()} and saved as '{output_filename}'"
        except Exception as e:
            return f"❌ Error converting data: {e}"
    
    @tool
    def _analyze_data(
        self,
        filename: Annotated[str, "Name of the data file to analyze"],
        format: Annotated[str, "Data format (json, xml, yaml, csv, toml, ini)"],
        directory: Annotated[str, "Directory containing the file (default: examples/artifacts)"] = "examples/artifacts"
    ) -> str:
        """Analyze data file and provide statistics."""
        try:
            filepath = os.path.join(directory, filename)
            
            # Read data based on format
            if format.lower() == 'json':
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            elif format.lower() == 'yaml':
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
            elif format.lower() == 'csv':
                with open(filepath, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    data = list(reader)
            else:
                return f"❌ Unsupported format: {format}"
            
            analysis = f"📊 Analysis of '{filename}':\n"
            analysis += f"📏 File size: {os.path.getsize(filepath)} bytes\n"
            analysis += f"🔢 Data type: {type(data).__name__}\n"
            
            if isinstance(data, dict):
                analysis += f"🔑 Keys: {len(data)}\n"
                analysis += f"📋 Key names: {', '.join(data.keys())}\n"
            elif isinstance(data, list):
                analysis += f"📊 Items: {len(data)}\n"
                if data:
                    analysis += f"🔢 First item type: {type(data[0]).__name__}\n"
            
            return analysis
        except Exception as e:
            return f"❌ Error analyzing data: {e}"
    
    @tool
    def _clean_data(
        self,
        filename: Annotated[str, "Name of the data file to clean"],
        format: Annotated[str, "Data format (json, xml, yaml, csv, toml, ini)"],
        output_filename: Annotated[str, "Name of the cleaned output file"],
        directory: Annotated[str, "Directory containing the file (default: examples/artifacts)"] = "examples/artifacts"
    ) -> str:
        """Clean data file by removing empty values, duplicates, etc."""
        try:
            filepath = os.path.join(directory, filename)
            output_path = os.path.join(directory, output_filename)
            
            # Read data based on format
            if format.lower() == 'json':
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            elif format.lower() == 'csv':
                with open(filepath, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    data = list(reader)
            else:
                return f"❌ Cleaning not yet implemented for format: {format}"
            
            # Clean data
            if isinstance(data, list):
                # Remove empty dictionaries
                cleaned_data = [item for item in data if item]
                # Remove duplicates (if items are hashable)
                try:
                    cleaned_data = list(dict.fromkeys(cleaned_data))
                except:
                    pass
            else:
                cleaned_data = data
            
            # Write cleaned data
            if format.lower() == 'json':
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(cleaned_data, f, indent=2, ensure_ascii=False)
            elif format.lower() == 'csv':
                with open(output_path, 'w', newline='', encoding='utf-8') as f:
                    if cleaned_data:
                        writer = csv.DictWriter(f, fieldnames=cleaned_data[0].keys())
                        writer.writeheader()
                        writer.writerows(cleaned_data)
            
            return f"✅ Cleaned data and saved to '{output_filename}'"
        except Exception as e:
            return f"❌ Error cleaning data: {e}"
    
    @tool
    def _validate_data(
        self,
        filename: Annotated[str, "Name of the data file to validate"],
        format: Annotated[str, "Data format (json, xml, yaml, csv, toml, ini)"],
        directory: Annotated[str, "Directory containing the file (default: examples/artifacts)"] = "examples/artifacts"
    ) -> str:
        """Validate data file format and structure."""
        try:
            filepath = os.path.join(directory, filename)
            
            if format.lower() == 'json':
                with open(filepath, 'r', encoding='utf-8') as f:
                    json.load(f)
                return f"✅ JSON file '{filename}' is valid"
            elif format.lower() == 'xml':
                ET.parse(filepath)
                return f"✅ XML file '{filename}' is valid"
            elif format.lower() == 'yaml':
                with open(filepath, 'r', encoding='utf-8') as f:
                    yaml.safe_load(f)
                return f"✅ YAML file '{filename}' is valid"
            elif format.lower() == 'csv':
                with open(filepath, 'r', encoding='utf-8') as f:
                    csv.DictReader(f)
                return f"✅ CSV file '{filename}' is valid"
            else:
                return f"❌ Validation not yet implemented for format: {format}"
        except Exception as e:
            return f"❌ Validation failed: {e}"
