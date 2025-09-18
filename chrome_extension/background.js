// Background script to handle API requests
console.log('Background script loaded');

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    console.log('Background script: Received message:', request);
    
    if (request.action === 'sanitize') {
        console.log('Background script: Processing sanitize request');
        
        fetch('http://localhost:5001/sanitize', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ text: request.text })
        })
        .then(response => {
            console.log('Background script: Response status:', response.status);
            if (!response.ok) {
                throw new Error(`Server error: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Background script: Response data:', data);
            sendResponse({ success: true, data: data });
        })
        .catch(error => {
            console.error('Background script: Error:', error);
            sendResponse({ success: false, error: error.message });
        });
        
        return true; // Keep message channel open for async response
    }
    
    // Handle other message types
    if (request.action === 'ping') {
        sendResponse({ success: true, message: 'Background script is alive' });
        return true;
    }
});

// Test if background script is working
chrome.runtime.onStartup.addListener(() => {
    console.log('Background script started');
});

chrome.runtime.onInstalled.addListener(() => {
    console.log('Background script installed');
});
