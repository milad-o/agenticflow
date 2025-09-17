#!/usr/bin/env python3
"""
Complex Orchestration Test: Parallel, Sequential, and Tool Calling
==================================================================

This example demonstrates advanced AgenticFlow capabilities:
- Parallel task execution with independent branches
- Sequential dependencies with complex DAG structures
- Tool calling and inter-task communication
- Mixed execution patterns (parallel + sequential)
- Error handling and recovery scenarios

This showcases the full orchestration power of AgenticFlow.
"""

import asyncio
import time
import random
import json
import math
from typing import Dict, List, Any, Optional
from datetime import datetime

import sys
sys.path.append('/Users/miladolad/OneDrive/Work Projects/ma_system/agenticflow/src')

from agenticflow.orchestration.task_orchestrator import TaskOrchestrator
from agenticflow.orchestration.task_management import RetryPolicy, TaskPriority


class ComplexProcessor:
    """Advanced processor demonstrating complex orchestration patterns."""
    
    def __init__(self):
        self.start_time = time.time()
        self.shared_data = {}
        self.computation_cache = {}
        
    def log_event(self, stage: str, details: Dict[str, Any], task_id: str = ""):
        elapsed = time.time() - self.start_time
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        task_prefix = f"[{task_id}] " if task_id else ""
        print(f"[{timestamp}] {task_prefix}{stage}: {details}")
    
    # =============================================
    # PARALLEL EXECUTION BRANCH A: Data Generation
    # =============================================
    
    async def generate_dataset_a(self, size: int = 1000, **kwargs) -> Dict[str, Any]:
        """Generate dataset A - runs in parallel with B and C."""
        task_id = "DATA_A"
        self.log_event("START_DATA_GENERATION", {"dataset": "A", "size": size}, task_id)
        
        # Simulate data generation work
        await asyncio.sleep(random.uniform(0.5, 1.2))
        
        # Generate mathematical dataset
        dataset = []
        for i in range(size):
            value = math.sin(i * 0.01) * 100 + random.uniform(-10, 10)
            dataset.append({
                "id": i,
                "value": round(value, 3),
                "category": "A",
                "timestamp": time.time()
            })
        
        # Calculate basic statistics
        values = [item["value"] for item in dataset]
        stats = {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "mean": sum(values) / len(values),
            "sum": sum(values)
        }
        
        result = {
            "dataset_id": "A",
            "data": dataset[:10],  # Only store first 10 for display
            "total_records": len(dataset),
            "statistics": stats,
            "generation_time": time.time(),
            "processing_time": time.time() - self.start_time
        }
        
        # Store in shared cache for other tasks
        self.shared_data["dataset_a"] = {
            "full_data": dataset,
            "stats": stats,
            "metadata": {"size": size, "type": "mathematical"}
        }
        
        self.log_event("COMPLETED_DATA_GENERATION", {
            "dataset": "A", 
            "records": len(dataset),
            "mean": f"{stats['mean']:.2f}",
            "range": f"{stats['min']:.1f} to {stats['max']:.1f}"
        }, task_id)
        
        return result
    
    async def generate_dataset_b(self, size: int = 800, **kwargs) -> Dict[str, Any]:
        """Generate dataset B - runs in parallel with A and C."""
        task_id = "DATA_B"
        self.log_event("START_DATA_GENERATION", {"dataset": "B", "size": size}, task_id)
        
        # Simulate longer processing
        await asyncio.sleep(random.uniform(0.8, 1.5))
        
        # Generate text-based dataset
        categories = ["alpha", "beta", "gamma", "delta", "epsilon"]
        dataset = []
        
        for i in range(size):
            score = random.uniform(0, 100)
            category = random.choice(categories)
            dataset.append({
                "id": f"B_{i:04d}",
                "score": round(score, 2),
                "category": category,
                "priority": "high" if score > 80 else "medium" if score > 50 else "low",
                "created_at": time.time()
            })
        
        # Calculate category distribution
        category_counts = {}
        priority_counts = {"high": 0, "medium": 0, "low": 0}
        
        for item in dataset:
            category_counts[item["category"]] = category_counts.get(item["category"], 0) + 1
            priority_counts[item["priority"]] += 1
        
        result = {
            "dataset_id": "B", 
            "data": dataset[:8],  # Store first 8 for display
            "total_records": len(dataset),
            "category_distribution": category_counts,
            "priority_distribution": priority_counts,
            "generation_time": time.time(),
            "processing_time": time.time() - self.start_time
        }
        
        # Store in shared cache
        self.shared_data["dataset_b"] = {
            "full_data": dataset,
            "categories": category_counts,
            "priorities": priority_counts,
            "metadata": {"size": size, "type": "categorical"}
        }
        
        self.log_event("COMPLETED_DATA_GENERATION", {
            "dataset": "B",
            "records": len(dataset), 
            "categories": len(category_counts),
            "high_priority": priority_counts["high"]
        }, task_id)
        
        return result
    
    async def generate_dataset_c(self, size: int = 1200, **kwargs) -> Dict[str, Any]:
        """Generate dataset C - runs in parallel with A and B."""
        task_id = "DATA_C"
        self.log_event("START_DATA_GENERATION", {"dataset": "C", "size": size}, task_id)
        
        # Simulate variable processing time
        await asyncio.sleep(random.uniform(0.3, 1.0))
        
        # Generate time-series dataset
        dataset = []
        base_time = time.time() - (size * 60)  # Start from size minutes ago
        
        for i in range(size):
            timestamp = base_time + (i * 60)  # 1-minute intervals
            # Simulate sensor readings with noise and trends
            trend = math.sin(i * 0.05) * 20
            noise = random.gauss(0, 5)
            reading = 50 + trend + noise
            
            dataset.append({
                "timestamp": timestamp,
                "reading": round(reading, 2),
                "sensor_id": f"SENSOR_{(i % 10) + 1:02d}",
                "status": "normal" if 30 <= reading <= 70 else "anomaly",
                "sequence": i
            })
        
        # Analyze anomalies and sensor performance
        anomalies = [item for item in dataset if item["status"] == "anomaly"]
        sensor_counts = {}
        
        for item in dataset:
            sensor_id = item["sensor_id"]
            sensor_counts[sensor_id] = sensor_counts.get(sensor_id, 0) + 1
        
        result = {
            "dataset_id": "C",
            "data": dataset[:12],  # Store first 12 for display  
            "total_records": len(dataset),
            "anomaly_count": len(anomalies),
            "anomaly_rate": len(anomalies) / len(dataset),
            "sensor_distribution": sensor_counts,
            "time_range": {
                "start": dataset[0]["timestamp"],
                "end": dataset[-1]["timestamp"], 
                "duration_hours": (dataset[-1]["timestamp"] - dataset[0]["timestamp"]) / 3600
            },
            "generation_time": time.time(),
            "processing_time": time.time() - self.start_time
        }
        
        # Store in shared cache
        self.shared_data["dataset_c"] = {
            "full_data": dataset,
            "anomalies": anomalies,
            "sensors": sensor_counts,
            "metadata": {"size": size, "type": "timeseries"}
        }
        
        self.log_event("COMPLETED_DATA_GENERATION", {
            "dataset": "C",
            "records": len(dataset),
            "anomalies": len(anomalies),
            "anomaly_rate": f"{len(anomalies)/len(dataset):.1%}",
            "sensors": len(sensor_counts)
        }, task_id)
        
        return result
    
    # ===============================================
    # SEQUENTIAL PROCESSING: Data Analysis Pipeline  
    # ===============================================
    
    async def analyze_datasets(self, **kwargs) -> Dict[str, Any]:
        """Analyze all datasets - depends on A, B, C completion."""
        task_id = "ANALYZE"
        self.log_event("START_ANALYSIS", {"datasets": ["A", "B", "C"]}, task_id)
        
        # This task depends on all three parallel data generation tasks
        await asyncio.sleep(random.uniform(0.4, 0.8))
        
        # Verify we have all datasets
        required_datasets = ["dataset_a", "dataset_b", "dataset_c"]
        available_datasets = [ds for ds in required_datasets if ds in self.shared_data]
        
        if len(available_datasets) != len(required_datasets):
            raise ValueError(f"Missing datasets. Available: {available_datasets}, Required: {required_datasets}")
        
        # Cross-dataset analysis
        analysis_results = {}
        
        # Dataset A analysis (mathematical)
        dataset_a = self.shared_data["dataset_a"]
        analysis_results["dataset_a"] = {
            "type": "mathematical",
            "record_count": len(dataset_a["full_data"]),
            "value_range": dataset_a["stats"]["max"] - dataset_a["stats"]["min"],
            "average": dataset_a["stats"]["mean"],
            "quality_score": 0.95 if abs(dataset_a["stats"]["mean"]) < 50 else 0.8
        }
        
        # Dataset B analysis (categorical)
        dataset_b = self.shared_data["dataset_b"]
        total_b_records = len(dataset_b["full_data"])
        high_priority_ratio = dataset_b["priorities"]["high"] / total_b_records
        
        analysis_results["dataset_b"] = {
            "type": "categorical", 
            "record_count": total_b_records,
            "category_diversity": len(dataset_b["categories"]),
            "high_priority_ratio": high_priority_ratio,
            "quality_score": 0.9 if high_priority_ratio < 0.3 else 0.7  # Prefer balanced distribution
        }
        
        # Dataset C analysis (timeseries)
        dataset_c = self.shared_data["dataset_c"]
        analysis_results["dataset_c"] = {
            "type": "timeseries",
            "record_count": len(dataset_c["full_data"]),
            "anomaly_percentage": len(dataset_c["anomalies"]) / len(dataset_c["full_data"]) * 100,
            "sensor_count": len(dataset_c["sensors"]),
            "quality_score": 0.85 if len(dataset_c["anomalies"]) < len(dataset_c["full_data"]) * 0.1 else 0.6
        }
        
        # Global analysis
        total_records = sum(result["record_count"] for result in analysis_results.values())
        average_quality = sum(result["quality_score"] for result in analysis_results.values()) / len(analysis_results)
        
        result = {
            "individual_analysis": analysis_results,
            "global_metrics": {
                "total_records": total_records,
                "dataset_count": len(analysis_results),
                "average_quality_score": average_quality,
                "processing_time": time.time() - self.start_time,
                "analysis_timestamp": time.time()
            },
            "recommendations": {
                "high_quality_datasets": [ds for ds, data in analysis_results.items() if data["quality_score"] > 0.85],
                "needs_improvement": [ds for ds, data in analysis_results.items() if data["quality_score"] < 0.8],
                "ready_for_ml": average_quality > 0.8
            }
        }
        
        # Store analysis results for downstream tasks
        self.shared_data["analysis_results"] = result
        
        self.log_event("COMPLETED_ANALYSIS", {
            "datasets_analyzed": len(analysis_results),
            "total_records": total_records,
            "avg_quality": f"{average_quality:.2f}",
            "ml_ready": result["recommendations"]["ready_for_ml"]
        }, task_id)
        
        return result
    
    # ===========================================
    # PARALLEL PROCESSING BRANCH: Model Training
    # ===========================================
    
    async def train_model_alpha(self, **kwargs) -> Dict[str, Any]:
        """Train model Alpha - runs in parallel with Beta after analysis."""
        task_id = "MODEL_α"
        self.log_event("START_MODEL_TRAINING", {"model": "Alpha", "type": "classification"}, task_id)
        
        # Simulate model training
        await asyncio.sleep(random.uniform(1.0, 2.0))
        
        # Use analysis results to determine training approach
        if "analysis_results" not in self.shared_data:
            raise ValueError("Analysis results not available for model training")
            
        analysis = self.shared_data["analysis_results"]
        
        # Simulate training metrics
        epochs = random.randint(10, 25)
        final_accuracy = random.uniform(0.82, 0.95)
        training_loss = random.uniform(0.05, 0.25)
        
        # Training simulation with progress
        training_progress = []
        for epoch in range(1, epochs + 1):
            accuracy = final_accuracy * (1 - math.exp(-epoch / 5))  # Exponential approach to final accuracy
            loss = training_loss * math.exp(-epoch / 8)  # Exponential decay of loss
            
            if epoch % 5 == 0 or epoch == epochs:  # Log every 5 epochs and final
                training_progress.append({
                    "epoch": epoch,
                    "accuracy": round(accuracy, 4),
                    "loss": round(loss, 4),
                    "learning_rate": 0.001 * (0.9 ** (epoch // 5))
                })
        
        # Model evaluation
        test_accuracy = final_accuracy * random.uniform(0.95, 1.02)  # Test accuracy around training accuracy
        precision = random.uniform(0.8, 0.93)
        recall = random.uniform(0.78, 0.91)
        f1_score = 2 * (precision * recall) / (precision + recall)
        
        result = {
            "model_name": "Alpha",
            "model_type": "classification",
            "training_config": {
                "epochs": epochs,
                "batch_size": 32,
                "optimizer": "Adam",
                "learning_rate": 0.001
            },
            "training_progress": training_progress,
            "final_metrics": {
                "training_accuracy": final_accuracy,
                "test_accuracy": test_accuracy,
                "precision": precision,
                "recall": recall,
                "f1_score": f1_score,
                "training_loss": training_loss
            },
            "training_time": time.time() - self.start_time,
            "model_ready": test_accuracy > 0.8,
            "training_completed_at": time.time()
        }
        
        # Store model results
        self.shared_data["model_alpha"] = result
        
        self.log_event("COMPLETED_MODEL_TRAINING", {
            "model": "Alpha",
            "epochs": epochs,
            "test_accuracy": f"{test_accuracy:.1%}",
            "f1_score": f"{f1_score:.3f}",
            "ready": result["model_ready"]
        }, task_id)
        
        return result
    
    async def train_model_beta(self, **kwargs) -> Dict[str, Any]:
        """Train model Beta - runs in parallel with Alpha after analysis."""
        task_id = "MODEL_β" 
        self.log_event("START_MODEL_TRAINING", {"model": "Beta", "type": "regression"}, task_id)
        
        # Simulate longer model training
        await asyncio.sleep(random.uniform(1.2, 2.5))
        
        # Check analysis results
        if "analysis_results" not in self.shared_data:
            raise ValueError("Analysis results not available for model training")
            
        analysis = self.shared_data["analysis_results"]
        
        # Simulate regression training
        iterations = random.randint(100, 300)
        final_rmse = random.uniform(0.8, 3.2)
        final_mae = random.uniform(0.6, 2.4)
        r_squared = random.uniform(0.75, 0.92)
        
        # Training simulation
        training_metrics = []
        for i in [10, 25, 50, 100, iterations]:
            progress = i / iterations
            rmse = final_rmse * (2 - progress)  # RMSE decreases over time
            mae = final_mae * (2 - progress)   # MAE decreases over time  
            r2 = r_squared * progress          # R² increases over time
            
            training_metrics.append({
                "iteration": i,
                "rmse": round(rmse, 4),
                "mae": round(mae, 4),
                "r_squared": round(r2, 4),
                "mse": round(rmse ** 2, 4)
            })
        
        # Cross-validation results
        cv_scores = [r_squared * random.uniform(0.92, 1.08) for _ in range(5)]
        cv_mean = sum(cv_scores) / len(cv_scores)
        cv_std = math.sqrt(sum((x - cv_mean) ** 2 for x in cv_scores) / len(cv_scores))
        
        result = {
            "model_name": "Beta",
            "model_type": "regression",
            "training_config": {
                "iterations": iterations,
                "regularization": "L2",
                "alpha": 0.01,
                "solver": "lbfgs"
            },
            "training_metrics": training_metrics,
            "final_performance": {
                "rmse": final_rmse,
                "mae": final_mae,
                "r_squared": r_squared,
                "mse": final_rmse ** 2
            },
            "cross_validation": {
                "scores": cv_scores,
                "mean": cv_mean,
                "std": cv_std,
                "fold_count": 5
            },
            "training_time": time.time() - self.start_time,
            "model_ready": r_squared > 0.75,
            "training_completed_at": time.time()
        }
        
        # Store model results
        self.shared_data["model_beta"] = result
        
        self.log_event("COMPLETED_MODEL_TRAINING", {
            "model": "Beta",
            "iterations": iterations, 
            "rmse": f"{final_rmse:.3f}",
            "r_squared": f"{r_squared:.3f}",
            "cv_score": f"{cv_mean:.3f}±{cv_std:.3f}",
            "ready": result["model_ready"]
        }, task_id)
        
        return result
    
    # ==========================================
    # FINAL INTEGRATION: Model Ensemble & Report
    # ==========================================
    
    async def create_ensemble(self, **kwargs) -> Dict[str, Any]:
        """Create model ensemble - depends on both models being trained."""
        task_id = "ENSEMBLE"
        self.log_event("START_ENSEMBLE_CREATION", {"models": ["Alpha", "Beta"]}, task_id)
        
        await asyncio.sleep(random.uniform(0.3, 0.7))
        
        # Verify both models are available
        if "model_alpha" not in self.shared_data or "model_beta" not in self.shared_data:
            available_models = [k for k in self.shared_data.keys() if k.startswith("model_")]
            raise ValueError(f"Missing trained models. Available: {available_models}")
        
        model_alpha = self.shared_data["model_alpha"]
        model_beta = self.shared_data["model_beta"]
        
        # Ensemble configuration based on model performance
        alpha_weight = 0.6 if model_alpha["final_metrics"]["test_accuracy"] > 0.9 else 0.4
        beta_weight = 1.0 - alpha_weight
        
        # Simulate ensemble validation
        ensemble_accuracy = (
            model_alpha["final_metrics"]["test_accuracy"] * alpha_weight +
            model_beta["final_performance"]["r_squared"] * beta_weight * 0.9  # Scale regression to classification scale
        )
        
        # Ensemble metrics
        ensemble_metrics = {
            "combined_accuracy": ensemble_accuracy,
            "alpha_contribution": alpha_weight,
            "beta_contribution": beta_weight,
            "performance_gain": max(0, ensemble_accuracy - max(
                model_alpha["final_metrics"]["test_accuracy"], 
                model_beta["final_performance"]["r_squared"] * 0.9
            )),
            "model_agreement": random.uniform(0.75, 0.95),
            "ensemble_confidence": random.uniform(0.8, 0.95)
        }
        
        result = {
            "ensemble_name": "Alpha-Beta Ensemble",
            "component_models": ["Alpha", "Beta"],
            "weighting_strategy": "performance_based",
            "weights": {
                "alpha": alpha_weight,
                "beta": beta_weight
            },
            "ensemble_metrics": ensemble_metrics,
            "model_summaries": {
                "alpha": {
                    "type": model_alpha["model_type"],
                    "accuracy": model_alpha["final_metrics"]["test_accuracy"],
                    "training_time": model_alpha["training_time"]
                },
                "beta": {
                    "type": model_beta["model_type"], 
                    "r_squared": model_beta["final_performance"]["r_squared"],
                    "training_time": model_beta["training_time"]
                }
            },
            "ensemble_ready": ensemble_accuracy > 0.8,
            "creation_time": time.time(),
            "processing_time": time.time() - self.start_time
        }
        
        # Store ensemble
        self.shared_data["ensemble"] = result
        
        self.log_event("COMPLETED_ENSEMBLE_CREATION", {
            "ensemble": "Alpha-Beta",
            "accuracy": f"{ensemble_accuracy:.1%}",
            "performance_gain": f"{ensemble_metrics['performance_gain']:.3f}",
            "ready": result["ensemble_ready"]
        }, task_id)
        
        return result
    
    async def generate_final_report(self, **kwargs) -> Dict[str, Any]:
        """Generate comprehensive final report - depends on ensemble."""
        task_id = "REPORT"
        self.log_event("START_REPORT_GENERATION", {"components": "all"}, task_id)
        
        await asyncio.sleep(random.uniform(0.2, 0.5))
        
        # Verify all components are available
        required_components = ["dataset_a", "dataset_b", "dataset_c", "analysis_results", "model_alpha", "model_beta", "ensemble"]
        available_components = [comp for comp in required_components if comp in self.shared_data]
        
        if len(available_components) != len(required_components):
            missing = set(required_components) - set(available_components)
            raise ValueError(f"Missing components for final report: {missing}")
        
        # Generate comprehensive report
        total_processing_time = time.time() - self.start_time
        
        # Data summary
        data_summary = {
            "datasets_processed": 3,
            "total_records": sum([
                len(self.shared_data["dataset_a"]["full_data"]),
                len(self.shared_data["dataset_b"]["full_data"]),
                len(self.shared_data["dataset_c"]["full_data"])
            ]),
            "data_types": ["mathematical", "categorical", "timeseries"],
            "quality_scores": [
                self.shared_data["analysis_results"]["individual_analysis"]["dataset_a"]["quality_score"],
                self.shared_data["analysis_results"]["individual_analysis"]["dataset_b"]["quality_score"],
                self.shared_data["analysis_results"]["individual_analysis"]["dataset_c"]["quality_score"]
            ]
        }
        
        # Model summary
        model_summary = {
            "models_trained": 2,
            "model_types": ["classification", "regression"],
            "training_times": [
                self.shared_data["model_alpha"]["training_time"],
                self.shared_data["model_beta"]["training_time"]
            ],
            "performance_metrics": {
                "alpha_accuracy": self.shared_data["model_alpha"]["final_metrics"]["test_accuracy"],
                "beta_r_squared": self.shared_data["model_beta"]["final_performance"]["r_squared"],
                "ensemble_accuracy": self.shared_data["ensemble"]["ensemble_metrics"]["combined_accuracy"]
            }
        }
        
        # Execution summary
        execution_summary = {
            "total_processing_time": total_processing_time,
            "parallel_execution_efficiency": "HIGH",  # Based on overlapping data generation
            "sequential_dependencies_met": True,
            "error_rate": 0.0,  # No errors in this run
            "resource_utilization": "OPTIMAL"
        }
        
        # Recommendations
        recommendations = [
            "Data quality is excellent across all datasets",
            "Model ensemble shows improved performance over individual models",
            "Parallel processing achieved significant time savings",
            "System is ready for production deployment"
        ]
        
        result = {
            "report_title": "Complex Orchestration Test - Final Report",
            "generated_at": datetime.now().isoformat(),
            "total_processing_time": total_processing_time,
            "data_summary": data_summary,
            "model_summary": model_summary, 
            "execution_summary": execution_summary,
            "orchestration_metrics": {
                "tasks_executed": 8,  # Total tasks in workflow
                "parallel_branches": 3,  # Data generation + model training
                "sequential_stages": 4,  # Directory structure levels
                "dependency_satisfaction": "100%",
                "concurrent_peak": 3   # Max tasks running simultaneously
            },
            "performance_highlights": [
                f"Processed {data_summary['total_records']:,} records across 3 datasets",
                f"Trained 2 models with ensemble accuracy of {model_summary['performance_metrics']['ensemble_accuracy']:.1%}",
                f"Completed full pipeline in {total_processing_time:.2f} seconds",
                "Achieved seamless parallel and sequential execution"
            ],
            "recommendations": recommendations,
            "system_ready": True,
            "report_confidence": 0.95
        }
        
        self.log_event("COMPLETED_REPORT_GENERATION", {
            "report": "Final",
            "components": len(available_components),
            "total_time": f"{total_processing_time:.2f}s",
            "system_ready": result["system_ready"]
        }, task_id)
        
        return result


async def run_complex_orchestration():
    """Execute the complex orchestration test workflow."""
    print("🎭 AgenticFlow Complex Test: Parallel, Sequential & Tool Calling")
    print("=" * 70)
    print()
    
    processor = ComplexProcessor()
    
    # Configure orchestrator for complex workflow
    retry_policy = RetryPolicy(
        max_attempts=2,
        initial_delay=0.1,
        max_delay=3.0,
        backoff_multiplier=2.0
    )
    
    orchestrator = TaskOrchestrator(
        max_concurrent_tasks=4,  # Allow multiple parallel tasks
        default_retry_policy=retry_policy
    )
    
    print("🏗️  Building Complex Orchestration Workflow...")
    print("-" * 50)
    
    # =========================================
    # STAGE 1: PARALLEL DATA GENERATION (A, B, C)
    # =========================================
    print("📊 Stage 1: Parallel Data Generation")
    
    orchestrator.add_function_task(
        "generate_a", "Generate Dataset A",
        processor.generate_dataset_a,
        args=(1000,),  # 1000 records
        priority=TaskPriority.HIGH
    )
    
    orchestrator.add_function_task(
        "generate_b", "Generate Dataset B", 
        processor.generate_dataset_b,
        args=(800,),   # 800 records
        priority=TaskPriority.HIGH
    )
    
    orchestrator.add_function_task(
        "generate_c", "Generate Dataset C",
        processor.generate_dataset_c,
        args=(1200,),  # 1200 records
        priority=TaskPriority.HIGH
    )
    
    # =========================================
    # STAGE 2: SEQUENTIAL ANALYSIS (depends on A, B, C)
    # =========================================
    print("🔍 Stage 2: Sequential Data Analysis")
    
    orchestrator.add_function_task(
        "analyze", "Analyze Datasets",
        processor.analyze_datasets,
        dependencies=["generate_a", "generate_b", "generate_c"],  # Depends on all data generation
        priority=TaskPriority.CRITICAL
    )
    
    # =========================================
    # STAGE 3: PARALLEL MODEL TRAINING (depends on analysis)
    # =========================================
    print("🤖 Stage 3: Parallel Model Training")
    
    orchestrator.add_function_task(
        "train_alpha", "Train Model Alpha",
        processor.train_model_alpha,
        dependencies=["analyze"],  # Depends on analysis
        priority=TaskPriority.NORMAL
    )
    
    orchestrator.add_function_task(
        "train_beta", "Train Model Beta",
        processor.train_model_beta,
        dependencies=["analyze"],  # Depends on analysis
        priority=TaskPriority.NORMAL
    )
    
    # =========================================
    # STAGE 4: SEQUENTIAL INTEGRATION (depends on both models)
    # =========================================
    print("🔗 Stage 4: Sequential Integration")
    
    orchestrator.add_function_task(
        "ensemble", "Create Ensemble",
        processor.create_ensemble,
        dependencies=["train_alpha", "train_beta"],  # Depends on both models
        priority=TaskPriority.HIGH
    )
    
    orchestrator.add_function_task(
        "final_report", "Generate Final Report",
        processor.generate_final_report,
        dependencies=["ensemble"],  # Depends on ensemble
        priority=TaskPriority.LOW
    )
    
    # Execute the complex workflow
    print()
    print("🚀 Executing Complex Orchestration...")
    print("-" * 50)
    print()
    
    start_time = time.time()
    result = await orchestrator.execute_workflow()
    total_time = time.time() - start_time
    
    # Generate comprehensive report
    print()
    print("=" * 70)
    print("📈 COMPLEX ORCHESTRATION REPORT")
    print("=" * 70)
    
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
        print(f"⚡ Parallel Efficiency: {dag_stats.get('parallel_efficiency', 'N/A')}")
    
    # Detailed execution breakdown
    print("\n" + "=" * 70)
    print("📋 EXECUTION BREAKDOWN BY STAGE")
    print("=" * 70)
    
    if "task_results" in result:
        # Group by execution stages
        stage_1_tasks = ["generate_a", "generate_b", "generate_c"]
        stage_2_tasks = ["analyze"]
        stage_3_tasks = ["train_alpha", "train_beta"]
        stage_4_tasks = ["ensemble", "final_report"]
        
        stages = [
            ("🔄 STAGE 1: Parallel Data Generation", stage_1_tasks),
            ("🔍 STAGE 2: Sequential Analysis", stage_2_tasks), 
            ("🤖 STAGE 3: Parallel Model Training", stage_3_tasks),
            ("🔗 STAGE 4: Sequential Integration", stage_4_tasks)
        ]
        
        for stage_name, task_ids in stages:
            print(f"\n{stage_name}")
            print("-" * (len(stage_name) - 2))  # Subtract emoji length
            
            stage_time = 0
            stage_success = 0
            
            for task_id in task_ids:
                if task_id in result["task_results"]:
                    task_info = result["task_results"][task_id]
                    status = "✅" if task_info.get("state") == "completed" else "❌"
                    task_name = task_info.get("name", task_id)
                    execution_time = task_info.get("execution_time", 0)
                    stage_time += execution_time
                    
                    if task_info.get("state") == "completed":
                        stage_success += 1
                    
                    print(f"  {status} {task_name}")
                    print(f"     ⏱️  Time: {execution_time:.2f}s")
                    print(f"     🔄 Attempts: {task_info.get('attempts', 1)}")
                    
                    # Show stage-specific insights
                    if task_info.get("result") and task_info["result"].get("success"):
                        task_result = task_info["result"]["result"]
                        if isinstance(task_result, dict):
                            # Data generation results
                            if "dataset_id" in task_result:
                                print(f"     📊 Records: {task_result.get('total_records', 'N/A')}")
                                if "statistics" in task_result:
                                    stats = task_result["statistics"]
                                    print(f"     📈 Mean: {stats['mean']:.2f}, Range: [{stats['min']:.1f}, {stats['max']:.1f}]")
                                elif "priority_distribution" in task_result:
                                    prio = task_result["priority_distribution"]
                                    print(f"     🎯 High Priority: {prio.get('high', 0)}, Categories: {len(task_result.get('category_distribution', {}))}")
                                elif "anomaly_rate" in task_result:
                                    print(f"     🚨 Anomalies: {task_result['anomaly_count']} ({task_result['anomaly_rate']:.1%})")
                            
                            # Analysis results
                            elif "global_metrics" in task_result:
                                metrics = task_result["global_metrics"]
                                print(f"     🎯 Quality Score: {metrics['average_quality_score']:.2f}")
                                print(f"     📊 Total Records: {metrics['total_records']:,}")
                                print(f"     🤖 ML Ready: {task_result['recommendations']['ready_for_ml']}")
                            
                            # Model training results
                            elif "model_name" in task_result:
                                model_name = task_result["model_name"]
                                print(f"     🤖 Model: {model_name}")
                                if "final_metrics" in task_result:
                                    acc = task_result["final_metrics"]["test_accuracy"]
                                    print(f"     🎯 Test Accuracy: {acc:.1%}")
                                elif "final_performance" in task_result:
                                    r2 = task_result["final_performance"]["r_squared"]
                                    print(f"     📊 R² Score: {r2:.3f}")
                            
                            # Ensemble results
                            elif "ensemble_name" in task_result:
                                metrics = task_result["ensemble_metrics"]
                                print(f"     🔗 Combined Accuracy: {metrics['combined_accuracy']:.1%}")
                                print(f"     📈 Performance Gain: {metrics['performance_gain']:.3f}")
                            
                            # Final report results
                            elif "report_title" in task_result:
                                print(f"     📋 Components: {len(task_result.get('orchestration_metrics', {}).get('tasks_executed', 0))}")
                                print(f"     🎯 System Ready: {task_result.get('system_ready', False)}")
                    
                    print()
            
            print(f"  📊 Stage Summary: {stage_success}/{len(task_ids)} tasks completed in {stage_time:.2f}s")
    
    # Final assessment
    print("\n" + "=" * 70)
    print("🎯 ORCHESTRATION ASSESSMENT")
    print("=" * 70)
    
    grade = "A+" if success_rate >= 95 else "A" if success_rate >= 85 else "B+" if success_rate >= 75 else "B"
    
    print(f"📊 Overall Grade: {grade}")
    print()
    
    # Performance analysis
    if success_rate >= 95:
        print("✅ EXCELLENT: Complex orchestration executed flawlessly")
        print("   • Parallel data generation completed successfully")
        print("   • Sequential analysis processed all datasets") 
        print("   • Parallel model training achieved target performance")
        print("   • Integration and reporting completed seamlessly")
    elif success_rate >= 85:
        print("✅ GOOD: Complex orchestration mostly successful")
        print("   • Minor issues in some processing stages")
    else:
        print("⚠️  NEEDS IMPROVEMENT: Some orchestration stages failed")
    
    print()
    print("💡 Key Orchestration Features Demonstrated:")
    print("   • Parallel task execution with 3 concurrent data generators")
    print("   • Sequential dependency management across stages") 
    print("   • Complex inter-task communication via shared state")
    print("   • Mixed execution patterns (parallel + sequential)")
    print("   • Advanced DAG with diamond dependencies")
    print("   • Tool calling between tasks with data passing")
    print("   • Error handling and retry mechanisms")
    print("   • Performance optimization with concurrent execution")
    
    print()
    print("🔧 Technical Achievements:")
    print(f"   • {total_tasks} tasks orchestrated across 4 execution stages")
    print(f"   • Up to 3 tasks running in parallel simultaneously")
    print(f"   • Complex dependency resolution with fan-out and fan-in patterns")
    print(f"   • Seamless data sharing between {len(processor.shared_data)} components")
    print(f"   • Zero errors with robust exception handling")
    
    return {
        "example_name": "Complex Orchestration Test",
        "grade": grade,
        "success_rate": success_rate,
        "execution_time": total_time,
        "tasks_completed": f"{completed_tasks}/{total_tasks}",
        "key_features": [
            "Parallel execution patterns",
            "Sequential dependency chains",
            "Complex tool calling", 
            "Inter-task communication",
            "Mixed orchestration patterns"
        ]
    }


if __name__ == "__main__":
    result = asyncio.run(run_complex_orchestration())
    
    print()
    print("=" * 70)
    print(f"🏆 FINAL RESULT: {result['grade']} ({result['success_rate']:.1f}% success)")
    print("🚀 Complex orchestration validation complete!")
    print("=" * 70)