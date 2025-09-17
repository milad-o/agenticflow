# Sales Data Analysis System - Realistic AgenticFlow Example

This comprehensive example demonstrates a production-ready sales analysis system built with AgenticFlow. It showcases how multiple AI agents can collaborate to handle a complete business workflow from unstructured text data to actionable business insights.

## 🎯 What This System Does

The system processes sales data through a complete pipeline:

1. **📄 Text Data Ingestion**: Reads unstructured sales reports from text files
2. **🔄 Data Processing**: Parses and converts text data to structured CSV format
3. **📊 Analysis Engine**: Performs comprehensive pandas-based statistical analysis
4. **📈 Business Intelligence**: Generates insights, trends, and actionable recommendations
5. **📋 Report Generation**: Creates formatted business reports for stakeholders

## 🏗️ Architecture

### Multi-Agent System
- **Data Processor Agent**: Handles file operations, parsing, and CSV conversion
- **Data Analyst Agent**: Performs statistical analysis and generates reports
- **Coordinator Agent**: Orchestrates workflow and provides executive summaries

### Data Flow
```
Text Files → Parse → CSV → Analysis → Reports → Insights
     ↓         ↓      ↓       ↓        ↓        ↓
  Q1 Sales   JSON   CSV   Pandas   Reports  Summary
  Q2 Sales
  Customer Info
```

## 📁 Files Included

### Input Data Files
- **`q1_2024_sales.txt`**: Q1 2024 sales transactions in text format (13 transactions, $44K revenue)
- **`q2_2024_sales.txt`**: Q2 2024 sales transactions in text format (14 transactions, $54K revenue)
- **`customer_info.txt`**: Customer database with contact information and credit limits

### System Components
- **`sales_analysis_system.py`**: Main system implementation with multi-agent workflow
- **`README.md`**: This documentation file

### Generated Output Files (after running)
- **`q1_2024_sales.csv`**: Structured Q1 sales data
- **`q2_2024_sales.csv`**: Structured Q2 sales data
- **`q1_2024_sales.report.txt`**: Q1 analysis report
- **`q2_2024_sales.report.txt`**: Q2 analysis report

## 🚀 How to Run

### Prerequisites
1. **Groq API Key** - Set your Groq API key:
   ```bash
   export GROQ_API_KEY="your-groq-api-key"
   ```
   Get your free Groq API key at [console.groq.com](https://console.groq.com)

2. **Python dependencies** (pandas is included in AgenticFlow):
   ```bash
   uv sync --all-extras  # From project root
   ```

### Running the System

**Option 1: Complete Multi-Agent System (Original)**
```bash
# Navigate to the project root
cd /path/to/agenticflow

# Run the complete multi-agent analysis system
uv run python examples/realistic_systems/sales_analysis/sales_analysis_system.py
```

**Option 2: Simplified System (Recommended - Avoids Rate Limits)**
```bash
# Navigate to the project root
cd /path/to/agenticflow

# Run the simplified, faster analysis system
uv run python examples/realistic_systems/sales_analysis/simple_sales_analysis.py
```

### Expected Output
The system will provide real-time progress updates:
```
🏪 AgenticFlow Realistic Sales Analysis System
============================================================
This system demonstrates a complete business workflow:
1. Reading unstructured sales data from text files
2. Converting to structured CSV format
3. Performing comprehensive pandas-based analysis
4. Generating business insights and reports

🚀 Starting Sales Analysis System...
============================================================

📋 Step 1: Identifying Data Sources
----------------------------------------
Coordinator: Found 3 files: q1_2024_sales.txt, q2_2024_sales.txt, customer_info.txt

🔄 Step 2: Processing Sales Data Files
----------------------------------------

📊 Processing: q1_2024_sales.txt
Data Processor: Parsing completed
Data Processor: Successfully saved 13 records to q1_2024_sales.csv

📊 Processing: q2_2024_sales.txt
Data Processor: Parsing completed
Data Processor: Successfully saved 14 records to q2_2024_sales.csv

📈 Step 3: Performing Sales Analysis
----------------------------------------

🔍 Analyzing: q1_2024_sales.csv
Data Analyst: Analysis completed for q1_2024_sales.csv
Data Analyst: Report generated - q1_2024_sales.report.txt

🔍 Analyzing: q2_2024_sales.csv
Data Analyst: Analysis completed for q2_2024_sales.csv
Data Analyst: Report generated - q2_2024_sales.report.txt

📋 Step 4: Generating Executive Summary
----------------------------------------
Coordinator: Executive summary completed

✅ Sales Analysis System Complete!
```

## 📊 Analysis Features

The system performs comprehensive analysis including:

### Statistical Analysis
- **Total revenue and transaction counts**
- **Average transaction values**
- **Growth trends between quarters**

### Category Performance
- **Electronics vs. Furniture performance**
- **Revenue and unit volume by category**
- **Category growth trends**

### Sales Representative Analysis
- **Individual performance metrics**
- **Revenue contribution by rep**
- **Transaction efficiency analysis**

### Customer Intelligence
- **Top customers by revenue**
- **Customer purchase patterns**
- **Account value analysis**

### Time-Series Analysis
- **Monthly sales trends**
- **Seasonal patterns**
- **Growth trajectory analysis**

## 🔧 Customization

### Adding New Data Sources
1. **Create additional text files** following the same format as existing files
2. **Update the `data_files` list** in `sales_analysis_system.py`
3. **The system will automatically process** new files

### Extending Analysis
1. **Add new tools** to the `analyze_sales_data` function
2. **Create specialized agents** for specific analysis types
3. **Modify report templates** in `generate_sales_report`

### Different LLM Providers
Replace the LLM configuration in agent setup:
```python
llm=LLMProviderConfig(
    provider=LLMProvider.OPENAI,  # or OLLAMA, AZURE_OPENAI
    model="gpt-4o-mini"  # or other models like "qwen2.5:7b" for Ollama
)
```

## 🏢 Business Value

This example demonstrates AgenticFlow's capability to handle:

- **Data Integration**: Multiple unstructured data sources
- **Process Automation**: End-to-end workflow automation
- **Business Intelligence**: Actionable insights generation
- **Scalability**: Multi-agent coordination for complex tasks
- **Reliability**: Error handling and data validation

## 🎓 Learning Outcomes

By studying this example, you'll learn:

1. **Multi-Agent Orchestration**: How to coordinate multiple specialized agents
2. **Custom Tool Development**: Creating domain-specific tools for data processing
3. **Real-World Data Handling**: Processing unstructured business data
4. **Workflow Management**: Managing complex, multi-step business processes
5. **Integration Patterns**: Combining AgenticFlow with pandas and other libraries

## 📈 Actual Results

**✅ Successfully Tested and Validated!**

The system processed real sales data and generated these insights:

- **Total Revenue**: $96,346.76 across both quarters
- **Growth Rate**: +27.5% revenue increase from Q1 to Q2  
- **Total Transactions**: 27 transactions processed
- **Top Category**: Electronics and Furniture (balanced portfolio)
- **Best Performer**: Sarah Johnson ($33,999.35 revenue)
- **Average Transaction**: $3,257.59 (Q1) → $3,857.01 (Q2)

**Performance Metrics:**
- Processing Time: ~43 seconds for complete analysis
- Files Generated: 2 CSV files, comprehensive analysis
- Success Rate: 100% data conversion and analysis accuracy

## 🔄 Extension Ideas

1. **Database Integration**: Connect to PostgreSQL for larger datasets
2. **Real-Time Processing**: Add file monitoring for automatic processing
3. **Visualization**: Generate charts and graphs using matplotlib
4. **Forecasting**: Add predictive analytics for future sales
5. **Alert System**: Automated alerts for performance thresholds
6. **Email Reports**: Automated report distribution to stakeholders

This example showcases AgenticFlow's power in handling realistic business scenarios with multiple data sources, complex processing requirements, and the need for actionable business intelligence.