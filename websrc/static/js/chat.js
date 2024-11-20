function chat() {
    return {
        messages: [],
        newMessage: '',
        isLoading: false,
        error: null,
        
        async initializeChat() {
            this.messages = [
                { 
                    id: Date.now(),
                    role: 'bot',
                    content: 'Hello! How can I assist you today?',
                    timestamp: new Date()
                }
            ];
            
            this.$watch('messages', () => {
                this.$nextTick(() => {
                    this.scrollToBottom();
                });
            });
        },
        
        async sendMessage() {
            if (!this.newMessage.trim() || this.isLoading) return;
            
            const userMessage = {
                id: Date.now(),
                role: 'user',
                content: this.newMessage,
                timestamp: new Date()
            };
            
            this.messages.push(userMessage);
            const message = this.newMessage;
            this.newMessage = '';
            this.isLoading = true;
            
            // Add temporary bot message with loading state
            const botMessage = {
                id: Date.now() + 1,
                role: 'bot',
                content: '',
                loading: true,
                timestamp: new Date()
            };
            this.messages.push(botMessage);
            
            try {
                const response = await fetch('/htmx/generate/text/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ prompt: message })
                });
                
                if (!response.ok) throw new Error('Failed to generate response');
                
                const data = await response.text();
                
                // Update bot message with response
                const index = this.messages.findIndex(m => m.id === botMessage.id);
                if (index !== -1) {
                    this.messages[index] = {
                        ...botMessage,
                        content: data,
                        loading: false
                    };
                }
            } catch (error) {
                console.error('Error:', error);
                const index = this.messages.findIndex(m => m.id === botMessage.id);
                if (index !== -1) {
                    this.messages[index] = {
                        ...botMessage,
                        content: 'Failed to generate response. Please try again.',
                        loading: false,
                        error: true
                    };
                }
            } finally {
                this.isLoading = false;
                this.scrollToBottom();
            }
        },
        
        scrollToBottom() {
            const container = this.$refs.messageContainer;
            container.scrollTop = container.scrollHeight;
        }
    };
} 