function chat() {
    return {
        conversation: null,
        messages: [],
        newMessage: '',
        isLoading: false,
        error: null,
        
        async initializeChat() {
            // Create a new conversation when chat initializes
            try {
                const response = await fetch('/conversations/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        title: 'New Conversation',
                        model_type: 'text',
                        model_name: document.querySelector('select[name="model_name"]').value
                    })
                });
                
                if (!response.ok) throw new Error('Failed to create conversation');
                
                const data = await response.json();
                this.conversation = {
                    id: data.id,
                    messages: []
                };
                
                this.messages = [
                    { 
                        id: Date.now(),
                        role: 'assistant',
                        content: 'Hello! How can I assist you today?',
                        timestamp: new Date()
                    }
                ];
            } catch (error) {
                console.error('Failed to initialize chat:', error);
                this.error = 'Failed to initialize chat';
            }
            
            this.$watch('messages', () => {
                this.$nextTick(() => {
                    this.scrollToBottom();
                });
            });
        },
        
        async sendMessage() {
            if (!this.newMessage.trim() || this.isLoading) return;
            
            const userMessage = {
                conversation_id: this.conversation.id,
                role: 'user',
                content: this.newMessage,
                timestamp: new Date()
            };
            
            try {
                // Add message to conversation
                const messageResponse = await fetch(`/conversations/${this.conversation.id}/messages`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(userMessage)
                });
                
                if (!messageResponse.ok) throw new Error('Failed to save message');
                
                const messageData = await messageResponse.json();
                userMessage.id = messageData.id;
                
                this.messages.push(userMessage);
                const message = this.newMessage;
                this.newMessage = '';
                this.isLoading = true;
                
                // Generate response
                const botMessage = {
                    conversation_id: this.conversation.id,
                    role: 'assistant',
                    content: '',
                    loading: true,
                    timestamp: new Date()
                };
                
                this.messages.push(botMessage);
                
                const response = await fetch('/htmx/generate/text/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ prompt: message })
                });
                
                if (!response.ok) throw new Error('Failed to generate response');
                
                const data = await response.text();
                
                // Save assistant message
                const assistantMessage = {
                    conversation_id: this.conversation.id,
                    role: 'assistant',
                    content: data,
                    timestamp: new Date()
                };
                
                const assistantResponse = await fetch(`/conversations/${this.conversation.id}/messages`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(assistantMessage)
                });
                
                if (!assistantResponse.ok) throw new Error('Failed to save assistant message');
                
                const assistantData = await assistantResponse.json();
                assistantMessage.id = assistantData.id;
                
                // Update bot message with response
                const index = this.messages.findIndex(m => m.loading);
                if (index !== -1) {
                    this.messages[index] = assistantMessage;
                }
            } catch (error) {
                console.error('Error:', error);
                const index = this.messages.findIndex(m => m.loading);
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