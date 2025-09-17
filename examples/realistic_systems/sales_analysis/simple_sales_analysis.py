#!/usr/bin/env python3
"""
Simplified Sales Analysis System - AgenticFlow Example
======================================================

This is a streamlined version of the sales analysis system that reduces
LLM API calls to avoid rate limits while still demonstrating core
AgenticFlow capabilities.
"""

import asyncio
import json
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd

from agenticflow import Agent
from agenticflow.config.settings import AgentConfig, LLMProvider, LLMProviderConfig, MemoryConfig
from agenticflow.tools import tool


# ================================================================
# CUSTOM TOOLS FOR SALES ANALYSIS
# ================================================================

@tool("process_sales_file", "Processes a sales text file and converts to CSV")
def process_sales_file(file_path: str) -> str:
    """Process a sales text file and convert it directly to CSV."""
    try:
        file_path = Path(file_path)
        if not file_path.exists():
            return f"Error: File {file_path} does not exist"
        
        # Read the text file
        content = file_path.read_text(encoding='utf-8')
        
        # Parse sales transactions
        transactions = []
        current_transaction = {}
        
        for line in content.split('\n'):
            line = line.strip()
            if not line:
                if current_transaction:
                    transactions.append(current_transaction)
                    current_transaction = {}
                continue
            
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower().replace(' ', '_')
                value = value.strip()
                
                # Parse specific fields
                if key == 'date':
                    current_transaction['date'] = value
                elif key == 'transaction_id':
                    current_transaction['transaction_id'] = value
                elif key == 'customer':
                    current_transaction['customer'] = value
                elif key == 'product':
                    current_transaction['product'] = value
                elif key == 'category':
                    current_transaction['category'] = value
                elif key == 'quantity':
                    current_transaction['quantity'] = int(value.split()[0])
                elif key == 'unit_price':
                    # Extract numeric value from currency string
                    price_str = value.replace('$', '').replace(',', '')
                    current_transaction['unit_price'] = float(price_str)
                elif key == 'total_amount':
                    # Extract numeric value from currency string
                    amount_str = value.replace('$', '').replace(',', '')
                    current_transaction['total_amount'] = float(amount_str)
                elif key == 'sales_rep':
                    current_transaction['sales_rep'] = value
        
        # Add the last transaction if exists
        if current_transaction:
            transactions.append(current_transaction)
        
        # Convert to DataFrame and save as CSV
        if transactions:
            df = pd.DataFrame(transactions)
            csv_path = file_path.with_suffix('.csv')
            df.to_csv(csv_path, index=False)
            return f"Successfully processed {len(transactions)} transactions from {file_path.name} and saved to {csv_path.name}"
        else:
            return f"No transactions found in {file_path.name}"
            
    except Exception as e:
        return f"Error processing {file_path}: {str(e)}"


@tool("analyze_and_report", "Analyzes CSV data and generates a comprehensive report")
def analyze_and_report(csv_file: str) -> str:
    """Analyze sales data from CSV file and generate a comprehensive report."""
    try:
        csv_path = Path(csv_file)
        if not csv_path.exists():
            return f"Error: CSV file {csv_file} does not exist"
        
        # Load the data
        df = pd.read_csv(csv_path)
        
        if df.empty:
            return f"Error: No data found in {csv_file}"
        
        # Perform comprehensive analysis
        analysis = {
            'total_transactions': len(df),
            'total_revenue': df['total_amount'].sum(),
            'average_transaction': df['total_amount'].mean(),
            'date_range': f"{df['date'].min()} to {df['date'].max()}"
        }
        
        # Category analysis
        if 'category' in df.columns:
            category_stats = df.groupby('category')['total_amount'].agg(['sum', 'count', 'mean'])
            analysis['category_performance'] = category_stats.to_dict()
        
        # Sales rep analysis
        if 'sales_rep' in df.columns:
            rep_stats = df.groupby('sales_rep')['total_amount'].agg(['sum', 'count', 'mean'])
            analysis['sales_rep_performance'] = rep_stats.to_dict()
        
        # Top customers
        if 'customer' in df.columns:
            customer_stats = df.groupby('customer')['total_amount'].sum().sort_values(ascending=False).head(5)
            analysis['top_customers'] = customer_stats.to_dict()
        
        # Top products
        if 'product' in df.columns:
            product_stats = df.groupby('product')['total_amount'].sum().sort_values(ascending=False).head(5)
            analysis['top_products'] = product_stats.to_dict()
        
        # Generate report
        report_lines = [
            f"SALES ANALYSIS REPORT - {csv_path.stem.upper()}",
            "=" * 60,
            "",
            "EXECUTIVE SUMMARY",
            "-" * 20,
            f"Total Transactions: {analysis['total_transactions']:,}",
            f"Total Revenue: ${analysis['total_revenue']:,.2f}",
            f"Average Transaction: ${analysis['average_transaction']:,.2f}",
            f"Period: {analysis['date_range']}",
            "",
        ]
        
        # Add category performance
        if 'category_performance' in analysis:
            report_lines.extend([
                "CATEGORY PERFORMANCE",
                "-" * 20
            ])
            for category in analysis['category_performance']['sum']:
                revenue = analysis['category_performance']['sum'][category]
                count = analysis['category_performance']['count'][category]
                avg = analysis['category_performance']['mean'][category]
                report_lines.append(f"{category}: ${revenue:,.2f} ({count} transactions, ${avg:,.2f} avg)")
            report_lines.append("")
        
        # Add sales rep performance
        if 'sales_rep_performance' in analysis:
            report_lines.extend([
                "SALES REPRESENTATIVE PERFORMANCE",
                "-" * 35
            ])
            for rep in analysis['sales_rep_performance']['sum']:
                revenue = analysis['sales_rep_performance']['sum'][rep]
                count = analysis['sales_rep_performance']['count'][rep]
                avg = analysis['sales_rep_performance']['mean'][rep]
                report_lines.append(f"{rep}: ${revenue:,.2f} ({count} transactions, ${avg:,.2f} avg)")
            report_lines.append("")
        
        # Add top customers
        if 'top_customers' in analysis:
            report_lines.extend([
                "TOP 5 CUSTOMERS BY REVENUE",
                "-" * 28
            ])
            for customer, revenue in analysis['top_customers'].items():
                report_lines.append(f"{customer}: ${revenue:,.2f}")
            report_lines.append("")
        
        # Add top products
        if 'top_products' in analysis:
            report_lines.extend([
                "TOP 5 PRODUCTS BY REVENUE",
                "-" * 26
            ])
            for product, revenue in analysis['top_products'].items():
                report_lines.append(f"{product}: ${revenue:,.2f}")
            report_lines.append("")
        
        report_lines.extend([
            "=" * 60,
            f"Report generated successfully for {csv_path.name}",
            f"Analysis complete - {len(df)} records processed"
        ])
        
        # Save report
        report_path = csv_path.with_suffix('.report.txt')
        report_content = '\n'.join(report_lines)
        report_path.write_text(report_content, encoding='utf-8')
        
        return f"Analysis completed for {csv_path.name}. Report saved as {report_path.name}. Summary: {analysis['total_transactions']} transactions, ${analysis['total_revenue']:,.2f} revenue"
        
    except Exception as e:
        return f"Error analyzing {csv_file}: {str(e)}"


# ================================================================
# SIMPLIFIED SALES ANALYSIS SYSTEM
# ================================================================

class SimpleSalesAnalysisSystem:
    """Simplified sales analysis system with minimal LLM calls."""
    
    def __init__(self):
        self.data_dir = Path(__file__).parent
        self.agent = None
    
    async def initialize_agent(self):
        """Initialize a single multi-purpose agent."""
        self.agent = Agent(AgentConfig(
            name="sales_analyst",
            instructions="""You are a sales data analyst. Your role is to:
1. Process sales text files and convert them to structured CSV format
2. Perform comprehensive statistical analysis on sales data
3. Generate detailed business reports and insights
4. Provide clear, actionable recommendations

Be thorough, accurate, and focus on delivering valuable business insights.""",
            llm=LLMProviderConfig(
                provider=LLMProvider.GROQ,
                model="llama-3.1-8b-instant"
            ),
            tools=["process_sales_file", "analyze_and_report"],
            memory=MemoryConfig(type="buffer", max_messages=20)
        ))
        await self.agent.start()
    
    async def run_analysis(self) -> Dict[str, Any]:
        """Run the complete sales analysis with minimal LLM calls."""
        print("🏪 AgenticFlow Simple Sales Analysis System")
        print("=" * 60)
        print("Processing sales data files and generating reports...")
        print()
        
        results = {}
        
        # Find sales data files
        data_files = [
            self.data_dir / "q1_2024_sales.txt",
            self.data_dir / "q2_2024_sales.txt"
        ]
        
        # Process each file in a single agent call
        for data_file in data_files:
            if data_file.exists():
                print(f"📊 Processing {data_file.name}...")
                
                # Single LLM call to process file and generate report
                result = await self.agent.execute_task(
                    f"Please process the sales data file {data_file} by: "
                    f"1. Converting it to CSV format using the process_sales_file tool "
                    f"2. Then analyzing the resulting CSV and generating a comprehensive report using analyze_and_report tool "
                    f"Provide a summary of the key findings."
                )
                
                print(f"✅ Completed analysis of {data_file.name}")
                results[data_file.stem] = result
        
        # Generate executive summary
        print("\n📋 Generating Executive Summary...")
        
        summary_task = """Based on the sales analysis completed for Q1 and Q2 2024, provide an executive summary that includes:
1. Overall performance comparison between quarters
2. Key trends and growth patterns
3. Top performing categories, products, and sales representatives
4. Strategic recommendations for business improvement
5. Summary of total business performance

Focus on actionable insights that would be valuable to executives."""
        
        summary_result = await self.agent.execute_task(summary_task)
        results['executive_summary'] = summary_result
        
        print("✅ Executive summary completed")
        print("\n🎉 Sales Analysis System Complete!")
        
        return results
    
    async def cleanup(self):
        """Clean up the agent."""
        if self.agent:
            await self.agent.stop()
        print("🛑 Agent stopped")


# ================================================================
# MAIN EXECUTION
# ================================================================

async def main():
    """Main execution function."""
    system = SimpleSalesAnalysisSystem()
    
    try:
        # Initialize agent
        await system.initialize_agent()
        
        # Run analysis
        results = await system.run_analysis()
        
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
        
        print(f"\n📊 Analysis Results:")
        print(f"   ✅ {len(csv_files)} data files processed")
        print(f"   ✅ {len(report_files)} detailed reports generated")
        print(f"   ✅ Executive summary completed")
        print(f"   ✅ All workflows successful")
        
    except Exception as e:
        print(f"❌ Error in sales analysis system: {e}")
    
    finally:
        await system.cleanup()


if __name__ == "__main__":
    asyncio.run(main())