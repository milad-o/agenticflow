#!/usr/bin/env python3
"""
Realistic Example 1: Data Analysis Pipeline
===========================================

This example demonstrates a comprehensive data analysis workflow using AgenticFlow:
- Data ingestion from multiple sources
- Data validation and cleaning
- Statistical analysis and feature engineering
- Machine learning model training
- Report generation and visualization

This showcases real-world enterprise data processing scenarios.
"""

import asyncio
import time
import random
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any

# All imports are now handled by the package structure

from agenticflow.orchestration.task_orchestrator import TaskOrchestrator
from agenticflow.orchestration.task_management import RetryPolicy, TaskPriority


class DataAnalysisPipeline:
    """Realistic data analysis pipeline with multiple stages."""
    
    def __init__(self):
        self.start_time = time.time()
        self.results = {}
        
    def log_event(self, stage: str, details: Dict[str, Any]):
        elapsed = time.time() - self.start_time
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {stage}: {details}")
        
    async def ingest_customer_data(self, source: str = "database", **kwargs) -> Dict[str, Any]:
        """Simulate ingesting customer data from various sources."""
        self.log_event("DATA_INGESTION", {"source": source, "type": "customer_data"})
        
        # Simulate data fetching with realistic delays
        await asyncio.sleep(random.uniform(0.5, 1.5))
        
        # Generate realistic customer data
        customers = []
        for i in range(random.randint(800, 1200)):
            customers.append({
                "id": f"CUST_{i:06d}",
                "age": random.randint(18, 80),
                "income": random.randint(25000, 150000),
                "tenure_months": random.randint(1, 120),
                "product_usage": random.uniform(0.1, 10.0)
            })
            
        result = {
            "source": source,
            "record_count": len(customers),
            "data": customers[:10],  # Sample for logging
            "full_dataset": customers,
            "ingestion_time": time.time(),
            "data_quality": random.uniform(0.85, 0.98)
        }
        
        self.log_event("INGESTION_COMPLETE", {
            "source": source, 
            "records": len(customers),
            "quality_score": result["data_quality"]
        })
        
        return result
    
    async def ingest_transaction_data(self, source: str = "warehouse", **kwargs) -> Dict[str, Any]:
        """Simulate ingesting transaction data."""
        self.log_event("DATA_INGESTION", {"source": source, "type": "transaction_data"})
        
        await asyncio.sleep(random.uniform(0.8, 2.0))
        
        # Generate realistic transaction data
        transactions = []
        for i in range(random.randint(5000, 8000)):
            transactions.append({
                "id": f"TXN_{i:08d}",
                "customer_id": f"CUST_{random.randint(0, 1199):06d}",
                "amount": random.uniform(10.0, 2000.0),
                "category": random.choice(["retail", "grocery", "gas", "restaurant", "online"]),
                "timestamp": datetime.now() - timedelta(days=random.randint(0, 365))
            })
        
        result = {
            "source": source,
            "record_count": len(transactions),
            "data": transactions[:10],
            "full_dataset": transactions,
            "ingestion_time": time.time(),
            "total_volume": sum(t["amount"] for t in transactions)
        }
        
        self.log_event("INGESTION_COMPLETE", {
            "source": source,
            "records": len(transactions),
            "total_volume": f"${result['total_volume']:,.2f}"
        })
        
        return result
    
    async def validate_and_clean_data(self, data_type: str, **kwargs) -> Dict[str, Any]:
        """Data validation and cleaning with quality checks."""
        self.log_event("DATA_VALIDATION", {"type": data_type, "stage": "starting"})
        
        await asyncio.sleep(random.uniform(0.3, 0.8))
        
        # Extract input data from context
        input_data = None
        for key, value in kwargs.items():
            if key.endswith('_result') and isinstance(value, dict):
                if value.get('source') and 'full_dataset' in value:
                    input_data = value
                    break
        
        if not input_data:
            raise ValueError(f"No valid input data found for {data_type} validation")
        
        # Simulate data cleaning operations
        original_count = input_data['record_count']
        cleaned_count = int(original_count * random.uniform(0.92, 0.98))
        duplicates_removed = original_count - cleaned_count
        
        # Simulate data quality improvements
        quality_improvements = {
            "missing_values_filled": random.randint(50, 200),
            "outliers_handled": random.randint(10, 50),
            "duplicates_removed": duplicates_removed,
            "format_standardizations": random.randint(100, 500)
        }
        
        result = {
            "data_type": data_type,
            "original_records": original_count,
            "cleaned_records": cleaned_count,
            "data_quality_score": random.uniform(0.94, 0.99),
            "improvements": quality_improvements,
            "cleaning_time": time.time(),
            "cleaned_data": input_data['full_dataset'][:cleaned_count]  # Simulate cleaning
        }
        
        self.log_event("VALIDATION_COMPLETE", {
            "type": data_type,
            "cleaned_records": cleaned_count,
            "quality_score": result["data_quality_score"],
            "improvements": quality_improvements
        })
        
        return result
    
    async def statistical_analysis(self, analysis_type: str = "comprehensive", **kwargs) -> Dict[str, Any]:
        """Perform comprehensive statistical analysis."""
        self.log_event("STATISTICAL_ANALYSIS", {"type": analysis_type, "stage": "starting"})
        
        await asyncio.sleep(random.uniform(1.0, 2.5))
        
        # Simulate complex statistical computations
        analysis_results = {
            "customer_segments": {
                "high_value": random.randint(150, 300),
                "medium_value": random.randint(400, 600),
                "low_value": random.randint(200, 400)
            },
            "key_metrics": {
                "avg_customer_value": random.uniform(1200, 2500),
                "churn_rate": random.uniform(0.05, 0.15),
                "customer_satisfaction": random.uniform(7.2, 9.1),
                "retention_rate": random.uniform(0.82, 0.94)
            },
            "trends": {
                "growth_rate": random.uniform(0.08, 0.25),
                "seasonal_patterns": ["Q4_peak", "Q2_dip"],
                "emerging_segments": ["digital_natives", "eco_conscious"]
            },
            "correlations": {
                "income_vs_usage": random.uniform(0.3, 0.7),
                "age_vs_product_preference": random.uniform(0.2, 0.5),
                "tenure_vs_loyalty": random.uniform(0.6, 0.9)
            }
        }
        
        result = {
            "analysis_type": analysis_type,
            "results": analysis_results,
            "confidence_level": random.uniform(0.92, 0.98),
            "analysis_time": time.time(),
            "sample_size": random.randint(8000, 12000),
            "statistical_significance": True
        }
        
        self.log_event("ANALYSIS_COMPLETE", {
            "type": analysis_type,
            "confidence": result["confidence_level"],
            "sample_size": result["sample_size"],
            "key_findings": len(analysis_results)
        })
        
        return result
    
    async def feature_engineering(self, **kwargs) -> Dict[str, Any]:
        """Create engineered features for machine learning."""
        self.log_event("FEATURE_ENGINEERING", {"stage": "starting"})
        
        await asyncio.sleep(random.uniform(0.8, 1.5))
        
        # Simulate feature engineering process
        features_created = [
            "customer_lifetime_value",
            "purchase_frequency_trend",
            "seasonal_spending_pattern",
            "product_affinity_score",
            "churn_risk_indicator",
            "cross_sell_potential",
            "engagement_score",
            "loyalty_index"
        ]
        
        feature_stats = {
            feature: {
                "mean": random.uniform(0.1, 10.0),
                "std": random.uniform(0.5, 3.0),
                "importance": random.uniform(0.1, 1.0)
            } for feature in features_created
        }
        
        result = {
            "features_created": features_created,
            "feature_count": len(features_created),
            "feature_statistics": feature_stats,
            "correlation_matrix_size": f"{len(features_created)}x{len(features_created)}",
            "engineering_time": time.time(),
            "quality_score": random.uniform(0.88, 0.96)
        }
        
        self.log_event("ENGINEERING_COMPLETE", {
            "features_created": len(features_created),
            "quality_score": result["quality_score"],
            "top_features": features_created[:3]
        })
        
        return result
    
    async def train_ml_model(self, model_type: str = "ensemble", **kwargs) -> Dict[str, Any]:
        """Train machine learning model with the processed data."""
        self.log_event("MODEL_TRAINING", {"model_type": model_type, "stage": "starting"})
        
        await asyncio.sleep(random.uniform(2.0, 4.0))  # ML training takes longer
        
        # Simulate realistic ML training metrics
        training_metrics = {
            "accuracy": random.uniform(0.82, 0.94),
            "precision": random.uniform(0.78, 0.91),
            "recall": random.uniform(0.75, 0.89),
            "f1_score": random.uniform(0.76, 0.90),
            "auc_roc": random.uniform(0.85, 0.96)
        }
        
        training_details = {
            "model_type": model_type,
            "algorithm": "Random Forest + XGBoost Ensemble",
            "training_samples": random.randint(6000, 9000),
            "validation_samples": random.randint(2000, 3000),
            "epochs": random.randint(50, 150),
            "cross_validation_folds": 5,
            "hyperparameters": {
                "n_estimators": random.randint(100, 300),
                "max_depth": random.randint(6, 15),
                "learning_rate": random.uniform(0.05, 0.2)
            }
        }
        
        result = {
            "model_type": model_type,
            "metrics": training_metrics,
            "training_details": training_details,
            "model_size_mb": random.uniform(15.5, 45.2),
            "training_time": time.time(),
            "ready_for_production": training_metrics["accuracy"] > 0.85
        }
        
        self.log_event("TRAINING_COMPLETE", {
            "model_type": model_type,
            "accuracy": training_metrics["accuracy"],
            "f1_score": training_metrics["f1_score"],
            "production_ready": result["ready_for_production"]
        })
        
        return result
    
    async def generate_insights_report(self, **kwargs) -> Dict[str, Any]:
        """Generate comprehensive business insights report."""
        self.log_event("REPORT_GENERATION", {"stage": "starting"})
        
        await asyncio.sleep(random.uniform(1.0, 2.0))
        
        # Collect all previous results from context
        pipeline_data = {}
        for key, value in kwargs.items():
            if key.endswith('_result') and isinstance(value, dict):
                stage_name = key.replace('_result', '')
                pipeline_data[stage_name] = value
        
        # Generate comprehensive business insights
        insights = {
            "executive_summary": {
                "total_customers_analyzed": random.randint(8000, 12000),
                "data_quality_score": random.uniform(0.94, 0.99),
                "model_accuracy": random.uniform(0.82, 0.94),
                "key_recommendations": 4
            },
            "customer_segments": {
                "high_value_growth_opportunity": "23% revenue increase potential",
                "retention_risk_segment": "15% of customers need immediate attention",
                "cross_sell_opportunities": "2.3x revenue multiplier identified"
            },
            "actionable_recommendations": [
                "Implement targeted retention campaign for high-risk customers",
                "Develop premium tier for high-value segment",
                "Launch cross-sell initiative for identified product affinities",
                "Optimize pricing strategy based on spending patterns"
            ],
            "expected_impact": {
                "revenue_increase": random.uniform(0.12, 0.28),
                "cost_reduction": random.uniform(0.08, 0.18),
                "customer_satisfaction_improvement": random.uniform(0.15, 0.32)
            }
        }
        
        result = {
            "report_type": "comprehensive_business_insights",
            "insights": insights,
            "data_sources_used": len(pipeline_data),
            "confidence_level": random.uniform(0.89, 0.97),
            "report_generation_time": time.time(),
            "pipeline_summary": {
                "total_processing_time": time.time() - self.start_time,
                "stages_completed": len(pipeline_data),
                "overall_success": True
            }
        }
        
        self.log_event("REPORT_COMPLETE", {
            "insights_generated": len(insights["actionable_recommendations"]),
            "confidence": result["confidence_level"],
            "expected_revenue_impact": f"{insights['expected_impact']['revenue_increase']:.1%}",
            "processing_time": f"{result['pipeline_summary']['total_processing_time']:.2f}s"
        })
        
        return result


async def run_data_analysis_pipeline():
    """Execute the complete data analysis pipeline."""
    print("🔬 AgenticFlow Realistic Example 1: Data Analysis Pipeline")
    print("=" * 65)
    print()
    
    pipeline = DataAnalysisPipeline()
    
    # Configure orchestrator for data pipeline
    retry_policy = RetryPolicy(
        max_attempts=3,
        initial_delay=0.5,
        max_delay=10.0,
        backoff_multiplier=2.0
    )
    
    orchestrator = TaskOrchestrator(
        max_concurrent_tasks=6,  # Allow parallel data processing
        default_retry_policy=retry_policy
    )
    
    print("📊 Building Data Analysis Pipeline...")
    print("-" * 40)
    
    # Stage 1: Data Ingestion (Parallel)
    orchestrator.add_function_task(
        "ingest_customers", "Ingest Customer Data",
        pipeline.ingest_customer_data,
        args=("customer_database",),
        priority=TaskPriority.HIGH
    )
    
    orchestrator.add_function_task(
        "ingest_transactions", "Ingest Transaction Data", 
        pipeline.ingest_transaction_data,
        args=("data_warehouse",),
        priority=TaskPriority.HIGH
    )
    
    # Stage 2: Data Validation (Depends on ingestion)
    orchestrator.add_function_task(
        "validate_customers", "Validate Customer Data",
        pipeline.validate_and_clean_data,
        args=("customer_data",),
        dependencies=["ingest_customers"],
        priority=TaskPriority.NORMAL
    )
    
    orchestrator.add_function_task(
        "validate_transactions", "Validate Transaction Data",
        pipeline.validate_and_clean_data,
        args=("transaction_data",),
        dependencies=["ingest_transactions"],
        priority=TaskPriority.NORMAL
    )
    
    # Stage 3: Analysis (Depends on validation)
    orchestrator.add_function_task(
        "statistical_analysis", "Statistical Analysis",
        pipeline.statistical_analysis,
        args=("comprehensive",),
        dependencies=["validate_customers", "validate_transactions"],
        priority=TaskPriority.NORMAL
    )
    
    # Stage 4: Feature Engineering (Parallel with analysis)
    orchestrator.add_function_task(
        "feature_engineering", "Feature Engineering",
        pipeline.feature_engineering,
        dependencies=["validate_customers", "validate_transactions"],
        priority=TaskPriority.NORMAL
    )
    
    # Stage 5: ML Model Training (Depends on features)
    orchestrator.add_function_task(
        "train_model", "Train ML Model",
        pipeline.train_ml_model,
        args=("ensemble",),
        dependencies=["feature_engineering", "statistical_analysis"],
        priority=TaskPriority.NORMAL
    )
    
    # Stage 6: Generate Final Report (Depends on everything)
    orchestrator.add_function_task(
        "generate_report", "Generate Business Insights",
        pipeline.generate_insights_report,
        dependencies=["statistical_analysis", "feature_engineering", "train_model"],
        priority=TaskPriority.CRITICAL
    )
    
    # Execute the pipeline
    print("🚀 Executing Data Analysis Pipeline...")
    print("-" * 40)
    
    start_time = time.time()
    result = await orchestrator.execute_workflow()
    total_time = time.time() - start_time
    
    # Generate comprehensive report
    print()
    print("=" * 65)
    print("📋 DATA ANALYSIS PIPELINE REPORT")
    print("=" * 65)
    
    success_rate = result["success_rate"]
    total_tasks = result["status"]["total_tasks"]
    completed_tasks = result["status"]["completed_tasks"]
    
    print(f"⏱️  Total Execution Time: {total_time:.2f} seconds")
    print(f"✅ Success Rate: {success_rate:.1f}%")
    print(f"📊 Tasks Completed: {completed_tasks}/{total_tasks}")
    print(f"🔄 Workflow Status: {'COMPLETED' if result['status']['is_complete'] else 'INCOMPLETE'}")
    
    if "dag_stats" in result:
        dag_stats = result["dag_stats"] 
        print(f"📈 Execution Levels: {dag_stats.get('execution_levels', 'N/A')}")
        print(f"🎯 Critical Path: {' → '.join(dag_stats.get('critical_path', []))}")
    
    # Task-by-task breakdown
    print("\n" + "-" * 65)
    print("📋 DETAILED TASK BREAKDOWN")
    print("-" * 65)
    
    if "task_results" in result:
        for task_id, task_info in result["task_results"].items():
            status = "✅" if task_info.get("state") == "completed" else "❌"
            task_name = task_info.get("name", task_id)
            execution_time = task_info.get("execution_time", 0)
            
            print(f"{status} {task_name}")
            print(f"   ⏱️  Time: {execution_time:.2f}s")
            print(f"   🔄 Attempts: {task_info.get('attempts', 1)}")
            
            if task_info.get("result") and task_info["result"].get("success"):
                task_result = task_info["result"]["result"]
                if isinstance(task_result, dict):
                    # Show relevant metrics
                    if "record_count" in task_result:
                        print(f"   📊 Records: {task_result['record_count']:,}")
                    if "confidence_level" in task_result:
                        print(f"   🎯 Confidence: {task_result['confidence_level']:.1%}")
                    if "accuracy" in task_result.get("metrics", {}):
                        print(f"   🎯 Accuracy: {task_result['metrics']['accuracy']:.1%}")
            print()
    
    # Final Assessment
    print("-" * 65)
    print("🎯 PIPELINE ASSESSMENT")
    print("-" * 65)
    
    grade = "A+" if success_rate >= 95 else "A" if success_rate >= 85 else "B+" if success_rate >= 75 else "B"
    
    print(f"📊 Overall Grade: {grade}")
    print()
    
    # Performance Analysis
    if success_rate >= 95:
        print("✅ EXCELLENT: Pipeline executed flawlessly")
        print("   • All data processing stages completed successfully")
        print("   • Machine learning model trained with high accuracy")
        print("   • Business insights generated with high confidence")
    elif success_rate >= 85:
        print("✅ GOOD: Pipeline mostly successful with minor issues")
    else:
        print("⚠️  NEEDS IMPROVEMENT: Some pipeline stages failed")
    
    print()
    print("💡 Key Achievements:")
    print("   • Parallel data ingestion from multiple sources")
    print("   • Automated data validation and cleaning")
    print("   • Statistical analysis with correlation discovery")  
    print("   • Feature engineering for ML readiness")
    print("   • End-to-end ML model training")
    print("   • Actionable business insights generation")
    
    print()
    print("🔧 Technical Highlights:")
    print(f"   • {total_tasks} tasks orchestrated in complex dependency graph")
    print(f"   • Up to 6 parallel data processing streams")
    print(f"   • Sophisticated retry logic with exponential backoff")
    print(f"   • Real-time progress monitoring and logging")
    print(f"   • Execution completed in {total_time:.2f}s")
    
    return {
        "example_name": "Data Analysis Pipeline",
        "grade": grade,
        "success_rate": success_rate,
        "execution_time": total_time,
        "tasks_completed": f"{completed_tasks}/{total_tasks}",
        "key_features": [
            "Multi-source data ingestion",
            "Automated data validation", 
            "Statistical analysis",
            "ML model training",
            "Business insights generation"
        ]
    }


if __name__ == "__main__":
    result = asyncio.run(run_data_analysis_pipeline())
    
    print()
    print("=" * 65)
    print(f"🏆 FINAL RESULT: {result['grade']} ({result['success_rate']:.1f}% success)")
    print("🚀 Data Analysis Pipeline validation complete!")
    print("=" * 65)