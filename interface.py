import asyncio
import os
import time
from dataclasses import dataclass
from typing import List, Optional

import gradio as gr
from gradio import Blocks, Markdown, Row, Column, Textbox, Dropdown, Checkbox, Button
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from browser_use import Agent

load_dotenv()


@dataclass
class ActionResult:
	is_done: bool
	extracted_content: Optional[str]
	error: Optional[str]
	include_in_memory: bool


@dataclass
class AgentHistoryList:
	all_results: List[ActionResult]
	all_model_outputs: List[dict]


def parse_agent_history(history_str: str) -> None:
	console = Console()

	# Split the content into sections based on ActionResult entries
	sections = history_str.split('ActionResult(')

	for i, section in enumerate(sections[1:], 1):  # Skip first empty section
		# Extract relevant information
		content = ''
		if 'extracted_content=' in section:
			content = section.split('extracted_content=')[1].split(',')[0].strip("'")

		if content:
			header = Text(f'Step {i}', style='bold blue')
			panel = Panel(content, title=header, border_style='blue')
			console.print(panel)
			console.print()


async def run_browser_task(
	task: str,
	api_key: str,
	provider: str = 'openai',
	model: str = 'gpt-4-vision',
	headless: bool = True,
) -> str:
	if not api_key.strip():
		return 'Please provide an API key'

	if provider == 'openai':
		os.environ['OPENAI_API_KEY'] = api_key
		llm = ChatOpenAI(model=model)
	elif provider == 'anthropic':
		os.environ['ANTHROPIC_API_KEY'] = api_key
		llm = ChatAnthropic(model=model)
	else:  # google
		os.environ['GOOGLE_API_KEY'] = api_key
		llm = ChatGoogleGenerativeAI(model=model)

	try:
		agent = Agent(
			task=task,
			llm=llm,
		)
		result = await agent.run()
		#  TODO: The result cloud be parsed better
		return result
	except Exception as e:
		return f'Error: {str(e)}'


def create_ui():
	with Blocks(title='HuggingScrape') as interface:
		Markdown('# HuggingScrape - A Browser Automation Tool')

		with Row():
			with Column():
				provider = Dropdown(
					choices=['openai', 'anthropic', 'google'],
					label='Provider',
					value='openai'
				)
				api_key = Textbox(
					label='API Key',
					placeholder='Enter your API key...',
					type='password'
				)
				task = Textbox(
					label='Task Description',
					placeholder='E.g., Find flights from New York to London for next week',
					lines=3,
				)
				model = Dropdown(
					choices=['gpt-4-vision'],
					label='Model',
					value='gpt-4-vision'
				)
				submit_btn = Button('Run Task')

			with Column():
				output = Textbox(label='Output', lines=10, interactive=False)
				with Row():
					gif_output = gr.Image(label="Task Recording", type="filepath", container=True)
					with gr.Column():
						gr.HTML("""
							<style>
								.gif-container img {
									max-width: 100%;
									height: auto;
									border-radius: 8px;
									box-shadow: 0 2px 6px rgba(0,0,0,0.1);
								}
							</style>
						""")
					download_btn = gr.File(label="Download Recording")

		def update_model_choices(provider):
			if provider == 'openai':
				return gr.Dropdown(choices=['gpt-4-vision'], value='gpt-4-vision')
			elif provider == 'anthropic':
				return gr.Dropdown(choices=['claude-3-opus', 'claude-3-sonnet'], value='claude-3-opus')
			else:  # google
				return gr.Dropdown(choices=['gemini-2.0-flash-exp', 'gemini-1.5-flash', 'gemini-1.5-flash-8b', 'gemini-1.5-pro'], value='gemini-pro-vision')

		provider.change(
			fn=update_model_choices,
			inputs=[provider],
			outputs=[model]
		)

		def on_task_complete(*args):
			result = asyncio.run(run_browser_task(*args))
			# Give a moment for the gif to be generated
			time.sleep(2)
			if os.path.exists("agent_history.gif"):
				return result, "agent_history.gif", "agent_history.gif"
			return result, None, None

		submit_btn.click(
			fn=on_task_complete,
			inputs=[task, api_key, provider, model],
			outputs=[output, gif_output, download_btn],
		)

	return interface


if __name__ == '__main__':
	demo = create_ui()
	demo.launch(share=True)
