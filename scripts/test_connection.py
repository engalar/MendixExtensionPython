# Source - https://stackoverflow.com/a
# Posted by Bhargav, modified by community. See post 'Timeline' for change history
# Retrieved 2026-01-12, License - CC BY-SA 4.0

import requests
import json

def test_fastmcp_server():
   base_url = "http://localhost:8000/mcp"
   headers = {
       'accept': 'application/json, text/event-stream',
       'content-type': 'application/json'
   }
   
   print("check 1")
   
   init_payload = {
       "jsonrpc": "2.0",
       "method": "initialize",
       "params": {
           "protocolVersion": "2024-11-05",
           "capabilities": {},
           "clientInfo": {
               "name": "python-client",
               "version": "1.0.0"
           }
       },
       "id": 1
   }
   
   response = requests.post(base_url, headers=headers, json=init_payload)
   session_id = response.headers.get('mcp-session-id')
   print(f"Session ID: {session_id}")
   
   if not session_id:
       print("No session ID received")
       return
   
   headers['Mcp-Session-Id'] = session_id
   
   init_complete_payload = {
       "jsonrpc": "2.0",
       "method": "notifications/initialized"
   }
   
   requests.post(base_url, headers=headers, json=init_complete_payload)
   print("Initialization complete")
   
   add_payload = {
       "jsonrpc": "2.0",
       "method": "tools/call",
       "params": {
           "name": "add",
           "arguments": {
               "a": 10,
               "b": 15
           }
       },
       "id": 2
   }
   
   response = requests.post(base_url, headers=headers, json=add_payload)
   
   lines = response.text.split('\n')
   data_line = next((line for line in lines if line.startswith('data: ')), None)
   
   if data_line:
       json_data = data_line[6:]
       result = json.loads(json_data)
       answer = result['result']['structuredContent']['result']
       print(f"Add result: {answer}")
   else:
       print("No data found in response")
       print("Raw response:", response.text)
   
   hello_payload = {
       "jsonrpc": "2.0",
       "method": "tools/call",
       "params": {
           "name": "greet",
           "arguments": {
               "name": "mendix"
           }
       },
       "id": 3
   }
   
   response = requests.post(base_url, headers=headers, json=hello_payload)
   lines = response.text.split('\n')
   data_line = next((line for line in lines if line.startswith('data: ')), None)
   
   if data_line:
       json_data = data_line[6:]
       result = json.loads(json_data)
       hello_response = result['result']['content'][0]['text']
       print(f"Hello response: {hello_response}")
   
   print("Test complete")

if __name__ == "__main__":
   try:
       test_fastmcp_server()
   except requests.exceptions.ConnectionError:
       print("Check MCP its not working on 8000")
   except Exception as e:
       print(f"Error: {e}")
