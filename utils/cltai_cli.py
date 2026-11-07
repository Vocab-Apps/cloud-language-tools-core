"""CLT-AI Agent chat CLI: a testing tool for the instant (chatbot) mode.

    uv run python utils/cltai_cli.py                                   # interactive chat
    uv run python utils/cltai_cli.py "pronounce in japanese: 今日は"     # one request, then exit
    uv run python utils/cltai_cli.py -i "if I give you chinese text, translate it and give me the pinyin"

The agent's trace (reasoning summaries, tool calls, tool results) is displayed while it works, through
pydantic-ai's event_stream_handler. Generated audio is played with mpv.
"""

import os
import sys
import json
import logging
import subprocess
from typing import Any, AsyncIterable, List, Optional

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import typer
import pydantic
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import FileHistory
from rich.console import Console, Group
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from pydantic_ai import RunContext
from pydantic_ai.messages import (
    AgentStreamEvent, PartStartEvent, PartDeltaEvent, PartEndEvent, FunctionToolCallEvent, FunctionToolResultEvent,
    ThinkingPart, ThinkingPartDelta)

import cloudlanguagetools.cltai
import cloudlanguagetools.cltai.agent
from cloudlanguagetools.cltai.models import SoundResult

app = typer.Typer()
console = Console()

HISTORY_FILE = os.path.expanduser('~/.cltai_cli_history')
MAX_ARGS_DISPLAY = 400
MAX_RESULT_DISPLAY = 300

COMMANDS = {
    '/instructions': 'show the standing instructions, or set them: /instructions <text>',
    '/clearinstructions': 'remove the standing instructions',
    '/reset': 'forget the conversation history (standing instructions are kept)',
    '/play': 'replay the audio of the last response: /play [number]',
    '/trace': 'toggle display of the agent trace',
    '/help': 'show this help',
    '/quit': 'exit',
}


def _shorten(text: str, limit: int) -> str:
    text = ' '.join(text.split())
    return text if len(text) <= limit else text[:limit] + f'… [{len(text) - limit} more chars]'


def _format_value(value: Any) -> str:
    if isinstance(value, pydantic.BaseModel):
        value = value.model_dump(mode='json')
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, default=str)


class TraceRenderer():
    """pydantic-ai event_stream_handler printing the agent's work as it happens: thinking (OpenAI reasoning
    summaries) is streamed, tool calls and their results are printed as they occur. Text parts are not
    streamed, the final answer is displayed once the run is complete."""

    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.thinking = False  # a thinking part is open
        self.thinking_started = False  # and some of its content has been printed
        self.tool_calls = {}  # tool_call_id -> (step, tool name)

    def end_thinking(self):
        if self.thinking_started:
            console.print()
        self.thinking = False
        self.thinking_started = False

    def stream_thinking(self, content: str):
        # OpenAI sends reasoning parts without a summary at times, only print parts with content
        if not content:
            return
        if not self.thinking_started:
            console.print(Text('💭 ', style='magenta'), end='')
            self.thinking_started = True
        console.print(Text(content, style='italic dim magenta'), end='')

    async def __call__(self, ctx: RunContext, events: AsyncIterable[AgentStreamEvent]):
        # called for each model request (response stream) and each batch of tool executions
        async for event in events:
            if self.enabled:
                self.handle(event)
        self.end_thinking()

    def handle(self, event: AgentStreamEvent):
        if isinstance(event, PartStartEvent):
            self.end_thinking()
            if isinstance(event.part, ThinkingPart):
                self.thinking = True
                self.stream_thinking(event.part.content)
        elif isinstance(event, PartDeltaEvent):
            if isinstance(event.delta, ThinkingPartDelta) and self.thinking:
                self.stream_thinking(event.delta.content_delta or '')
        elif isinstance(event, PartEndEvent):
            self.end_thinking()
        elif isinstance(event, FunctionToolCallEvent):
            self.end_thinking()
            step = len(self.tool_calls) + 1
            self.tool_calls[event.tool_call_id] = (step, event.part.tool_name)
            line = Text(f'🔧 [{step}] {event.part.tool_name} ', style='bold yellow')
            line.append(_shorten(_format_value(event.part.args_as_dict()), MAX_ARGS_DISPLAY), style='yellow')
            console.print(line)
        elif isinstance(event, FunctionToolResultEvent):
            self.end_thinking()
            part = event.part
            step, tool_name = self.tool_calls.get(event.tool_call_id, ('?', part.tool_name))
            success = part.outcome == 'success'
            style = 'green' if success else 'red'
            line = Text(f'   ↳ [{step}] {tool_name}' + ('' if success else f' {part.outcome}') + ': ', style='bold ' + style)
            line.append(_shorten(_format_value(part.content), MAX_RESULT_DISPLAY), style=style)
            console.print(line)


def play_audio(sound: SoundResult):
    try:
        subprocess.run(['mpv', '--no-video', '--really-quiet', sound.audio_path], check=True)
    except FileNotFoundError:
        console.print('[red]mpv not found, install mpv to play audio.[/red]')
    except subprocess.CalledProcessError as e:
        console.print(f'[red]mpv playback error: {e}[/red]')


class ChatCli():

    def __init__(self, standing_instructions: Optional[str], model: str, allow_llm: bool, play: bool, trace: bool):
        self.standing_instructions = standing_instructions
        self.allow_llm = allow_llm
        self.play = play
        self.trace = trace
        self.message_history: Optional[List[Any]] = None
        self.last_sounds: List[SoundResult] = []
        with console.status('loading CLT-AI client...'):
            self.clt = cloudlanguagetools.cltai.create_client(cloudlanguagetools.cltai.CltAPIVersion.v1)
            self.agent = cloudlanguagetools.cltai.agent.CltAIAgent(self.clt, model=model)
        self.model = model

    def send(self, message: str):
        renderer = TraceRenderer(enabled=self.trace)
        console.rule('[dim]agent[/dim]', style='dim')
        try:
            response = self.agent.run_instant(message, standing_instructions=self.standing_instructions,
                message_history=self.message_history, allow_llm=self.allow_llm, event_stream_handler=renderer)
        except KeyboardInterrupt:
            renderer.end_thinking()
            console.print('[yellow]interrupted[/yellow]')
            return
        except Exception as e:
            renderer.end_thinking()
            console.print(f'[bold red]{type(e).__name__}:[/bold red] {e}')
            return
        self.message_history = response.messages
        self.show_response(response)
        self.last_sounds = response.sounds
        if self.play:
            self.play_sounds(self.last_sounds)

    def show_response(self, response: cloudlanguagetools.cltai.agent.InstantResponse):
        body = [Markdown(response.text or '(no text)')]
        if response.sounds:
            table = Table(show_header=True, header_style='bold', box=None, padding=(0, 1))
            for column in ['#', 'text', 'service', 'voice', 'language', 'file']:
                table.add_column(column)
            for i, sound in enumerate(response.sounds, start=1):
                table.add_row(str(i), sound.text, sound.service.name, sound.voice_name, sound.audio_language.name,
                    sound.audio_path)
            body += [Text(''), Text('🔊 audio', style='bold'), table]
        console.print(Panel(Group(*body), title='[bold green]CLT-AI[/bold green]', border_style='green'))

    def play_sounds(self, sounds: List[SoundResult]):
        for i, sound in enumerate(sounds, start=1):
            console.print(f'[green]▶ playing {i}/{len(sounds)}: {sound.text}[/green]')
            play_audio(sound)

    # commands
    # ========

    def command(self, line: str) -> bool:
        """handle a /command, returns False to exit"""
        command, _, argument = line.partition(' ')
        argument = argument.strip()
        if command in ('/quit', '/exit'):
            return False
        if command == '/instructions':
            if argument:
                self.standing_instructions = argument
                console.print('[green]standing instructions set[/green]')
            console.print(Panel(self.standing_instructions or '(none)', title='standing instructions', border_style='blue'))
        elif command == '/clearinstructions':
            self.standing_instructions = None
            console.print('[green]standing instructions removed[/green]')
        elif command == '/reset':
            self.message_history = None
            console.print('[green]conversation history cleared[/green]')
        elif command == '/play':
            if not self.last_sounds:
                console.print('[yellow]no audio in the last response[/yellow]')
            elif argument:
                try:
                    self.play_sounds([self.last_sounds[int(argument) - 1]])
                except (ValueError, IndexError):
                    console.print(f'[red]choose a number between 1 and {len(self.last_sounds)}[/red]')
            else:
                self.play_sounds(self.last_sounds)
        elif command == '/trace':
            self.trace = not self.trace
            console.print(f'[green]trace {"on" if self.trace else "off"}[/green]')
        elif command == '/help':
            self.show_help()
        else:
            console.print(f'[red]unknown command {command}, type /help[/red]')
        return True

    def show_help(self):
        table = Table(show_header=False, box=None, padding=(0, 2))
        for command, description in COMMANDS.items():
            table.add_row(f'[bold cyan]{command}[/bold cyan]', description)
        console.print(Panel(Group(
            Text('Type a request, e.g. "pronounce in japanese: 今日はいい天気ですね" or "pinyin for 我想喝咖啡".'),
            Text('Set standing instructions to apply to every message, then just type the input.'),
            Text(''), table), title=f'CLT-AI chat ({self.model})', border_style='blue'))

    def bottom_toolbar(self):
        instructions = self.standing_instructions or 'none'
        if len(instructions) > 70:
            instructions = instructions[:70] + '…'
        turns = sum(1 for m in (self.message_history or []) if getattr(m, 'kind', None) == 'request')
        return (f' instructions: {instructions} │ history: {turns} requests │ trace: {"on" if self.trace else "off"}'
            f' │ audio: {"auto-play" if self.play else "off"}')

    def run(self):
        self.show_help()
        if self.standing_instructions:
            console.print(Panel(self.standing_instructions, title='standing instructions', border_style='blue'))
        session = PromptSession(history=FileHistory(HISTORY_FILE), bottom_toolbar=self.bottom_toolbar,
            completer=WordCompleter(list(COMMANDS) + ['/exit'], sentence=True))
        while True:
            try:
                line = session.prompt('clt-ai> ').strip()
            except KeyboardInterrupt:
                continue
            except EOFError:
                break
            if not line:
                continue
            if line.startswith('/'):
                if not self.command(line):
                    break
            else:
                self.send(line)
        console.print('[dim]Goodbye.[/dim]')


@app.command()
def main(message: Optional[str] = typer.Argument(None, help='send this single request and exit'),
        instructions: Optional[str] = typer.Option(None, '--instructions', '-i', help='standing instructions applied to every message'),
        model: str = typer.Option(cloudlanguagetools.cltai.agent.DEFAULT_AGENT_MODEL, '--model', '-m', help='OpenAI model of the agent'),
        no_llm: bool = typer.Option(False, '--no-llm', help='do not give the agent the llm verb'),
        no_play: bool = typer.Option(False, '--no-play', help='do not play the generated audio'),
        no_trace: bool = typer.Option(False, '--no-trace', help='hide the agent trace (thinking, tool calls)'),
        log_level: str = typer.Option('ERROR', '--log-level', help='python logging level')):
    """CLT-AI Agent chat: test the instant (chatbot) mode with a trace of the agent's work."""
    level = getattr(logging, log_level.upper())
    logging.basicConfig(level=level, format='%(asctime)s %(name)s %(levelname)s %(message)s')
    # jieba (used for pinyin) logs to its own stderr handler at DEBUG level
    logging.getLogger('jieba').setLevel(max(level, logging.WARNING))
    cli = ChatCli(instructions, model=model, allow_llm=not no_llm, play=not no_play, trace=not no_trace)
    if message:
        cli.send(message)
    else:
        cli.run()


if __name__ == '__main__':
    app()
