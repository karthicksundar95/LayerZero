# LayerZero - Privacy at Layer Zero

**The foundational privacy layer for AI**

LayerZero is a comprehensive privacy protection system that sanitizes user input before it reaches AI models, ensuring personal information remains secure while preserving the intent and answerability of queries.

## 🔒 Overview

LayerZero provides three levels of privacy protection:

- **Masked**: Replaces personally identifiable information (PII) with clear placeholders
- **Rephrased**: Rewords input to remove personal references while maintaining context
- **Synthetic**: Creates fictional scenarios that preserve the original question's intent

## 🏗️ Architecture

The system consists of three main components:

### 1. Flask Backend (`app.py`)
- RESTful API server running on port 5001
- Handles text sanitization requests
- Integrates with Ollama for AI processing
- Implements CORS for Chrome extension compatibility
- Includes timeout handling and error management

### 2. AI Processing Engine (`privacy_ai.py`)
- Manages Ollama server lifecycle
- Processes text through AI models (currently using Gemma2:2b)
- Implements sophisticated prompt engineering for privacy protection
- Handles JSON parsing and fallback mechanisms
- Supports both text and non-text content (code, terminal output, etc.)

### 3. Chrome Extension (`chrome_extension/`)
- Browser extension for seamless integration
- Detects text input fields across websites
- Provides privacy icons for user interaction
- Displays sanitization suggestions in elegant UI panels
- Supports per-domain enable/disable functionality

## 🚀 Features

### Privacy Protection Modes

#### Masked Mode
- Replaces names, addresses, locations, dates with `[NAME]`, `[ADDRESS]`, `[LOCATION]`, `[DATE]`
- Preserves code structure and technical content
- Maintains original formatting and intent

#### Rephrased Mode
- Removes personal references while keeping questions intact
- Maintains technical accuracy for code and terminal output
- Preserves the core request or question

#### Synthetic Mode
- Creates fictional scenarios with generic characters
- Maintains the original question's context and answerability
- Generates safe alternatives for sensitive content

### Smart Content Detection
- Automatically classifies text vs. non-text content
- Handles code snippets, terminal commands, and error messages
- Preserves technical information while sanitizing personal data
- Maintains code structure and functionality

### Browser Integration
- Seamless Chrome extension with modern UI
- Automatic detection of text input fields
- Per-domain enable/disable functionality
- Real-time privacy suggestions
- Elegant suggestion panels with one-click application

## 📦 Installation

### Prerequisites
- Python 3.9+
- Ollama installed and configured
- Chrome browser for extension

### Backend Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd LayerZero
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install flask flask-cors ollama requests
   ```

4. **Install and configure Ollama**
   ```bash
   # Install Ollama (visit https://ollama.ai for installation instructions)
   ollama pull gemma2:2b
   ```

5. **Start the Flask server**
   ```bash
   python app.py
   ```
   The server will run on `http://localhost:5001`

### Chrome Extension Setup

1. **Load the extension**
   - Open Chrome and navigate to `chrome://extensions/`
   - Enable "Developer mode"
   - Click "Load unpacked" and select the `chrome_extension` folder

2. **Configure permissions**
   - The extension will request permissions for active tab access
   - Grant permissions to allow text field detection

3. **Enable on desired websites**
   - Click the LayerZero extension icon
   - Toggle the extension on/off for specific domains
   - The extension will reload the page to activate

## 🔧 Configuration

### Model Configuration
Edit `privacy_ai.py` to change the AI model:
```python
OLLAMA_MODEL = "gemma2:2b"  # Change to your preferred model
```

### Server Configuration
Modify `app.py` for different ports or CORS settings:
```python
app.run(host='0.0.0.0', port=5001, debug=True)
```

### Extension Permissions
Update `chrome_extension/manifest.json` for different host permissions:
```json
"host_permissions": [
    "http://localhost:5001/*",
    "http://127.0.0.1:5001/*"
]
```

## 📖 Usage

### Web Interface
1. Navigate to any website with text input fields
2. Enable LayerZero for the domain using the extension popup
3. Look for the privacy shield icon (🔒) in text fields
4. Click the icon to get privacy suggestions
5. Choose from Masked, Rephrased, or Synthetic options
6. Click any suggestion to apply it to the text field

### API Usage
Send POST requests to `http://localhost:5001/sanitize`:

```bash
curl -X POST http://localhost:5001/sanitize \
  -H "Content-Type: application/json" \
  -d '{"text": "I am John and I live in New York at 123 Main St. What is the best pizza place near me?"}'
```

Response:
```json
{
  "Masked": "I am [NAME] and I live in [LOCATION] at [ADDRESS]. What is the best pizza place near me?",
  "Rephrased": "What is the best pizza place near 123 Main St, New York?",
  "Synthetic": "Alex lives in a big city and is searching for the best pizza place near his home on Main St. What is the best pizza place near him?"
}
```

## 🛠️ Development

### Project Structure
```
LayerZero/
├── app.py                 # Flask backend server
├── privacy_ai.py          # AI processing engine
├── setup.py              # Package configuration
├── src/
│   ├── prompt.py         # Basic prompt template
│   └── prompt_detailed.py # Advanced prompt with examples
└── chrome_extension/
    ├── manifest.json     # Extension configuration
    ├── background.js     # Service worker
    ├── content.js        # Content script
    ├── popup.html        # Extension popup UI
    ├── popup.js          # Popup functionality
    ├── styles.css        # Popup styling
    ├── content.css       # Content script styling
    └── images/           # Extension icons
```

### Key Components

#### Prompt Engineering (`src/prompt_detailed.py`)
- Sophisticated prompt templates for different content types
- Examples for text, code, and terminal output
- Instructions for maintaining intent while preserving privacy

#### Error Handling (`privacy_ai.py`)
- Robust JSON parsing with fallback mechanisms
- Regex-based extraction for malformed responses
- Timeout handling and server management

#### Browser Integration (`chrome_extension/`)
- Modern Chrome extension architecture (Manifest V3)
- Dynamic content script injection
- Elegant UI with Apple-inspired design
- Real-time suggestion panels

## 🔍 Testing

### Backend Testing
```bash
# Test server health
curl http://localhost:5001/

# Test sanitization endpoint
curl -X POST http://localhost:5001/sanitize \
  -H "Content-Type: application/json" \
  -d '{"text": "Your test text here"}'
```

### Extension Testing
1. Load the extension in Chrome
2. Navigate to a test website (e.g., Google, GitHub)
3. Enable LayerZero for the domain
4. Test text input fields for privacy icon appearance
5. Verify suggestion functionality

## 🚨 Troubleshooting

### Common Issues

#### Ollama Server Not Starting
- Ensure Ollama is installed: `ollama --version`
- Check if the model is available: `ollama list`
- Pull the required model: `ollama pull gemma2:2b`

#### Extension Not Working
- Check Chrome extension permissions
- Verify the Flask server is running on port 5001
- Check browser console for errors
- Reload the extension if needed

#### CORS Issues
- Ensure Flask server includes proper CORS headers
- Check that extension manifest includes correct host permissions
- Verify server is running on the expected port

#### JSON Parsing Errors
- Check Ollama model output format
- Verify prompt template is correctly formatted
- Review server logs for detailed error messages

## 🔒 Privacy & Security

### Data Handling
- All processing happens locally via Ollama
- No data is sent to external services
- Text is processed in memory and not stored
- Extension only communicates with local Flask server

### Security Considerations
- Extension requests minimal permissions
- Server runs locally with CORS restrictions
- No persistent storage of user data
- All communications are localhost-only

## 🔮 Development Roadmap

### Current Architecture Considerations
LayerZero currently uses local Ollama processing, which provides complete privacy but requires local setup. We're actively developing more user-friendly alternatives:

#### Planned Improvements
- **Browser-Native Processing**: WebLLM/Transformer.js integration for in-browser LLM execution
- **Cloud API Option**: Hosted service alternative with privacy controls
- **Hybrid Architecture**: Flexible deployment options based on user preferences

### Performance Optimization
- Smaller model variants for reduced resource usage
- Docker containerization for easier deployment
- Resource monitoring and optimization tools

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

### Development Guidelines
- Follow Python PEP 8 style guidelines
- Use meaningful variable and function names
- Add comments for complex logic
- Test all functionality before submitting
- Update documentation as needed

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built with Flask and Ollama
- Chrome Extension API for browser integration
- Apple-inspired UI design principles
- Privacy-first development approach

## 📞 Support

For issues, questions, or contributions:
- Create an issue in the repository
- Check the troubleshooting section
- Review the code documentation
- Test with the provided examples

---

**LayerZero** - Protecting privacy at the foundational layer of AI interactions.
