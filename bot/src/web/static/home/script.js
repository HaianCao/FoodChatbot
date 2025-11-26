// Configuration
const API_ENDPOINT = '/api/chat'; // Update this to your backend endpoint
const RESET_ENDPOINT = '/api/reset'; // Reset conversation endpoint

// DOM Elements
const chatMessages = document.getElementById('chatMessages');
const chatForm = document.getElementById('chatForm');
const userInput = document.getElementById('userInput');
const sendButton = document.getElementById('sendButton');
const resetButton = document.getElementById('resetButton');
const typingIndicator = document.getElementById('typingIndicator');

// Auto-resize textarea
userInput.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = (this.scrollHeight) + 'px';
});

// Handle key press (Enter to send, Shift+Enter for new line)
function handleKeyPress(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage(event);
    }
}

// Send message
async function sendMessage(event) {
    if (event) {
        event.preventDefault();
    }

    const message = userInput.value.trim();
    if (!message) return;

    // Add user message to chat
    appendMessage('user', message);
    
    // Clear input
    userInput.value = '';
    userInput.style.height = 'auto';
    
    // Disable send button
    sendButton.disabled = true;
    
    // Show typing indicator
    showTypingIndicator();

    try {
        // Send message to backend
        const response = await fetch(API_ENDPOINT, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                conversation_history: getConversationHistory()
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        
        // Hide typing indicator
        hideTypingIndicator();
        
        // Add bot response to chat
        appendMessage('bot', data.response, data.sources);

    } catch (error) {
        console.error('Error:', error);
        hideTypingIndicator();
        appendMessage('bot', '❌ Sorry, I encountered an error. Please make sure the backend server is running and try again.', null, true);
    } finally {
        // Re-enable send button
        sendButton.disabled = false;
        userInput.focus();
    }
}

// Append message to chat
function appendMessage(sender, text, sources = null, isError = false) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message ${isError ? 'error-message' : ''}`;

    if (sender === 'bot') {
        messageDiv.innerHTML = `
            <div class="message-avatar">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 2C6.48 2 2 6.48 2 12C2 17.52 6.48 22 12 22C17.52 22 22 17.52 22 12C22 6.48 17.52 2 12 2ZM12 5C13.66 5 15 6.34 15 8C15 9.66 13.66 11 12 11C10.34 11 9 9.66 9 8C9 6.34 10.34 5 12 5ZM12 19.2C9.5 19.2 7.29 17.92 6 15.98C6.03 13.99 10 12.9 12 12.9C13.99 12.9 17.97 13.99 18 15.98C16.71 17.92 14.5 19.2 12 19.2Z" fill="currentColor"/>
                </svg>
            </div>
            <div class="message-content">
                <div class="message-text">
                    ${formatMessage(text)}
                    ${sources && sources.length > 0 ? formatSources(sources) : ''}
                </div>
            </div>
        `;
    } else {
        messageDiv.innerHTML = `
            <div class="message-avatar">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 2C6.48 2 2 6.48 2 12C2 17.52 6.48 22 12 22C17.52 22 22 17.52 22 12C22 6.48 17.52 2 12 2ZM12 5C13.66 5 15 6.34 15 8C15 9.66 13.66 11 12 11C10.34 11 9 9.66 9 8C9 6.34 10.34 5 12 5ZM12 19.2C9.5 19.2 7.29 17.92 6 15.98C6.03 13.99 10 12.9 12 12.9C13.99 12.9 17.97 13.99 18 15.98C16.71 17.92 14.5 19.2 12 19.2Z" fill="currentColor"/>
                </svg>
            </div>
            <div class="message-content">
                <div class="message-text">
                    ${escapeHtml(text)}
                </div>
            </div>
        `;
    }

    chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

// Format bot message (preserve line breaks and basic formatting)
function formatMessage(text) {
    // Extract URLs BEFORE escaping HTML (works with any language)
    const urlRegex = /https?:\/\/[^\s]+/gi;
    let sourceLink = null;
    const urls = text.match(urlRegex);
    
    if (urls && urls.length > 0) {
        // Get the last URL (usually the source at the end)
        sourceLink = urls[urls.length - 1];
        // Remove URL and the line containing it from text
        const lines = text.split('\n');
        text = lines.filter(line => !line.includes(sourceLink)).join('\n');
    }
    
    // Now escape HTML
    text = escapeHtml(text);
    
    // Convert markdown-style formatting
    text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>'); // Bold
    text = text.replace(/\*(.*?)\*/g, '<em>$1</em>'); // Italic
    text = text.replace(/\n/g, '<br>'); // Line breaks
    
    // Convert lists
    text = text.replace(/^- (.*?)$/gm, '<li>$1</li>');
    text = text.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
    
    // Add source link preview if exists
    if (sourceLink) {
        text += formatSourcePreview(sourceLink);
    }
    
    return text;
}

// Format source preview with clickable link (like messaging apps)
function formatSourcePreview(url) {
    const previewId = 'preview-' + Math.random().toString(36).substr(2, 9);
    
    // Create placeholder with loading state
    const placeholder = `
        <a href="${url}" target="_blank" rel="noopener noreferrer" class="link-preview-card" id="${previewId}">
            <div class="link-preview-image loading">
                <div class="loading-spinner"></div>
            </div>
            <div class="link-preview-content">
                <div class="link-preview-title">Loading preview...</div>
                <div class="link-preview-domain">${new URL(url).hostname.replace('www.', '')}</div>
            </div>
            <div class="link-preview-arrow">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M10 6L8.59 7.41L13.17 12L8.59 16.59L10 18L16 12L10 6Z" fill="currentColor"/>
                </svg>
            </div>
        </a>
    `;
    
    // Fetch preview data asynchronously
    fetchLinkPreview(url, previewId);
    
    return placeholder;
}

// Fetch link preview metadata
async function fetchLinkPreview(url, previewId) {
    try {
        // Using microlink.io API (free tier)
        const apiUrl = `https://api.microlink.io?url=${encodeURIComponent(url)}`;
        const response = await fetch(apiUrl);
        const data = await response.json();
        
        if (data.status === 'success') {
            const { title, description, image } = data.data;
            const domain = new URL(url).hostname.replace('www.', '');
            
            // Update preview card with actual data
            const card = document.getElementById(previewId);
            if (card) {
                card.innerHTML = `
                    ${image ? `
                        <div class="link-preview-image">
                            <img src="${image.url}" alt="${title || 'Recipe'}" onerror="this.parentElement.innerHTML='<svg viewBox=\\'0 0 24 24\\' fill=\\'none\\'><path d=\\'M12 2L2 7V17C2 20.31 4.69 22 12 22C19.31 22 22 20.31 22 17V7L12 2Z\\' fill=\\'currentColor\\'/></svg>'">
                        </div>
                    ` : `
                        <div class="link-preview-image">
                            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <path d="M12 2L2 7V17C2 20.31 4.69 22 12 22C19.31 22 22 20.31 22 17V7L12 2Z" fill="currentColor"/>
                            </svg>
                        </div>
                    `}
                    <div class="link-preview-content">
                        <div class="link-preview-title">${title || 'Recipe'}</div>
                        <div class="link-preview-domain">${domain}</div>
                    </div>
                    <div class="link-preview-arrow">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M10 6L8.59 7.41L13.17 12L8.59 16.59L10 18L16 12L10 6Z" fill="currentColor"/>
                        </svg>
                    </div>
                `;
            }
        }
    } catch (error) {
        console.log('Preview fetch failed, using fallback:', error);
        // Keep the loading placeholder or show fallback
    }
}

// Format sources
function formatSources(sources) {
    if (!sources || sources.length === 0) return '';
    
    let html = '<div class="message-sources"><div class="message-sources-title">📚 Sources:</div>';
    sources.forEach(source => {
        html += `<div class="source-item">${escapeHtml(source)}</div>`;
    });
    html += '</div>';
    return html;
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Show typing indicator
function showTypingIndicator() {
    typingIndicator.classList.add('active');
    scrollToBottom();
}

// Hide typing indicator
function hideTypingIndicator() {
    typingIndicator.classList.remove('active');
}

// Scroll to bottom of chat
function scrollToBottom() {
    setTimeout(() => {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }, 100);
}

// Get conversation history
function getConversationHistory() {
    const messages = chatMessages.querySelectorAll('.message:not(.error-message)');
    const history = [];
    
    messages.forEach(msg => {
        if (msg.classList.contains('user-message')) {
            const text = msg.querySelector('.message-text').textContent.trim();
            history.push({ role: 'user', content: text });
        } else if (msg.classList.contains('bot-message')) {
            const text = msg.querySelector('.message-text').textContent.trim();
            history.push({ role: 'assistant', content: text });
        }
    });
    
    return history;
}

// Clear chat
function clearChat() {
    if (confirm('Are you sure you want to clear the conversation?')) {
        // Remove all messages except the welcome message
        const messages = chatMessages.querySelectorAll('.message');
        messages.forEach((msg, index) => {
            if (index > 0) { // Keep first message (welcome)
                msg.remove();
            }
        });
        
        // Clear input
        userInput.value = '';
        userInput.style.height = 'auto';
        userInput.focus();
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    userInput.focus();
    scrollToBottom();
    
    // Add example queries as quick actions (optional)
    addExampleQueries();
});

// Add example queries
function addExampleQueries() {
    const examples = [
        "Show me the 10 lowest calorie dishes",
        "What are the highest protein recipes?",
        "Món ăn có ít hơn 5mg sắt",
        "Find recipes with less than 500 calories"
    ];
    
    // You can uncomment this to add quick action buttons
    // const examplesDiv = document.createElement('div');
    // examplesDiv.className = 'example-queries';
    // examples.forEach(example => {
    //     const btn = document.createElement('button');
    //     btn.textContent = example;
    //     btn.onclick = () => {
    //         userInput.value = example;
    //         userInput.focus();
    //     };
    //     examplesDiv.appendChild(btn);
    // });
    // chatMessages.appendChild(examplesDiv);
}

// Reset conversation
async function resetConversation() {
    try {
        // Disable reset button during operation
        resetButton.disabled = true;
        resetButton.innerHTML = `
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" fill="none"/>
                <path d="m15 9-6 6" stroke="currentColor" stroke-width="2"/>
                <path d="m9 9 6 6" stroke="currentColor" stroke-width="2"/>
            </svg>
            Resetting...
        `;
        
        // Call reset API
        const response = await fetch(RESET_ENDPOINT, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Clear chat messages (keep welcome message)
        clearChatMessages();
        
        // Show success message
        appendMessage('bot', '✅ Conversation has been reset successfully. How can I help you today?');
        
        console.log('Conversation reset:', data.message);
        
    } catch (error) {
        console.error('Reset failed:', error);
        appendMessage('bot', '❌ Failed to reset conversation. Please try again.', null, true);
    } finally {
        // Re-enable reset button
        resetButton.disabled = false;
        resetButton.innerHTML = `
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M17.65 6.35C16.2 4.9 14.21 4 12 4C7.58 4 4 7.58 4 12S7.58 20 12 20C15.73 20 18.84 17.45 19.73 14H17.65C16.83 16.33 14.61 18 12 18C8.69 18 6 15.31 6 12S8.69 6 12 6C13.66 6 15.14 6.69 16.22 7.78L13 11H20V4L17.65 6.35Z" fill="currentColor"/>
            </svg>
            Reset
        `;
    }
}

// Clear chat messages except welcome message
function clearChatMessages() {
    // Find all messages except the first welcome message
    const messages = chatMessages.querySelectorAll('.message');
    for (let i = 1; i < messages.length; i++) {
        messages[i].remove();
    }
    
    // Scroll to top
    chatMessages.scrollTop = 0;
}

// Show/hide typing indicator functions
function showTypingIndicator() {
    typingIndicator.style.display = 'flex';
    scrollToBottom();
}

function hideTypingIndicator() {
    typingIndicator.style.display = 'none';
}

// Scroll to bottom of chat
function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Get conversation history (optional for this implementation)
function getConversationHistory() {
    // For this implementation, we'll return empty as conversation context
    // is maintained on the server side
    return [];
}

// Handle connection errors
window.addEventListener('online', () => {
    console.log('Connection restored');
});

window.addEventListener('offline', () => {
    appendMessage('bot', '⚠️ You are offline. Please check your internet connection.', null, true);
});