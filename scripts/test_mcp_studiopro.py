# Source - https://stackoverflow.com/a
# Posted by Bhargav, modified by community. See post 'Timeline' for change history
# Retrieved 2026-01-12, License - CC BY-SA 4.0

import requests
import json


def test_fastmcp_server():
    base_url = "http://localhost:8008/a/mcp"
    headers = {
        "accept": "application/json, text/event-stream",
        "content-type": "application/json",
    }

    print("check 1")

    init_payload = {
        "jsonrpc": "2.0",
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "python-client", "version": "1.0.0"},
        },
        "id": 1,
    }

    response = requests.post(base_url, headers=headers, json=init_payload)
    session_id = response.headers.get("mcp-session-id")
    print(f"Session ID: {session_id}")

    if not session_id:
        print("No session ID received")
        return

    headers["Mcp-Session-Id"] = session_id

    init_complete_payload = {"jsonrpc": "2.0", "method": "notifications/initialized"}

    requests.post(base_url, headers=headers, json=init_complete_payload)
    print("Initialization complete")

    add_payload = {
        "jsonrpc": "2.0",
        "method": "resources/read",
        "params": {"uri": "model://dsl/domain/ECommerceDemo.mxdomain.txt"},
        "id": 2,
    }

    response = requests.post(base_url, headers=headers, json=add_payload)

    # 修改：使用 content.decode("utf-8") 替代 text，强制修复中文乱码
    lines = response.content.decode("utf-8").split("\n")
    data_line = next((line for line in lines if line.startswith("data: ")), None)

    if data_line:
        json_data = data_line[6:]
        result = json.loads(json_data)
        uri = result["result"]["contents"][0]['uri'] 
        text = result["result"]["contents"][0]['text'] # mimeType is text/plain then get text
        print(f"resources read result: {uri} \n {text}")
    else:
        print("No data found in response")
        print("Raw response:", response.text)

    print("Test complete")


if __name__ == "__main__":
    try:
        test_fastmcp_server()
    except requests.exceptions.ConnectionError:
        print("Check MCP its not working on 8000")
    except Exception as e:
        print(f"Error: {e}")
