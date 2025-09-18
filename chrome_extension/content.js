// Debug version - simpler and more robust
console.log('LayerZero content script loaded!');

class LayerZero {
    constructor() {
        console.log('LayerZero constructor called');
        this.textInputs = new Set();
        this.shieldIcons = new Map();
        this.suggestionPanels = new Map();
        this.isProcessing = new Set();
        this.isEnabled = false;
        this.init();
    }

    async init() {
        console.log('LayerZero init called');
        
        // Check if extension is enabled for this tab
        await this.checkIfEnabled();
        
        if (this.isEnabled) {
            this.findTextInputs();
            this.observeNewInputs();
            this.setupEventListeners();
        } else {
            console.log('LayerZero is disabled for this page');
        }
    }

    async checkIfEnabled() {
        return new Promise((resolve) => {
            // Get current tab ID from URL or use a different approach
            chrome.storage.local.get(['enabledTabs'], (result) => {
                const enabledTabs = result.enabledTabs || [];
                
                // Since we can't get tab ID in content script, we'll use a different approach
                // We'll check if the current URL is in the enabled list
                const currentUrl = window.location.href;
                const currentDomain = window.location.hostname;
                
                // Check if this domain is enabled
                const isDomainEnabled = enabledTabs.some(tab => {
                    if (typeof tab === 'string') {
                        return tab === currentDomain || tab === currentUrl;
                    }
                    return false;
                });
                
                this.isEnabled = isDomainEnabled;
                console.log('Extension enabled for this domain:', this.isEnabled);
                resolve();
            });
        });
    }

    findTextInputs() {
        if (!this.isEnabled) return;
        
        console.log('Finding text inputs...');
        const selectors = [
            'input[type="text"]',
            'input[type="email"]',
            'input[type="password"]',
            'input[type="search"]',
            'input[type="url"]',
            'textarea',
            '[contenteditable="true"]',
            '[contenteditable=""]'
        ];

        let foundInputs = 0;
        selectors.forEach(selector => {
            const inputs = document.querySelectorAll(selector);
            console.log(`Found ${inputs.length} inputs for selector: ${selector}`);
            inputs.forEach(input => {
                this.addShieldIcon(input);
                foundInputs++;
            });
        });
        console.log(`Total inputs found: ${foundInputs}`);
    }

    observeNewInputs() {
        if (!this.isEnabled) return;
        
        console.log('Setting up mutation observer...');
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                mutation.addedNodes.forEach((node) => {
                    if (node.nodeType === Node.ELEMENT_NODE) {
                        const inputs = node.querySelectorAll ? 
                            node.querySelectorAll('input, textarea, [contenteditable]') : [];
                        
                        inputs.forEach(input => {
                            this.addShieldIcon(input);
                        });
                    }
                });
            });
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }

    addShieldIcon(input) {
        if (!this.isEnabled || this.textInputs.has(input) || !this.isValidInput(input)) {
            return;
        }

        console.log('Adding privacy icon to input:', input);
        this.textInputs.add(input);
        
        // Create privacy icon
        const icon = this.createShieldIcon(input);
        this.shieldIcons.set(input, icon);

        // Position the icon
        this.positionIcon(input, icon);

        // Add event listeners
        this.setupInputListeners(input, icon);
    }

    createShieldIcon(input) {
        console.log('Creating privacy icon...');
        const icon = document.createElement('div');
        icon.className = 'layerzero-privacy-icon';
        icon.title = 'LayerZero - Click to sanitize text for AI safety';
        
        // Add click handler
        icon.addEventListener('click', (e) => {
            e.stopPropagation();
            console.log('Privacy icon clicked!');
            this.handleShieldClick(input, icon);
        });

        document.body.appendChild(icon);
        console.log('Privacy icon added to DOM');
        return icon;
    }

    positionIcon(input, icon) {
        const updatePosition = () => {
            const rect = input.getBoundingClientRect();
            const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
            const scrollLeft = window.pageXOffset || document.documentElement.scrollLeft;

            icon.style.position = 'absolute';
            icon.style.left = `${rect.right - 30 + scrollLeft}px`;
            icon.style.top = `${rect.top + 5 + scrollTop}px`;
            icon.style.zIndex = '9999';
            icon.style.display = 'none'; // Initially hidden
        };

        updatePosition();
        
        // Update position on scroll and resize
        window.addEventListener('scroll', updatePosition);
        window.addEventListener('resize', updatePosition);
    }

    setupInputListeners(input, icon) {
        let timeout;
        
        const showIcon = () => {
            clearTimeout(timeout);
            timeout = setTimeout(() => {
                // Show icon if there's text OR if the input is focused
                if (this.hasText(input) || document.activeElement === input) {
                    console.log('Showing privacy icon');
                    icon.style.display = 'block';
                } else {
                    console.log('Hiding privacy icon');
                    icon.style.display = 'none';
                }
            }, 300);
        };

        input.addEventListener('input', showIcon);
        input.addEventListener('focus', () => {
            console.log('Input focused, showing icon');
            icon.style.display = 'block';
        });
        input.addEventListener('blur', () => {
            setTimeout(() => {
                if (document.activeElement !== input) {
                    this.hideSuggestionPanel(input);
                    // Only hide icon if there's no text
                    if (!this.hasText(input)) {
                        console.log('Input blurred and empty, hiding icon');
                        icon.style.display = 'none';
                    }
                }
            }, 200);
        });

        // Initial check
        showIcon();
    }

    async handleShieldClick(input, icon) {
        console.log('Handling privacy icon click...');
        const text = this.getText(input);
        
        if (!text.trim()) {
            this.showNotification('Please enter some text first!', 'warning');
            return;
        }

        if (this.isProcessing.has(input)) {
            return;
        }

        this.isProcessing.add(input);
        this.showLoadingIcon(icon);
        this.hideSuggestionPanel(input);

        try {
            console.log('Getting suggestions for text:', text.substring(0, 50));
            const suggestions = await this.getSuggestions(text);
            console.log('Got suggestions:', suggestions);
            this.showSuggestionPanel(input, suggestions);
        } catch (error) {
            console.error('Error getting suggestions:', error);
            this.showDetailedError(error);
        } finally {
            this.isProcessing.delete(input);
            this.hideLoadingIcon(icon);
        }
    }

    async getSuggestions(text) {
        console.log('Sending request to background script...');
        
        // Check if chrome.runtime is available
        if (typeof chrome === 'undefined' || !chrome.runtime) {
            throw new Error('Chrome runtime not available');
        }
        
        return new Promise((resolve, reject) => {
            // Add timeout to prevent hanging
            const timeout = setTimeout(() => {
                reject(new Error('Request timeout - background script not responding'));
            }, 10000);
            
            chrome.runtime.sendMessage({
                action: 'sanitize',
                text: text
            }, (response) => {
                clearTimeout(timeout);
                
                if (chrome.runtime.lastError) {
                    console.error('Chrome runtime error:', chrome.runtime.lastError);
                    reject(new Error(chrome.runtime.lastError.message));
                    return;
                }
                
                if (!response) {
                    reject(new Error('No response from background script'));
                    return;
                }
                
                if (response.success) {
                    console.log('Background script response:', response.data);
                    resolve({
                        original: text,
                        masked: response.data.Masked || '',
                        rephrased: response.data.Rephrased || '',
                        synthetic: response.data.Synthetic || ''
                    });
                } else {
                    console.error('Background script error:', response.error);
                    reject(new Error(response.error));
                }
            });
        });
    }

    showDetailedError(error) {
        let message = 'Failed to get suggestions. ';
        
        if (error.message.includes('Chrome runtime not available')) {
            message += 'Extension context not available. Please reload the page.';
        } else if (error.message.includes('Request timeout')) {
            message += 'Background script not responding. Please check if Flask server is running.';
        } else if (error.message.includes('Failed to fetch')) {
            message += 'Cannot connect to server. Make sure Flask server is running on port 5001.';
        } else if (error.message.includes('Server error: 500')) {
            message += 'Server error occurred. Check server logs.';
        } else if (error.message.includes('Server error: 403')) {
            message += 'Access denied. CORS issue detected.';
        } else {
            message += error.message;
        }
        
        console.error('Error message:', message);
        this.showNotification(message, 'error');
    }

    showSuggestionPanel(input, suggestions) {
        console.log('Showing suggestion panel...');
        this.hideSuggestionPanel(input);

        const panel = document.createElement('div');
        panel.className = 'layerzero-suggestion-panel';
        
        panel.innerHTML = `
            <div class="panel-header">
                <span class="panel-title">LayerZero Privacy Suggestions</span>
                <button class="panel-close">×</button>
            </div>
            <div class="suggestions">
                <div class="suggestion-item masked" data-type="masked">
                    <div class="suggestion-label">Masked</div>
                    <div class="suggestion-text">${this.escapeHtml(suggestions.masked)}</div>
                </div>
                <div class="suggestion-item rephrased" data-type="rephrased">
                    <div class="suggestion-label">Rephrased</div>
                    <div class="suggestion-text">${this.escapeHtml(suggestions.rephrased)}</div>
                </div>
                <div class="suggestion-item synthetic" data-type="synthetic">
                    <div class="suggestion-label">Synthetic</div>
                    <div class="suggestion-text">${this.escapeHtml(suggestions.synthetic)}</div>
                </div>
            </div>
        `;

        // Add event listeners
        panel.querySelectorAll('.suggestion-item').forEach(item => {
            item.addEventListener('click', () => {
                const type = item.dataset.type;
                this.applySuggestion(input, suggestions[type]);
                this.hideSuggestionPanel(input);
            });
        });

        panel.querySelector('.panel-close').addEventListener('click', () => {
            this.hideSuggestionPanel(input);
        });

        document.body.appendChild(panel);
        this.suggestionPanels.set(input, panel);
        this.positionSuggestionPanel(input, panel);
    }

    positionSuggestionPanel(input, panel) {
        const rect = input.getBoundingClientRect();
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        const scrollLeft = window.pageXOffset || document.documentElement.scrollLeft;

        panel.style.position = 'absolute';
        panel.style.left = `${rect.left + scrollLeft}px`;
        panel.style.top = `${rect.bottom + 5 + scrollTop}px`;
        panel.style.zIndex = '10000';
    }

    hideSuggestionPanel(input) {
        const panel = this.suggestionPanels.get(input);
        if (panel) {
            panel.remove();
            this.suggestionPanels.delete(input);
        }
    }

    applySuggestion(input, text) {
        if (input.tagName === 'TEXTAREA' || input.tagName === 'INPUT') {
            input.value = text;
            input.dispatchEvent(new Event('input', { bubbles: true }));
        } else if (input.contentEditable === 'true') {
            input.textContent = text;
            input.dispatchEvent(new Event('input', { bubbles: true }));
        }
        
        this.showNotification('Text updated successfully!', 'success');
    }

    showLoadingIcon(icon) {
        icon.innerHTML = '<div class="loading-spinner"></div>';
        icon.classList.add('loading');
    }

    hideLoadingIcon(icon) {
        icon.innerHTML = '';
        icon.classList.remove('loading');
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `layerzero-notification ${type}`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.classList.add('show');
        }, 100);
        
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        }, 5000);
    }

    // Utility functions
    isValidInput(input) {
        return input.offsetWidth > 0 && input.offsetHeight > 0 && !input.disabled;
    }

    hasText(input) {
        if (input.tagName === 'TEXTAREA' || input.tagName === 'INPUT') {
            return input.value.trim().length > 0;
        } else if (input.contentEditable === 'true') {
            return input.textContent.trim().length > 0;
        }
        return false;
    }

    getText(input) {
        if (input.tagName === 'TEXTAREA' || input.tagName === 'INPUT') {
            return input.value;
        } else if (input.contentEditable === 'true') {
            return input.textContent;
        }
        return '';
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    setupEventListeners() {
        // Hide panels when clicking outside
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.layerzero-suggestion-panel') && 
                !e.target.closest('.layerzero-privacy-icon')) {
                this.suggestionPanels.forEach((panel, input) => {
                    this.hideSuggestionPanel(input);
                });
            }
        });

        // Handle escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.suggestionPanels.forEach((panel, input) => {
                    this.hideSuggestionPanel(input);
                });
            }
        });
    }
}

// Initialize when DOM is ready
console.log('Content script starting...');

if (document.readyState === 'loading') {
    console.log('DOM still loading, waiting...');
    document.addEventListener('DOMContentLoaded', () => {
        console.log('DOM loaded, initializing LayerZero...');
        new LayerZero();
    });
} else {
    console.log('DOM already loaded, initializing LayerZero...');
    new LayerZero();
}

console.log('Content script loaded completely');
