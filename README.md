# 🤖 HuggingScrape - AI-Powered Web Interface

HuggingScrape provides an elegant Gradio interface for AI-powered web automation. Simply describe your task in plain English, and watch as the AI navigates and interacts with websites through our intuitive interface.

## 🎨 Interface Features

### Multi-Model Support
- **OpenAI Integration**: Leverage GPT-4 Vision for advanced visual understanding
- **Anthropic Models**: Access Claude-3 Opus and Sonnet for sophisticated reasoning
- **Google AI**: Utilize Gemini's powerful models for diverse tasks
- **Easy Switching**: Seamlessly switch between AI providers through the dropdown menu

### Visual Task Recording
- **Live GIF Generation**: Watch your automation tasks unfold in real-time
- **Downloadable Recordings**: Save and share your automation sessions
- **Visual Feedback**: See exactly how the AI interacts with websites
- **Progress Tracking**: Monitor task completion through the interface

### User-Friendly Controls
- **Task Description Box**: Write natural language instructions
- **Secure API Key Input**: Safely enter and manage API keys
- **Provider Selection**: Choose your preferred AI model provider
- **Model Selection**: Pick specific models based on your needs
- **Run Task Button**: One-click execution of your automation tasks

### Real-Time Output
- **Task Results Display**: See extracted data and task outcomes immediately
- **Error Handling**: Clear feedback when issues occur
- **Progress Updates**: Follow along as your task executes
- **Visual Results**: View both text output and visual recordings

## 🚀 Quick Start

1. Launch the interface:
```bash
uv run interface.py
```

2. Configure your environment:
```env
ANTHROPIC_API_KEY=your_claude_api_key  # For Claude models
OPENAI_API_KEY=your_openai_api_key    # For GPT-4 Vision
GOOGLE_API_KEY=your_google_api_key    # For Gemini models
```

3. Access the interface:
- Open your browser to the provided local URL
- Select your preferred AI provider
- Enter your API key
- Describe your task
- Click "Run Task" and watch the magic happen!

## 💡 Example Tasks

The interface excels at tasks like:
```
"Find the best-selling products on Amazon"
"Extract contact information from a company website"
"Compare prices across multiple e-commerce sites"
"Fill out a web form with specific information"
```

## 🎯 Interface Layout

```
┌─────────────────────────────────────┐
│        HuggingScrape Header         │
├───────────────────┬─────────────────┤
│   Control Panel   │  Output Panel   │
│ ┌───────────────┐ │ ┌─────────────┐ │
│ │  AI Provider  │ │ │    Task     │ │
│ │   API Key     │ │ │   Output    │ │
│ │     Task      │ │ │             │ │
│ │    Model      │ │ │             │ │
│ │   Run Task    │ │ │             │ │
│ └───────────────┘ │ └─────────────┘ │
│                   │ ┌─────────────┐ │
│                   │ │  Recording  │ │
│                   │ │    View     │ │
│                   │ └─────────────┘ │
└───────────────────┴─────────────────┘
```

## 🔧 Technical Requirements

- Python 3.12 or higher
- UV package manager
- Required Python packages:
  - gradio
  - langchain_openai
  - langchain_anthropic
  - langchain_google_genai
  - python-dotenv

## 🚨 Troubleshooting Interface Issues

- **API Key Errors**: Verify API key is correctly entered and valid
- **Model Selection**: Ensure selected model matches the API provider
- **Recording Issues**: Check if task completed successfully
- **Display Problems**: Verify browser compatibility and refresh

---

Built with Gradio 🎨 and HuggingFace 🤗
