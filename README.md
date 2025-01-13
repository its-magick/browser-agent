# 🤖 Browser Agent - Your Web-Surfing AI Sidekick

Ever wished you had a robot friend who could browse the web for you? Well, now you do! 
(Just don't ask it to solve CAPTCHAs - it's not a fan of picking out traffic lights 😅)

## 🌟 What's Inside?

This project contains two powerful components that work together like peanut butter and jelly (but more technical):

### 🚀 api.py - The REST API Hero
- Handles HTTP requests like a champ
- Provides a FastAPI endpoint at `/task`
- Caches results in Redis (because nobody likes waiting twice)
- Perfect for when you need a quick answer and don't want to start a long-term relationship with your browser

### ⚡ realtime.py - The Always-On Warrior
- Runs continuously like that one friend who never sleeps
- Uses Ably for real-time message handling
- Polls for new tasks like a very eager puppy
- Processes browser automation tasks with the patience of a saint
- Publishes results back to Ably channels faster than you can say "websocket"

### 🎨 interface.py - The Pretty Face
- A sleek Gradio UI that makes task submission a breeze
- Lets you chat with your browser agent like it's a coffee date ☕
- Switch between OpenAI and Anthropic models like changing radio stations 📻
- Rock GPT-4 Vision or jam with Claude-3 - your choice of AI superstar 🎸
- Shows you what your AI buddy is up to in real-time
- Comes with a headless mode for those "I'm not here for the visuals" moments
- Perfect for when you want to point-and-click your way to automation glory 🎯

## 🗄️ Redis - The Memory Keeper

Redis runs system-wide because, like gossip in a small town, everyone needs access to the same information! It:
- Caches task results for 5 minutes (TTL=300)
- Uses cache keys in format: `browseragent:cache:{task}`
- Prevents duplicate work (work smarter, not harder! 🧠)

## 🔧 Environment Setup

Create a `.env` file in your project root (and keep it secret, keep it safe! 🧙‍♂️):

```env
ANTHROPIC_API_KEY=your_claude_api_key  # Required if using Anthropic models
OPENAI_API_KEY=your_openai_api_key  # Required if using OpenAI models
ABLY_API_KEY=your_ably_key
REDIS_URL=redis://your.redis.host:6379
CHANNEL_NAME=your_ably_channel
PORT=3000  # Optional, defaults to 3000
LOG_LEVEL=INFO  # Optional, defaults to INFO. Valid levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
```

The LOG_LEVEL environment variable controls the verbosity of logging:
- DEBUG: Detailed information for debugging
- INFO: General operational information
- WARNING: Warning messages for potential issues
- ERROR: Error messages for serious problems
- CRITICAL: Critical issues that may cause system failure

## 🐳 Docker Setup

Our Dockerfile is like a gourmet recipe, but for computers:

1. Start with a slim Python 3.12 base (we're watching our container weight 🏋️‍♂️)
2. Add a pinch of system dependencies
3. Sprinkle in some Rust (because we're fancy like that)
4. Install Playwright (our puppet master for web browsing)
5. Add UV package manager for extra speed 🏃‍♂️
6. Mix in all Python requirements
7. Serve hot! 🔥

To build and run:
```bash
docker build -t browser-agent .
docker run -p 3000:3000 --env-file .env browser-agent
```

## 🚨 Common Issues

- Check your Redis URL if it isn't connecting, make sure it's not on vacation (running)
- Playwright must be installed at the root directory level
- If all else fails, grab a coffee ☕ and check the logs

## 🎭 A Note on Playwright

Yes, we're using Playwright for browser automation. No, it's not because we couldn't figure out Selenium - we just have better taste! 😉

---

Made with a questionable amount of 🪄
