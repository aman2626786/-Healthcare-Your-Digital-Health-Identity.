/**
 * Chatbot logic for Swasthya Sampark
 * Connects to n8n webhook via POST request
 */

document.addEventListener('DOMContentLoaded', () => {
    // UI Elements
    const toggleBtn = document.getElementById('chatbot-toggle-btn');
    const closeBtn = document.getElementById('chatbot-close-btn');
    const chatbotWindow = document.getElementById('chatbot-window');
    const messagesContainer = document.getElementById('chatbot-messages');
    const inputField = document.getElementById('chatbot-input');
    const sendBtn = document.getElementById('chatbot-send-btn');

    // N8N Webhook Configuration
    const WEBHOOK_URL = 'http://localhost:5678/webhook/c9e7ec7e-48c6-46f1-9cc9-986991332820';
    
    // Generate an anonymous session ID so n8n can preserve memory conversation
    let sessionId = localStorage.getItem('swasthya_chatbot_session_id');
    if (!sessionId) {
        sessionId = 'session_' + Math.random().toString(36).substring(2, 15);
        localStorage.setItem('swasthya_chatbot_session_id', sessionId);
    }

    let isWaitingForResponse = false;

    // --- Core Logic ---

    // Toggle Window Visibility
    function toggleChat() {
        if (chatbotWindow.classList.contains('chatbot-visible')) {
            chatbotWindow.classList.remove('chatbot-visible');
        } else {
            chatbotWindow.classList.add('chatbot-visible');
            inputField.focus();
            
            // Add welcome message if chat is empty
            if (messagesContainer.children.length === 0) {
                appendMessage('bot', 'Hello! I am the Swasthya Sampark AI Assistant. How can I help you today?');
            }
        }
    }

    // Add a message bubble to the chat container
    function appendMessage(sender, text) {
        const msgDiv = document.createElement('div');
        msgDiv.classList.add('chat-message', sender);
        
        // Simple markdown and newline formatting
        let formattedText = text
            .replace(/\n/g, '<br>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>');
        
        msgDiv.innerHTML = formattedText;
        
        // Remove loading state if it exists when bot responds
        removeLoadingIndicator();
        
        messagesContainer.appendChild(msgDiv);
        scrollToBottom();
    }

    // Add animated loading indicator
    function showLoadingIndicator() {
        const loadingDiv = document.createElement('div');
        loadingDiv.classList.add('chat-loading');
        loadingDiv.id = 'chatbot-loading-indicator';
        loadingDiv.innerHTML = '<div class="dot"></div><div class="dot"></div><div class="dot"></div>';
        messagesContainer.appendChild(loadingDiv);
        scrollToBottom();
    }

    function removeLoadingIndicator() {
        const loadingDiv = document.getElementById('chatbot-loading-indicator');
        if (loadingDiv) {
            loadingDiv.remove();
        }
    }

    function scrollToBottom() {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    // Send the user input to n8n webhook
    async function sendMessage() {
        const text = inputField.value.trim();
        if (!text || isWaitingForResponse) return;

        // Update UI: Add user message, clear input, show loader
        appendMessage('user', text);
        inputField.value = '';
        isWaitingForResponse = true;
        sendBtn.disabled = true;
        showLoadingIndicator();

        try {
            // Standard N8N AI Agent expects `chatInput` or similar. 
            // We pass sessionId for memory nodes.
            const payload = {
                sessionId: sessionId,
                chatInput: text,
                message: text // sending both in case n8n expects `message` instead of `chatInput`
            };

            const response = await fetch(WEBHOOK_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }

            // Attempt to parse JSON response sent by Respond To Webhook N8N node
            let data = await response.json();
            
            // If n8n returns an array (e.g. [{"output": "..."}]), extract the first object
            if (Array.isArray(data) && data.length > 0) {
                data = data[0];
            }
            
            // Extract the bot's text response. N8n AI agent usually returns 'output'.
            // Fallback to 'string' response if no output field.
            let replyText = "I'm sorry, I couldn't understand the response from the server.";
            
            if (data.output) {
                replyText = data.output;
            } else if (data.text) {
                replyText = data.text;
            } else if (data.response) {
                replyText = data.response;
            } else if (typeof data === 'string') {
                replyText = data;
            } else if (data.choices && data.choices[0] && data.choices[0].message) {
                // OpenAI format fallback
                replyText = data.choices[0].message.content;
            } else {
                // Return stringified JSON if we can't find a direct text field
                replyText = typeof data === 'object' ? JSON.stringify(data) : String(data);
            }

            appendMessage('bot', replyText);

        } catch (error) {
            console.error('Chatbot Webhook Error:', error);
            appendMessage('bot', 'Sorry, I am having trouble connecting to the server. Please check if the automation workflow is running. Error: ' + error.message);
        } finally {
            // Restore UI state
            isWaitingForResponse = false;
            sendBtn.disabled = false;
            inputField.focus();
        }
    }

    // --- Event Listeners ---

    // Toggle button click
    toggleBtn.addEventListener('click', toggleChat);
    
    // Header Close button click
    closeBtn.addEventListener('click', () => chatbotWindow.classList.remove('chatbot-visible'));

    // Send button click
    sendBtn.addEventListener('click', sendMessage);

    // Enter key press in input field
    inputField.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault(); // Prevent accidental form submissions if any
            sendMessage();
        }
    });

});
