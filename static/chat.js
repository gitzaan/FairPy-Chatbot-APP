document.addEventListener('DOMContentLoaded', (event) => {
    const chatBox = document.getElementById('chat-box');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');

    // Get the customer name from the reservation details
    const customerName = document.getElementById('customer-name').textContent.trim();

    // Function to add a message to the chat box
    function addMessage(message, isUser = false) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message');
        messageElement.classList.add(isUser ? 'user-message' : 'assistant-message');
        
        // Use markdown rendering and handle newlines (\n)
        const formattedMessage = marked.parse(message.replace(/\n/g, '<br>'));
        messageElement.innerHTML = formattedMessage; // Set HTML content to support bold, newlines, etc.
        
        chatBox.appendChild(messageElement);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    // Add initial welcome message with customer's name
    addMessage(`Welcome, ${customerName}! How can I assist you with your reservation today?`);

    // Function to send a message to the server
    async function sendMessage(message) {
        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: message }),
            });
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            const data = await response.json();
            addMessage(data.reply); // Append the assistant's reply to the chat box
        } catch (error) {
            console.error('Error:', error);
            addMessage('Sorry, there was an error processing your request. Please try again.');
        }
    }

    // Event listener for send button
    sendButton.addEventListener('click', () => {
        const message = userInput.value.trim();
        if (message) {
            addMessage(message, true); // Add the user's message to the chat box
            sendMessage(message); // Send the message to the server
            userInput.value = ''; // Clear input after sending
        }
    });

    // Event listener for Enter key
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendButton.click();
        }
    });
});
