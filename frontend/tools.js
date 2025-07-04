// Tool management for the chat interface
class ToolManager {
    constructor() {
        this.weatherEnabled = false;
        this.toggle = null;
    }
    
    initialize() {
        this.toggle = document.getElementById('weather-toggle');
        if (this.toggle) {
            this.toggle.addEventListener('change', (e) => {
                this.weatherEnabled = e.target.checked;
                this.onToggleChange();
            });
        }
    }
    
    onToggleChange() {
        const status = this.weatherEnabled ? 'enabled' : 'disabled';
        console.log(`Weather tool ${status}`);
        
        // Add visual feedback
        if (window.chatClient) {
            window.chatClient.addSystemMessage(`Weather tool ${status}`);
        }
    }
    
    isWeatherEnabled() {
        return this.weatherEnabled;
    }
    
    getEnabledTools() {
        const tools = [];
        if (this.weatherEnabled) {
            tools.push('weather');
        }
        return tools;
    }
    
    setWeatherEnabled(enabled) {
        this.weatherEnabled = enabled;
        if (this.toggle) {
            this.toggle.checked = enabled;
        }
    }
}

// Global tool manager instance
window.toolManager = new ToolManager();

// Initialize tools when DOM is ready
function initializeTools() {
    window.toolManager.initialize();
}