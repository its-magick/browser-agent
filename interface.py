import asyncio
import os
from dataclasses import dataclass
from typing import List, Optional

import gradio as gr
from gradio import Blocks, Markdown, Row, Column, Textbox, Dropdown, Checkbox, Button
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
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
	else:  # anthropic
		os.environ['ANTHROPIC_API_KEY'] = api_key
		llm = ChatAnthropic(model=model)

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
	with Blocks(title='Browser Use GUI') as interface:
		Markdown('# Browser Use Task Automation')

		with Row():
			with Column():
				provider = Dropdown(
					choices=['openai', 'anthropic'],
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
				headless = Checkbox(label='Run Headless', value=True)
				submit_btn = Button('Run Task')

			with Column():
				output = Textbox(label='Output', lines=10, interactive=False)

		def update_model_choices(provider):
			if provider == 'openai':
				return gr.Dropdown(choices=['gpt-4o', 'gpt-4o-mini'], value='gpt-4o')
			else:  # anthropic
				return gr.Dropdown(choices=['claude-3-5-sonnet-latest', 'claude-3-opus-latest'], value='claude-3-5-sonnet-latest')

		provider.change(
			fn=update_model_choices,
			inputs=[provider],
			outputs=[model]
		)

		submit_btn.click(
			fn=lambda *args: asyncio.run(run_browser_task(*args)),
			inputs=[task, api_key, provider, model, headless],
			outputs=output,
		)

	return interface


if __name__ == '__main__':
	demo = create_ui()
	demo.launch()
