document.addEventListener('DOMContentLoaded', function() {
    const toggleBtn = document.getElementById('toggleExtension');
    const toggleText = toggleBtn.querySelector('.toggle-text');
    const statusDot = document.getElementById('statusDot');
    const statusText = document.getElementById('statusText');
    const statusDescription = document.getElementById('statusDescription');
    
    // Check if extension is enabled for current tab
    chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
        const currentTab = tabs[0];
        const currentDomain = currentTab.url ? new URL(currentTab.url).hostname : '';
        
        chrome.storage.local.get(['enabledTabs'], function(result) {
            const enabledTabs = result.enabledTabs || [];
            const isEnabled = enabledTabs.includes(currentDomain);
            
            updateUI(isEnabled);
        });
    });
    
    toggleBtn.addEventListener('click', function() {
        chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
            const currentTab = tabs[0];
            const currentDomain = currentTab.url ? new URL(currentTab.url).hostname : '';
            
            chrome.storage.local.get(['enabledTabs'], function(result) {
                const enabledTabs = result.enabledTabs || [];
                const isEnabled = enabledTabs.includes(currentDomain);
                
                if (isEnabled) {
                    // Disable extension
                    const newEnabledTabs = enabledTabs.filter(domain => domain !== currentDomain);
                    chrome.storage.local.set({enabledTabs: newEnabledTabs});
                    updateUI(false);
                    
                    // Reload the page to remove content script
                    chrome.tabs.reload(currentTab.id);
                } else {
                    // Enable extension
                    enabledTabs.push(currentDomain);
                    chrome.storage.local.set({enabledTabs: enabledTabs});
                    updateUI(true);
                    
                    // Reload the page to inject content script
                    chrome.tabs.reload(currentTab.id);
                }
            });
        });
    });
    
    function updateUI(isEnabled) {
        if (isEnabled) {
            // Extension is enabled
            statusDot.classList.remove('inactive');
            statusDot.classList.add('active');
            statusText.textContent = 'Active on this page';
            statusDescription.textContent = 'Look for the privacy icon in text fields. Click it to get AI-safe suggestions!';
            toggleText.textContent = 'Disable LayerZero';
            toggleBtn.classList.remove('enable');
            toggleBtn.classList.add('disable');
        } else {
            // Extension is disabled
            statusDot.classList.remove('active');
            statusDot.classList.add('inactive');
            statusText.textContent = 'Inactive on this page';
            statusDescription.textContent = 'Enable LayerZero to see the privacy icon in text fields and get AI-safe suggestions!';
            toggleText.textContent = 'Enable LayerZero';
            toggleBtn.classList.remove('disable');
            toggleBtn.classList.add('enable');
        }
    }
});