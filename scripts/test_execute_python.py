import asyncio
import httpx
import json
from typing import Optional
from pathlib import Path

# Base URL for the MCP server
MCP_BASE_URL = "http://127.0.0.1:8008/a/mcp"  # Default Mendix port is 8008
CODE_FILE_PATH = Path(__file__).parent / "test_python_code.py"


async def initialize_mcp_session() -> Optional[str]:
    """Initializes a session with the MCP server and returns the session ID."""
    headers = {
        "accept": "application/json, text/event-stream",
        "content-type": "application/json",
    }

    init_payload = {
        "jsonrpc": "2.0",
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "python-test-client", "version": "1.0.0"},
        },
        "id": 1,
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            print("Attempting to initialize MCP session...")
            response = await client.post(
                MCP_BASE_URL, headers=headers, json=init_payload
            )
            response.raise_for_status()

            session_id = response.headers.get("mcp-session-id")
            print(f"MCP Session ID: {session_id}")

            if not session_id:
                print("Error: Did not receive session ID from MCP server.")
                return None

            headers["Mcp-Session-Id"] = session_id

            init_complete_payload = {
                "jsonrpc": "2.0",
                "method": "notifications/initialized",
            }
            await client.post(MCP_BASE_URL, headers=headers, json=init_complete_payload)
            print("MCP session initialized.")
            return session_id

    except httpx.HTTPStatusError as e:
        print(f"HTTP error during initialization: {e}")
        print(f"Response body: {e.response.text}")
        return None
    except httpx.RequestError as e:
        print(f"Request error during initialization: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during initialization: {e}")
        return None


async def call_execute_python(session_id: str):
    """Calls the execute_python tool with code from a file."""
    headers = {
        "accept": "application/json, text/event-stream",
        "content-type": "application/json",
        "Mcp-Session-Id": session_id,
    }

    try:
        print(f"Reading code from: {CODE_FILE_PATH}")
        with open(CODE_FILE_PATH, "r", encoding="utf-8") as f:
            python_code = f.read()
        print("Code read successfully.")
    except FileNotFoundError:
        print(f"Error: Code file not found at {CODE_FILE_PATH}")
        return
    except Exception as e:
        print(f"Error reading code file: {e}")
        return

    execute_python_payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "execute_python",
            "arguments": {
                "code": python_code,
            },
        },
        "id": 2,
    }

    try:
        print("Sending request to execute_python tool...")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                MCP_BASE_URL, headers=headers, json=execute_python_payload
            )
            response.raise_for_status()

            data_line = next(
                (line for line in response.text.splitlines() if line.startswith("data: ")),
                None,
            )

            if data_line:
                json_str = data_line[len("data: ") :]
                try:
                    data = json.loads(json_str)
                    structured_result = data.get("result", {}).get("structuredContent", {}).get("result")

                    if structured_result:
                        print("--- Result from Structured Content ---")
                        print(structured_result)
                        print("--- End Result ---")
                    else:
                        print("--- Full Parsed JSON Response (structuredContent.result not found) ---")
                        print(json.dumps(data, indent=2))
                        print("--- End Full Response ---")

                except json.JSONDecodeError:
                    print(f"--- JSON Decode Error ---")
                    print(f"Failed to parse JSON from payload: {json_str}")
                    print(f"--- Raw Response Text ---")
                    print(response.text)
            else:
                print("--- No 'data:' line found in SSE response ---")
                print(f"Raw response: {response.text}")

    except httpx.HTTPStatusError as e:
        print(f"HTTP error during python execution: {e}")
        print(f"Response body: {e.response.text}")
    except httpx.RequestError as e:
        print(f"Request error during python execution: {e}")
    except json.JSONDecodeError as e:
        print(f"JSON decoding error in response: {e}")
        print(f"Raw response: {response.text}")
    except Exception as e:
        print(f"An unexpected error occurred during python execution: {e}")


async def main():
    print(f"Testing execute_python tool on {MCP_BASE_URL}")

    session_id = await initialize_mcp_session()
    if not session_id:
        print("Failed to initialize MCP session. Exiting.")
        return

    await call_execute_python(session_id)

    print("Test complete.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except httpx.ConnectError:
        print(
            f"Error: Could not connect to MCP server at {MCP_BASE_URL}. Please ensure it is running."
        )
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
