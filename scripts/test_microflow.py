import asyncio
import httpx
import json
from typing import Optional

# Base URL for the MCP server
MCP_BASE_URL = "http://127.0.0.1:8008/a/mcp"  # need 127.0.0.1 instead localhost


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


async def call_ensure_microflows(session_id: str):
    """Calls the ensure_microflows tool to create a test microflow."""
    headers = {
        "accept": "application/json, text/event-stream",
        "content-type": "application/json",
        "Mcp-Session-Id": session_id,
    }

    microflow_request_payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "ensure_microflows",
            "arguments": {
                "requests": [
                    {
                        "FullPath": "GoogleGenai/Use_Cases/Inference/ACT_Inference_CreateAndQueue",
                        "Parameters": [
                            {
                                "Name": "UploadedFile",
                                "Type": "GoogleGenai.UploadedFile",
                            },
                            {"Name": "Prompt", "Type": "String"},
                        ],
                        "ReturnType": "GoogleGenai.InferenceRequest",
                        "ReturnExp": "$NewInferenceRequest",
                        "Activities": [
                            {
                                "ActivityType": "CreateObject",
                                "EntityName": "GoogleGenai.InferenceRequest",
                                "OutputVariable": "NewInferenceRequest",
                            },
                            {
                                "ActivityType": "Change",
                                "VariableName": "$NewInferenceRequest",
                                "EntityName": "GoogleGenai.InferenceRequest",
                                "Changes": [
                                    {
                                        "AttributeName": "Prompt",
                                        "ValueExpression": "$Prompt",
                                    },
                                    {
                                        "AttributeName": "Status",
                                        "ValueExpression": "GoogleGenai.InferenceStatus.Queued.toString()",
                                    },
                                ],
                            },
                            {
                                "ActivityType": "Change",
                                "VariableName": "$NewInferenceRequest",
                                "EntityName": "GoogleGenai.InferenceRequest",
                                "Changes": [
                                    {
                                        "AssociationName": "GoogleGenai.InferenceRequest_UploadedFile",
                                        "ValueExpression": "$UploadedFile",
                                    }
                                ],
                            },
                            {
                                "ActivityType": "Commit",
                                "VariableName": "$NewInferenceRequest",
                            },
                        ],
                    }
                ]
            },
        },
        "id": 2,
    }

    try:
        print("Sending request to create microflow...")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                MCP_BASE_URL, headers=headers, json=microflow_request_payload
            )
            response.raise_for_status()

            # Attempt to parse SSE "data:" line from the raw response
            data_line = next(
                (line for line in response.text.splitlines() if line.startswith("data: ")),
                None,
            )

            if data_line:
                json_str = data_line[len("data: ") :]
                try:
                    data = json.loads(json_str)

                    # Extract the content from result.structuredContent.result
                    structured_result = data.get("result", {}).get("structuredContent", {}).get("result")

                    if structured_result:
                        print("--- Result from Structured Content ---")
                        # The content is often a long string with newlines
                        print(structured_result)
                        print("--- End Result ---")
                    else:
                        # Fallback to printing the whole parsed JSON if the specific path doesn't exist
                        print("--- Full Parsed JSON Response (structuredContent.result not found) ---")
                        print(json.dumps(data, indent=2, ensure_ascii=False))
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
        print(f"HTTP error during microflow creation: {e}")
        print(f"Response body: {e.response.text}")
    except httpx.RequestError as e:
        print(f"Request error during microflow creation: {e}")
    except json.JSONDecodeError as e:
        print(f"JSON decoding error in response: {e}")
        print(f"Raw response: {response.text}")
    except Exception as e:
        print(f"An unexpected error occurred during microflow creation: {e}")


async def main():
    print(f"Testing ensure_microflows tool on {MCP_BASE_URL}")

    session_id = await initialize_mcp_session()
    if not session_id:
        print("Failed to initialize MCP session. Exiting.")
        return

    await call_ensure_microflows(session_id)

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
