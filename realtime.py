import asyncio
from ably import AblyRest
from langchain_openai import ChatOpenAI
from ably.types.message import Message
from browser_use import Agent, Controller
from browser_use.browser.browser import Browser, BrowserConfig
import redis
import json
import os
import sys
import signal
import logging
from dotenv import load_dotenv
import threading

# Configure logging with level from environment
VALID_LOG_LEVELS = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}

# Get log level from environment or default to INFO
log_level_name = os.getenv('LOG_LEVEL', 'INFO').upper()
if log_level_name not in VALID_LOG_LEVELS:
    print(f"Warning: Invalid LOG_LEVEL '{log_level_name}'. Defaulting to INFO.")
    log_level = logging.INFO
else:
    log_level = VALID_LOG_LEVELS[log_level_name]

# Configure logging with detailed format
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(levelname)s - [%(name)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Console handler
        logging.FileHandler('realtime.log')  # File handler
    ]
)
logger = logging.getLogger(__name__)
logger.info(f"Initializing Browser Agent Realtime Service with log level: {log_level_name}")

# Load and validate environment variables
load_dotenv()
logger.info("Loading environment variables")

# Define and validate required environment variables
required_vars = {
    "ANTHROPIC_API_KEY": "API key for Claude language model",
    "ABLY_API_KEY": "API key for Ably realtime messaging",
    "REDIS_URL": "URL for Redis cache connection",
    "CHANNEL_NAME": "Ably channel name for task communication"
}

# Check for missing environment variables with descriptions
missing_vars = [f"{var} ({desc})" for var, desc in required_vars.items() if not os.getenv(var)]
if missing_vars:
    logger.error(f"Missing required environment variables:\n" + "\n".join(f"- {var}" for var in missing_vars))
    sys.exit(1)
logger.info("All required environment variables found")

# Initialize core services with detailed logging
logger.info("Initializing core services")

try:
    # Initialize browser with production configuration
    logger.info("Setting up browser configuration")
    browser = Browser(
        config=BrowserConfig(
            headless=True,  # Headless mode for production
            disable_security=True  # Required for certain automation tasks
        )
    )
    logger.info("Browser initialized successfully")

    # Initialize Ably client
    logger.info("Setting up Ably client")
    ably_api_key = os.getenv("ABLY_API_KEY")
    ably = AblyRest(ably_api_key)
    logger.info("Ably client initialized successfully")

    # Initialize controller for browser automation
    logger.info("Initializing browser controller")
    controller = Controller()
    logger.info("Controller initialized successfully")

    # Initialize language model
    logger.info("Setting up OpenAI language model")
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0.0,
    )
    logger.info("Language model initialized successfully")

    # Initialize Redis connection
    logger.info("Connecting to Redis cache")
    redis_url = os.getenv("REDIS_URL")
    redis_client = redis.StrictRedis.from_url(redis_url)
    # Test Redis connection
    redis_client.ping()
    logger.info("Redis connection established successfully")

except Exception as e:
    logger.error(f"Critical error during service initialization: {str(e)}", exc_info=True)
    sys.exit(1)

logger.info("All core services initialized successfully")

async def fetch_result(task: str, session: str):
    """
    Process a task using the browser agent and publish results to Ably.
    
    Args:
        task (str): The task description to process
        session (str): Session identifier for result tracking
        
    Returns:
        str: The serialized result of the task execution
        
    Raises:
        ValueError: If task or session is invalid
        Exception: For various execution errors
    """
    logger.info(f"Processing task for session {session}: {task[:100]}...")  # Log first 100 chars
    
    try:
        # Validate input parameters
        if not task or not session:
            logger.error("Missing required parameters")
            raise ValueError("Task and session are required parameters")

        cache_key = f"browseragent:cache:{task}"
        logger.debug(f"Generated cache key: {cache_key}")
        
        # Try to get from cache
        try:
            logger.debug("Attempting to fetch from cache")
            cached_result = redis_client.get(cache_key)
            if cached_result:
                logger.info(f"Cache hit for task: {task}")
                decoded_result = json.loads(cached_result)
                logger.debug(f"Successfully decoded cached result: {type(decoded_result)}")
                return decoded_result
        except redis.RedisError as e:
            logger.error(f"Redis error while fetching cache: {str(e)}", exc_info=True)
            logger.warning("Continuing without cache due to Redis error")
        
        try:
            # Initialize and run agent
            logger.info("Initializing browser agent")
            agent = Agent(
                llm=llm,
                task=task,
                browser=browser,
                controller=controller,
                validate_output=False
            )
            logger.info("Starting agent execution with max_steps=30")
            result = await agent.run(max_steps=30)
            
            if not result or not result.history:
                logger.error("Agent returned empty or invalid result")
                raise ValueError("Agent returned invalid result")
            
            result_str = result.history[-1].result
            logger.debug(f"Raw result type: {type(result_str)}")
            
            result_serializable = result_str if isinstance(result_str, str) else str(result_str)
            logger.debug(f"Serialized result length: {len(result_serializable)}")
            
            # Try to cache the result
            try:
                logger.debug("Attempting to cache result")
                redis_client.setex(cache_key, 300, json.dumps(result_serializable))
                logger.info(f"Result cached successfully with TTL: 300 seconds")
            except redis.RedisError as e:
                logger.error(f"Redis error while setting cache: {str(e)}", exc_info=True)
                logger.warning("Continuing without caching due to Redis error")
            
            logger.info(f"Task {task[:50]}... completed successfully")
            
            # Publish result to Ably
            try:
                logger.debug("Publishing result to Ably channel 'browser-result'")
                await ably.channels.get('browser-result').publish(
                    'result', 
                    {'task': task, 'session': session, 'result': json.dumps(result_serializable)}
                )
                logger.info("Result published successfully to Ably")
            except Exception as e:
                logger.error(f"Ably publishing error: {str(e)}", exc_info=True)
                # Re-raise as this is critical for the application flow
                raise
                
            return result_serializable
            
        except Exception as e:
            error_msg = f"Error processing task: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            # Publish error to Ably
            try:
                logger.debug("Publishing error to Ably channel 'browser-result'")
                await ably.channels.get('browser-result').publish(
                    'error',
                    {'task': task, 'session': session, 'error': error_msg}
                )
                logger.info("Error published to Ably")
            except Exception as ably_err:
                logger.error(f"Failed to publish error to Ably: {str(ably_err)}", exc_info=True)
            
            raise
            
    except Exception as e:
        logger.error(f"Critical error in fetch_result: {str(e)}", exc_info=True)
        logger.error("Stack trace:", stack_info=True)
        raise

async def ably_message_handler(message: Message):
    """
    Handle incoming Ably messages by processing tasks.
    
    Args:
        message (Message): The Ably message containing task details
    """
    try:
        logger.debug("Received Ably message")
        
        if not message or not message.data:
            logger.error("Received invalid message format")
            return
            
        task = message.data.get('task')
        session = message.data.get('session')
        
        if not task or not session:
            logger.error(f"Missing required fields in message: {message.data}")
            return
        
        logger.info(f"Processing message for session {session}")
        await fetch_result(task, session)
        logger.info(f"Message processing completed for session {session}")
        
    except Exception as e:
        logger.error(f"Error in message handler: {str(e)}", exc_info=True)
        logger.warning("Continuing to process other messages")
        

async def poll_ably_channel():
    """
    Continuously poll Ably channel for new messages.
    Implements retry logic with exponential backoff for resilience.
    """
    channel_name = os.getenv("CHANNEL_NAME")
    if not channel_name:
        logger.error("CHANNEL_NAME environment variable is not set")
        raise ValueError("CHANNEL_NAME environment variable is not set")
    
    logger.info(f"Starting to poll Ably channel: {channel_name}")
        
    retry_count = 0
    max_retries = 3
    retry_delay = 5  # seconds
    
    while True:
        try:
            logger.debug(f"Fetching history from channel {channel_name}")
            history = await ably.channels.get(channel_name).history()
            retry_count = 0  # Reset counter on successful connection
            
            message_count = len(history.items)
            logger.debug(f"Retrieved {message_count} messages from history")
            
            for message in history.items:
                try:
                    logger.debug(f"Processing message: {message.id}")
                    await ably_message_handler(message)
                except Exception as e:
                    logger.error(f"Error processing message: {str(e)}", exc_info=True)
                    continue  # Continue with next message
            
            logger.debug("Waiting 10 seconds before next poll")
            await asyncio.sleep(10)  # Poll every 10 seconds
            
        except Exception as e:
            logger.error(f"Error polling Ably channel: {str(e)}", exc_info=True)
            retry_count += 1
            
            if retry_count >= max_retries:
                logger.warning("Max retries reached, implementing longer backoff")
                await asyncio.sleep(60)  # Wait longer between retry batches
                retry_count = 0
            else:
                logger.info(f"Retry attempt {retry_count}/{max_retries} in {retry_delay} seconds")
                await asyncio.sleep(retry_delay)

def cleanup():
    """
    Cleanup function to be called on shutdown.
    Ensures proper cleanup of resources and connections.
    """
    logger.info("Starting cleanup process")
    try:
        # Close browser
        logger.debug("Attempting to close browser")
        browser.close()
        logger.info("Browser closed successfully")
        
        # Close Redis connection
        logger.debug("Closing Redis connection")
        redis_client.close()
        logger.info("Redis connection closed")
        
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}", exc_info=True)
    finally:
        logger.info("Cleanup process completed")

if __name__ == "__main__":
    # Register signal handlers for graceful shutdown
    def signal_handler(sig, frame):
        """Handle shutdown signals by cleaning up resources"""
        signal_name = signal.Signals(sig).name
        logger.info(f"Received shutdown signal: {signal_name}")
        logger.info("Initiating graceful shutdown...")
        cleanup()
        logger.info("Shutdown complete")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        logger.info("Initializing event loop")
        loop = asyncio.get_event_loop()
        loop.create_task(poll_ably_channel())

        def run_forever():
            """Keep the application running in the background"""
            try:
                while True:
                    time.sleep(3600)  # Sleep for an hour
            except Exception as e:
                logger.error(f"Error in background thread: {str(e)}", exc_info=True)
                sys.exit(1)

        thread = threading.Thread(target=run_forever)
        thread.daemon = True
        thread.start()

        logger.info("Application is running in the background")
        logger.info("Press Ctrl+C to stop")
        loop.run_forever()
        
    except Exception as e:
        logger.error(f"Critical application error: {str(e)}", exc_info=True)
        cleanup()
        sys.exit(1)
