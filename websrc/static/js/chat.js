/*function chat() {
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
                        title: "Conversation Title",
                        type: "text",
                        name: document.querySelector('select[name="model_name"]').value
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
            
            this.isLoading = true;
            
            try {
                // First add the user message
                const messageResponse = await fetch(`/conversations/${this.currentConversation.id}/messages`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        role: 'user',
                        content: this.newMessage,
                        metadata: {}
                    })
                });

                if (!messageResponse.ok) throw new Error('Failed to send message');

                // Then generate the AI response
                const generateResponse = await fetch('/htmx/generate/text/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        prompt: this.newMessage,
                        conversation_id: this.currentConversation.id,
                        type: 'text',
                        name: document.querySelector('select[name="model_name"]').value,
                        max_length: 1000,
                        temperature: 0.7
                    })
                });

                if (!generateResponse.ok) throw new Error('Failed to generate response');

                // Clear the input after successful send
                this.newMessage = '';
                
                // Refresh messages
                await this.loadMessages(this.currentConversation.id);

            } catch (error) {
                console.error('Error sending message:', error);
                // Add error handling UI feedback here
            } finally {
                this.isLoading = false;
            }
        },
        
        scrollToBottom() {
            const container = this.$refs.messageContainer;
            container.scrollTop = container.scrollHeight;
        },
        
        async startNewConversation(type = 'text') {
            try {
                const modelSelect = document.querySelector('select[name="model_name"]');
                if (!modelSelect) {
                    console.error('Model selection not found');
                    return;
                }

                const response = await fetch('/conversations/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        title: type === 'text' ? 'New Text Chat' : 'New Image Chat',
                        type: type,
                        name: modelSelect.value
                    })
                });

                if (!response.ok) {
                    const error = await response.json();
                    console.error('Failed to create conversation:', error);
                    return;
                }

                const data = await response.json();
                await this.loadConversations();
                await this.loadConversation(data.id);
            } catch (error) {
                console.error('Error creating conversation:', error);
            }
        },
        
        async loadConversations() {
            try {
                const response = await fetch('/conversations/');
                if (!response.ok) {
                    console.error('Failed to load conversations');
                    return;
                }
                this.conversations = await response.json();
            } catch (error) {
                console.error('Error loading conversations:', error);
                this.conversations = [];
            }
        },
        
        async loadConversation(id) {
            if (!id) {
                console.log('No conversation ID provided');
                return;
            }
            // ... rest of loadConversation logic
        }
    };
} */