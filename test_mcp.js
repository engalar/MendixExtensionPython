/**
 * MCP SSE 客户端测试
 * 参考 Tampermonkey GM_xmlhttpRequest 实现逻辑
 */

const http = require('http');
const https = require('https');
const url = require('url');

class MCPClient {
    constructor(baseUrl) {
        this.baseUrl = baseUrl;
        this.sessionId = null;
        this.msgId = 0;
        this.pendingRequests = new Map();
        this.isConnecting = false;
    }

    /**
     * 连接 SSE 并执行握手
     */
    async connect() {
        if (this.sessionId) {
            console.log('[MCP] 已连接，Session ID:', this.sessionId);
            return;
        }

        if (this.isConnecting) {
            // 等待连接完成
            await new Promise(resolve => setTimeout(resolve, 500));
            return this.connect();
        }

        this.isConnecting = true;

        return new Promise((resolve, reject) => {
            const sseUrl = `${this.baseUrl}`;
            console.log(`[MCP] 正在连接到 ${sseUrl} ...`);

            const parsedUrl = url.parse(sseUrl);
            const client = parsedUrl.protocol === 'https:' ? https : http;

            const req = client.get(sseUrl, {
                headers: {
                    'Cache-Control': 'no-cache',
                    'Accept': 'text/event-stream'
                }
            }, (res) => {
                if (res.statusCode !== 200) {
                    reject(new Error(`HTTP ${res.statusCode}: ${res.statusMessage}`));
                    return;
                }

                let buffer = '';
                let currentEvent = 'message';

                res.on('data', (chunk) => {
                    buffer += chunk.toString();
                    const lines = buffer.split('\n');
                    buffer = lines.pop() || '';

                    for (const line of lines) {
                        if (!line.trim()) continue;

                        if (line.startsWith('event:')) {
                            currentEvent = line.substring(6).trim();
                        } else if (line.startsWith('data:')) {
                            const dataStr = line.substring(5).trim();
                            this.handleSSEMessage(currentEvent, dataStr, resolve, reject);
                            currentEvent = 'message';
                        }
                    }
                });

                res.on('end', () => {
                    console.log('[MCP] SSE 连接已关闭');
                    this.sessionId = null;
                    this.isConnecting = false;
                });

                res.on('error', (err) => {
                    console.error('[MCP] SSE 错误:', err.message);
                    this.isConnecting = false;
                    reject(err);
                });
            });

            req.on('error', (err) => {
                this.isConnecting = false;
                reject(err);
            });
        });
    }

    /**
     * 处理 SSE 消息
     */
    async handleSSEMessage(event, data, resolveInit, rejectInit) {
        if (event === 'endpoint') {
            // 获取 session_id
            const match = data.match(/(?:session_id|sessionId)=([^&]+)/);
            if (match && match[1]) {
                this.sessionId = match[1];
                console.log(`[MCP] ✅ SSE 已连接. Session ID: ${this.sessionId}`);

                // 执行握手
                try {
                    await this.performHandshake();
                    console.log('[MCP] 🤝 握手完成');
                    this.isConnecting = false;
                    if (resolveInit) resolveInit();
                } catch (e) {
                    console.error('[MCP] ❌ 握手失败:', e.message);
                    this.isConnecting = false;
                    if (rejectInit) rejectInit(e);
                }
            }
        } else if (event === 'message') {
            try {
                const msg = JSON.parse(data);
                const reqId = msg.id;

                if (reqId !== undefined && this.pendingRequests.has(reqId)) {
                    const resolver = this.pendingRequests.get(reqId);
                    this.pendingRequests.delete(reqId);

                    if (msg.error) {
                        resolver({ error: msg.error.message || msg.error });
                    } else if (msg.result) {
                        if (msg.result.capabilities) {
                            // initialize 响应
                            resolver(msg.result);
                        } else if (msg.result.content) {
                            // tool call 响应
                            const content = msg.result.content;
                            if (Array.isArray(content) && content.length > 0) {
                                resolver(content[0].text);
                            } else {
                                resolver(JSON.stringify(msg.result));
                            }
                        } else {
                            // 其他响应 (如 tools/list)
                            resolver(msg.result);
                        }
                    } else {
                        resolver(msg);
                    }
                }
            } catch (e) {
                console.error('[MCP] JSON 解析错误:', e.message);
            }
        }
    }

    /**
     * 执行握手
     */
    async performHandshake() {
        // 1. 发送 initialize
        const initId = 0;
        const initPromise = new Promise(resolve => {
            this.pendingRequests.set(initId, resolve);
        });

        this.sendPost({
            jsonrpc: "2.0",
            method: "initialize",
            params: {
                protocolVersion: "2024-11-05",
                capabilities: {
                    sampling: {},
                    roots: { listChanged: true }
                },
                clientInfo: {
                    name: "Node.js-Test-Client",
                    version: "1.0.0"
                }
            },
            id: initId
        });

        await initPromise;
        console.log('[MCP] ✅ Initialize 成功');

        // 2. 发送 initialized 通知
        this.sendPost({
            jsonrpc: "2.0",
            method: "notifications/initialized"
        });
    }

    /**
     * 发送 POST 请求
     */
    sendPost(payload) {
        if (!this.sessionId) {
            throw new Error('未连接，请先调用 connect()');
        }

        const postUrl = `${this.baseUrl}/message?sessionId=${this.sessionId}`;
        const data = JSON.stringify(payload);

        const parsedUrl = url.parse(postUrl);
        const client = parsedUrl.protocol === 'https:' ? https : http;

        const req = client.request(postUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Content-Length': Buffer.byteLength(data)
            }
        }, (res) => {
            // 响应通过 SSE 返回，这里只处理 HTTP 错误
            if (res.statusCode >= 400) {
                console.error(`[MCP] POST 失败 (HTTP ${res.statusCode})`);
                if (payload.id !== undefined && this.pendingRequests.has(payload.id)) {
                    const resolver = this.pendingRequests.get(payload.id);
                    this.pendingRequests.delete(payload.id);
                    resolver({ error: `HTTP ${res.statusCode}` });
                }
            }
            // 消耗响应体
            res.resume();
        });

        req.on('error', (err) => {
            console.error('[MCP] POST 网络错误:', err.message);
            if (payload.id !== undefined && this.pendingRequests.has(payload.id)) {
                const resolver = this.pendingRequests.get(payload.id);
                this.pendingRequests.delete(payload.id);
                resolver({ error: err.message });
            }
        });

        req.write(data);
        req.end();
    }

    /**
     * 调用工具
     */
    async callTool(toolName, toolArgs) {
        if (!this.sessionId) {
            await this.connect();
        }

        const requestId = ++this.msgId;
        const responsePromise = new Promise(resolve => {
            this.pendingRequests.set(requestId, resolve);
        });

        this.sendPost({
            jsonrpc: "2.0",
            method: "tools/call",
            params: {
                name: toolName,
                arguments: toolArgs
            },
            id: requestId
        });

        return responsePromise;
    }

    /**
     * 获取工具列表
     */
    async listTools() {
        if (!this.sessionId) {
            await this.connect();
        }

        const requestId = ++this.msgId;
        const responsePromise = new Promise(resolve => {
            this.pendingRequests.set(requestId, resolve);
        });

        this.sendPost({
            jsonrpc: "2.0",
            method: "tools/list",
            id: requestId
        });

        const result = await responsePromise;
        return result.tools || [];
    }

    /**
     * 执行 Python 代码
     */
    async executePython(code) {
        const result = await this.callTool('execute_python', { code });
        if (result && result.error) {
            return `错误: ${result.error}`;
        }
        return result;
    }
}

// ============ 测试代码 ============

async function main() {
    const client = new MCPClient('http://localhost:8008/a/mcp');

    try {
        // 测试 1: 获取工具列表
        console.log('\n' + '='.repeat(60));
        console.log('测试 1: 获取工具列表');
        console.log('='.repeat(60));

        const tools = await client.listTools();
        console.log(`可用工具数量: ${tools.length}`);
        tools.forEach(tool => {
            const desc = (tool.description || '').substring(0, 60);
            console.log(`  - ${tool.name}: ${desc}`);
        });

        // 测试 2: 简单打印
        console.log('\n' + '='.repeat(60));
        console.log('测试 2: 简单打印语句');
        console.log('='.repeat(60));

        const code2 = `
print("Hello from Node.js MCP!")
print(f"计算结果: {2 + 2}")
`;
        const result2 = await client.executePython(code2);
        console.log('结果:', result2);

        // 测试 3: 返回值
        console.log('\n' + '='.repeat(60));
        console.log('测试 3: 返回值测试');
        console.log('='.repeat(60));

        const code3 = `result = '测试成功! 2 + 2 = ' + str(2 + 2)`;
        const result3 = await client.executePython(code3);
        console.log('结果:', result3);

        // 测试 4: 访问 Mendix 服务
        console.log('\n' + '='.repeat(60));
        console.log('测试 4: 访问 Mendix 服务');
        console.log('='.repeat(60));

        const code4 = `
import pymx.mcp.mendix_context as ctx
modules = ctx.moduleService.GetAllModules()
result = f"项目中有 {len(modules)} 个模块"
`;
        const result4 = await client.executePython(code4);
        console.log('结果:', result4);

        console.log('\n' + '='.repeat(60));
        console.log('✅ 所有测试完成');
        console.log('='.repeat(60));

    } catch (error) {
        console.error('测试失败:', error.message);
    }
}

// 运行测试
main().catch(console.error);
