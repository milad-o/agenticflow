#!/usr/bin/env python3
"""
Realistic Example 2: Content Management Workflow
===============================================

This example demonstrates a comprehensive content management and publishing workflow:
- Content creation and authoring
- Editorial review and approval
- SEO optimization and metadata generation
- Multi-channel publishing
- Analytics and performance tracking

This showcases real-world digital content operations and publishing pipelines.
"""

import asyncio
import time
import random
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any

import sys
sys.path.append('/Users/miladolad/OneDrive/Work Projects/ma_system/agenticflow/src')

from agenticflow.orchestration.task_orchestrator import TaskOrchestrator
from agenticflow.orchestration.task_management import RetryPolicy, TaskPriority


class ContentWorkflow:
    """Realistic content management and publishing workflow."""
    
    def __init__(self):
        self.start_time = time.time()
        self.content_database = {}
        
    def log_event(self, stage: str, details: Dict[str, Any]):
        elapsed = time.time() - self.start_time
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {stage}: {details}")
        
    async def create_content(self, content_type: str = "article", topic: str = "technology", **kwargs) -> Dict[str, Any]:
        """Simulate content creation process."""
        self.log_event("CONTENT_CREATION", {"type": content_type, "topic": topic})
        
        # Simulate content creation time based on type
        creation_time = {
            "article": random.uniform(1.0, 2.5),
            "blog_post": random.uniform(0.8, 1.8),
            "video_script": random.uniform(1.5, 3.0),
            "social_media": random.uniform(0.3, 0.8)
        }.get(content_type, 1.5)
        
        await asyncio.sleep(creation_time)
        
        # Generate realistic content metadata
        content_titles = {
            "technology": ["AI Revolution in Enterprise", "Future of Cloud Computing", "Cybersecurity Trends 2024"],
            "business": ["Digital Transformation Guide", "Remote Work Strategies", "Market Analysis Q4"],
            "lifestyle": ["Wellness in Modern Life", "Sustainable Living Tips", "Work-Life Balance"]
        }
        
        title = random.choice(content_titles.get(topic, ["Generic Content Title"]))
        word_count = random.randint(800, 2500)
        
        content_data = {
            "id": f"CONTENT_{int(time.time()*1000)}",
            "title": title,
            "type": content_type,
            "topic": topic,
            "word_count": word_count,
            "author": random.choice(["Sarah Johnson", "Mike Chen", "Elena Rodriguez", "David Kim"]),
            "created_at": datetime.now(),
            "status": "draft",
            "content_quality_score": random.uniform(0.75, 0.95),
            "reading_time": word_count // 200,  # ~200 words per minute
            "content_summary": f"Comprehensive {topic} content covering key industry insights"
        }
        
        result = {
            "content": content_data,
            "creation_time": creation_time,
            "word_count": word_count,
            "initial_quality": content_data["content_quality_score"],
            "status": "created"
        }
        
        self.log_event("CREATION_COMPLETE", {
            "title": title,
            "type": content_type,
            "word_count": word_count,
            "author": content_data["author"],
            "quality_score": content_data["content_quality_score"]
        })
        
        return result
    
    async def editorial_review(self, review_type: str = "comprehensive", **kwargs) -> Dict[str, Any]:
        """Simulate editorial review and approval process."""
        self.log_event("EDITORIAL_REVIEW", {"type": review_type, "stage": "starting"})
        
        await asyncio.sleep(random.uniform(1.2, 2.8))
        
        # Extract content from context
        content_data = None
        for key, value in kwargs.items():
            if key.endswith('_result') and isinstance(value, dict) and 'content' in value:
                content_data = value['content']
                break
        
        if not content_data:
            raise ValueError("No content data found for editorial review")
        
        # Simulate editorial review process
        review_categories = {
            "grammar_spelling": random.uniform(0.85, 0.98),
            "clarity_readability": random.uniform(0.80, 0.95),
            "factual_accuracy": random.uniform(0.88, 0.97),
            "brand_alignment": random.uniform(0.82, 0.94),
            "audience_relevance": random.uniform(0.78, 0.92)
        }
        
        overall_score = sum(review_categories.values()) / len(review_categories)
        
        # Editorial feedback and improvements
        improvements_made = []
        if review_categories["grammar_spelling"] < 0.90:
            improvements_made.append("Grammar and spelling corrections")
        if review_categories["clarity_readability"] < 0.85:
            improvements_made.append("Clarity and readability enhancements")
        if review_categories["factual_accuracy"] < 0.92:
            improvements_made.append("Fact-checking and source verification")
        
        # Approval decision
        approved = overall_score >= 0.85
        
        result = {
            "content_id": content_data["id"],
            "review_type": review_type,
            "reviewer": random.choice(["Chief Editor", "Senior Editor", "Content Manager"]),
            "review_scores": review_categories,
            "overall_score": overall_score,
            "approved": approved,
            "improvements_made": improvements_made,
            "review_time": time.time(),
            "feedback": "Content meets editorial standards" if approved else "Requires revisions",
            "revised_content": {**content_data, "status": "approved" if approved else "revision_needed"}
        }
        
        self.log_event("REVIEW_COMPLETE", {
            "content_id": content_data["id"],
            "reviewer": result["reviewer"],
            "overall_score": overall_score,
            "approved": approved,
            "improvements": len(improvements_made)
        })
        
        return result
    
    async def seo_optimization(self, optimization_level: str = "advanced", **kwargs) -> Dict[str, Any]:
        """Perform SEO optimization and metadata generation."""
        self.log_event("SEO_OPTIMIZATION", {"level": optimization_level, "stage": "starting"})
        
        await asyncio.sleep(random.uniform(0.8, 1.8))
        
        # Extract content from context
        content_data = None
        for key, value in kwargs.items():
            if key.endswith('_result') and isinstance(value, dict):
                if 'revised_content' in value:
                    content_data = value['revised_content']
                elif 'content' in value:
                    content_data = value['content']
        
        if not content_data:
            raise ValueError("No content data found for SEO optimization")
        
        # Generate SEO-optimized metadata
        keywords = [
            "digital transformation", "enterprise technology", "business innovation",
            "cloud computing", "artificial intelligence", "data analytics",
            "cybersecurity", "automation", "machine learning"
        ]
        
        selected_keywords = random.sample(keywords, random.randint(3, 6))
        
        seo_metadata = {
            "primary_keyword": selected_keywords[0],
            "secondary_keywords": selected_keywords[1:],
            "meta_title": f"{content_data['title']} - Expert Insights",
            "meta_description": f"Discover {content_data['topic']} insights and strategies. {content_data['content_summary'][:100]}...",
            "slug": content_data['title'].lower().replace(" ", "-").replace(",", ""),
            "canonical_url": f"https://example.com/insights/{content_data['id']}",
            "schema_markup": "Article",
            "social_media_tags": {
                "og_title": content_data['title'],
                "og_description": content_data['content_summary'],
                "twitter_card": "summary_large_image"
            }
        }
        
        # SEO performance predictions
        seo_scores = {
            "keyword_density": random.uniform(1.5, 3.5),  # Percentage
            "readability_score": random.uniform(65, 85),   # Flesch reading ease
            "title_optimization": random.uniform(0.80, 0.95),
            "meta_description_quality": random.uniform(0.75, 0.92),
            "internal_link_potential": random.randint(3, 8),
            "estimated_seo_rank": random.randint(15, 45)   # Expected Google ranking
        }
        
        result = {
            "content_id": content_data["id"],
            "optimization_level": optimization_level,
            "seo_metadata": seo_metadata,
            "seo_scores": seo_scores,
            "keywords_targeted": len(selected_keywords),
            "optimization_time": time.time(),
            "seo_ready": seo_scores["title_optimization"] > 0.85,
            "optimized_content": {**content_data, "seo_metadata": seo_metadata, "status": "seo_optimized"}
        }
        
        self.log_event("SEO_COMPLETE", {
            "content_id": content_data["id"],
            "primary_keyword": seo_metadata["primary_keyword"],
            "keywords_count": len(selected_keywords),
            "readability_score": seo_scores["readability_score"],
            "estimated_rank": seo_scores["estimated_seo_rank"]
        })
        
        return result
    
    async def publish_to_channels(self, channels: str = "multi-channel", **kwargs) -> Dict[str, Any]:
        """Publish content to multiple channels and platforms."""
        self.log_event("MULTI_CHANNEL_PUBLISHING", {"channels": channels, "stage": "starting"})
        
        await asyncio.sleep(random.uniform(1.0, 2.5))
        
        # Extract optimized content
        content_data = None
        for key, value in kwargs.items():
            if key.endswith('_result') and isinstance(value, dict):
                if 'optimized_content' in value:
                    content_data = value['optimized_content']
        
        if not content_data:
            raise ValueError("No optimized content found for publishing")
        
        # Define publishing channels
        publishing_channels = {
            "company_website": {
                "status": "published" if random.random() > 0.05 else "failed",
                "publish_time": time.time(),
                "url": f"https://company.com/blog/{content_data['id']}",
                "estimated_reach": random.randint(1500, 8000)
            },
            "linkedin": {
                "status": "published" if random.random() > 0.08 else "failed",
                "publish_time": time.time(),
                "post_id": f"LI_{random.randint(100000, 999999)}",
                "estimated_reach": random.randint(500, 3000)
            },
            "twitter": {
                "status": "published" if random.random() > 0.10 else "failed",
                "publish_time": time.time(),
                "tweet_id": f"TW_{random.randint(1000000, 9999999)}",
                "estimated_reach": random.randint(200, 1500)
            },
            "newsletter": {
                "status": "scheduled" if random.random() > 0.03 else "failed",
                "scheduled_time": time.time() + 3600,  # 1 hour later
                "subscriber_count": random.randint(5000, 25000)
            }
        }
        
        # Calculate success metrics
        successful_channels = [ch for ch, data in publishing_channels.items() if data["status"] in ["published", "scheduled"]]
        total_estimated_reach = sum(data.get("estimated_reach", 0) for data in publishing_channels.values())
        
        # Content performance predictions
        performance_predictions = {
            "estimated_views": random.randint(2000, 15000),
            "estimated_engagement_rate": random.uniform(0.02, 0.08),
            "estimated_shares": random.randint(50, 500),
            "seo_impact_timeline": "2-4 weeks",
            "expected_conversions": random.randint(10, 100)
        }
        
        result = {
            "content_id": content_data["id"],
            "publishing_channels": publishing_channels,
            "successful_channels": len(successful_channels),
            "total_channels": len(publishing_channels),
            "success_rate": len(successful_channels) / len(publishing_channels),
            "total_estimated_reach": total_estimated_reach,
            "performance_predictions": performance_predictions,
            "publishing_time": time.time(),
            "status": "live",
            "published_content": {**content_data, "status": "published", "channels": successful_channels}
        }
        
        self.log_event("PUBLISHING_COMPLETE", {
            "content_id": content_data["id"],
            "successful_channels": len(successful_channels),
            "total_channels": len(publishing_channels),
            "estimated_reach": total_estimated_reach,
            "performance_prediction": f"{performance_predictions['estimated_views']:,} views"
        })
        
        return result
    
    async def track_analytics(self, tracking_period: str = "initial", **kwargs) -> Dict[str, Any]:
        """Track and analyze content performance."""
        self.log_event("ANALYTICS_TRACKING", {"period": tracking_period, "stage": "starting"})
        
        await asyncio.sleep(random.uniform(0.5, 1.2))
        
        # Extract published content
        published_data = None
        for key, value in kwargs.items():
            if key.endswith('_result') and isinstance(value, dict):
                if 'published_content' in value:
                    published_data = value
                    break
        
        if not published_data:
            raise ValueError("No published content data found for analytics")
        
        # Simulate realistic analytics data
        content_id = published_data['published_content']['id']
        
        # Generate performance metrics based on predictions
        predicted_views = published_data['performance_predictions']['estimated_views']
        actual_performance = {
            "total_views": int(predicted_views * random.uniform(0.7, 1.3)),
            "unique_visitors": int(predicted_views * random.uniform(0.6, 0.9)),
            "bounce_rate": random.uniform(0.35, 0.65),
            "avg_time_on_page": random.uniform(120, 480),  # seconds
            "social_shares": int(published_data['performance_predictions']['estimated_shares'] * random.uniform(0.8, 1.2)),
            "comments": random.randint(5, 50),
            "conversions": random.randint(8, 75)
        }
        
        # Channel-specific analytics
        channel_analytics = {}
        for channel in published_data['successful_channels']:
            channel_analytics[channel] = {
                "views": random.randint(100, 2000),
                "engagement_rate": random.uniform(0.01, 0.12),
                "click_through_rate": random.uniform(0.005, 0.035),
                "conversion_rate": random.uniform(0.001, 0.015)
            }
        
        # SEO performance
        seo_performance = {
            "search_impressions": random.randint(500, 5000),
            "search_clicks": random.randint(50, 800),
            "average_position": random.uniform(15, 55),
            "keyword_rankings": {
                "primary_keyword": random.randint(8, 45),
                "secondary_keywords_avg": random.randint(25, 75)
            }
        }
        
        # Performance assessment
        performance_score = (
            min(actual_performance["total_views"] / predicted_views, 1.2) * 0.3 +
            (1 - actual_performance["bounce_rate"]) * 0.2 +
            min(actual_performance["social_shares"] / 100, 1.0) * 0.2 +
            min(seo_performance["search_clicks"] / 500, 1.0) * 0.3
        )
        
        result = {
            "content_id": content_id,
            "tracking_period": tracking_period,
            "actual_performance": actual_performance,
            "channel_analytics": channel_analytics,
            "seo_performance": seo_performance,
            "performance_score": performance_score,
            "tracking_time": time.time(),
            "insights": {
                "top_performing_channel": max(channel_analytics.keys(), key=lambda x: channel_analytics[x]["views"]) if channel_analytics else "N/A",
                "engagement_quality": "high" if actual_performance["avg_time_on_page"] > 300 else "medium",
                "seo_trend": "improving" if seo_performance["average_position"] < 30 else "stable",
                "conversion_effectiveness": "excellent" if actual_performance["conversions"] > 50 else "good"
            }
        }
        
        self.log_event("ANALYTICS_COMPLETE", {
            "content_id": content_id,
            "total_views": actual_performance["total_views"],
            "performance_score": performance_score,
            "top_channel": result["insights"]["top_performing_channel"],
            "seo_position": seo_performance["average_position"]
        })
        
        return result


async def run_content_workflow():
    """Execute the complete content management workflow."""
    print("📝 AgenticFlow Realistic Example 2: Content Management Workflow")
    print("=" * 68)
    print()
    
    workflow = ContentWorkflow()
    
    # Configure orchestrator for content workflow
    retry_policy = RetryPolicy(
        max_attempts=3,
        initial_delay=0.3,
        max_delay=5.0,
        backoff_multiplier=1.8
    )
    
    orchestrator = TaskOrchestrator(
        max_concurrent_tasks=4,
        default_retry_policy=retry_policy
    )
    
    print("📋 Building Content Management Workflow...")
    print("-" * 45)
    
    # Stage 1: Content Creation
    orchestrator.add_function_task(
        "create_content", "Create Content",
        workflow.create_content,
        args=("article", "technology"),
        priority=TaskPriority.HIGH
    )
    
    # Stage 2: Editorial Review (depends on creation)
    orchestrator.add_function_task(
        "editorial_review", "Editorial Review",
        workflow.editorial_review,
        args=("comprehensive",),
        dependencies=["create_content"],
        priority=TaskPriority.HIGH
    )
    
    # Stage 3: SEO Optimization (depends on review)
    orchestrator.add_function_task(
        "seo_optimization", "SEO Optimization",
        workflow.seo_optimization,
        args=("advanced",),
        dependencies=["editorial_review"],
        priority=TaskPriority.NORMAL
    )
    
    # Stage 4: Multi-Channel Publishing (depends on SEO)
    orchestrator.add_function_task(
        "publish_content", "Multi-Channel Publishing",
        workflow.publish_to_channels,
        args=("multi-channel",),
        dependencies=["seo_optimization"],
        priority=TaskPriority.CRITICAL
    )
    
    # Stage 5: Analytics Tracking (depends on publishing)
    orchestrator.add_function_task(
        "track_analytics", "Analytics Tracking",
        workflow.track_analytics,
        args=("initial",),
        dependencies=["publish_content"],
        priority=TaskPriority.NORMAL
    )
    
    # Execute the workflow
    print("🚀 Executing Content Management Workflow...")
    print("-" * 45)
    
    start_time = time.time()
    result = await orchestrator.execute_workflow()
    total_time = time.time() - start_time
    
    # Generate comprehensive report
    print()
    print("=" * 68)
    print("📊 CONTENT WORKFLOW REPORT")
    print("=" * 68)
    
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
    
    # Detailed workflow analysis
    print("\n" + "-" * 68)
    print("📋 CONTENT WORKFLOW BREAKDOWN")
    print("-" * 68)
    
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
                    # Show stage-specific metrics
                    if "content" in task_result:
                        content = task_result["content"]
                        print(f"   📝 Content: {content.get('title', 'N/A')}")
                        print(f"   📊 Word Count: {content.get('word_count', 0):,}")
                    elif "overall_score" in task_result:
                        print(f"   🎯 Review Score: {task_result['overall_score']:.1%}")
                        print(f"   ✅ Approved: {task_result['approved']}")
                    elif "seo_scores" in task_result:
                        seo_scores = task_result["seo_scores"]
                        print(f"   🔍 SEO Rank: {seo_scores.get('estimated_seo_rank', 'N/A')}")
                        print(f"   📖 Readability: {seo_scores.get('readability_score', 0):.1f}")
                    elif "successful_channels" in task_result:
                        print(f"   📢 Channels: {task_result['successful_channels']}/{task_result['total_channels']}")
                        print(f"   👥 Est. Reach: {task_result.get('total_estimated_reach', 0):,}")
                    elif "performance_score" in task_result:
                        perf = task_result["actual_performance"]
                        print(f"   📈 Views: {perf.get('total_views', 0):,}")
                        print(f"   💯 Score: {task_result['performance_score']:.2f}")
            print()
    
    # Final Assessment
    print("-" * 68)
    print("🎯 WORKFLOW ASSESSMENT")
    print("-" * 68)
    
    grade = "A+" if success_rate >= 95 else "A" if success_rate >= 85 else "B+" if success_rate >= 75 else "B"
    
    print(f"📊 Overall Grade: {grade}")
    print()
    
    # Performance Analysis
    if success_rate >= 95:
        print("✅ EXCELLENT: Content workflow executed flawlessly")
        print("   • Content created and reviewed to high standards")
        print("   • SEO optimization completed successfully")  
        print("   • Multi-channel publishing achieved")
        print("   • Analytics tracking providing valuable insights")
    elif success_rate >= 85:
        print("✅ GOOD: Content workflow mostly successful")
        print("   • Minor issues in some stages, overall solid execution")
    else:
        print("⚠️  NEEDS IMPROVEMENT: Some workflow stages encountered issues")
    
    print()
    print("💡 Key Achievements:")
    print("   • End-to-end content creation and publishing")
    print("   • Comprehensive editorial review and approval process")
    print("   • Advanced SEO optimization with metadata generation")
    print("   • Multi-channel publishing across platforms")
    print("   • Real-time analytics and performance tracking")
    
    print()
    print("🔧 Technical Highlights:")
    print(f"   • {total_tasks} stages in sequential content pipeline")
    print(f"   • Dependency-based workflow execution")
    print(f"   • Realistic content processing times")
    print(f"   • Multi-platform publishing coordination")
    print(f"   • Comprehensive performance analytics")
    
    return {
        "example_name": "Content Management Workflow",
        "grade": grade,
        "success_rate": success_rate,
        "execution_time": total_time,
        "tasks_completed": f"{completed_tasks}/{total_tasks}",
        "key_features": [
            "Content creation & authoring",
            "Editorial review & approval",
            "SEO optimization",
            "Multi-channel publishing",
            "Analytics tracking"
        ]
    }


if __name__ == "__main__":
    result = asyncio.run(run_content_workflow())
    
    print()
    print("=" * 68)
    print(f"🏆 FINAL RESULT: {result['grade']} ({result['success_rate']:.1f}% success)")
    print("🚀 Content Management Workflow validation complete!")
    print("=" * 68)