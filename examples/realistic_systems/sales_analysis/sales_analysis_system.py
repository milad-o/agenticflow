#!/usr/bin/env python3
"""
Sales Data Analysis System - AgenticFlow Realistic Example
==========================================================

This example demonstrates a complete end-to-end sales analysis system using AgenticFlow.
The system:
1. Reads sales data from text files
2. Converts text data to structured CSV format
3. Performs comprehensive data analysis using pandas
4. Generates insights and reports

This showcases AgenticFlow's ability to handle realistic business workflows
with multiple specialized agents working together.
"""

import asyncio
import csv
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

import pandas as pd

from agenticflow import Agent
from agenticflow.config.settings import AgentConfig, LLMProviderConfig, LLMProvider, MemoryConfig
from agenticflow.tools.registry import tool


# ================================================================
# CUSTOM TOOLS FOR SALES DATA PROCESSING
# ================================================================

@tool("read_text_file", "Reads content from a text file")
def read_text_file(file_path: str) -> str:
    """Read the contents of a text file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        return f"Successfully read {len(content)} characters from {file_path}"
    except Exception as e:
        return f"Error reading file {file_path}: {str(e)}"


@tool("parse_sales_data", "Parses sales transaction data from text format")
def parse_sales_data(file_path: str) -> str:
    """Parse sales transactions from text file and return structured data."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        transactions = []
        current_transaction = {}
        
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('Transaction ID:'):
                if current_transaction:
                    transactions.append(current_transaction)
                current_transaction = {'transaction_id': line.split(':', 1)[1].strip()}
            elif line.startswith('Date:'):
                current_transaction['date'] = line.split(':', 1)[1].strip()
            elif line.startswith('Product:'):
                current_transaction['product'] = line.split(':', 1)[1].strip()
            elif line.startswith('Category:'):
                current_transaction['category'] = line.split(':', 1)[1].strip()
            elif line.startswith('Quantity:'):
                current_transaction['quantity'] = int(line.split(':', 1)[1].strip())
            elif line.startswith('Unit Price:'):
                price_str = line.split(':', 1)[1].strip().replace('$', '').replace(',', '')
                current_transaction['unit_price'] = float(price_str)
            elif line.startswith('Customer:'):
                current_transaction['customer'] = line.split(':', 1)[1].strip()
            elif line.startswith('Sales Rep:'):
                current_transaction['sales_rep'] = line.split(':', 1)[1].strip()
            elif line.startswith('Total:'):
                total_str = line.split(':', 1)[1].strip().replace('$', '').replace(',', '')
                current_transaction['total'] = float(total_str)
        
        # Add the last transaction
        if current_transaction:
            transactions.append(current_transaction)
        
        return json.dumps(transactions, indent=2)
    
    except Exception as e:
        return f"Error parsing sales data from {file_path}: {str(e)}"


@tool("save_to_csv", "Saves structured data to CSV format")
def save_to_csv(data_json: str, output_file: str) -> str:
    """Convert JSON data to CSV format and save to file."""
    try:
        data = json.loads(data_json)
        
        if not data:
            return "No data to save"
        
        # Write to CSV
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = data[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        
        return f"Successfully saved {len(data)} records to {output_file}"
    
    except Exception as e:
        return f"Error saving to CSV {output_file}: {str(e)}"


@tool("analyze_sales_data", "Performs comprehensive sales data analysis using pandas")
def analyze_sales_data(csv_file: str) -> str:
    """Analyze sales data from CSV file using pandas."""
    try:
        df = pd.read_csv(csv_file)
        
        # Basic statistics
        total_records = len(df)
        total_revenue = df['total'].sum()
        avg_transaction = df['total'].mean()
        
        # Category analysis
        category_sales = df.groupby('category').agg({
            'total': ['sum', 'count'],
            'quantity': 'sum'
        }).round(2)
        
        # Sales rep performance
        rep_performance = df.groupby('sales_rep').agg({
            'total': ['sum', 'count'],
            'quantity': 'sum'
        }).round(2)
        
        # Monthly trends (assuming date format YYYY-MM-DD)
        df['date'] = pd.to_datetime(df['date'])
        df['month'] = df['date'].dt.to_period('M')
        monthly_sales = df.groupby('month').agg({
            'total': 'sum',
            'quantity': 'sum'
        }).round(2)
        
        # Top products
        product_sales = df.groupby('product').agg({
            'total': 'sum',
            'quantity': 'sum'
        }).sort_values('total', ascending=False).head(10).round(2)
        
        # Customer analysis
        customer_sales = df.groupby('customer').agg({
            'total': 'sum',
            'quantity': 'sum'
        }).sort_values('total', ascending=False).head(10).round(2)
        
        analysis = {
            "summary": {
                "total_records": int(total_records),
                "total_revenue": float(total_revenue),
                "average_transaction": float(avg_transaction)
            },
            "category_analysis": category_sales.to_dict(),
            "sales_rep_performance": rep_performance.to_dict(),
            "monthly_trends": monthly_sales.to_dict(),
            "top_products": product_sales.to_dict(),
            "top_customers": customer_sales.to_dict()
        }
        
        return json.dumps(analysis, indent=2, default=str)
    
    except Exception as e:
        return f"Error analyzing sales data from {csv_file}: {str(e)}"


@tool("generate_sales_report", "Generates a comprehensive sales report")
def generate_sales_report(analysis_json: str, output_file: str) -> str:
    """Generate a formatted sales report from analysis data."""
    try:
        analysis = json.loads(analysis_json)
        
        report_lines = [
            "=" * 60,
            "COMPREHENSIVE SALES ANALYSIS REPORT",
            "=" * 60,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "EXECUTIVE SUMMARY",
            "-" * 20,
            f"Total Transactions: {analysis['summary']['total_records']:,}",
            f"Total Revenue: ${analysis['summary']['total_revenue']:,.2f}",
            f"Average Transaction Value: ${analysis['summary']['average_transaction']:,.2f}",
            "",
            "CATEGORY PERFORMANCE",
            "-" * 20
        ]
        
        # Add category analysis
        if 'category_analysis' in analysis:
            for category, data in analysis['category_analysis'].items():
                if isinstance(data, dict) and 'sum' in data:
                    revenue = data['sum']
                    count = data.get('count', 'N/A')
                    report_lines.append(f"{category}: ${revenue:,.2f} ({count} transactions)")
        
        report_lines.extend([
            "",
            "SALES REPRESENTATIVE PERFORMANCE",
            "-" * 35
        ])
        
        # Add sales rep performance
        if 'sales_rep_performance' in analysis:
            for rep, data in analysis['sales_rep_performance'].items():
                if isinstance(data, dict) and 'sum' in data:
                    revenue = data['sum']
                    count = data.get('count', 'N/A')
                    report_lines.append(f"{rep}: ${revenue:,.2f} ({count} transactions)")
        
        report_lines.extend([
            "",
            "TOP PERFORMING PRODUCTS",
            "-" * 25
        ])
        
        # Add top products
        if 'top_products' in analysis:
            for product, data in analysis['top_products'].items():
                if isinstance(data, dict):
                    revenue = data.get('total', 0)
                    quantity = data.get('quantity', 0)
                    report_lines.append(f"{product}: ${revenue:,.2f} ({quantity} units)")
        
        report_lines.extend([
            "",
            "=" * 60,
            "End of Report"
        ])
        
        # Write report to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))
        
        return f"Sales report generated successfully: {output_file}"
    
    except Exception as e:
        return f"Error generating report {output_file}: {str(e)}"


@tool("list_files", "Lists files in a directory")
def list_files(directory: str, pattern: str = "*.txt") -> str:
    """List files in a directory matching a pattern."""
    try:
        from pathlib import Path
        import fnmatch
        
        dir_path = Path(directory)
        if not dir_path.exists():
            return f"Directory {directory} does not exist"
        
        files = []
        for file_path in dir_path.iterdir():
            if file_path.is_file() and fnmatch.fnmatch(file_path.name, pattern):
                files.append(str(file_path))
        
        return f"Found {len(files)} files: {', '.join([Path(f).name for f in files])}"
    
    except Exception as e:
        return f"Error listing files: {str(e)}"


# ================================================================
# SPECIALIZED AGENTS
# ================================================================

class SalesAnalysisSystem:
    """Complete sales analysis system using multiple AgenticFlow agents."""
    
    def __init__(self):
        self.data_dir = Path(__file__).parent
        self.agents = {}
        
    async def initialize_agents(self):
        """Initialize specialized agents for different tasks."""
        
        # Data Processing Agent
        self.agents['data_processor'] = Agent(AgentConfig(
            name="data_processor",
            instructions="""You are a data processing specialist. Your role is to:
1. Read and parse text files containing sales data
2. Convert unstructured text data to structured CSV format
3. Handle data validation and cleaning
4. Work with file operations efficiently

Always be thorough in data parsing and ensure data integrity.""",
            llm=LLMProviderConfig(
                provider=LLMProvider.GROQ,
                model="llama-3.1-8b-instant"
            ),
            tools=[
                "read_text_file", 
                "parse_sales_data", 
                "save_to_csv", 
                "list_files"
            ],
            memory=MemoryConfig(type="buffer", max_messages=50)
        ))
        
        # Data Analysis Agent
        self.agents['data_analyst'] = Agent(AgentConfig(
            name="data_analyst",
            instructions="""You are a sales data analyst expert. Your role is to:
1. Perform comprehensive statistical analysis on sales data
2. Identify trends, patterns, and insights
3. Generate actionable business intelligence
4. Create detailed analysis reports

Focus on providing valuable business insights and recommendations.""",
            llm=LLMProviderConfig(
                provider=LLMProvider.GROQ,
                model="llama-3.1-8b-instant"
            ),
            tools=[
                "analyze_sales_data", 
                "generate_sales_report"
            ],
            memory=MemoryConfig(type="buffer", max_messages=30)
        ))
        
        # Coordinator Agent
        self.agents['coordinator'] = Agent(AgentConfig(
            name="coordinator",
            instructions="""You are a project coordinator managing a sales analysis workflow. Your role is to:
1. Orchestrate the entire data processing and analysis pipeline
2. Coordinate between data processing and analysis teams
3. Ensure quality and completeness of the workflow
4. Provide executive summaries and final insights

Maintain high standards and ensure all steps are completed successfully.""",
            llm=LLMProviderConfig(
                provider=LLMProvider.GROQ,
                model="llama-3.1-8b-instant"
            ),
            tools=["list_files"],
            memory=MemoryConfig(type="buffer", max_messages=100)
        ))
        
        # Start all agents
        for agent in self.agents.values():
            await agent.start()
    
    async def run_analysis_workflow(self) -> Dict[str, Any]:
        """Run the complete sales analysis workflow."""
        results = {}
        
        print("🚀 Starting Sales Analysis System...")
        print("=" * 60)
        
        # Step 1: Coordinator identifies available data files
        print("\n📋 Step 1: Identifying Data Sources")
        print("-" * 40)
        
        file_list_result = await self.agents['coordinator'].execute_task(
            f"List all .txt files in the directory {self.data_dir} to identify sales data files"
        )
        print(f"Coordinator: {file_list_result.get('response', 'No response')}")
        results['file_discovery'] = file_list_result
        
        # Step 2: Data processing for each file
        print("\n🔄 Step 2: Processing Sales Data Files")
        print("-" * 40)
        
        data_files = [
            self.data_dir / "q1_2024_sales.txt",
            self.data_dir / "q2_2024_sales.txt"
        ]
        
        all_csv_files = []
        for data_file in data_files:
            if data_file.exists():
                print(f"\n📊 Processing: {data_file.name}")
                
                # Parse sales data
                parse_result = await self.agents['data_processor'].execute_task(
                    f"Parse the sales transaction data from {data_file} and extract all transaction details"
                )
                print(f"Data Processor: Parsing completed")
                
                # Convert to CSV
                csv_file = data_file.with_suffix('.csv')
                csv_result = await self.agents['data_processor'].execute_task(
                    f"Convert the parsed sales data to CSV format and save it as {csv_file}"
                )
                print(f"Data Processor: {csv_result.get('response', 'CSV conversion completed')}")
                all_csv_files.append(str(csv_file))
                
                results[f'processing_{data_file.stem}'] = {
                    'parse': parse_result,
                    'csv': csv_result
                }
        
        # Step 3: Comprehensive analysis
        print("\n📈 Step 3: Performing Sales Analysis")
        print("-" * 40)
        
        analysis_results = []
        for csv_file in all_csv_files:
            if Path(csv_file).exists():
                print(f"\n🔍 Analyzing: {Path(csv_file).name}")
                
                analysis_result = await self.agents['data_analyst'].execute_task(
                    f"Perform comprehensive sales data analysis on {csv_file} including trends, performance metrics, and insights"
                )
                print(f"Data Analyst: Analysis completed for {Path(csv_file).name}")
                analysis_results.append(analysis_result)
                
                # Generate individual report
                report_file = Path(csv_file).with_suffix('.report.txt')
                report_result = await self.agents['data_analyst'].execute_task(
                    f"Generate a detailed sales report based on the analysis and save it as {report_file}"
                )
                print(f"Data Analyst: Report generated - {report_file.name}")
                
                results[f'analysis_{Path(csv_file).stem}'] = {
                    'analysis': analysis_result,
                    'report': report_result
                }
        
        # Step 4: Executive summary and insights
        print("\n📋 Step 4: Generating Executive Summary")
        print("-" * 40)
        
        summary_result = await self.agents['coordinator'].execute_task(
            f"""Based on the completed analysis of sales data files, provide an executive summary including:
1. Overall business performance insights
2. Key trends and patterns identified
3. Recommendations for business strategy
4. Summary of the analysis workflow completion
            
The analysis has been completed for files: {', '.join([Path(f).name for f in all_csv_files])}"""
        )
        print(f"Coordinator: {summary_result.get('response', 'Executive summary completed')}")
        results['executive_summary'] = summary_result
        
        print("\n✅ Sales Analysis System Complete!")
        print("=" * 60)
        
        return results
    
    async def cleanup(self):
        """Clean up agents and resources."""
        for agent in self.agents.values():
            await agent.stop()
        print("🛑 All agents stopped")


# ================================================================
# MAIN EXECUTION
# ================================================================

async def main():
    """Main execution function."""
    print("🏪 AgenticFlow Realistic Sales Analysis System")
    print("=" * 60)
    print("This system demonstrates a complete business workflow:")
    print("1. Reading unstructured sales data from text files")
    print("2. Converting to structured CSV format")
    print("3. Performing comprehensive pandas-based analysis")
    print("4. Generating business insights and reports")
    print()
    
    # Initialize the system
    system = SalesAnalysisSystem()
    
    try:
        # Initialize agents
        await system.initialize_agents()
        
        # Run the complete workflow
        results = await system.run_analysis_workflow()
        
        # Display final results summary
        print("\n📊 FINAL RESULTS SUMMARY")
        print("=" * 40)
        print(f"✅ Workflow completed with {len(results)} major steps")
        print(f"✅ Data files processed successfully")
        print(f"✅ CSV files generated and analyzed")
        print(f"✅ Business reports created")
        print(f"✅ Executive insights provided")
        
        # Show generated files
        data_dir = Path(__file__).parent
        csv_files = list(data_dir.glob("*.csv"))
        report_files = list(data_dir.glob("*.report.txt"))
        
        print(f"\n📁 Generated Files:")
        print(f"   CSV files: {len(csv_files)} files")
        for csv_file in csv_files:
            print(f"     - {csv_file.name}")
        print(f"   Reports: {len(report_files)} files")
        for report_file in report_files:
            print(f"     - {report_file.name}")
            
    except Exception as e:
        print(f"❌ Error in sales analysis system: {e}")
        
    finally:
        # Cleanup
        await system.cleanup()


if __name__ == "__main__":
    asyncio.run(main())