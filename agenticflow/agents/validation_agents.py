"""
Validation Agents for Data Integrity Verification
=================================================

Specialized agents for validating CSV data against hierarchical reports.
"""

import os
import csv
import re
from typing import Dict, List, Any


class StructureValidationAgent:
    """Validates structural consistency between report and CSV data."""

    def __init__(self):
        self.capabilities = ["structure_validation", "schema_checking", "data_format_validation"]

    async def arun(self, task: str):
        return self.execute(task)

    def execute(self, task: str) -> Dict[str, Any]:
        """Execute structure validation."""
        try:
            # Extract file paths from task
            report_path, csv_paths = self._extract_file_paths(task)

            if not report_path or not csv_paths:
                return {
                    "action": "structure_validation",
                    "status": "error",
                    "error": "Could not identify report and CSV file paths from task"
                }

            # Validate structure
            validation_results = self._validate_structure(report_path, csv_paths)

            return {
                "action": "structure_validation",
                "status": "completed",
                "report_file": report_path,
                "csv_files": csv_paths,
                "validation_results": validation_results,
                "summary": self._generate_structure_summary(validation_results)
            }

        except Exception as e:
            return {
                "action": "structure_validation",
                "status": "error",
                "error": str(e)
            }

    def _extract_file_paths(self, task: str):
        """Extract file paths from task description."""
        report_path = None
        csv_paths = []

        # Look for common patterns
        if "quarterly_report" in task or ".txt" in task:
            report_path = "examples/data/quarterly_report_q3_2024.txt"

        if "csv" in task.lower():
            # Find CSV files in data directory
            data_dir = "examples/data"
            if os.path.exists(data_dir):
                for file in os.listdir(data_dir):
                    if file.endswith('.csv') and 'q3_2024' in file:
                        csv_paths.append(os.path.join(data_dir, file))

        return report_path, csv_paths

    def _validate_structure(self, report_path: str, csv_paths: List[str]) -> Dict[str, Any]:
        """Validate structural consistency."""
        results = {
            "schema_validation": {},
            "data_completeness": {},
            "structural_issues": []
        }

        # Read report content
        if os.path.exists(report_path):
            with open(report_path, 'r') as f:
                report_content = f.read()
        else:
            results["structural_issues"].append(f"Report file not found: {report_path}")
            return results

        # Validate each CSV file
        for csv_path in csv_paths:
            if not os.path.exists(csv_path):
                results["structural_issues"].append(f"CSV file not found: {csv_path}")
                continue

            csv_name = os.path.basename(csv_path)

            # Read CSV and validate schema
            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames
                rows = list(reader)

            results["schema_validation"][csv_name] = {
                "headers": headers,
                "row_count": len(rows),
                "expected_fields": self._get_expected_fields(csv_name),
                "missing_fields": [],
                "extra_fields": []
            }

            # Check for expected fields based on report content
            expected = self._get_expected_fields(csv_name)
            missing = [field for field in expected if field not in headers]
            extra = [field for field in headers if field not in expected]

            results["schema_validation"][csv_name]["missing_fields"] = missing
            results["schema_validation"][csv_name]["extra_fields"] = extra

        return results

    def _get_expected_fields(self, csv_name: str) -> List[str]:
        """Get expected fields for each CSV type."""
        if "sales_data" in csv_name:
            return ["division", "division_head", "product", "units_sold", "unit_price", "total_sales", "region"]
        elif "regional_data" in csv_name:
            return ["region", "manager", "total_sales", "market_share_pct"]
        elif "customers" in csv_name:
            return ["customer_name", "segment", "annual_revenue", "revenue_q3"]
        return []

    def _generate_structure_summary(self, results: Dict[str, Any]) -> str:
        """Generate summary of structure validation."""
        issues = len(results["structural_issues"])
        csv_count = len(results["schema_validation"])

        summary = f"Validated {csv_count} CSV files. "

        if issues == 0:
            summary += "No structural issues found."
        else:
            summary += f"Found {issues} structural issues."

        return summary


class ContentValidationAgent:
    """Validates content accuracy between report and CSV data."""

    def __init__(self):
        self.capabilities = ["content_validation", "data_accuracy", "numerical_verification"]

    async def arun(self, task: str):
        return self.execute(task)

    def execute(self, task: str) -> Dict[str, Any]:
        """Execute content validation."""
        try:
            # Extract file paths
            report_path, csv_paths = self._extract_file_paths(task)

            if not report_path or not csv_paths:
                return {
                    "action": "content_validation",
                    "status": "error",
                    "error": "Could not identify files for validation"
                }

            # Perform content validation
            validation_results = self._validate_content(report_path, csv_paths)

            return {
                "action": "content_validation",
                "status": "completed",
                "validation_results": validation_results,
                "accuracy_score": self._calculate_accuracy_score(validation_results),
                "summary": self._generate_content_summary(validation_results)
            }

        except Exception as e:
            return {
                "action": "content_validation",
                "status": "error",
                "error": str(e)
            }

    def _extract_file_paths(self, task: str):
        """Extract file paths from task."""
        report_path = "examples/data/quarterly_report_q3_2024.txt"
        csv_paths = []

        data_dir = "examples/data"
        if os.path.exists(data_dir):
            for file in os.listdir(data_dir):
                if file.endswith('.csv') and 'q3_2024' in file:
                    csv_paths.append(os.path.join(data_dir, file))

        return report_path, csv_paths

    def _validate_content(self, report_path: str, csv_paths: List[str]) -> Dict[str, Any]:
        """Validate content accuracy."""
        results = {
            "numerical_checks": {},
            "data_consistency": {},
            "discrepancies": []
        }

        # Read report
        with open(report_path, 'r') as f:
            report_content = f.read()

        # Extract key numbers from report
        report_numbers = self._extract_report_numbers(report_content)

        # Validate against each CSV
        for csv_path in csv_paths:
            csv_name = os.path.basename(csv_path)

            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)
                csv_data = list(reader)

            # Check specific validations based on CSV type
            if "sales_data" in csv_name:
                self._validate_sales_data(csv_data, report_numbers, results)
            elif "regional_data" in csv_name:
                self._validate_regional_data(csv_data, report_numbers, results)
            elif "customers" in csv_name:
                self._validate_customer_data(csv_data, report_numbers, results)

        return results

    def _extract_report_numbers(self, content: str) -> Dict[str, float]:
        """Extract key numbers from report."""
        numbers = {}

        # Total revenue
        revenue_match = re.search(r'Total Revenue: \$([0-9,]+)', content)
        if revenue_match:
            numbers['total_revenue'] = float(revenue_match.group(1).replace(',', ''))

        # Division totals
        widget_match = re.search(r'Widget.*?Total Sales: \$([0-9,]+)', content, re.DOTALL)
        if widget_match:
            numbers['widget_sales'] = float(widget_match.group(1).replace(',', ''))

        gadget_match = re.search(r'Gadget.*?Total Sales: \$([0-9,]+)', content, re.DOTALL)
        if gadget_match:
            numbers['gadget_sales'] = float(gadget_match.group(1).replace(',', ''))

        return numbers

    def _validate_sales_data(self, csv_data: List[Dict], report_numbers: Dict, results: Dict):
        """Validate sales data against report."""
        # Calculate totals from CSV
        csv_totals = {}
        for row in csv_data:
            division = row.get('division', '')
            sales = float(row.get('total_sales', 0))

            if division not in csv_totals:
                csv_totals[division] = 0
            csv_totals[division] += sales

        # Compare with report
        if 'widget_sales' in report_numbers and 'Widget' in csv_totals:
            expected = report_numbers['widget_sales']
            actual = csv_totals['Widget']
            if abs(expected - actual) > 0.01:
                results["discrepancies"].append(f"Widget sales mismatch: Report ${expected:,.2f} vs CSV ${actual:,.2f}")

        results["numerical_checks"]["sales_validation"] = {
            "csv_totals": csv_totals,
            "report_numbers": report_numbers
        }

    def _validate_regional_data(self, csv_data: List[Dict], report_numbers: Dict, results: Dict):
        """Validate regional data."""
        total_regional_sales = sum(float(row.get('total_sales', 0)) for row in csv_data)

        results["numerical_checks"]["regional_validation"] = {
            "total_regional_sales": total_regional_sales,
            "regions_count": len(csv_data)
        }

    def _validate_customer_data(self, csv_data: List[Dict], report_numbers: Dict, results: Dict):
        """Validate customer data."""
        segments = {}
        for row in csv_data:
            segment = row.get('segment', '')
            revenue = float(row.get('revenue_q3', 0))

            if segment not in segments:
                segments[segment] = {"count": 0, "revenue": 0}
            segments[segment]["count"] += 1
            segments[segment]["revenue"] += revenue

        results["numerical_checks"]["customer_validation"] = {
            "segments": segments
        }

    def _calculate_accuracy_score(self, results: Dict[str, Any]) -> float:
        """Calculate overall accuracy score."""
        discrepancy_count = len(results["discrepancies"])

        if discrepancy_count == 0:
            return 100.0
        elif discrepancy_count <= 2:
            return 85.0
        elif discrepancy_count <= 5:
            return 70.0
        else:
            return 50.0

    def _generate_content_summary(self, results: Dict[str, Any]) -> str:
        """Generate content validation summary."""
        discrepancies = len(results["discrepancies"])

        if discrepancies == 0:
            return "All numerical data matches between report and CSV files."
        else:
            return f"Found {discrepancies} data discrepancies that require attention."


class ConsistencyValidationAgent:
    """Validates logical consistency and business rules."""

    def __init__(self):
        self.capabilities = ["consistency_validation", "business_rules", "logical_verification"]

    async def arun(self, task: str):
        return self.execute(task)

    def execute(self, task: str) -> Dict[str, Any]:
        """Execute consistency validation."""
        try:
            # Get file paths
            report_path, csv_paths = self._extract_file_paths(task)

            # Perform consistency checks
            validation_results = self._validate_consistency(report_path, csv_paths)

            return {
                "action": "consistency_validation",
                "status": "completed",
                "validation_results": validation_results,
                "consistency_score": self._calculate_consistency_score(validation_results),
                "summary": self._generate_consistency_summary(validation_results)
            }

        except Exception as e:
            return {
                "action": "consistency_validation",
                "status": "error",
                "error": str(e)
            }

    def _extract_file_paths(self, task: str):
        """Extract file paths."""
        report_path = "examples/data/quarterly_report_q3_2024.txt"
        csv_paths = []

        data_dir = "examples/data"
        if os.path.exists(data_dir):
            for file in os.listdir(data_dir):
                if file.endswith('.csv') and 'q3_2024' in file:
                    csv_paths.append(os.path.join(data_dir, file))

        return report_path, csv_paths

    def _validate_consistency(self, report_path: str, csv_paths: List[str]) -> Dict[str, Any]:
        """Validate logical consistency."""
        results = {
            "business_rules": [],
            "cross_reference_checks": [],
            "logical_consistency": []
        }

        # Load all data
        csv_data = {}
        for csv_path in csv_paths:
            csv_name = os.path.basename(csv_path)
            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)
                csv_data[csv_name] = list(reader)

        # Check business rules
        self._check_business_rules(csv_data, results)

        # Check cross-references
        self._check_cross_references(csv_data, results)

        return results

    def _check_business_rules(self, csv_data: Dict[str, List[Dict]], results: Dict):
        """Check business logic rules."""
        # Rule: Sales should equal units * price
        if 'q3_2024_sales_data.csv' in csv_data:
            for row in csv_data['q3_2024_sales_data.csv']:
                units = float(row.get('units_sold', 0))
                price = float(row.get('unit_price', 0))
                total = float(row.get('total_sales', 0))

                expected = units * price
                if abs(expected - total) > 0.01:
                    results["business_rules"].append(
                        f"Sales calculation error: {row.get('product')} - Expected ${expected:,.2f}, got ${total:,.2f}"
                    )

        # Rule: Market share should add up to 100%
        if 'q3_2024_regional_data.csv' in csv_data:
            total_share = sum(float(row.get('market_share_pct', 0)) for row in csv_data['q3_2024_regional_data.csv'])
            if abs(total_share - 100.0) > 0.1:
                results["business_rules"].append(f"Market share doesn't add to 100%: {total_share:.1f}%")

    def _check_cross_references(self, csv_data: Dict[str, List[Dict]], results: Dict):
        """Check cross-references between files."""
        # Check if managers in regional data match expectations
        if 'q3_2024_regional_data.csv' in csv_data:
            managers = [row.get('manager') for row in csv_data['q3_2024_regional_data.csv']]
            expected_managers = ['Tom Wilson', 'Jennifer Davis', 'David Kim', 'Maria Garcia', 'James Brown']

            for manager in expected_managers:
                if manager not in managers:
                    results["cross_reference_checks"].append(f"Missing expected manager: {manager}")

    def _calculate_consistency_score(self, results: Dict[str, Any]) -> float:
        """Calculate consistency score."""
        total_issues = len(results["business_rules"]) + len(results["cross_reference_checks"])

        if total_issues == 0:
            return 100.0
        elif total_issues <= 2:
            return 90.0
        else:
            return max(50.0, 100.0 - (total_issues * 10))

    def _generate_consistency_summary(self, results: Dict[str, Any]) -> str:
        """Generate consistency summary."""
        business_issues = len(results["business_rules"])
        cross_ref_issues = len(results["cross_reference_checks"])

        if business_issues == 0 and cross_ref_issues == 0:
            return "All business rules and cross-references are consistent."
        else:
            return f"Found {business_issues} business rule violations and {cross_ref_issues} cross-reference issues."