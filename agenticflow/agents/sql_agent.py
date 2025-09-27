"""
SQL Agent - Database Operations and Query Management
===================================================

Comprehensive SQL operations, query generation, and database management.
"""

import sqlite3
import tempfile
import os
import json
import re
from typing import Dict, List, Any, Optional, Union
import pandas as pd
from datetime import datetime


class SQLAgent:
    """Agent for SQL operations and database management."""

    def __init__(self, default_db_path: str = None):
        self.capabilities = [
            "sql_query_execution",
            "database_creation",
            "table_management",
            "data_insertion",
            "query_optimization",
            "schema_analysis",
            "data_export",
            "csv_to_sql_import"
        ]
        self.default_db_path = default_db_path or self._create_temp_db()
        self.connection = None
        self.query_history = []

    async def arun(self, task: str) -> Dict[str, Any]:
        """Async execution wrapper."""
        return self.execute(task)

    def execute(self, task: str) -> Dict[str, Any]:
        """Execute SQL-related tasks."""
        task_lower = task.lower()

        if any(keyword in task_lower for keyword in ["create database", "create db", "new database"]):
            return self._create_database_task(task)
        elif any(keyword in task_lower for keyword in ["create table", "create schema"]):
            return self._create_table_task(task)
        elif any(keyword in task_lower for keyword in ["insert", "add data", "populate"]):
            return self._insert_data_task(task)
        elif any(keyword in task_lower for keyword in ["select", "query", "find", "search"]):
            return self._query_data_task(task)
        elif any(keyword in task_lower for keyword in ["import csv", "csv to sql", "load csv"]):
            return self._import_csv_task(task)
        elif any(keyword in task_lower for keyword in ["export", "dump", "backup"]):
            return self._export_data_task(task)
        elif any(keyword in task_lower for keyword in ["analyze", "schema", "structure"]):
            return self._analyze_database_task(task)
        elif any(keyword in task_lower for keyword in ["optimize", "index", "performance"]):
            return self._optimize_query_task(task)
        else:
            return self._general_sql_task(task)

    def _create_database_task(self, task: str) -> Dict[str, Any]:
        """Create a new database."""
        db_name = self._extract_database_name(task)
        if not db_name:
            db_name = f"database_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"

        db_path = os.path.join(tempfile.gettempdir(), db_name)

        try:
            conn = sqlite3.connect(db_path)
            conn.close()

            return {
                "action": "database_creation",
                "success": True,
                "database_path": db_path,
                "database_name": db_name,
                "message": f"Database '{db_name}' created successfully"
            }
        except Exception as e:
            return {
                "action": "database_creation",
                "success": False,
                "error": str(e)
            }

    def _create_table_task(self, task: str) -> Dict[str, Any]:
        """Create tables based on task description."""
        table_info = self._extract_table_info(task)

        if not table_info:
            # Generate a sample table based on common patterns
            table_info = self._generate_sample_table_info(task)

        sql_query = self._generate_create_table_sql(table_info)
        result = self._execute_sql(sql_query)

        return {
            "action": "table_creation",
            "table_info": table_info,
            "sql_query": sql_query,
            **result
        }

    def _insert_data_task(self, task: str) -> Dict[str, Any]:
        """Insert data into tables."""
        # Extract data and table information
        insert_info = self._extract_insert_info(task)

        if not insert_info:
            return {
                "action": "data_insertion",
                "success": False,
                "error": "Could not extract data insertion information"
            }

        sql_query = self._generate_insert_sql(insert_info)
        result = self._execute_sql(sql_query)

        return {
            "action": "data_insertion",
            "insert_info": insert_info,
            "sql_query": sql_query,
            **result
        }

    def _query_data_task(self, task: str) -> Dict[str, Any]:
        """Execute SQL queries."""
        sql_query = self._extract_or_generate_query(task)
        result = self._execute_sql(sql_query)

        # Format results for better readability
        if result.get("success") and result.get("data"):
            formatted_data = self._format_query_results(result["data"])
            result["formatted_results"] = formatted_data

        return {
            "action": "data_query",
            "sql_query": sql_query,
            **result
        }

    def _import_csv_task(self, task: str) -> Dict[str, Any]:
        """Import CSV data into SQL database."""
        csv_path = self._extract_file_path(task)
        table_name = self._extract_table_name(task) or "imported_data"

        if not csv_path or not os.path.exists(csv_path):
            return {
                "action": "csv_import",
                "success": False,
                "error": f"CSV file not found: {csv_path}"
            }

        try:
            # Read CSV and infer schema
            df = pd.read_csv(csv_path)
            schema = self._infer_schema_from_dataframe(df, table_name)

            # Create table
            create_sql = self._generate_create_table_sql(schema)
            create_result = self._execute_sql(create_sql)

            if not create_result.get("success"):
                return {
                    "action": "csv_import",
                    "success": False,
                    "error": f"Failed to create table: {create_result.get('error')}"
                }

            # Insert data
            with self._get_connection() as conn:
                df.to_sql(table_name, conn, if_exists='append', index=False)

            return {
                "action": "csv_import",
                "success": True,
                "csv_path": csv_path,
                "table_name": table_name,
                "rows_imported": len(df),
                "columns": list(df.columns),
                "schema": schema
            }

        except Exception as e:
            return {
                "action": "csv_import",
                "success": False,
                "error": str(e)
            }

    def _export_data_task(self, task: str) -> Dict[str, Any]:
        """Export data from database."""
        table_name = self._extract_table_name(task)
        export_format = self._extract_export_format(task)

        if not table_name:
            # List all tables
            return self._list_tables()

        try:
            query = f"SELECT * FROM {table_name}"
            result = self._execute_sql(query)

            if not result.get("success"):
                return result

            data = result["data"]

            if export_format.lower() == "csv":
                csv_path = self._export_to_csv(data, table_name)
                return {
                    "action": "data_export",
                    "success": True,
                    "table_name": table_name,
                    "export_format": "CSV",
                    "export_path": csv_path,
                    "rows_exported": len(data)
                }
            else:
                return {
                    "action": "data_export",
                    "success": True,
                    "table_name": table_name,
                    "data": data,
                    "rows_exported": len(data)
                }

        except Exception as e:
            return {
                "action": "data_export",
                "success": False,
                "error": str(e)
            }

    def _analyze_database_task(self, task: str) -> Dict[str, Any]:
        """Analyze database schema and structure."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Get all tables
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]

                schema_info = {}
                for table in tables:
                    # Get table info
                    cursor.execute(f"PRAGMA table_info({table})")
                    columns = cursor.fetchall()

                    # Get row count
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    row_count = cursor.fetchone()[0]

                    schema_info[table] = {
                        "columns": [
                            {
                                "name": col[1],
                                "type": col[2],
                                "nullable": not col[3],
                                "primary_key": bool(col[5])
                            }
                            for col in columns
                        ],
                        "row_count": row_count
                    }

                return {
                    "action": "database_analysis",
                    "success": True,
                    "database_path": self.default_db_path,
                    "tables": tables,
                    "schema_info": schema_info,
                    "total_tables": len(tables)
                }

        except Exception as e:
            return {
                "action": "database_analysis",
                "success": False,
                "error": str(e)
            }

    def _optimize_query_task(self, task: str) -> Dict[str, Any]:
        """Optimize SQL queries and suggest improvements."""
        query = self._extract_or_generate_query(task)

        optimization_suggestions = []

        # Basic optimization checks
        if "SELECT *" in query.upper():
            optimization_suggestions.append("Consider selecting specific columns instead of SELECT *")

        if "WHERE" not in query.upper() and "SELECT" in query.upper():
            optimization_suggestions.append("Consider adding WHERE clause to filter data")

        if query.upper().count("JOIN") > 2:
            optimization_suggestions.append("Multiple JOINs detected - consider query restructuring")

        # Execute query and measure performance
        import time
        start_time = time.time()
        result = self._execute_sql(query)
        execution_time = time.time() - start_time

        return {
            "action": "query_optimization",
            "original_query": query,
            "execution_time": execution_time,
            "optimization_suggestions": optimization_suggestions,
            "query_result": result
        }

    def _general_sql_task(self, task: str) -> Dict[str, Any]:
        """Handle general SQL tasks."""
        # Try to extract SQL from the task
        sql_query = self._extract_sql_from_task(task)

        if sql_query:
            result = self._execute_sql(sql_query)
            return {
                "action": "sql_execution",
                "sql_query": sql_query,
                **result
            }
        else:
            # Generate helpful response
            return {
                "action": "sql_assistance",
                "success": True,
                "message": "I can help with SQL operations. Try asking me to:",
                "suggestions": [
                    "Create a database or table",
                    "Insert data into a table",
                    "Query data with SELECT statements",
                    "Import CSV files to SQL",
                    "Export data to CSV",
                    "Analyze database schema",
                    "Optimize SQL queries"
                ]
            }

    def _execute_sql(self, sql_query: str) -> Dict[str, Any]:
        """Execute SQL query safely."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql_query)

                # Check if it's a SELECT query
                if sql_query.strip().upper().startswith('SELECT'):
                    data = cursor.fetchall()
                    column_names = [description[0] for description in cursor.description]
                    return {
                        "success": True,
                        "data": data,
                        "columns": column_names,
                        "row_count": len(data)
                    }
                else:
                    conn.commit()
                    return {
                        "success": True,
                        "message": "Query executed successfully",
                        "rows_affected": cursor.rowcount
                    }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "query": sql_query
            }
        finally:
            # Add to history
            self.query_history.append({
                "query": sql_query,
                "timestamp": datetime.now().isoformat(),
                "success": "success" in locals()
            })

    def _get_connection(self):
        """Get database connection."""
        return sqlite3.connect(self.default_db_path)

    def _create_temp_db(self) -> str:
        """Create temporary database."""
        temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        temp_db.close()
        return temp_db.name

    def _extract_database_name(self, task: str) -> str:
        """Extract database name from task."""
        # Look for patterns like "create database named X" or "database X"
        patterns = [
            r"database\s+named\s+(\w+)",
            r"database\s+(\w+)",
            r"db\s+(\w+)",
            r"call\s+it\s+(\w+)"
        ]

        for pattern in patterns:
            match = re.search(pattern, task, re.IGNORECASE)
            if match:
                return match.group(1)

        return None

    def _extract_table_info(self, task: str) -> Dict[str, Any]:
        """Extract table information from task."""
        # Simple extraction - in practice, you'd use more sophisticated NLP
        table_name = self._extract_table_name(task)

        if not table_name:
            return None

        # Look for column definitions
        columns = []

        # Common patterns for column definitions
        if "columns" in task.lower():
            # Extract columns from description
            words = task.split()
            in_columns = False
            for word in words:
                if word.lower() == "columns":
                    in_columns = True
                elif in_columns and word.isalnum():
                    columns.append({"name": word, "type": "TEXT"})

        if not columns:
            # Generate default columns based on context
            if "user" in task.lower():
                columns = [
                    {"name": "id", "type": "INTEGER PRIMARY KEY"},
                    {"name": "username", "type": "TEXT"},
                    {"name": "email", "type": "TEXT"},
                    {"name": "created_at", "type": "TIMESTAMP"}
                ]
            elif "product" in task.lower():
                columns = [
                    {"name": "id", "type": "INTEGER PRIMARY KEY"},
                    {"name": "name", "type": "TEXT"},
                    {"name": "price", "type": "REAL"},
                    {"name": "category", "type": "TEXT"}
                ]
            else:
                columns = [
                    {"name": "id", "type": "INTEGER PRIMARY KEY"},
                    {"name": "name", "type": "TEXT"},
                    {"name": "value", "type": "TEXT"}
                ]

        return {
            "table_name": table_name,
            "columns": columns
        }

    def _extract_table_name(self, task: str) -> str:
        """Extract table name from task."""
        patterns = [
            r"table\s+(\w+)",
            r"into\s+(\w+)",
            r"from\s+(\w+)",
            r"table\s+named\s+(\w+)"
        ]

        for pattern in patterns:
            match = re.search(pattern, task, re.IGNORECASE)
            if match:
                return match.group(1)

        return None

    def _generate_create_table_sql(self, table_info: Dict[str, Any]) -> str:
        """Generate CREATE TABLE SQL."""
        table_name = table_info["table_name"]
        columns = table_info["columns"]

        column_defs = []
        for col in columns:
            col_def = f"{col['name']} {col['type']}"
            if col.get("primary_key"):
                col_def += " PRIMARY KEY"
            if not col.get("nullable", True):
                col_def += " NOT NULL"
            column_defs.append(col_def)

        return f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(column_defs)})"

    def _extract_or_generate_query(self, task: str) -> str:
        """Extract SQL query from task or generate one."""
        # First try to extract existing SQL
        sql = self._extract_sql_from_task(task)
        if sql:
            return sql

        # Generate query based on task description
        task_lower = task.lower()

        if "all" in task_lower and "from" in task_lower:
            table_name = self._extract_table_name(task)
            if table_name:
                return f"SELECT * FROM {table_name}"

        if "count" in task_lower:
            table_name = self._extract_table_name(task)
            if table_name:
                return f"SELECT COUNT(*) FROM {table_name}"

        # Default query
        return "SELECT name FROM sqlite_master WHERE type='table'"

    def _extract_sql_from_task(self, task: str) -> str:
        """Extract SQL query from task text."""
        # Look for SQL keywords
        sql_patterns = [
            r"(SELECT.*?(?:;|$))",
            r"(INSERT.*?(?:;|$))",
            r"(UPDATE.*?(?:;|$))",
            r"(DELETE.*?(?:;|$))",
            r"(CREATE.*?(?:;|$))"
        ]

        for pattern in sql_patterns:
            match = re.search(pattern, task, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip().rstrip(';')

        return None

    def _format_query_results(self, data: List[tuple]) -> str:
        """Format query results for display."""
        if not data:
            return "No results found"

        # Simple tabular format
        formatted = []
        for row in data[:10]:  # Limit to first 10 rows
            formatted.append(" | ".join(str(cell) for cell in row))

        if len(data) > 10:
            formatted.append(f"... and {len(data) - 10} more rows")

        return "\n".join(formatted)

    def _infer_schema_from_dataframe(self, df: pd.DataFrame, table_name: str) -> Dict[str, Any]:
        """Infer SQL schema from pandas DataFrame."""
        columns = []

        for col_name, dtype in df.dtypes.items():
            if dtype == 'object':
                sql_type = 'TEXT'
            elif dtype == 'int64':
                sql_type = 'INTEGER'
            elif dtype == 'float64':
                sql_type = 'REAL'
            else:
                sql_type = 'TEXT'

            columns.append({
                "name": col_name,
                "type": sql_type,
                "nullable": True
            })

        return {
            "table_name": table_name,
            "columns": columns
        }

    def _export_to_csv(self, data: List[tuple], table_name: str) -> str:
        """Export data to CSV file."""
        csv_path = os.path.join(tempfile.gettempdir(), f"{table_name}_export.csv")

        df = pd.DataFrame(data)
        df.to_csv(csv_path, index=False)

        return csv_path

    def _list_tables(self) -> Dict[str, Any]:
        """List all tables in database."""
        query = "SELECT name FROM sqlite_master WHERE type='table'"
        result = self._execute_sql(query)

        if result.get("success"):
            tables = [row[0] for row in result["data"]]
            return {
                "action": "list_tables",
                "success": True,
                "tables": tables,
                "table_count": len(tables)
            }
        else:
            return result

    def get_capabilities(self) -> List[str]:
        """Get agent capabilities."""
        return self.capabilities

    def get_query_history(self) -> List[Dict[str, Any]]:
        """Get SQL query history."""
        return self.query_history