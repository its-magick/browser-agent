from langchain_anthropic import ChatAnthropic
from browser_use.agent.service import Agent, Controller
from browser_use.browser.browser import Browser, BrowserConfig
from browser_use.browser.context import BrowserContextConfig
import requests
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
from typing import Optional, Dict, Any
import redis
import json
import os
import sys
import signal
import logging
from dotenv import load_dotenv

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
        logging.FileHandler('api.log')  # File handler
    ]
)
logger = logging.getLogger(__name__)
logger.info(f"Initializing Browser Agent API with log level: {log_level_name}")

# Load environment variables from .env file and validate required variables
load_dotenv()
logger.info("Loading environment variables")

# Define and validate required environment variables
required_vars = {
    "ANTHROPIC_API_KEY": "API key for Claude language model",
    "REDIS_URL": "URL for Redis cache connection"
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
    # Initialize browser with custom configuration
    logger.info("Setting up browser configuration")
    browser = Browser(
        config=BrowserConfig(
            disable_security=True,  # Required for certain automation tasks
            headless=False,  # GUI mode for development
            new_context_config=BrowserContextConfig(),
        )
    )
    logger.info("Browser initialized successfully")

    # Initialize controller for browser automation
    logger.info("Initializing browser controller")
    controller = Controller()
    logger.info("Controller initialized successfully")

    # Initialize language model
    logger.info("Setting up Claude language model")
    llm = ChatAnthropic(
        model='claude-3-5-sonnet-latest', 
        api_key=os.getenv("ANTHROPIC_API_KEY")
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

# Initialize FastAPI application with metadata
app = FastAPI(
    title="Browser Agent API",
    description="API for browser automation tasks using Claude language model",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)
logger.info("FastAPI application initialized")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TaskRequest(BaseModel):
    task: str
    postback_url: Optional[str] = None

    @validator('task')
    def validate_task(cls, v):
        if not v or not v.strip():
            raise ValueError("Task cannot be empty")
        return v.strip()

    @validator('postback_url')
    def validate_postback_url(cls, v):
        if v and not v.startswith(('http://', 'https://')):
            raise ValueError("Postback URL must start with http:// or https://")
        return v

async def fetch_result(task: str) -> Dict[str, Any]:
    """
    Fetch result for a given task, either from cache or by running the browser agent.
    
    Args:
        task (str): The task description to process
        
    Returns:
        Dict[str, Any]: Result dictionary containing the task result and cache status
        
    Raises:
        HTTPException: On various error conditions with appropriate status codes
    """
    logger.info(f"Processing task: {task}")
    try:
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
                return {"result": decoded_result, "cached": True}
            logger.debug("Cache miss")
        except redis.RedisError as e:
            logger.error(f"Redis error while fetching cache: {str(e)}", exc_info=True)
            logger.warning("Continuing without cache due to Redis error")
        
        # Initialize and run agent with detailed logging
        try:
            logger.info("Initializing browser agent")
            agent = Agent(
                llm=llm,
                task=task,
                browser=browser,
                controller=controller,
                validate_output=True
            )
            agent.browser.headless = True
            logger.info("Starting agent execution")
            
            result = await agent.run()
            logger.debug("Agent execution completed")
            
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
            
            logger.info("Task processing completed successfully")
            return {"result": result_serializable, "cached": False}
            
        except Exception as e:
            logger.error(f"Agent error during task execution: {str(e)}", exc_info=True)
            error_context = {
                "task": task,
                "error_type": type(e).__name__,
                "error_details": str(e)
            }
            logger.error(f"Error context: {json.dumps(error_context, indent=2)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to process task: {str(e)}"
            )
            
    except Exception as e:
        logger.error(f"Critical error in fetch_result: {str(e)}", exc_info=True)
        logger.error(f"Stack trace:", stack_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error - Please check server logs for details"
        )

@app.post("/task", response_model=Dict[str, Any], description="Execute a browser automation task")
async def run_task(request: TaskRequest):
    """
    Execute a browser automation task and optionally send results to a postback URL.
    
    Args:
        request (TaskRequest): The task request containing the task description and optional postback URL
        
    Returns:
        Dict[str, Any]: Response containing task result and execution details
    """
    logger.info(f"Received task request: {request.task[:100]}...")  # Log first 100 chars of task
    try:
        result_data = await fetch_result(request.task)
        
        if request.postback_url:
            try:
                response = requests.post(
                    request.postback_url,
                    json={"result": result_data["result"]},
                    timeout=10
                )
                response.raise_for_status()
                logger.info(f"Successfully posted result to {request.postback_url}")
            except requests.exceptions.RequestException as e:
                logger.error(f"Failed to post result to {request.postback_url}: {str(e)}")
                # Don't fail the request, but include the error in response
                result_data["postback_error"] = str(e)
        
        return {
            "status": "success",
            "data": result_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in run_task: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "message": exc.detail
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "Internal server error"
        }
    )

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
        port = int(os.getenv("PORT", 3000))
        logger.info(f"Starting server on port {port}")
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=port,
            log_level="info"
        )
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}")
        cleanup()
        sys.exit(1)
