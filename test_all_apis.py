import asyncio
import json
import time
import requests
import random
import websockets
from concurrent.futures import ThreadPoolExecutor
import threading
from datetime import datetime

# API endpoint URLs
BASE_URL = "http://localhost:8001"
ORDER_URL = f"{BASE_URL}/api/order"
ORDERS_URL = f"{BASE_URL}/api/orders"
WEBSOCKET_URL = "ws://localhost:8001/ws/orders"

# Sample menu items for random order generation
MENU_ITEMS = [
    "Burger", "Pizza", "Pasta", "Salad", "Steak", 
    "Sushi", "Taco", "Sandwich", "Soup", "Ice Cream"
]

# For tracking test results
test_results = {
    "post_api": {"passed": 0, "failed": 0},
    "get_api": {"passed": 0, "failed": 0},
    "websocket_api": {"passed": 0, "failed": 0},
    "concurrency": {"passed": 0, "failed": 0}
}

def print_colored(text, color_code=32):
    """Print text with color"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] \033[{color_code}m{text}\033[0m")

def create_random_order():
    """Generate a random order for testing"""
    table_num = random.randint(1, 10)
    num_items = random.randint(1, 3)
    
    items = []
    for _ in range(num_items):
        name = random.choice(MENU_ITEMS)
        quantity = random.randint(1, 3)
        items.append({"name": name, "quantity": quantity})
    
    order = {
        "table": f"Table {table_num}",
        "items": items
    }
    
    return order

def test_post_api():
    """Test POST /api/order endpoint"""
    print_colored("\n--- Testing POST /api/order API ---", 36)
    
    # Create a sample order
    order_data = {
        "table": "Test Table",
        "items": [
            {"name": "Test Burger", "quantity": 2},
            {"name": "Test Drink", "quantity": 1}
        ]
    }
    
    print_colored(f"Sending order: {json.dumps(order_data, indent=2)}")
    
    response = requests.post(ORDER_URL, json=order_data)
    
    if response.status_code == 201:
        print_colored(f"✅ POST API Test Passed (status: {response.status_code})", 32)
        print_colored(f"Response: {json.dumps(response.json(), indent=2)}")
        test_results["post_api"]["passed"] += 1
        return response.json()
    else:
        print_colored(f"❌ POST API Test Failed (status: {response.status_code})", 31)
        print_colored(f"Response: {response.text}", 31)
        test_results["post_api"]["failed"] += 1
        return None

def test_get_api():
    """Test GET /api/orders endpoint"""
    print_colored("\n--- Testing GET /api/orders API ---", 36)
    
    response = requests.get(ORDERS_URL)
    
    if response.status_code == 200:
        orders = response.json()
        print_colored(f"✅ GET API Test Passed (status: {response.status_code})", 32)
        print_colored(f"Retrieved {len(orders)} orders")
        if orders:
            print_colored(f"First order: {json.dumps(orders[0], indent=2)}")
        test_results["get_api"]["passed"] += 1
        return orders
    else:
        print_colored(f"❌ GET API Test Failed (status: {response.status_code})", 31)
        print_colored(f"Response: {response.text}", 31)
        test_results["get_api"]["failed"] += 1
        return None

async def test_websocket_api():
    """Test WebSocket /ws/orders endpoint"""
    print_colored("\n--- Testing WebSocket /ws/orders API ---", 36)
    
    try:
        # Connect to WebSocket
        print_colored("Connecting to WebSocket...")
        async with websockets.connect(WEBSOCKET_URL) as websocket:
            print_colored("✅ WebSocket connection established", 32)
            test_results["websocket_api"]["passed"] += 1
            
            # Step 1: Receive initial orders
            print_colored("Waiting for initial orders...")
            initial_data = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            initial_data = json.loads(initial_data)
            
            if "orders" in initial_data and initial_data["type"] == "initial":
                print_colored(f"✅ Received initial orders ({len(initial_data['orders'])} orders)", 32)
                test_results["websocket_api"]["passed"] += 1
            else:
                print_colored("❌ Initial orders format incorrect", 31)
                test_results["websocket_api"]["failed"] += 1
            
            # Step 2: Create a new order and check for real-time update
            print_colored("\nTesting real-time updates...")
            print_colored("Creating a new order via REST API")
            
            # Create a unique order to clearly identify it
            unique_order = {
                "table": f"WebSocket Test Table {random.randint(1000, 9999)}",
                "items": [
                    {"name": "WebSocket Test Item", "quantity": random.randint(1, 5)}
                ]
            }
            
            # Use a separate thread to create the order
            order_thread = threading.Thread(
                target=lambda: requests.post(ORDER_URL, json=unique_order)
            )
            order_thread.start()
            
            # Wait for the WebSocket update
            print_colored("Waiting for WebSocket update...")
            try:
                update_data = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                update_data = json.loads(update_data)
                
                if update_data["type"] == "new_order" and update_data["order"]["table"] == unique_order["table"]:
                    print_colored("✅ Received real-time order update", 32)
                    print_colored(f"Order data: {json.dumps(update_data['order'], indent=2)}")
                    test_results["websocket_api"]["passed"] += 1
                else:
                    print_colored(f"❌ Unexpected WebSocket data: {update_data}", 31)
                    test_results["websocket_api"]["failed"] += 1
            except asyncio.TimeoutError:
                print_colored("❌ Timed out waiting for WebSocket update", 31)
                test_results["websocket_api"]["failed"] += 1
            
            order_thread.join()
    except Exception as e:
        print_colored(f"❌ WebSocket Test Failed: {str(e)}", 31)
        test_results["websocket_api"]["failed"] += 1

def test_concurrency():
    """Test system with concurrent order creation"""
    print_colored("\n--- Testing Concurrency ---", 36)
    num_orders = 10
    print_colored(f"Creating {num_orders} concurrent orders...")
    
    with ThreadPoolExecutor(max_workers=num_orders) as executor:
        futures = []
        for i in range(num_orders):
            order_data = create_random_order()
            order_data["table"] = f"Concurrent Table {i+1}"
            print_colored(f"Queueing order {i+1}: {order_data['table']}")
            futures.append(executor.submit(requests.post, ORDER_URL, json=order_data))
        
        # Check results
        successes = 0
        for i, future in enumerate(futures):
            response = future.result()
            if response.status_code == 201:
                successes += 1
            else:
                print_colored(f"❌ Order {i+1} failed (status: {response.status_code})", 31)
    
    if successes == num_orders:
        print_colored(f"✅ All {num_orders} concurrent orders succeeded", 32)
        test_results["concurrency"]["passed"] += 1
    else:
        print_colored(f"❌ Only {successes}/{num_orders} concurrent orders succeeded", 31)
        test_results["concurrency"]["failed"] += 1
    
    # Verify orders were created
    response = requests.get(ORDERS_URL)
    if response.status_code == 200:
        orders = response.json()
        concurrent_orders = [o for o in orders if o["table"].startswith("Concurrent Table")]
        if len(concurrent_orders) >= num_orders:
            print_colored(f"✅ All {num_orders} concurrent orders found in database", 32)
            test_results["concurrency"]["passed"] += 1
        else:
            print_colored(f"❌ Only found {len(concurrent_orders)}/{num_orders} concurrent orders in database", 31)
            test_results["concurrency"]["failed"] += 1

def print_test_summary():
    """Print a summary of all test results"""
    print_colored("\n\n=== TEST SUMMARY ===", 36)
    
    total_passed = sum(category["passed"] for category in test_results.values())
    total_failed = sum(category["failed"] for category in test_results.values())
    total_tests = total_passed + total_failed
    
    # Print individual test categories
    for category, results in test_results.items():
        passed = results["passed"]
        failed = results["failed"]
        total = passed + failed
        if total == 0:
            continue
            
        success_rate = (passed / total) * 100 if total > 0 else 0
        color = 32 if failed == 0 else 31  # Green if all tests passed, otherwise red
        
        print_colored(f"{category.upper()} Tests: {passed}/{total} passed ({success_rate:.1f}%)", color)
    
    # Print overall summary
    overall_success_rate = (total_passed / total_tests) * 100 if total_tests > 0 else 0
    overall_color = 32 if total_failed == 0 else 31
    
    print_colored(f"\nOVERALL: {total_passed}/{total_tests} tests passed ({overall_success_rate:.1f}%)", overall_color)
    
    if total_failed == 0:
        print_colored("\n🎉 All tests passed successfully! 🎉", 32)
    else:
        print_colored(f"\n⚠️ {total_failed} tests failed. See above for details.", 31)

async def run_tests():
    """Run all tests in sequence"""
    print_colored("=== BISTRO92 API TEST SUITE ===", 36)
    print_colored("Starting comprehensive API testing...\n", 36)
    
    # Test 1: GET API
    test_get_api()
    
    # Test 2: POST API
    test_post_api()
    
    # Test 3: GET API again (verify the order was created)
    test_get_api()
    
    # Test 4: Concurrency
    test_concurrency()
    
    # Test 5: WebSocket API
    await test_websocket_api()
    
    # Print test summary
    print_test_summary()

if __name__ == "__main__":
    asyncio.run(run_tests()) 