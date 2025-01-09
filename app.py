from langchain_anthropic import ChatAnthropic
from browser_use.agent.service import Agent, Controller
from browser_use.browser.browser import Browser, BrowserConfig
from browser_use.browser.context import BrowserContextConfig
import requests
from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import Optional
import redis
import json
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

browser = Browser(
	config=BrowserConfig(
		disable_security=True,
		headless=False,
		new_context_config=BrowserContextConfig(),
	)
)
app = FastAPI()
controller=Controller()
llm=ChatAnthropic(model='claude-3-5-sonnet-latest', api_key=os.getenv("ANTHROPIC_API_KEY"))
redis_url = os.getenv("REDIS_URL")
redis_client = redis.StrictRedis.from_url(redis_url)  # Connect to Redis using environment variable

class TaskRequest(BaseModel):
    task: str
    postback_url: Optional[str] = None

async def fetch_result(task: str):
    cache_key = f"browseragent:cache:{task}"
    cached_result = redis_client.get(cache_key)
    if cached_result:
        return json.loads(cached_result)
    agent = Agent(llm=llm, task=task, browser=browser, controller=controller, validate_output=True)  # Initialize the agent without headless argument
    agent.browser.headless = True  # Set headless mode to false
    result = await agent.run()
    result_str = result.history[-1].result  # Extract the result string from the last history entry
    result_serializable = result_str if isinstance(result_str, str) else str(result_str)  # Ensure result is serializable
    redis_client.setex(cache_key, 300, json.dumps(result_serializable))  # Cache result string with a TTL of 5 minutes
    return result_serializable

@app.post("/task")
async def run_task(request: TaskRequest):
    result = await fetch_result(request.task)  # Await the fetch_result function
    if request.postback_url:
        try:
            requests.post(request.postback_url, json={"result": result})
        except requests.exceptions.RequestException:
            pass
    return {"status": "Task completed"}

if __name__ == "__main__":
    import uvicorn
    port = os.getenv("PORT", 3000)
    uvicorn.run(app, host="0.0.0.0", port=port)
