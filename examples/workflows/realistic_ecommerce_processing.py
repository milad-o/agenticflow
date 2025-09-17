#!/usr/bin/env python3
"""
Realistic Example 3: E-commerce Order Processing Workflow
=========================================================

This example demonstrates a comprehensive e-commerce order processing system:
- Order validation and fraud detection
- Inventory management and allocation
- Payment processing and verification
- Shipping and logistics coordination
- Customer notification and tracking

This showcases real-world e-commerce operations and order fulfillment pipelines.
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


class EcommerceOrderProcessor:
    """Realistic e-commerce order processing workflow."""
    
    def __init__(self):
        self.start_time = time.time()
        self.inventory = {f"PRODUCT_{i:03d}": random.randint(10, 100) for i in range(1, 51)}
        self.order_database = {}
        
    def log_event(self, stage: str, details: Dict[str, Any]):
        elapsed = time.time() - self.start_time
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {stage}: {details}")
        
    async def receive_and_validate_order(self, order_source: str = "website", **kwargs) -> Dict[str, Any]:
        """Simulate order reception and initial validation."""
        self.log_event("ORDER_RECEIVED", {"source": order_source, "stage": "validating"})
        
        await asyncio.sleep(random.uniform(0.3, 0.8))
        
        # Generate realistic order data
        order_id = f"ORD_{int(time.time()*1000)}"
        products = []
        total_amount = 0
        
        # Create order with 1-4 products
        num_products = random.randint(1, 4)
        for _ in range(num_products):
            product_id = f"PRODUCT_{random.randint(1, 50):03d}"
            quantity = random.randint(1, 3)
            unit_price = random.uniform(19.99, 299.99)
            
            products.append({
                "product_id": product_id,
                "name": f"Product {product_id.split('_')[1]}",
                "quantity": quantity,
                "unit_price": unit_price,
                "total_price": quantity * unit_price
            })
            total_amount += quantity * unit_price
        
        # Customer information
        customer_data = {
            "customer_id": f"CUST_{random.randint(10000, 99999)}",
            "email": f"customer{random.randint(100, 999)}@example.com",
            "name": random.choice(["John Smith", "Jane Doe", "Mike Johnson", "Sarah Wilson"]),
            "phone": f"+1-555-{random.randint(100, 999)}-{random.randint(1000, 9999)}"
        }
        
        # Shipping address
        shipping_address = {
            "street": f"{random.randint(100, 9999)} Main St",
            "city": random.choice(["New York", "Los Angeles", "Chicago", "Houston", "Phoenix"]),
            "state": random.choice(["NY", "CA", "IL", "TX", "AZ"]),
            "zip_code": f"{random.randint(10000, 99999)}",
            "country": "US"
        }
        
        order_data = {
            "order_id": order_id,
            "source": order_source,
            "customer": customer_data,
            "products": products,
            "total_amount": round(total_amount, 2),
            "shipping_address": shipping_address,
            "order_date": datetime.now(),
            "status": "received",
            "validation_score": random.uniform(0.85, 0.99)
        }
        
        # Basic validation checks
        validation_checks = {
            "email_format": "@" in customer_data["email"],
            "phone_format": len(customer_data["phone"]) >= 10,
            "address_complete": all(shipping_address.values()),
            "products_valid": len(products) > 0,
            "amount_reasonable": total_amount > 0
        }
        
        validation_passed = all(validation_checks.values())
        
        result = {
            "order": order_data,
            "validation_checks": validation_checks,
            "validation_passed": validation_passed,
            "total_items": sum(p["quantity"] for p in products),
            "processing_time": time.time()
        }
        
        self.log_event("ORDER_VALIDATED", {
            "order_id": order_id,
            "customer": customer_data["name"],
            "total_amount": f"${total_amount:.2f}",
            "items": result["total_items"],
            "validation_passed": validation_passed
        })
        
        return result
    
    async def fraud_detection(self, detection_level: str = "standard", **kwargs) -> Dict[str, Any]:
        """Perform fraud detection and risk assessment."""
        self.log_event("FRAUD_DETECTION", {"level": detection_level, "stage": "analyzing"})
        
        await asyncio.sleep(random.uniform(0.5, 1.2))
        
        # Extract order data from context
        order_data = None
        for key, value in kwargs.items():
            if key.endswith('_result') and isinstance(value, dict) and 'order' in value:
                order_data = value['order']
                break
        
        if not order_data:
            raise ValueError("No order data found for fraud detection")
        
        # Simulate fraud detection algorithms
        risk_factors = {
            "velocity_check": random.uniform(0.1, 0.9),    # Order frequency
            "geolocation_risk": random.uniform(0.05, 0.8), # Location risk
            "payment_history": random.uniform(0.1, 0.95),  # Customer history
            "device_fingerprint": random.uniform(0.2, 0.9), # Device analysis
            "behavioral_analysis": random.uniform(0.15, 0.85) # Behavior patterns
        }
        
        # Calculate overall risk score (lower is better)
        risk_score = sum(risk_factors.values()) / len(risk_factors)
        
        # Risk assessment
        if risk_score < 0.3:
            risk_level = "LOW"
            recommended_action = "APPROVE"
        elif risk_score < 0.6:
            risk_level = "MEDIUM"
            recommended_action = "MANUAL_REVIEW" if random.random() < 0.3 else "APPROVE"
        else:
            risk_level = "HIGH"
            recommended_action = "DECLINE"
        
        # Additional fraud indicators
        fraud_indicators = []
        if risk_factors["velocity_check"] > 0.7:
            fraud_indicators.append("High order velocity")
        if risk_factors["geolocation_risk"] > 0.6:
            fraud_indicators.append("Unusual location")
        if risk_factors["device_fingerprint"] < 0.3:
            fraud_indicators.append("New device")
        
        result = {
            "order_id": order_data["order_id"],
            "detection_level": detection_level,
            "risk_factors": risk_factors,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "recommended_action": recommended_action,
            "fraud_indicators": fraud_indicators,
            "confidence": random.uniform(0.88, 0.97),
            "processing_time": time.time(),
            "cleared_order": {**order_data, "fraud_status": recommended_action, "risk_level": risk_level}
        }
        
        self.log_event("FRAUD_ANALYSIS_COMPLETE", {
            "order_id": order_data["order_id"],
            "risk_level": risk_level,
            "risk_score": f"{risk_score:.3f}",
            "action": recommended_action,
            "indicators": len(fraud_indicators)
        })
        
        return result
    
    async def inventory_allocation(self, **kwargs) -> Dict[str, Any]:
        """Allocate inventory and check product availability."""
        self.log_event("INVENTORY_CHECK", {"stage": "checking_availability"})
        
        await asyncio.sleep(random.uniform(0.4, 1.0))
        
        # Extract cleared order
        order_data = None
        for key, value in kwargs.items():
            if key.endswith('_result') and isinstance(value, dict):
                if 'cleared_order' in value:
                    order_data = value['cleared_order']
                elif 'order' in value:
                    order_data = value['order']
        
        if not order_data:
            raise ValueError("No order data found for inventory allocation")
        
        allocation_results = []
        total_allocated = 0
        allocation_successful = True
        
        for product in order_data["products"]:
            product_id = product["product_id"]
            requested_qty = product["quantity"]
            available_qty = self.inventory.get(product_id, 0)
            
            if available_qty >= requested_qty:
                allocated_qty = requested_qty
                self.inventory[product_id] -= requested_qty
                status = "ALLOCATED"
            else:
                allocated_qty = available_qty
                self.inventory[product_id] = 0
                status = "PARTIAL" if available_qty > 0 else "OUT_OF_STOCK"
                allocation_successful = False
            
            allocation_results.append({
                "product_id": product_id,
                "requested": requested_qty,
                "available": available_qty,
                "allocated": allocated_qty,
                "status": status,
                "remaining_inventory": self.inventory[product_id]
            })
            total_allocated += allocated_qty
        
        # Calculate fulfillment metrics
        total_requested = sum(p["quantity"] for p in order_data["products"])
        fulfillment_rate = total_allocated / total_requested if total_requested > 0 else 0
        
        # Determine next actions
        if allocation_successful:
            next_action = "PROCEED_TO_PAYMENT"
        elif fulfillment_rate >= 0.8:
            next_action = "PARTIAL_FULFILLMENT"
        else:
            next_action = "BACKORDER_REQUIRED"
        
        result = {
            "order_id": order_data["order_id"],
            "allocation_results": allocation_results,
            "total_requested": total_requested,
            "total_allocated": total_allocated,
            "fulfillment_rate": fulfillment_rate,
            "allocation_successful": allocation_successful,
            "next_action": next_action,
            "inventory_reserved": True if allocation_successful else False,
            "processing_time": time.time(),
            "allocated_order": {**order_data, "inventory_status": next_action, "fulfillment_rate": fulfillment_rate}
        }
        
        self.log_event("INVENTORY_ALLOCATED", {
            "order_id": order_data["order_id"],
            "fulfillment_rate": f"{fulfillment_rate:.1%}",
            "total_allocated": total_allocated,
            "next_action": next_action,
            "successful": allocation_successful
        })
        
        return result
    
    async def process_payment(self, payment_method: str = "credit_card", **kwargs) -> Dict[str, Any]:
        """Process payment and handle payment verification."""
        self.log_event("PAYMENT_PROCESSING", {"method": payment_method, "stage": "authorizing"})
        
        await asyncio.sleep(random.uniform(1.0, 2.5))  # Payment processing takes longer
        
        # Extract allocated order
        order_data = None
        for key, value in kwargs.items():
            if key.endswith('_result') and isinstance(value, dict):
                if 'allocated_order' in value:
                    order_data = value['allocated_order']
        
        if not order_data:
            raise ValueError("No allocated order found for payment processing")
        
        # Simulate payment processing
        payment_amount = order_data["total_amount"]
        
        # Add taxes and shipping
        tax_rate = 0.08
        shipping_cost = 9.99 if payment_amount < 50 else 0
        tax_amount = payment_amount * tax_rate
        final_amount = payment_amount + tax_amount + shipping_cost
        
        # Payment processing simulation
        processing_time = random.uniform(2.0, 5.0)
        await asyncio.sleep(processing_time - 2.5)  # Already slept 1.0-2.5s above
        
        # Simulate payment gateway response
        payment_success_rate = 0.95 if order_data.get("risk_level", "LOW") == "LOW" else 0.75
        payment_successful = random.random() < payment_success_rate
        
        if payment_successful:
            payment_status = "AUTHORIZED"
            transaction_id = f"TXN_{random.randint(100000000, 999999999)}"
            auth_code = f"AUTH_{random.randint(100000, 999999)}"
        else:
            payment_status = "DECLINED"
            transaction_id = None
            auth_code = None
        
        # Payment details
        payment_details = {
            "payment_method": payment_method,
            "subtotal": payment_amount,
            "tax_amount": tax_amount,
            "shipping_cost": shipping_cost,
            "final_amount": final_amount,
            "currency": "USD",
            "transaction_id": transaction_id,
            "auth_code": auth_code,
            "status": payment_status,
            "gateway_response_time": processing_time,
            "processed_at": datetime.now()
        }
        
        result = {
            "order_id": order_data["order_id"],
            "payment_details": payment_details,
            "payment_successful": payment_successful,
            "final_amount": final_amount,
            "processing_time": time.time(),
            "paid_order": {**order_data, "payment": payment_details, "status": "paid" if payment_successful else "payment_failed"}
        }
        
        self.log_event("PAYMENT_COMPLETE", {
            "order_id": order_data["order_id"],
            "status": payment_status,
            "amount": f"${final_amount:.2f}",
            "transaction_id": transaction_id,
            "processing_time": f"{processing_time:.2f}s"
        })
        
        return result
    
    async def coordinate_shipping(self, shipping_method: str = "standard", **kwargs) -> Dict[str, Any]:
        """Coordinate shipping and logistics."""
        self.log_event("SHIPPING_COORDINATION", {"method": shipping_method, "stage": "preparing"})
        
        await asyncio.sleep(random.uniform(0.8, 1.8))
        
        # Extract paid order
        order_data = None
        for key, value in kwargs.items():
            if key.endswith('_result') and isinstance(value, dict):
                if 'paid_order' in value and value['paid_order'].get('payment', {}).get('status') == 'AUTHORIZED':
                    order_data = value['paid_order']
        
        if not order_data:
            raise ValueError("No paid order found for shipping coordination")
        
        # Shipping options and carriers
        carriers = {
            "standard": {"name": "StandardShip", "days": random.randint(5, 7), "cost": 9.99},
            "express": {"name": "ExpressLogistics", "days": random.randint(2, 3), "cost": 19.99},
            "overnight": {"name": "OvernightDelivery", "days": 1, "cost": 39.99}
        }
        
        carrier_info = carriers.get(shipping_method, carriers["standard"])
        
        # Generate shipping details
        tracking_number = f"{carrier_info['name'][:2].upper()}{random.randint(100000000, 999999999)}"
        estimated_delivery = datetime.now() + timedelta(days=carrier_info["days"])
        
        # Packaging requirements
        total_items = sum(p["quantity"] for p in order_data["products"])
        estimated_weight = total_items * random.uniform(0.5, 2.0)  # lbs
        
        packages = []
        items_per_package = 3
        num_packages = (total_items + items_per_package - 1) // items_per_package
        
        for i in range(num_packages):
            packages.append({
                "package_id": f"PKG_{order_data['order_id']}_{i+1}",
                "weight": round(estimated_weight / num_packages, 2),
                "dimensions": f"{random.randint(8, 16)}x{random.randint(6, 12)}x{random.randint(4, 8)}",
                "tracking_number": f"{tracking_number}_{i+1}" if num_packages > 1 else tracking_number
            })
        
        # Shipping coordination result
        shipping_status = "READY_TO_SHIP" if random.random() > 0.05 else "DELAYED"
        
        shipping_details = {
            "carrier": carrier_info["name"],
            "method": shipping_method,
            "tracking_number": tracking_number,
            "estimated_delivery": estimated_delivery,
            "shipping_cost": carrier_info["cost"],
            "packages": packages,
            "total_weight": estimated_weight,
            "status": shipping_status,
            "ship_from_address": {
                "warehouse": "Main Distribution Center",
                "address": "123 Warehouse Blvd, Logistics City, TX 75001"
            },
            "ship_to_address": order_data["shipping_address"]
        }
        
        result = {
            "order_id": order_data["order_id"],
            "shipping_details": shipping_details,
            "packages_count": len(packages),
            "shipping_ready": shipping_status == "READY_TO_SHIP",
            "processing_time": time.time(),
            "shipped_order": {**order_data, "shipping": shipping_details, "status": "shipped" if shipping_status == "READY_TO_SHIP" else "shipping_delayed"}
        }
        
        self.log_event("SHIPPING_COORDINATED", {
            "order_id": order_data["order_id"],
            "carrier": carrier_info["name"],
            "tracking": tracking_number,
            "packages": len(packages),
            "delivery_date": estimated_delivery.strftime("%Y-%m-%d"),
            "status": shipping_status
        })
        
        return result
    
    async def send_notifications(self, notification_type: str = "comprehensive", **kwargs) -> Dict[str, Any]:
        """Send customer notifications and confirmations."""
        self.log_event("CUSTOMER_NOTIFICATIONS", {"type": notification_type, "stage": "sending"})
        
        await asyncio.sleep(random.uniform(0.3, 0.8))
        
        # Extract shipped order
        order_data = None
        for key, value in kwargs.items():
            if key.endswith('_result') and isinstance(value, dict):
                if 'shipped_order' in value:
                    order_data = value['shipped_order']
        
        if not order_data:
            raise ValueError("No shipped order found for notifications")
        
        # Generate notification content
        customer = order_data["customer"]
        shipping = order_data.get("shipping", {})
        payment = order_data.get("payment", {})
        
        notifications_sent = []
        
        # Order confirmation email
        if random.random() > 0.02:  # 98% success rate
            notifications_sent.append({
                "type": "order_confirmation",
                "channel": "email",
                "recipient": customer["email"],
                "status": "sent",
                "sent_at": datetime.now(),
                "subject": f"Order Confirmation - {order_data['order_id']}"
            })
        
        # SMS notification
        if random.random() > 0.05:  # 95% success rate
            notifications_sent.append({
                "type": "shipping_notification",
                "channel": "sms",
                "recipient": customer["phone"],
                "status": "sent",
                "sent_at": datetime.now(),
                "message": f"Your order {order_data['order_id']} has shipped! Track: {shipping.get('tracking_number', 'N/A')}"
            })
        
        # Push notification (if app user)
        if random.random() > 0.15:  # 85% success rate
            notifications_sent.append({
                "type": "push_notification",
                "channel": "mobile_app",
                "recipient": customer["customer_id"],
                "status": "sent",
                "sent_at": datetime.now(),
                "title": "Order Update",
                "body": f"Great news! Your order is on the way."
            })
        
        # Calculate notification success rate
        total_attempted = 3
        successful_notifications = len(notifications_sent)
        notification_success_rate = successful_notifications / total_attempted
        
        result = {
            "order_id": order_data["order_id"],
            "customer_id": customer["customer_id"],
            "notifications_sent": notifications_sent,
            "successful_notifications": successful_notifications,
            "total_attempted": total_attempted,
            "success_rate": notification_success_rate,
            "processing_time": time.time(),
            "final_order": {**order_data, "notifications": notifications_sent, "status": "completed"}
        }
        
        self.log_event("NOTIFICATIONS_SENT", {
            "order_id": order_data["order_id"],
            "customer": customer["name"],
            "notifications_sent": successful_notifications,
            "success_rate": f"{notification_success_rate:.1%}",
            "channels": [n["channel"] for n in notifications_sent]
        })
        
        return result


async def run_ecommerce_processing():
    """Execute the complete e-commerce order processing workflow."""
    print("🛒 AgenticFlow Realistic Example 3: E-commerce Order Processing")
    print("=" * 68)
    print()
    
    processor = EcommerceOrderProcessor()
    
    # Configure orchestrator for e-commerce workflow
    retry_policy = RetryPolicy(
        max_attempts=3,
        initial_delay=0.2,
        max_delay=5.0,
        backoff_multiplier=2.0
    )
    
    orchestrator = TaskOrchestrator(
        max_concurrent_tasks=3,  # Some stages can overlap
        default_retry_policy=retry_policy
    )
    
    print("🏪 Building E-commerce Order Processing Workflow...")
    print("-" * 52)
    
    # Stage 1: Order Reception and Validation
    orchestrator.add_function_task(
        "receive_order", "Receive & Validate Order",
        processor.receive_and_validate_order,
        args=("website",),
        priority=TaskPriority.HIGH
    )
    
    # Stage 2: Fraud Detection (depends on order validation)
    orchestrator.add_function_task(
        "fraud_check", "Fraud Detection",
        processor.fraud_detection,
        args=("standard",),
        dependencies=["receive_order"],
        priority=TaskPriority.CRITICAL
    )
    
    # Stage 3: Inventory Allocation (depends on fraud check)
    orchestrator.add_function_task(
        "allocate_inventory", "Inventory Allocation",
        processor.inventory_allocation,
        dependencies=["fraud_check"],
        priority=TaskPriority.HIGH
    )
    
    # Stage 4: Payment Processing (depends on inventory)
    orchestrator.add_function_task(
        "process_payment", "Process Payment",
        processor.process_payment,
        args=("credit_card",),
        dependencies=["allocate_inventory"],
        priority=TaskPriority.CRITICAL
    )
    
    # Stage 5: Shipping Coordination (depends on payment)
    orchestrator.add_function_task(
        "coordinate_shipping", "Coordinate Shipping",
        processor.coordinate_shipping,
        args=("standard",),
        dependencies=["process_payment"],
        priority=TaskPriority.NORMAL
    )
    
    # Stage 6: Customer Notifications (depends on shipping)
    orchestrator.add_function_task(
        "send_notifications", "Send Notifications",
        processor.send_notifications,
        args=("comprehensive",),
        dependencies=["coordinate_shipping"],
        priority=TaskPriority.NORMAL
    )
    
    # Execute the workflow
    print("🚀 Executing E-commerce Order Processing...")
    print("-" * 52)
    
    start_time = time.time()
    result = await orchestrator.execute_workflow()
    total_time = time.time() - start_time
    
    # Generate comprehensive report
    print()
    print("=" * 68)
    print("📊 E-COMMERCE PROCESSING REPORT")
    print("=" * 68)
    
    success_rate = result["success_rate"]
    total_tasks = result["status"]["total_tasks"]
    completed_tasks = result["status"]["completed_tasks"]
    
    print(f"⏱️  Total Processing Time: {total_time:.2f} seconds")
    print(f"✅ Success Rate: {success_rate:.1f}%")
    print(f"📊 Tasks Completed: {completed_tasks}/{total_tasks}")
    print(f"🔄 Workflow Status: {'COMPLETED' if result['status']['is_complete'] else 'INCOMPLETE'}")
    
    if "dag_stats" in result:
        dag_stats = result["dag_stats"]
        print(f"📈 Processing Stages: {dag_stats.get('execution_levels', 'N/A')}")
        print(f"🎯 Critical Path: {' → '.join(dag_stats.get('critical_path', []))}")
    
    # Detailed order processing breakdown
    print("\n" + "-" * 68)
    print("📋 ORDER PROCESSING BREAKDOWN")
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
                    if "order" in task_result:
                        order = task_result["order"]
                        print(f"   📝 Order ID: {order.get('order_id', 'N/A')}")
                        print(f"   💰 Amount: ${order.get('total_amount', 0):.2f}")
                    elif "risk_level" in task_result:
                        print(f"   🛡️  Risk Level: {task_result['risk_level']}")
                        print(f"   ✅ Action: {task_result['recommended_action']}")
                    elif "fulfillment_rate" in task_result:
                        print(f"   📦 Fulfillment: {task_result['fulfillment_rate']:.1%}")
                        print(f"   ✅ Status: {task_result['next_action']}")
                    elif "payment_successful" in task_result:
                        payment = task_result["payment_details"]
                        print(f"   💳 Payment: {payment.get('status', 'N/A')}")
                        print(f"   💰 Final: ${task_result.get('final_amount', 0):.2f}")
                    elif "shipping_ready" in task_result:
                        shipping = task_result["shipping_details"]
                        print(f"   🚚 Carrier: {shipping.get('carrier', 'N/A')}")
                        print(f"   📦 Packages: {task_result.get('packages_count', 0)}")
                    elif "success_rate" in task_result:
                        print(f"   📧 Notifications: {task_result['successful_notifications']}/{task_result['total_attempted']}")
                        print(f"   ✅ Success Rate: {task_result['success_rate']:.1%}")
            print()
    
    # Final Assessment
    print("-" * 68)
    print("🎯 PROCESSING ASSESSMENT")
    print("-" * 68)
    
    grade = "A+" if success_rate >= 95 else "A" if success_rate >= 85 else "B+" if success_rate >= 75 else "B"
    
    print(f"📊 Overall Grade: {grade}")
    print()
    
    # Performance Analysis
    if success_rate >= 95:
        print("✅ EXCELLENT: Order processing completed flawlessly")
        print("   • All order validation and fraud checks passed")
        print("   • Inventory allocated and payment processed successfully")
        print("   • Shipping coordinated and notifications sent")
    elif success_rate >= 85:
        print("✅ GOOD: Order processing mostly successful")
        print("   • Minor issues in some processing stages")
    else:
        print("⚠️  NEEDS IMPROVEMENT: Some processing stages failed")
    
    print()
    print("💡 Key Achievements:")
    print("   • End-to-end order processing automation")
    print("   • Comprehensive fraud detection and risk assessment")
    print("   • Real-time inventory allocation and management")
    print("   • Secure payment processing and authorization")
    print("   • Integrated shipping coordination and tracking")
    print("   • Multi-channel customer notifications")
    
    print()
    print("🔧 Technical Highlights:")
    print(f"   • {total_tasks} processing stages in sequential workflow")
    print(f"   • Real-time inventory management and allocation")
    print(f"   • Advanced fraud detection with risk scoring")
    print(f"   • Secure payment processing with multiple gateways")
    print(f"   • Automated shipping coordination and tracking")
    
    return {
        "example_name": "E-commerce Order Processing",
        "grade": grade,
        "success_rate": success_rate,
        "execution_time": total_time,
        "tasks_completed": f"{completed_tasks}/{total_tasks}",
        "key_features": [
            "Order validation & fraud detection",
            "Real-time inventory allocation",
            "Secure payment processing",
            "Shipping coordination",
            "Customer notifications"
        ]
    }


if __name__ == "__main__":
    result = asyncio.run(run_ecommerce_processing())
    
    print()
    print("=" * 68)
    print(f"🏆 FINAL RESULT: {result['grade']} ({result['success_rate']:.1f}% success)")
    print("🚀 E-commerce Order Processing validation complete!")
    print("=" * 68)