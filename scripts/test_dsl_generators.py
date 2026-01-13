#!/usr/bin/env python3
"""
Comprehensive test script for all DSL generator functions.

Tests both tool and resource endpoints for:
1. Domain Model DSL
2. Microflow DSL
3. Page DSL
4. Workflow DSL
5. Module Tree DSL
"""

import requests
import json

# Configuration
BASE_URL = "http://127.0.0.1:8008/a/mcp"
HEADERS = {
    "accept": "application/json, text/event-stream",
    "content-type": "application/json",
}

# Test Data (modify based on your Mendix project)
TEST_MODULE = "Administration"  # Change to your module name
TEST_MICROFLOW = "Administration.ChangeMyPassword"  # Change to your microflow
TEST_PAGE = "Administration.RuntimeInstances"  # Change to your page
TEST_WORKFLOW = "MyFirstModule.MyWorkflow"  # Change to your workflow (9.24+)


def init_session():
    """Initialize MCP session and return session ID."""
    init_payload = {
        "jsonrpc": "2.0",
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-dsl-client", "version": "1.0.0"},
        },
        "id": 1,
    }

    response = requests.post(BASE_URL, headers=HEADERS, json=init_payload)
    session_id = response.headers.get("mcp-session-id")

    if not session_id:
        raise Exception("No session ID received")

    headers_with_session = HEADERS.copy()
    headers_with_session["Mcp-Session-Id"] = session_id

    # Complete initialization
    init_complete_payload = {"jsonrpc": "2.0", "method": "notifications/initialized"}
    requests.post(BASE_URL, headers=headers_with_session, json=init_complete_payload)

    return headers_with_session


def parse_sse_response(response):
    """Parse SSE response and return JSON result."""
    lines = response.content.decode("utf-8").split("\n")
    data_line = next((line for line in lines if line.startswith("data: ")), None)

    if not data_line:
        return None

    json_data = data_line[6:]
    return json.loads(json_data)


def test_resource(headers, uri, name):
    """Test a DSL resource endpoint."""
    print(f"\n{'='*60}")
    print(f"Testing Resource: {name}")
    print(f"URI: {uri}")
    print('='*60)

    payload = {
        "jsonrpc": "2.0",
        "method": "resources/read",
        "params": {"uri": uri},
        "id": 2,
    }

    response = requests.post(BASE_URL, headers=headers, json=payload)
    result = parse_sse_response(response)

    if result and "result" in result:
        uri_val = result["result"]["contents"][0]['uri']
        text = result["result"]["contents"][0]['text']
        print(f"[OK] Success")
        print(f"Output preview (first 500 chars):\n{text[:500]}...")
        return True
    else:
        print(f"[FAIL] Failed")
        print(f"Response: {response.text[:500]}")
        return False


def test_tool(headers, tool_name, params, name):
    """Test a DSL tool endpoint."""
    print(f"\n{'='*60}")
    print(f"Testing Tool: {name}")
    print(f"Tool: {tool_name}")
    print('='*60)

    payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": {"data": params},
        },
        "id": 3,
    }

    response = requests.post(BASE_URL, headers=headers, json=payload)
    result = parse_sse_response(response)

    if result and "result" in result:
        content = result["result"]["content"][0]['text']
        print(f"[OK] Success")
        print(f"Output preview (first 500 chars):\n{content[:500]}...")
        return True
    else:
        print(f"[FAIL] Failed")
        print(f"Response: {response.text[:500]}")
        return False


def run_all_tests():
    """Run all DSL generator tests."""
    print("\n" + "="*60)
    print("DSL Generator Test Suite")
    print("="*60)

    try:
        headers = init_session()
        print("[OK] Session initialized")
    except Exception as e:
        print(f"[FAIL] Failed to initialize session: {e}")
        print("Make sure the MCP server is running on port 8008")
        return

    results = []

    # Test 1: Domain Model DSL (Resource)
    results.append(test_resource(
        headers,
        f"model://dsl/domain/{TEST_MODULE}.mxdomain.txt",
        "Domain Model DSL"
    ))

    # Test 2: Domain Model DSL (Tool)
    results.append(test_tool(
        headers,
        "generate_domain_model_dsl",
        {"ModuleName": TEST_MODULE},
        "Domain Model DSL (Tool)"
    ))

    # Test 3: Microflow DSL (Resource)
    results.append(test_resource(
        headers,
        f"model://dsl/microflow/{TEST_MICROFLOW}.mfmicroflow.txt",
        "Microflow DSL"
    ))

    # Test 4: Microflow DSL (Tool)
    results.append(test_tool(
        headers,
        "generate_microflow_dsl",
        {"QualifiedName": TEST_MICROFLOW},
        "Microflow DSL (Tool)"
    ))

    # Test 5: Page DSL (Resource)
    results.append(test_resource(
        headers,
        f"model://dsl/page/{TEST_PAGE}.mfpage.txt",
        "Page DSL"
    ))

    # Test 6: Page DSL (Tool)
    results.append(test_tool(
        headers,
        "generate_page_dsl",
        {"QualifiedName": TEST_PAGE},
        "Page DSL (Tool)"
    ))

    # Test 7: Workflow DSL (Resource) - only if Mendix 9.24+
    results.append(test_resource(
        headers,
        f"model://dsl/workflow/{TEST_WORKFLOW}.mfworkflow.txt",
        "Workflow DSL"
    ))

    # Test 8: Workflow DSL (Tool)
    results.append(test_tool(
        headers,
        "generate_workflow_dsl",
        {"QualifiedName": TEST_WORKFLOW},
        "Workflow DSL (Tool)"
    ))

    # Test 9: Module Tree DSL (Resource)
    results.append(test_resource(
        headers,
        f"model://dsl/module/{TEST_MODULE}.mfmodule.tree.txt",
        "Module Tree DSL"
    ))

    # Test 10: Module Tree DSL (Tool)
    results.append(test_tool(
        headers,
        "generate_module_tree_dsl",
        {"ModuleName": TEST_MODULE},
        "Module Tree DSL (Tool)"
    ))

    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("[OK] All tests passed!")
    else:
        print(f"[FAIL] {total - passed} test(s) failed")


if __name__ == "__main__":
    try:
        run_all_tests()
    except requests.exceptions.ConnectionError:
        print("[FAIL] Connection Error: MCP server not running on port 8008")
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
