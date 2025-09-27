"""
ETL Agent - Extract, Transform, Load Operations
==============================================

Comprehensive data pipeline operations for enterprise data processing.
"""

import pandas as pd
import numpy as np
import sqlite3
import json
import csv
import tempfile
import os
from typing import Dict, List, Any, Optional, Union, Callable
from datetime import datetime, timedelta
import requests
import yaml
from pathlib import Path
import logging


class ETLAgent:
    """Agent for Extract, Transform, Load operations and data pipelines."""

    def __init__(self):
        self.capabilities = [
            "data_extraction",
            "data_transformation",
            "data_loading",
            "pipeline_creation",
            "data_quality_checks",
            "batch_processing",
            "incremental_loads",
            "data_deduplication",
            "data_validation",
            "pipeline_monitoring"
        ]
        self.pipeline_history = []
        self.data_cache = {}

    async def arun(self, task: str) -> Dict[str, Any]:
        """Async execution wrapper."""
        return self.execute(task)

    def execute(self, task: str) -> Dict[str, Any]:
        """Execute ETL operations."""
        task_lower = task.lower()

        if any(keyword in task_lower for keyword in ["extract", "pull", "get data"]):
            return self._extract_data_task(task)
        elif any(keyword in task_lower for keyword in ["transform", "clean", "process"]):
            return self._transform_data_task(task)
        elif any(keyword in task_lower for keyword in ["load", "insert", "save"]):
            return self._load_data_task(task)
        elif any(keyword in task_lower for keyword in ["pipeline", "workflow", "etl"]):
            return self._pipeline_task(task)
        elif any(keyword in task_lower for keyword in ["validate", "quality", "check"]):
            return self._data_quality_task(task)
        elif any(keyword in task_lower for keyword in ["deduplicate", "duplicate", "unique"]):
            return self._deduplication_task(task)
        elif any(keyword in task_lower for keyword in ["merge", "join", "combine"]):
            return self._merge_data_task(task)
        elif any(keyword in task_lower for keyword in ["aggregate", "summarize", "group"]):
            return self._aggregation_task(task)
        elif any(keyword in task_lower for keyword in ["schedule", "batch", "incremental"]):
            return self._batch_processing_task(task)
        else:
            return self._general_etl_task(task)

    def _extract_data_task(self, task: str) -> Dict[str, Any]:
        """Extract data from various sources."""
        extraction_info = self._extract_extraction_info(task)

        try:
            source_type = extraction_info.get("source_type", "file")
            source_path = extraction_info.get("source_path")
            extraction_config = extraction_info.get("config", {})

            if source_type == "file":
                data = self._extract_from_file(source_path, extraction_config)
            elif source_type == "database":
                data = self._extract_from_database(source_path, extraction_config)
            elif source_type == "api":
                data = self._extract_from_api(source_path, extraction_config)
            elif source_type == "web":
                data = self._extract_from_web(source_path, extraction_config)
            else:
                return {
                    "action": "data_extraction",
                    "success": False,
                    "error": f"Unsupported source type: {source_type}"
                }

            # Cache extracted data
            cache_key = f"extract_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.data_cache[cache_key] = data

            self._log_pipeline_operation("extract", source_type, True)

            return {
                "action": "data_extraction",
                "success": True,
                "source_type": source_type,
                "source_path": source_path,
                "data_shape": self._get_data_shape(data),
                "cache_key": cache_key,
                "extracted_records": len(data) if isinstance(data, list) else 1,
                "data_preview": self._get_data_preview(data)
            }

        except Exception as e:
            self._log_pipeline_operation("extract", extraction_info.get("source_type"), False, str(e))
            return {
                "action": "data_extraction",
                "success": False,
                "error": str(e)
            }

    def _transform_data_task(self, task: str) -> Dict[str, Any]:
        """Transform data using various operations."""
        transform_info = self._extract_transform_info(task)

        try:
            source_key = transform_info.get("source_key")
            transformations = transform_info.get("transformations", [])

            # Get data from cache or load from file
            if source_key and source_key in self.data_cache:
                data = self.data_cache[source_key]
            else:
                data_path = transform_info.get("data_path")
                if not data_path or not os.path.exists(data_path):
                    return {
                        "action": "data_transformation",
                        "success": False,
                        "error": "No data source specified or found"
                    }
                data = self._load_data_for_transformation(data_path)

            # Apply transformations
            transformed_data, transformation_log = self._apply_transformations(data, transformations)

            # Cache transformed data
            cache_key = f"transform_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.data_cache[cache_key] = transformed_data

            self._log_pipeline_operation("transform", f"{len(transformations)} operations", True)

            return {
                "action": "data_transformation",
                "success": True,
                "transformations_applied": transformations,
                "transformation_log": transformation_log,
                "original_shape": self._get_data_shape(data),
                "transformed_shape": self._get_data_shape(transformed_data),
                "cache_key": cache_key,
                "data_preview": self._get_data_preview(transformed_data)
            }

        except Exception as e:
            self._log_pipeline_operation("transform", "transformation", False, str(e))
            return {
                "action": "data_transformation",
                "success": False,
                "error": str(e)
            }

    def _load_data_task(self, task: str) -> Dict[str, Any]:
        """Load data to target destinations."""
        load_info = self._extract_load_info(task)

        try:
            source_key = load_info.get("source_key")
            target_type = load_info.get("target_type", "file")
            target_path = load_info.get("target_path")
            load_config = load_info.get("config", {})

            # Get data from cache
            if source_key and source_key in self.data_cache:
                data = self.data_cache[source_key]
            else:
                return {
                    "action": "data_loading",
                    "success": False,
                    "error": "No data source specified in cache"
                }

            if target_type == "file":
                result = self._load_to_file(data, target_path, load_config)
            elif target_type == "database":
                result = self._load_to_database(data, target_path, load_config)
            elif target_type == "api":
                result = self._load_to_api(data, target_path, load_config)
            else:
                return {
                    "action": "data_loading",
                    "success": False,
                    "error": f"Unsupported target type: {target_type}"
                }

            self._log_pipeline_operation("load", target_type, True)

            return {
                "action": "data_loading",
                "success": True,
                "target_type": target_type,
                "target_path": target_path,
                "records_loaded": result.get("records_loaded", 0),
                "load_details": result
            }

        except Exception as e:
            self._log_pipeline_operation("load", load_info.get("target_type"), False, str(e))
            return {
                "action": "data_loading",
                "success": False,
                "error": str(e)
            }

    def _pipeline_task(self, task: str) -> Dict[str, Any]:
        """Execute complete ETL pipeline."""
        pipeline_info = self._extract_pipeline_info(task)

        try:
            pipeline_steps = pipeline_info.get("steps", [])
            pipeline_name = pipeline_info.get("name", f"pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}")

            if not pipeline_steps:
                # Create default pipeline
                pipeline_steps = [
                    {"type": "extract", "source": pipeline_info.get("source")},
                    {"type": "transform", "operations": ["clean", "validate"]},
                    {"type": "load", "target": pipeline_info.get("target")}
                ]

            pipeline_results = []
            current_data_key = None

            for i, step in enumerate(pipeline_steps):
                step_type = step.get("type")
                step_name = f"{pipeline_name}_step_{i+1}_{step_type}"

                if step_type == "extract":
                    result = self._execute_pipeline_extract(step, step_name)
                    current_data_key = result.get("cache_key")
                elif step_type == "transform":
                    result = self._execute_pipeline_transform(step, current_data_key, step_name)
                    current_data_key = result.get("cache_key")
                elif step_type == "load":
                    result = self._execute_pipeline_load(step, current_data_key, step_name)
                else:
                    result = {"success": False, "error": f"Unknown step type: {step_type}"}

                pipeline_results.append({
                    "step": i + 1,
                    "type": step_type,
                    "name": step_name,
                    "success": result.get("success", False),
                    "result": result
                })

                if not result.get("success", False):
                    break

            pipeline_success = all(step["success"] for step in pipeline_results)

            self._log_pipeline_operation("pipeline", pipeline_name, pipeline_success)

            return {
                "action": "etl_pipeline",
                "success": pipeline_success,
                "pipeline_name": pipeline_name,
                "steps_executed": len(pipeline_results),
                "pipeline_results": pipeline_results,
                "final_data_key": current_data_key
            }

        except Exception as e:
            self._log_pipeline_operation("pipeline", "execution", False, str(e))
            return {
                "action": "etl_pipeline",
                "success": False,
                "error": str(e)
            }

    def _data_quality_task(self, task: str) -> Dict[str, Any]:
        """Perform data quality checks."""
        quality_info = self._extract_quality_info(task)

        try:
            source_key = quality_info.get("source_key")
            data_path = quality_info.get("data_path")
            checks = quality_info.get("checks", ["completeness", "consistency", "accuracy"])

            # Get data
            if source_key and source_key in self.data_cache:
                data = self.data_cache[source_key]
            elif data_path and os.path.exists(data_path):
                data = self._load_data_for_transformation(data_path)
            else:
                return {
                    "action": "data_quality_check",
                    "success": False,
                    "error": "No data source specified"
                }

            # Perform quality checks
            quality_results = self._perform_quality_checks(data, checks)

            self._log_pipeline_operation("quality_check", f"{len(checks)} checks", True)

            return {
                "action": "data_quality_check",
                "success": True,
                "checks_performed": checks,
                "quality_results": quality_results,
                "overall_score": quality_results.get("overall_score", 0),
                "data_shape": self._get_data_shape(data)
            }

        except Exception as e:
            self._log_pipeline_operation("quality_check", "validation", False, str(e))
            return {
                "action": "data_quality_check",
                "success": False,
                "error": str(e)
            }

    def _deduplication_task(self, task: str) -> Dict[str, Any]:
        """Remove duplicate records from data."""
        dedup_info = self._extract_dedup_info(task)

        try:
            source_key = dedup_info.get("source_key")
            data_path = dedup_info.get("data_path")
            key_columns = dedup_info.get("key_columns", [])

            # Get data
            if source_key and source_key in self.data_cache:
                data = self.data_cache[source_key]
            elif data_path and os.path.exists(data_path):
                data = self._load_data_for_transformation(data_path)
            else:
                return {
                    "action": "data_deduplication",
                    "success": False,
                    "error": "No data source specified"
                }

            # Perform deduplication
            deduplicated_data, dedup_stats = self._deduplicate_data(data, key_columns)

            # Cache deduplicated data
            cache_key = f"dedup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.data_cache[cache_key] = deduplicated_data

            self._log_pipeline_operation("deduplicate", f"removed {dedup_stats['duplicates_removed']}", True)

            return {
                "action": "data_deduplication",
                "success": True,
                "original_count": dedup_stats["original_count"],
                "final_count": dedup_stats["final_count"],
                "duplicates_removed": dedup_stats["duplicates_removed"],
                "cache_key": cache_key,
                "key_columns": key_columns
            }

        except Exception as e:
            self._log_pipeline_operation("deduplicate", "operation", False, str(e))
            return {
                "action": "data_deduplication",
                "success": False,
                "error": str(e)
            }

    def _general_etl_task(self, task: str) -> Dict[str, Any]:
        """Handle general ETL tasks."""
        return {
            "action": "etl_assistance",
            "success": True,
            "message": "I can help with ETL operations. Try asking me to:",
            "capabilities": [
                "Extract data from files, databases, APIs, and web sources",
                "Transform data with cleaning, validation, and processing",
                "Load data to files, databases, and API endpoints",
                "Create and execute complete ETL pipelines",
                "Perform data quality checks and validation",
                "Remove duplicate records and clean data",
                "Merge and aggregate data from multiple sources",
                "Schedule and monitor batch processing",
                "Handle incremental data loads",
                "Generate data processing reports"
            ],
            "supported_sources": ["CSV", "JSON", "XML", "Database", "API", "Web"],
            "supported_targets": ["CSV", "JSON", "Database", "API"],
            "examples": [
                "Extract data from 'sales.csv'",
                "Transform data by removing duplicates and null values",
                "Load processed data to 'clean_sales.csv'",
                "Create pipeline: extract from API, clean data, load to database",
                "Check data quality of 'customer_data.json'",
                "Merge 'orders.csv' and 'customers.csv' on customer_id"
            ]
        }

    # Helper methods for ETL operations
    def _extract_from_file(self, file_path: str, config: Dict[str, Any]) -> Any:
        """Extract data from file."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        file_ext = Path(file_path).suffix.lower()

        if file_ext == '.csv':
            return pd.read_csv(file_path, **config).to_dict('records')
        elif file_ext == '.json':
            with open(file_path, 'r') as f:
                return json.load(f)
        elif file_ext in ['.xlsx', '.xls']:
            return pd.read_excel(file_path, **config).to_dict('records')
        else:
            with open(file_path, 'r') as f:
                return f.read()

    def _extract_from_database(self, connection_string: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract data from database."""
        query = config.get("query", "SELECT * FROM table")

        # Simple SQLite example
        conn = sqlite3.connect(connection_string)
        df = pd.read_sql_query(query, conn)
        conn.close()

        return df.to_dict('records')

    def _extract_from_api(self, url: str, config: Dict[str, Any]) -> Any:
        """Extract data from API."""
        headers = config.get("headers", {})
        params = config.get("params", {})

        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()

        return response.json()

    def _extract_from_web(self, url: str, config: Dict[str, Any]) -> str:
        """Extract data from web page."""
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        return response.text

    def _apply_transformations(self, data: Any, transformations: List[str]) -> tuple[Any, List[str]]:
        """Apply data transformations."""
        transformed_data = data.copy() if hasattr(data, 'copy') else data
        log = []

        for transformation in transformations:
            if transformation == "clean":
                transformed_data, clean_log = self._clean_data(transformed_data)
                log.extend(clean_log)
            elif transformation == "validate":
                transformed_data, validate_log = self._validate_data(transformed_data)
                log.extend(validate_log)
            elif transformation == "normalize":
                transformed_data, normalize_log = self._normalize_data(transformed_data)
                log.extend(normalize_log)
            elif transformation == "deduplicate":
                transformed_data, dedup_stats = self._deduplicate_data(transformed_data, [])
                log.append(f"Removed {dedup_stats['duplicates_removed']} duplicates")

        return transformed_data, log

    def _clean_data(self, data: Any) -> tuple[Any, List[str]]:
        """Clean data by removing nulls, empty values, etc."""
        log = []

        if isinstance(data, list) and data and isinstance(data[0], dict):
            original_count = len(data)

            # Remove empty records
            cleaned_data = [record for record in data if any(record.values())]
            removed_empty = original_count - len(cleaned_data)

            if removed_empty > 0:
                log.append(f"Removed {removed_empty} empty records")

            # Clean string fields
            for record in cleaned_data:
                for key, value in record.items():
                    if isinstance(value, str):
                        record[key] = value.strip()

            log.append("Trimmed whitespace from string fields")

            return cleaned_data, log

        return data, log

    def _validate_data(self, data: Any) -> tuple[Any, List[str]]:
        """Validate data quality."""
        log = []

        if isinstance(data, list) and data and isinstance(data[0], dict):
            # Check for required fields
            first_record_keys = set(data[0].keys())
            for i, record in enumerate(data[1:], 1):
                if set(record.keys()) != first_record_keys:
                    log.append(f"Inconsistent fields in record {i}")

            log.append("Validated data structure consistency")

        return data, log

    def _normalize_data(self, data: Any) -> tuple[Any, List[str]]:
        """Normalize data formats."""
        log = []

        if isinstance(data, list) and data and isinstance(data[0], dict):
            # Normalize email addresses, phone numbers, etc.
            for record in data:
                for key, value in record.items():
                    if isinstance(value, str):
                        if 'email' in key.lower():
                            record[key] = value.lower().strip()
                        elif 'phone' in key.lower():
                            # Simple phone normalization
                            record[key] = ''.join(filter(str.isdigit, value))

            log.append("Normalized email and phone formats")

        return data, log

    def _deduplicate_data(self, data: Any, key_columns: List[str]) -> tuple[Any, Dict[str, int]]:
        """Remove duplicate records."""
        if not isinstance(data, list) or not data:
            return data, {"original_count": 0, "final_count": 0, "duplicates_removed": 0}

        original_count = len(data)

        if key_columns:
            # Deduplicate based on specific columns
            seen = set()
            deduplicated = []

            for record in data:
                key = tuple(record.get(col) for col in key_columns)
                if key not in seen:
                    seen.add(key)
                    deduplicated.append(record)
        else:
            # Remove exact duplicates
            seen = set()
            deduplicated = []

            for record in data:
                if isinstance(record, dict):
                    key = tuple(sorted(record.items()))
                else:
                    key = record

                if key not in seen:
                    seen.add(key)
                    deduplicated.append(record)

        final_count = len(deduplicated)
        duplicates_removed = original_count - final_count

        return deduplicated, {
            "original_count": original_count,
            "final_count": final_count,
            "duplicates_removed": duplicates_removed
        }

    def _load_to_file(self, data: Any, file_path: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Load data to file."""
        file_ext = Path(file_path).suffix.lower()

        if file_ext == '.csv':
            if isinstance(data, list) and data and isinstance(data[0], dict):
                df = pd.DataFrame(data)
                df.to_csv(file_path, index=False, **config)
                return {"records_loaded": len(data)}
        elif file_ext == '.json':
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            return {"records_loaded": len(data) if isinstance(data, list) else 1}

        return {"records_loaded": 0}

    def _load_to_database(self, data: Any, connection_string: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Load data to database."""
        table_name = config.get("table_name", "imported_data")

        if isinstance(data, list) and data and isinstance(data[0], dict):
            df = pd.DataFrame(data)
            conn = sqlite3.connect(connection_string)
            df.to_sql(table_name, conn, if_exists='append', index=False)
            conn.close()

            return {"records_loaded": len(data)}

        return {"records_loaded": 0}

    def _perform_quality_checks(self, data: Any, checks: List[str]) -> Dict[str, Any]:
        """Perform data quality checks."""
        results = {"checks": {}}

        if isinstance(data, list) and data:
            total_records = len(data)

            if "completeness" in checks:
                # Check for missing values
                if isinstance(data[0], dict):
                    total_fields = len(data[0]) * total_records
                    missing_count = sum(
                        sum(1 for v in record.values() if v is None or v == "")
                        for record in data
                    )
                    completeness_score = 1 - (missing_count / total_fields)
                else:
                    completeness_score = 1.0

                results["checks"]["completeness"] = {
                    "score": completeness_score,
                    "missing_values": missing_count if 'missing_count' in locals() else 0
                }

            if "consistency" in checks:
                # Check field consistency
                consistency_score = 1.0
                if isinstance(data[0], dict):
                    first_keys = set(data[0].keys())
                    inconsistent_records = sum(
                        1 for record in data[1:]
                        if set(record.keys()) != first_keys
                    )
                    consistency_score = 1 - (inconsistent_records / total_records)

                results["checks"]["consistency"] = {
                    "score": consistency_score,
                    "inconsistent_records": inconsistent_records if 'inconsistent_records' in locals() else 0
                }

            if "accuracy" in checks:
                # Basic accuracy checks (could be enhanced with domain-specific rules)
                accuracy_score = 0.95  # Placeholder
                results["checks"]["accuracy"] = {"score": accuracy_score}

        # Calculate overall score
        scores = [check["score"] for check in results["checks"].values()]
        results["overall_score"] = sum(scores) / len(scores) if scores else 0

        return results

    def _get_data_shape(self, data: Any) -> str:
        """Get data shape description."""
        if isinstance(data, list):
            return f"List with {len(data)} items"
        elif isinstance(data, dict):
            return f"Dictionary with {len(data)} keys"
        elif hasattr(data, 'shape'):
            return f"Array shape: {data.shape}"
        else:
            return f"Data type: {type(data).__name__}"

    def _get_data_preview(self, data: Any) -> str:
        """Get data preview."""
        if isinstance(data, list):
            preview_count = min(3, len(data))
            return f"First {preview_count} items: {data[:preview_count]}"
        elif isinstance(data, dict):
            keys = list(data.keys())[:5]
            return f"Keys: {keys}{'...' if len(data) > 5 else ''}"
        else:
            return str(data)[:200] + "..." if len(str(data)) > 200 else str(data)

    def _load_data_for_transformation(self, file_path: str) -> Any:
        """Load data for transformation operations."""
        return self._extract_from_file(file_path, {})

    def _log_pipeline_operation(self, operation: str, details: str, success: bool, error: str = None):
        """Log pipeline operation."""
        self.pipeline_history.append({
            "operation": operation,
            "details": details,
            "success": success,
            "error": error,
            "timestamp": datetime.now().isoformat()
        })

    # Extract info methods
    def _extract_extraction_info(self, task: str) -> Dict[str, Any]:
        """Extract extraction configuration from task."""
        info = {}

        if "file" in task.lower() or any(ext in task.lower() for ext in [".csv", ".json", ".xlsx"]):
            info["source_type"] = "file"
        elif "database" in task.lower() or "sql" in task.lower():
            info["source_type"] = "database"
        elif "api" in task.lower() or "http" in task.lower():
            info["source_type"] = "api"
        elif "web" in task.lower() or "url" in task.lower():
            info["source_type"] = "web"

        # Extract file/URL path
        import re
        path_match = re.search(r'["\']([^"\']+)["\']', task)
        if path_match:
            info["source_path"] = path_match.group(1)

        return info

    def get_capabilities(self) -> List[str]:
        """Get agent capabilities."""
        return self.capabilities

    def get_pipeline_history(self) -> List[Dict[str, Any]]:
        """Get pipeline operation history."""
        return self.pipeline_history

    def get_cached_data_keys(self) -> List[str]:
        """Get available cached data keys."""
        return list(self.data_cache.keys())