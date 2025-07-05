// Updated chat client for MCP-integrated backend
class ChatClient {
    constructor(serverUrl = 'http://localhost:8000') {
        this.serverUrl = serverUrl;
        this.messages = [];
        this.isGenerating = false;
        this.currentResponse = '';
        this.messagesContainer = null;
    }
    
    initialize() {
        this.messagesContainer = document.getElementById('messages');
        this.checkConnection();
    }
    
    async checkConnection() {
        try {
            const response = await fetch(`${this.serverUrl}/health`);
            if (response.ok) {
                const data = await response.json();
                const mcpConnected = data.details?.mcp_status?.connected;
                window.updateConnectionStatus(mcpConnected ? 'CONNECTED' : 'ERROR');
            } else {
                window.updateConnectionStatus('ERROR');
            }
        } catch (error) {
            window.updateConnectionStatus('ERROR');
            console.error('Connection check failed:', error);
        }
    }
    
    async sendMessage(content) {
        if (this.isGenerating) return;
        
        this.isGenerating = true;
        window.updateSendButton(true);
        
        this.addMessage('user', content);
        this.messages.push({ role: 'user', content });
        
        this.showTypingIndicator();
        
        try {
            await this.streamResponse();
        } catch (error) {
            this.addMessage('error', `Error: ${error.message}`);
        } finally {
            this.hideTypingIndicator();
            this.isGenerating = false;
            window.updateSendButton(false);
        }
    }
    
    async streamResponse() {
        const requestData = {
            jsonrpc: '2.0',
            method: 'chat',
            params: {
                messages: this.messages,
                tools_enabled: window.toolManager.isWeatherEnabled(),
                stream: true
            },
            id: Date.now().toString()
        };
        
        const response = await fetch(`${this.serverUrl}/rpc`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData)
        });
        
        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }
        
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        
        this.currentResponse = '';
        let assistantMessageEl = null;
        
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            buffer += decoder.decode(value, { stream: true });
            
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';
            
            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6));
                        
                        if (data.type === 'content') {
                            this.currentResponse += data.content;
                            
                            if (!assistantMessageEl) {
                                assistantMessageEl = this.addMessage('assistant', '');
                            }
                            
                            assistantMessageEl.textContent = this.currentResponse;
                            this.scrollToBottom();
                        }
                        else if (data.type === 'done') {
                            if (this.currentResponse) {
                                this.messages.push({ role: 'assistant', content: this.currentResponse });
                            }
                            return;
                        }
                        else if (data.type === 'error') {
                            throw new Error(data.error);
                        }
                    } catch (e) {
                        console.error('Error parsing stream data:', e);
                    }
                }
            }
        }
    }
    
    addMessage(role, content) {
        const messageEl = document.createElement('div');
        messageEl.className = `message ${role}`;
        messageEl.textContent = content;
        
        this.messagesContainer.appendChild(messageEl);
        this.scrollToBottom();
        
        return messageEl;
    }
    
    addSystemMessage(content) {
        this.addMessage('system', content);
    }
    
    showTypingIndicator() {
        const typingEl = document.createElement('div');
        typingEl.className = 'typing-indicator';
        typingEl.id = 'typing-indicator';
        typingEl.innerHTML = `
            <span>Assistant is typing</span>
            <div class="typing-dots">
                <span></span>
                <span></span>
                <span></span>
            </div>
        `;
        
        this.messagesContainer.appendChild(typingEl);
        this.scrollToBottom();
    }
    
    hideTypingIndicator() {
        const typingEl = document.getElementById('typing-indicator');
        if (typingEl) {
            typingEl.remove();
        }
    }
    
    scrollToBottom() {
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    }
    
    clearMessages() {
        this.messages = [];
        this.messagesContainer.innerHTML = '';
    }
}

window.chatClient = new ChatClient();

function initializeChat() {
    window.chatClient.initialize();
}