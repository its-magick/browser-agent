import asyncio
from ably import AblyRest
from langchain_anthropic import ChatAnthropic
from ably.types.message import Message
from browser_use import Agent, Controller
from browser_use.browser.browser import Browser, BrowserConfig
import redis
import json
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file


browser = Browser(
	config=BrowserConfig(
		headless=True,  # This is True in production
		disable_security=True
	)
)
ably_api_key = os.getenv("ABLY_API_KEY")

llm=ChatAnthropic(model='claude-3-5-sonnet-latest', api_key=os.getenv("ANTHROPIC_API_KEY"))
ably = AblyRest(ably_api_key)
controller=Controller()
redis_url = os.getenv("REDIS_URL")
redis_client = redis.StrictRedis.from_url(redis_url)  # Connect to Redis using environment variable

async def fetch_result(task: str, session: str):
    cache_key = f"browseragent:cache:{task}"
    cached_result = redis_client.get(cache_key)
    if cached_result:
        return json.loads(cached_result)
    agent = Agent(llm=llm, task=task, browser=browser, controller=controller, validate_output=False)  # Initialize the agent without headless argument
    result = await agent.run(max_steps=30)
    result_str = result.history[-1].result  # Extract the result string from the last history entry
    result_serializable = result_str if isinstance(result_str, str) else str(result_str)  # Ensure result is serializable
    redis_client.setex(cache_key, 300, json.dumps(result_serializable))  # Cache result string with a TTL of 5 minutes
    print(f"Task {task} completed. Result: {result_serializable}")
    print(f"Publishing result to Ably channel 'browser-result'")
    await ably.channels.get('browser-result').publish('result', {'task': task, 'session': session, 'result': json.dumps(result_serializable)})
    print(f"Result published to Ably channel 'browser-result' Resume polling...")
    return result_serializable

async def ably_message_handler(message: Message):
    task = message.data.get('task')
    session = message.data.get('session')
    if task:
        await fetch_result(task, session)
        

async def poll_ably_channel():
    channel_name = os.getenv("CHANNEL_NAME")
    while True:
        history = await ably.channels.get(channel_name).history()
        for message in history.items:
            await ably_message_handler(message)
        await asyncio.sleep(10)  # Poll every 10 seconds

if __name__ == "__main__":
    import threading
    import time

    loop = asyncio.get_event_loop()
    loop.create_task(poll_ably_channel())

    def run_forever():
        while True:
            time.sleep(3600)  # Sleep for an hour to keep the application running

    thread = threading.Thread(target=run_forever)
    thread.daemon = True  # Allow the thread to be killed when the main program exits
    thread.start()

    print("Application is running in the background. Press Ctrl+C to stop.")
    loop.run_forever()  # Keep the asyncio loop running
