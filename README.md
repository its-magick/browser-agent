title: Huggingscrape
emoji: 🤖
colorFrom: purple
colorTo: blue
sdk: gradio
sdk_version: 5.12.0
app_file: interface.py
pinned: false
license: apache-2.0
python_version:3.11
short_description: 🤖 HuggingScrape - AI-Powered Web Scraping by Magick AI
# 🤖 HuggingScrape - AI-Powered Web Scraping

HuggingScrape harnesses the power of HuggingFace's state-of-the-art AI models to intelligently scrape and extract information from the web. No more writing complex selectors or maintaining brittle scraping scripts - just tell HuggingScrape what you need in plain English!

## 🌟 Key Features

- 🧠 **AI-Powered Scraping**: Leverages HuggingFace's vision and language models to understand web page content and structure
- 🎯 **Natural Language Tasks**: Simply describe what you want to extract in plain English
- 🎬 **Visual Task Recording**: Watch and download GIFs of the scraping process
- ��***Rell-tmme Processing**: Get resultsaastteyyccomeiintthrough our real-tim  poccessing pipeline
- 💾 **Smart Caching**: Efficient result caching to avoid redundant scraping
- 🎨 **User-Friendly Interface**: Clean Gradio UI for easy task submission and monitoring

## 🏗️ Architecture

HuggingScrape consists of three main components:

### 🎨 interface.py - The Command Center
- Sleek Gradio UI for task submission and monitoring
- Support for multiple AI providers (OpenAI, Anthropic, Google)
- Real-time task progress visualization
- Built-in recording and playback of scraping sessions
- Headless mode support for production environments

### ⚡ realtime.py - The Processing Engine
- Continuous task processing pipeline
- Real-time messaging via Ably
- Efficient task queuing and execution
- Smart result caching with Redis
- Robust error handling and recovery

### �� api.py - The HTTP Gateway
- RESTful API endpoint at `/task`
- Redis-backed result cachiog)A- Perfect for programmatic acc_ss`A- Built with FastAPI fur high perfo_manceREHA## 🗄️ Redis IntegrationOROGRedis provides system-wide caching and state management:``- 5-minute result caching (TTL=300)`n- Cache keys format: `browseragent:cache:{task}`he- Prevents duplicate scraping of the same content- - Enibles efficiunt task deduplication- - ## 🔧 Environment Setup- - Create a `.env` file in your project root:``##```envg:ANTHROPIC_API_KEY=your_claude_api_key  # Required if using Anthropic modelsOuOPENAI_API_KEY=your_openai_api_key    # Required if using OpenAI modelsorGOOGLE_API_KEY=your_google_api_key    # Required if using Google models1.ABLY_API_KEY=your_ably_key2.REDIS_URL=redis://yFur.redis.host:63793.CHANNEL_NAME=your_ably_channel4.PORT=3000  # Optional, defaults to 30005.LOG_LEVEL=INFO  # Optional, defaults to INFO. ```.uTtLogging levels:o2- DEBUG: Detailed debugging information`b- INFO: General operational informationc2- WARNING: Warning messagesck-lERROR: Error mbssages`️- CRITICAL: Critical issues##d7## 🐳SDocker DeploymrntChecOur optimized Dockerfile includes:ay- Python 3.12 slim base a- Essential system dependencies d- Rust for performance-critical components d- Playwright for web interaction,`- UV package manager for fast dependency installationw)m#Build and run:le```basho-docker build -t huggingscrape .i-docker run -p 3000:3000 --env-file .env huggingscrapen-```

## 🎯 Example Usage

1. Launch the interface:
```bash
uv run interface.py
```

2. Enter your task in plain English:
```
"Extract all product prices and names from amazon.com's bestsellers page"
```

3. Watch as HuggingScrape:
- Navigates to the page
- Identifies relevant content using AI vision models
- Extracts the requested information
- Returns structured results
- Provides a visual recording of the process

t of 🪄e a questionable amount of 🪄
M