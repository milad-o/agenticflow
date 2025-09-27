"""
Data Format Agent - XML/JSON/CSV Processing and Conversion
=========================================================

Comprehensive data format operations including parsing, validation, conversion, and transformation.
"""

import json
import xml.etree.ElementTree as ET
import xml.dom.minidom
import csv
import yaml
import pandas as pd
import tempfile
import os
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import io
import jsonschema
from pathlib import Path


class DataFormatAgent:
    """Agent for data format processing and conversion."""

    def __init__(self):
        self.capabilities = [
            "json_processing",
            "xml_processing",
            "csv_processing",
            "yaml_processing",
            "data_conversion",
            "data_validation",
            "schema_generation",
            "data_transformation",
            "format_detection",
            "data_cleaning"
        ]
        self.operation_history = []

    async def arun(self, task: str) -> Dict[str, Any]:
        """Async execution wrapper."""
        return self.execute(task)

    def execute(self, task: str) -> Dict[str, Any]:
        """Execute data format operations."""
        task_lower = task.lower()

        if any(keyword in task_lower for keyword in ["convert", "transform", "change format"]):
            return self._convert_data_task(task)
        elif any(keyword in task_lower for keyword in ["validate", "check", "verify"]):
            return self._validate_data_task(task)
        elif any(keyword in task_lower for keyword in ["parse", "read", "load"]):
            return self._parse_data_task(task)
        elif any(keyword in task_lower for keyword in ["generate", "create", "make"]):
            return self._generate_data_task(task)
        elif any(keyword in task_lower for keyword in ["clean", "normalize", "standardize"]):
            return self._clean_data_task(task)
        elif any(keyword in task_lower for keyword in ["analyze", "inspect", "examine"]):
            return self._analyze_data_task(task)
        elif any(keyword in task_lower for keyword in ["merge", "combine", "join"]):
            return self._merge_data_task(task)
        elif any(keyword in task_lower for keyword in ["split", "separate", "divide"]):
            return self._split_data_task(task)
        elif any(keyword in task_lower for keyword in ["schema", "structure", "format"]):
            return self._schema_task(task)
        else:
            return self._general_data_format_task(task)

    def _convert_data_task(self, task: str) -> Dict[str, Any]:
        """Convert between data formats."""
        conversion_info = self._extract_conversion_info(task)

        if not conversion_info.get("source_format") or not conversion_info.get("target_format"):
            return {
                "action": "data_conversion",
                "success": False,
                "error": "Source and target formats must be specified"
            }

        try:
            source_format = conversion_info["source_format"].lower()
            target_format = conversion_info["target_format"].lower()
            data_path = conversion_info.get("data_path")
            data_content = conversion_info.get("data_content")

            # Load source data
            if data_path and os.path.exists(data_path):
                source_data = self._load_data_from_file(data_path, source_format)
            elif data_content:
                source_data = self._parse_data_content(data_content, source_format)
            else:
                return {
                    "action": "data_conversion",
                    "success": False,
                    "error": "No data source provided"
                }

            # Convert data
            converted_data = self._convert_data_format(source_data, source_format, target_format)

            # Save converted data
            output_path = self._save_converted_data(converted_data, target_format)

            self._log_operation("convert", f"{source_format} -> {target_format}", True)

            return {
                "action": "data_conversion",
                "success": True,
                "source_format": source_format,
                "target_format": target_format,
                "output_path": output_path,
                "converted_data": converted_data if len(str(converted_data)) < 1000 else f"<Large data: {len(str(converted_data))} characters>",
                "data_preview": str(converted_data)[:500] + "..." if len(str(converted_data)) > 500 else converted_data
            }

        except Exception as e:
            self._log_operation("convert", f"{conversion_info.get('source_format')} -> {conversion_info.get('target_format')}", False, str(e))
            return {
                "action": "data_conversion",
                "success": False,
                "error": str(e)
            }

    def _validate_data_task(self, task: str) -> Dict[str, Any]:
        """Validate data format and structure."""
        validation_info = self._extract_validation_info(task)

        if not validation_info.get("data_format"):
            return {
                "action": "data_validation",
                "success": False,
                "error": "Data format must be specified"
            }

        try:
            data_format = validation_info["data_format"].lower()
            data_path = validation_info.get("data_path")
            data_content = validation_info.get("data_content")
            schema_path = validation_info.get("schema_path")

            # Load data
            if data_path and os.path.exists(data_path):
                with open(data_path, 'r', encoding='utf-8') as f:
                    raw_data = f.read()
            elif data_content:
                raw_data = data_content
            else:
                return {
                    "action": "data_validation",
                    "success": False,
                    "error": "No data source provided"
                }

            # Validate based on format
            validation_result = self._validate_format(raw_data, data_format, schema_path)

            self._log_operation("validate", data_format, validation_result["valid"])

            return {
                "action": "data_validation",
                "success": True,
                "data_format": data_format,
                **validation_result
            }

        except Exception as e:
            self._log_operation("validate", validation_info.get("data_format"), False, str(e))
            return {
                "action": "data_validation",
                "success": False,
                "error": str(e)
            }

    def _parse_data_task(self, task: str) -> Dict[str, Any]:
        """Parse data from various formats."""
        parse_info = self._extract_parse_info(task)

        try:
            data_path = parse_info.get("data_path")
            data_format = parse_info.get("data_format")

            if not data_path or not os.path.exists(data_path):
                return {
                    "action": "data_parsing",
                    "success": False,
                    "error": f"Data file not found: {data_path}"
                }

            # Auto-detect format if not specified
            if not data_format:
                data_format = self._detect_data_format(data_path)

            # Parse data
            parsed_data = self._load_data_from_file(data_path, data_format)

            # Generate analysis
            analysis = self._analyze_parsed_data(parsed_data, data_format)

            self._log_operation("parse", f"{data_path} ({data_format})", True)

            return {
                "action": "data_parsing",
                "success": True,
                "data_path": data_path,
                "detected_format": data_format,
                "parsed_data": parsed_data if len(str(parsed_data)) < 1000 else f"<Large data structure>",
                "analysis": analysis,
                "data_preview": str(parsed_data)[:500] + "..." if len(str(parsed_data)) > 500 else parsed_data
            }

        except Exception as e:
            self._log_operation("parse", parse_info.get("data_path"), False, str(e))
            return {
                "action": "data_parsing",
                "success": False,
                "error": str(e)
            }

    def _generate_data_task(self, task: str) -> Dict[str, Any]:
        """Generate data in specified format."""
        generation_info = self._extract_generation_info(task)

        try:
            data_format = generation_info.get("data_format", "json")
            template_type = generation_info.get("template_type", "sample")
            size = generation_info.get("size", 10)

            # Generate sample data
            generated_data = self._generate_sample_data(data_format, template_type, size)

            # Save to file
            output_path = self._save_generated_data(generated_data, data_format)

            self._log_operation("generate", f"{data_format} ({template_type})", True)

            return {
                "action": "data_generation",
                "success": True,
                "data_format": data_format,
                "template_type": template_type,
                "output_path": output_path,
                "generated_data": generated_data,
                "size": size
            }

        except Exception as e:
            self._log_operation("generate", generation_info.get("data_format"), False, str(e))
            return {
                "action": "data_generation",
                "success": False,
                "error": str(e)
            }

    def _clean_data_task(self, task: str) -> Dict[str, Any]:
        """Clean and normalize data."""
        clean_info = self._extract_clean_info(task)

        try:
            data_path = clean_info.get("data_path")
            data_format = clean_info.get("data_format")
            operations = clean_info.get("operations", ["remove_empty", "trim_whitespace"])

            if not data_path or not os.path.exists(data_path):
                return {
                    "action": "data_cleaning",
                    "success": False,
                    "error": f"Data file not found: {data_path}"
                }

            # Load data
            if not data_format:
                data_format = self._detect_data_format(data_path)

            original_data = self._load_data_from_file(data_path, data_format)

            # Clean data
            cleaned_data, cleaning_report = self._clean_data(original_data, data_format, operations)

            # Save cleaned data
            output_path = self._save_cleaned_data(cleaned_data, data_format)

            self._log_operation("clean", f"{data_path} ({data_format})", True)

            return {
                "action": "data_cleaning",
                "success": True,
                "data_path": data_path,
                "data_format": data_format,
                "operations": operations,
                "output_path": output_path,
                "cleaning_report": cleaning_report,
                "cleaned_data": cleaned_data if len(str(cleaned_data)) < 1000 else f"<Large cleaned dataset>"
            }

        except Exception as e:
            self._log_operation("clean", clean_info.get("data_path"), False, str(e))
            return {
                "action": "data_cleaning",
                "success": False,
                "error": str(e)
            }

    def _analyze_data_task(self, task: str) -> Dict[str, Any]:
        """Analyze data structure and content."""
        analyze_info = self._extract_analyze_info(task)

        try:
            data_path = analyze_info.get("data_path")

            if not data_path or not os.path.exists(data_path):
                return {
                    "action": "data_analysis",
                    "success": False,
                    "error": f"Data file not found: {data_path}"
                }

            # Detect format and load data
            data_format = self._detect_data_format(data_path)
            data = self._load_data_from_file(data_path, data_format)

            # Perform comprehensive analysis
            analysis = self._perform_data_analysis(data, data_format)

            self._log_operation("analyze", f"{data_path} ({data_format})", True)

            return {
                "action": "data_analysis",
                "success": True,
                "data_path": data_path,
                "data_format": data_format,
                "analysis": analysis
            }

        except Exception as e:
            self._log_operation("analyze", analyze_info.get("data_path"), False, str(e))
            return {
                "action": "data_analysis",
                "success": False,
                "error": str(e)
            }

    def _schema_task(self, task: str) -> Dict[str, Any]:
        """Generate or validate data schemas."""
        schema_info = self._extract_schema_info(task)

        try:
            data_path = schema_info.get("data_path")
            operation = schema_info.get("operation", "generate")  # generate or validate

            if not data_path or not os.path.exists(data_path):
                return {
                    "action": "schema_operation",
                    "success": False,
                    "error": f"Data file not found: {data_path}"
                }

            data_format = self._detect_data_format(data_path)
            data = self._load_data_from_file(data_path, data_format)

            if operation == "generate":
                schema = self._generate_schema(data, data_format)
                schema_path = self._save_schema(schema, data_format)

                return {
                    "action": "schema_generation",
                    "success": True,
                    "data_path": data_path,
                    "data_format": data_format,
                    "schema": schema,
                    "schema_path": schema_path
                }
            else:
                # Schema validation would go here
                return {
                    "action": "schema_validation",
                    "success": True,
                    "message": "Schema validation not yet implemented"
                }

        except Exception as e:
            self._log_operation("schema", schema_info.get("operation"), False, str(e))
            return {
                "action": "schema_operation",
                "success": False,
                "error": str(e)
            }

    def _general_data_format_task(self, task: str) -> Dict[str, Any]:
        """Handle general data format tasks."""
        return {
            "action": "data_format_assistance",
            "success": True,
            "message": "I can help with data format operations. Try asking me to:",
            "capabilities": [
                "Convert between JSON, XML, CSV, YAML formats",
                "Validate data format and structure",
                "Parse and analyze data files",
                "Generate sample data in various formats",
                "Clean and normalize data",
                "Create data schemas",
                "Merge and split data files",
                "Detect data formats automatically"
            ],
            "supported_formats": ["JSON", "XML", "CSV", "YAML", "TSV"],
            "examples": [
                "Convert 'data.csv' to JSON format",
                "Validate this JSON: {'name': 'test'}",
                "Parse the XML file 'config.xml'",
                "Generate sample CSV data with 100 rows",
                "Clean the data in 'messy_data.json'",
                "Analyze the structure of 'dataset.csv'"
            ]
        }

    # Helper methods for data operations
    def _load_data_from_file(self, file_path: str, data_format: str) -> Any:
        """Load data from file based on format."""
        with open(file_path, 'r', encoding='utf-8') as f:
            if data_format == 'json':
                return json.load(f)
            elif data_format == 'xml':
                return ET.parse(f).getroot()
            elif data_format == 'csv':
                return list(csv.DictReader(f))
            elif data_format == 'yaml':
                return yaml.safe_load(f)
            else:
                return f.read()

    def _parse_data_content(self, content: str, data_format: str) -> Any:
        """Parse data content based on format."""
        if data_format == 'json':
            return json.loads(content)
        elif data_format == 'xml':
            return ET.fromstring(content)
        elif data_format == 'csv':
            return list(csv.DictReader(io.StringIO(content)))
        elif data_format == 'yaml':
            return yaml.safe_load(content)
        else:
            return content

    def _convert_data_format(self, data: Any, source_format: str, target_format: str) -> Any:
        """Convert data between formats."""
        # Normalize data to Python objects first
        if source_format == 'xml':
            data = self._xml_to_dict(data)
        elif source_format == 'csv':
            # CSV is already a list of dicts
            pass

        # Convert to target format
        if target_format == 'json':
            return json.dumps(data, indent=2, default=str)
        elif target_format == 'xml':
            return self._dict_to_xml(data)
        elif target_format == 'csv':
            return self._dict_to_csv(data)
        elif target_format == 'yaml':
            return yaml.dump(data, default_flow_style=False)
        else:
            return str(data)

    def _xml_to_dict(self, element) -> Dict[str, Any]:
        """Convert XML element to dictionary."""
        result = {}

        # Handle attributes
        if element.attrib:
            result.update(element.attrib)

        # Handle children
        for child in element:
            child_data = self._xml_to_dict(child)
            if child.tag in result:
                # Convert to list if multiple children with same tag
                if not isinstance(result[child.tag], list):
                    result[child.tag] = [result[child.tag]]
                result[child.tag].append(child_data)
            else:
                result[child.tag] = child_data

        # Handle text content
        if element.text and element.text.strip():
            if result:
                result['_text'] = element.text.strip()
            else:
                return element.text.strip()

        return result

    def _dict_to_xml(self, data: Dict[str, Any], root_name: str = "root") -> str:
        """Convert dictionary to XML string."""
        def dict_to_xml_element(d, name):
            elem = ET.Element(name)

            if isinstance(d, dict):
                for key, value in d.items():
                    if key.startswith('_'):
                        continue
                    child = dict_to_xml_element(value, key)
                    elem.append(child)
            elif isinstance(d, list):
                for item in d:
                    child = dict_to_xml_element(item, name[:-1] if name.endswith('s') else 'item')
                    elem.append(child)
            else:
                elem.text = str(d)

            return elem

        root = dict_to_xml_element(data, root_name)
        return ET.tostring(root, encoding='unicode')

    def _dict_to_csv(self, data: Any) -> str:
        """Convert data to CSV string."""
        output = io.StringIO()

        if isinstance(data, list) and data and isinstance(data[0], dict):
            # List of dictionaries
            fieldnames = data[0].keys()
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        elif isinstance(data, dict):
            # Single dictionary
            writer = csv.DictWriter(output, fieldnames=data.keys())
            writer.writeheader()
            writer.writerow(data)
        else:
            # Fallback
            writer = csv.writer(output)
            writer.writerow(['value'])
            writer.writerow([str(data)])

        return output.getvalue()

    def _detect_data_format(self, file_path: str) -> str:
        """Auto-detect data format from file."""
        extension = Path(file_path).suffix.lower()

        format_map = {
            '.json': 'json',
            '.xml': 'xml',
            '.csv': 'csv',
            '.tsv': 'csv',
            '.yaml': 'yaml',
            '.yml': 'yaml'
        }

        return format_map.get(extension, 'text')

    def _validate_format(self, data: str, data_format: str, schema_path: str = None) -> Dict[str, Any]:
        """Validate data format."""
        try:
            if data_format == 'json':
                parsed = json.loads(data)
                return {"valid": True, "parsed_data": parsed, "message": "Valid JSON"}
            elif data_format == 'xml':
                parsed = ET.fromstring(data)
                return {"valid": True, "parsed_data": "XML parsed successfully", "message": "Valid XML"}
            elif data_format == 'csv':
                lines = data.strip().split('\n')
                reader = csv.reader(lines)
                rows = list(reader)
                return {"valid": True, "rows": len(rows), "columns": len(rows[0]) if rows else 0, "message": "Valid CSV"}
            elif data_format == 'yaml':
                parsed = yaml.safe_load(data)
                return {"valid": True, "parsed_data": parsed, "message": "Valid YAML"}
            else:
                return {"valid": False, "message": f"Unsupported format: {data_format}"}

        except Exception as e:
            return {"valid": False, "error": str(e), "message": f"Invalid {data_format.upper()}"}

    def _analyze_parsed_data(self, data: Any, data_format: str) -> Dict[str, Any]:
        """Analyze parsed data structure."""
        analysis = {
            "data_type": type(data).__name__,
            "format": data_format
        }

        if isinstance(data, list):
            analysis["length"] = len(data)
            if data:
                analysis["first_item_type"] = type(data[0]).__name__
                if isinstance(data[0], dict):
                    analysis["columns"] = list(data[0].keys())
        elif isinstance(data, dict):
            analysis["keys"] = list(data.keys())
            analysis["key_count"] = len(data)

        return analysis

    def _generate_sample_data(self, data_format: str, template_type: str, size: int) -> Any:
        """Generate sample data."""
        if template_type == "users":
            sample_data = [
                {"id": i, "name": f"User {i}", "email": f"user{i}@example.com", "age": 20 + (i % 40)}
                for i in range(1, size + 1)
            ]
        elif template_type == "products":
            sample_data = [
                {"id": i, "name": f"Product {i}", "price": round(10.99 + (i * 5.50), 2), "category": "Electronics"}
                for i in range(1, size + 1)
            ]
        else:
            sample_data = [{"id": i, "value": f"Data {i}", "timestamp": datetime.now().isoformat()} for i in range(size)]

        return sample_data

    def _save_converted_data(self, data: Any, target_format: str) -> str:
        """Save converted data to file."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"converted_{timestamp}.{target_format}"
        file_path = os.path.join(tempfile.gettempdir(), filename)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(data)

        return file_path

    def _save_generated_data(self, data: Any, data_format: str) -> str:
        """Save generated data to file."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"generated_{timestamp}.{data_format}"
        file_path = os.path.join(tempfile.gettempdir(), filename)

        with open(file_path, 'w', encoding='utf-8') as f:
            if data_format == 'json':
                json.dump(data, f, indent=2)
            elif data_format == 'csv':
                writer = csv.DictWriter(f, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
            else:
                f.write(str(data))

        return file_path

    def _clean_data(self, data: Any, data_format: str, operations: List[str]) -> tuple[Any, Dict[str, Any]]:
        """Clean data based on specified operations."""
        cleaned_data = data
        report = {"operations_performed": operations, "changes": []}

        # Implementation would depend on data format and operations
        # This is a simplified version

        if "remove_empty" in operations and isinstance(data, list):
            original_length = len(data)
            cleaned_data = [item for item in data if item]
            removed = original_length - len(cleaned_data)
            if removed > 0:
                report["changes"].append(f"Removed {removed} empty items")

        return cleaned_data, report

    def _save_cleaned_data(self, data: Any, data_format: str) -> str:
        """Save cleaned data to file."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"cleaned_{timestamp}.{data_format}"
        file_path = os.path.join(tempfile.gettempdir(), filename)

        with open(file_path, 'w', encoding='utf-8') as f:
            if data_format == 'json':
                json.dump(data, f, indent=2)
            else:
                f.write(str(data))

        return file_path

    def _perform_data_analysis(self, data: Any, data_format: str) -> Dict[str, Any]:
        """Perform comprehensive data analysis."""
        analysis = {
            "format": data_format,
            "data_type": type(data).__name__,
            "size_estimate": len(str(data))
        }

        if isinstance(data, list):
            analysis.update({
                "item_count": len(data),
                "is_homogeneous": len(set(type(item).__name__ for item in data)) == 1 if data else True
            })

            if data and isinstance(data[0], dict):
                all_keys = set()
                for item in data:
                    if isinstance(item, dict):
                        all_keys.update(item.keys())
                analysis["unique_fields"] = list(all_keys)
                analysis["field_count"] = len(all_keys)

        elif isinstance(data, dict):
            analysis.update({
                "field_count": len(data),
                "fields": list(data.keys())
            })

        return analysis

    def _generate_schema(self, data: Any, data_format: str) -> Dict[str, Any]:
        """Generate schema for data."""
        schema = {"format": data_format}

        if isinstance(data, list) and data and isinstance(data[0], dict):
            # Generate JSON schema for list of objects
            properties = {}
            for key in data[0].keys():
                # Simple type inference
                sample_value = data[0][key]
                if isinstance(sample_value, str):
                    properties[key] = {"type": "string"}
                elif isinstance(sample_value, int):
                    properties[key] = {"type": "integer"}
                elif isinstance(sample_value, float):
                    properties[key] = {"type": "number"}
                elif isinstance(sample_value, bool):
                    properties[key] = {"type": "boolean"}
                else:
                    properties[key] = {"type": "string"}

            schema.update({
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": properties
                }
            })

        return schema

    def _save_schema(self, schema: Dict[str, Any], data_format: str) -> str:
        """Save generated schema to file."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"schema_{timestamp}.json"
        file_path = os.path.join(tempfile.gettempdir(), filename)

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(schema, f, indent=2)

        return file_path

    def _log_operation(self, operation: str, details: str, success: bool, error: str = None):
        """Log data format operation."""
        self.operation_history.append({
            "operation": operation,
            "details": details,
            "success": success,
            "error": error,
            "timestamp": datetime.now().isoformat()
        })

    # Extraction methods for parsing tasks
    def _extract_conversion_info(self, task: str) -> Dict[str, Any]:
        """Extract conversion information from task."""
        info = {}

        # Simple pattern matching - in practice, you'd use more sophisticated NLP
        formats = ["json", "xml", "csv", "yaml"]

        for fmt in formats:
            if fmt in task.lower():
                if "from" in task.lower() and task.lower().index(fmt) < task.lower().index("to"):
                    info["source_format"] = fmt
                elif "to" in task.lower() and task.lower().index(fmt) > task.lower().index("to"):
                    info["target_format"] = fmt

        # Extract file path
        import re
        file_match = re.search(r'["\']([^"\']+\.[a-zA-Z]+)["\']', task)
        if file_match:
            info["data_path"] = file_match.group(1)

        return info

    def get_capabilities(self) -> List[str]:
        """Get agent capabilities."""
        return self.capabilities

    def get_operation_history(self) -> List[Dict[str, Any]]:
        """Get operation history."""
        return self.operation_history