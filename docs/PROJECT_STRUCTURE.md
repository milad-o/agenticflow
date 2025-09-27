# AgenticFlow Project Structure

## 📁 Core Framework
```
agenticflow/
├── core/
│   ├── flow.py                 # Main Flow orchestration class
│   ├── observable_flow.py      # Enhanced Flow with observability
│   └── __init__.py
├── teams/
│   ├── supervisor.py           # SupervisorAgent for coordination
│   ├── team_state.py          # TeamState management
│   ├── team_graph.py          # LangGraph-based workflow
│   └── __init__.py
├── agents/
│   ├── filesystem_worker.py   # File operations worker
│   ├── analysis_worker.py     # Data analysis worker
│   ├── reporting_worker.py    # Report generation worker
│   ├── validation_agents.py   # Data validation workers
│   └── __init__.py
├── observability/
│   ├── event_tracker.py       # Event tracking system
│   ├── observer.py            # Flow observation and monitoring
│   ├── metrics.py             # Metrics collection
│   ├── visualization.py       # Streamlit UI components
│   └── __init__.py
└── __init__.py
```

## 🎨 User Interfaces
```
agenticflow_ui.py              # Main unified monitoring interface
examples/ui/
├── chat_ui.py                 # Chat-style monitoring interface
├── enhanced_chat_ui.py        # Premium chat interface
├── progress_ui.py             # Real-time progress monitoring
├── ui_launcher.py             # Standard observatory
└── launch_ui.py               # Multi-interface launcher
```

## 📊 Examples & Demos
```
examples/
├── data/
│   ├── sales_data.csv         # Sample sales data
│   ├── customer_data.csv      # Sample customer data
│   ├── q3_2024_*.csv         # Q3 business data
│   └── quarterly_report_q3_2024.txt  # Hierarchical report
├── artifact/                 # Generated reports directory
└── quick_start.py             # Simple usage example
```

## 📚 Documentation
```
README.md                      # Main project documentation
OBSERVABILITY.md              # Comprehensive observability guide
UI_FEATURES.md                # Complete UI features documentation
PROJECT_STRUCTURE.md          # This file
```

## 🔧 Configuration
```
.env                          # Environment variables (API keys)
pyproject.toml                # Project dependencies and metadata
uv.lock                       # Dependency lock file
.gitignore                    # Git ignore rules
```

## 🚀 Quick Start Files
- `agenticflow_ui.py` - **Main interface** (recommended)
- `examples/quick_start.py` - Simple code example
- `simple_validation_demo.py` - Validation workflow demo
- `observable_demo.py` - Comprehensive observability demo

## 📦 Key Components

### Core Framework
- **Flow**: Main orchestration with worker management
- **ObservableFlow**: Enhanced Flow with real-time monitoring
- **SupervisorAgent**: LLM-powered task coordination
- **Workers**: Specialized agents (FileSystem, Analysis, Reporting)

### Observability System
- **EventTracker**: Comprehensive event capture and storage
- **FlowObserver**: Advanced monitoring and real-time callbacks
- **MetricsCollector**: Performance metrics and analytics
- **Visualization**: Beautiful Streamlit UI components

### User Interfaces
- **Main UI**: Unified monitoring dashboard
- **Chat UI**: Interactive conversation-style monitoring
- **Progress UI**: Real-time execution progress tracking
- **Enhanced UI**: Premium experience with animations

## 🎯 Usage Patterns

### Basic Usage
```python
from agenticflow import Flow
flow = Flow()
flow.add_worker("worker_name", WorkerInstance())
result = flow.run("Your task")
```

### With Observability
```python
from agenticflow import ObservableFlow
flow = ObservableFlow()
flow.add_worker("worker_name", WorkerInstance())
result = flow.run("Your task")
# Access observability data
events = flow.get_event_tracker().events
```

### Launch UI
```bash
# Main interface
uv run streamlit run agenticflow_ui.py

# Specialized interfaces
uv run streamlit run examples/ui/progress_ui.py
uv run streamlit run examples/ui/chat_ui.py
```

## 🏗️ Architecture Highlights

1. **Hierarchical Teams**: Clean supervisor-worker pattern
2. **LangGraph Integration**: State-based workflow management
3. **Real-time Observability**: Comprehensive monitoring system
4. **Beautiful UIs**: Multiple Streamlit interfaces
5. **Event-driven**: Complete event tracking and visualization
6. **Production Ready**: Error handling, recovery, metrics

## 📈 Monitoring Capabilities

- Real-time flow execution progress
- Agent activity and status tracking
- Tool usage analytics and visualization
- Performance metrics and success rates
- Event streams and timeline visualization
- Agent reflection and decision-making insights
- Error tracking and recovery monitoring

---

**AgenticFlow**: Production-ready hierarchical multi-agent orchestration with enterprise-grade observability and beautiful real-time monitoring interfaces.