import os
import sys
import shlex
import subprocess
import threading

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import typer
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter, Completer, Completion
from prompt_toolkit.formatted_text import HTML
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.spinner import Spinner
from rich.text import Text

import cloudlanguagetools.servicemanager
import cloudlanguagetools.constants

app = typer.Typer()
console = Console()

PAGE_SIZE = 20


class TTSRepl:
    def __init__(self):
        self.manager = None
        self.all_voices = []
        self.filtered_voices = []
        self.selected_voice = None
        self.input_text = ""
        self.voice_options = {}

        # filters
        self.filter_service = None
        self.filter_gender = None
        self.filter_language = None
        self.filter_locale = None
        self.filter_name = None

        # pagination
        self.page = 0

    def initialize(self):
        with console.status("[bold green]Loading services and voices..."):
            self.manager = cloudlanguagetools.servicemanager.ServiceManager()
            self.manager.configure_default()
            self.all_voices = self.manager.get_tts_voice_list_json()
            self.filtered_voices = list(self.all_voices)
        console.print(f"[green]Loaded {len(self.all_voices)} voices.[/green]")

    def _fuzzy_match(self, value, pattern):
        return pattern.lower() in value.lower()

    def apply_filters(self):
        self.filtered_voices = list(self.all_voices)
        if self.filter_service:
            self.filtered_voices = [
                v for v in self.filtered_voices
                if self._fuzzy_match(v['service'], self.filter_service)
            ]
        if self.filter_gender:
            self.filtered_voices = [
                v for v in self.filtered_voices
                if self._fuzzy_match(v['gender'], self.filter_gender)
            ]
        if self.filter_language:
            self.filtered_voices = [
                v for v in self.filtered_voices
                if self._fuzzy_match(v['language_code'], self.filter_language)
                or self._fuzzy_match(v['audio_language_name'], self.filter_language)
            ]
        if self.filter_locale:
            self.filtered_voices = [
                v for v in self.filtered_voices
                if self._fuzzy_match(v['audio_language_code'], self.filter_locale)
                or self._fuzzy_match(v['audio_language_name'], self.filter_locale)
            ]
        if self.filter_name:
            self.filtered_voices = [
                v for v in self.filtered_voices
                if self._fuzzy_match(v['voice_name'], self.filter_name)
            ]
        self.page = 0

    def cmd_voices(self, args):
        """List voices with pagination."""
        if args:
            try:
                self.page = int(args[0]) - 1
            except ValueError:
                console.print("[red]Usage: voices [page_number][/red]")
                return

        total = len(self.filtered_voices)
        total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
        self.page = max(0, min(self.page, total_pages - 1))
        start = self.page * PAGE_SIZE
        end = min(start + PAGE_SIZE, total)

        table = Table(title=f"Voices (page {self.page + 1}/{total_pages}, {total} total)")
        table.add_column("#", style="dim", width=6)
        table.add_column("Service", style="cyan")
        table.add_column("Language", style="green")
        table.add_column("Locale")
        table.add_column("Gender", style="magenta")
        table.add_column("Name", style="bold")

        for i in range(start, end):
            v = self.filtered_voices[i]
            table.add_row(
                str(i),
                v['service'],
                v['audio_language_name'],
                v['audio_language_code'],
                v['gender'],
                v['voice_name'],
            )

        console.print(table)
        console.print(f"  [dim]Use 'next'/'prev' to navigate, or 'voices <page>'[/dim]")

    def cmd_next(self, args):
        """Next page."""
        self.page += 1
        self.cmd_voices([])

    def cmd_prev(self, args):
        """Previous page."""
        self.page -= 1
        self.cmd_voices([])

    def cmd_filter(self, args):
        """Set a filter. Usage: filter <field> <value>"""
        if not args:
            self._show_filters()
            return

        field = args[0].lower()
        value = " ".join(args[1:]) if len(args) > 1 else None

        valid_fields = ['service', 'gender', 'language', 'locale', 'name']
        if field not in valid_fields:
            console.print(f"[red]Unknown filter field '{field}'. Valid: {', '.join(valid_fields)}[/red]")
            return

        if value is None:
            # clear this filter
            setattr(self, f'filter_{field}', None)
            console.print(f"[yellow]Cleared filter: {field}[/yellow]")
        else:
            setattr(self, f'filter_{field}', value)
            console.print(f"[green]Filter {field} = '{value}'[/green]")

        self.apply_filters()
        console.print(f"[dim]{len(self.filtered_voices)} voices match current filters.[/dim]")

    def _show_filters(self):
        table = Table(title="Active Filters")
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="green")
        for field in ['service', 'gender', 'language', 'locale', 'name']:
            val = getattr(self, f'filter_{field}')
            table.add_row(field, val or "[dim]<not set>[/dim]")
        console.print(table)
        console.print(f"[dim]{len(self.filtered_voices)} voices match current filters.[/dim]")

    def cmd_clearfilters(self, args):
        """Clear all filters."""
        self.filter_service = None
        self.filter_gender = None
        self.filter_language = None
        self.filter_locale = None
        self.filter_name = None
        self.apply_filters()
        console.print(f"[green]All filters cleared. {len(self.filtered_voices)} voices.[/green]")

    def cmd_select(self, args):
        """Select a voice by index."""
        if not args:
            if self.selected_voice:
                console.print(f"[green]Selected:[/green] {self.selected_voice['voice_description']}")
            else:
                console.print("[yellow]No voice selected. Usage: select <index>[/yellow]")
            return

        try:
            idx = int(args[0])
        except ValueError:
            console.print("[red]Usage: select <index>[/red]")
            return

        if idx < 0 or idx >= len(self.filtered_voices):
            console.print(f"[red]Index out of range. Valid: 0-{len(self.filtered_voices) - 1}[/red]")
            return

        self.selected_voice = self.filtered_voices[idx]
        self.voice_options = {}
        console.print(f"[green]Selected:[/green] {self.selected_voice['voice_description']}")

    def cmd_text(self, args):
        """Set input text."""
        if not args:
            if self.input_text:
                console.print(f"[green]Text:[/green] {self.input_text}")
            else:
                console.print("[yellow]No text set. Usage: text <your text>[/yellow]")
            return

        self.input_text = " ".join(args)
        console.print(f"[green]Text set:[/green] {self.input_text}")

    def cmd_options(self, args):
        """List voice options for selected voice."""
        if not self.selected_voice:
            console.print("[red]No voice selected. Use 'select <index>' first.[/red]")
            return

        options = self.selected_voice.get('options', {})
        if not options:
            console.print("[yellow]This voice has no configurable options.[/yellow]")
            return

        table = Table(title=f"Options for {self.selected_voice['voice_name']}")
        table.add_column("Name", style="cyan")
        table.add_column("Type", style="magenta")
        table.add_column("Default")
        table.add_column("Range/Values")
        table.add_column("Current", style="green bold")

        for name, opt in options.items():
            opt_type = opt.get('type', '?')
            default = str(opt.get('default', ''))
            current = str(self.voice_options.get(name, '')) or "[dim]-[/dim]"

            if opt_type in ('number', 'number_int'):
                range_str = f"{opt.get('min', '')} .. {opt.get('max', '')}"
            elif opt_type == 'list':
                range_str = ", ".join(opt.get('values', []))
            else:
                range_str = ""

            table.add_row(name, opt_type, default, range_str, current)

        console.print(table)

    def cmd_set(self, args):
        """Set a voice option. Usage: set <option> <value>"""
        if not self.selected_voice:
            console.print("[red]No voice selected.[/red]")
            return

        if len(args) < 2:
            console.print("[red]Usage: set <option> <value>[/red]")
            return

        name = args[0]
        value_str = " ".join(args[1:])
        options = self.selected_voice.get('options', {})

        if name not in options:
            console.print(f"[red]Unknown option '{name}'. Use 'options' to see available options.[/red]")
            return

        opt = options[name]
        opt_type = opt.get('type', 'text')

        try:
            if opt_type == 'number':
                value = float(value_str)
                if 'min' in opt and value < opt['min']:
                    console.print(f"[red]Value below minimum ({opt['min']})[/red]")
                    return
                if 'max' in opt and value > opt['max']:
                    console.print(f"[red]Value above maximum ({opt['max']})[/red]")
                    return
            elif opt_type == 'number_int':
                value = int(value_str)
                if 'min' in opt and value < opt['min']:
                    console.print(f"[red]Value below minimum ({opt['min']})[/red]")
                    return
                if 'max' in opt and value > opt['max']:
                    console.print(f"[red]Value above maximum ({opt['max']})[/red]")
                    return
            elif opt_type == 'list':
                value = value_str
                if 'values' in opt and value not in opt['values']:
                    console.print(f"[red]Invalid value. Choose from: {', '.join(opt['values'])}[/red]")
                    return
            else:
                value = value_str
        except ValueError:
            console.print(f"[red]Invalid value for type '{opt_type}'[/red]")
            return

        self.voice_options[name] = value
        console.print(f"[green]Set {name} = {value}[/green]")

    def cmd_clear(self, args):
        """Clear a voice option. Usage: clear <option>"""
        if not args:
            console.print("[red]Usage: clear <option> (or 'clearoptions' to clear all)[/red]")
            return

        name = args[0]
        if name in self.voice_options:
            del self.voice_options[name]
            console.print(f"[yellow]Cleared option: {name}[/yellow]")
        else:
            console.print(f"[yellow]Option '{name}' was not set.[/yellow]")

    def cmd_clearoptions(self, args):
        """Clear all voice options."""
        self.voice_options = {}
        console.print("[green]All voice options cleared.[/green]")

    def cmd_play(self, args):
        """Generate audio and play with mpv."""
        if not self.selected_voice:
            console.print("[red]No voice selected. Use 'select <index>' first.[/red]")
            return
        if not self.input_text:
            console.print("[red]No text set. Use 'text <your text>' first.[/red]")
            return

        audio_file = None
        error = None

        def generate():
            nonlocal audio_file, error
            try:
                audio_file = self.manager.get_tts_audio(
                    self.input_text,
                    self.selected_voice['service'],
                    self.selected_voice['voice_key'],
                    self.voice_options,
                )
            except Exception as e:
                error = e

        with Live(
            Spinner("dots", text=Text("Generating audio...", style="bold cyan")),
            console=console,
            refresh_per_second=10,
            transient=True,
        ) as live:
            thread = threading.Thread(target=generate)
            thread.start()
            thread.join()

        if error:
            console.print(f"[red]Audio generation failed: {error}[/red]")
            return

        console.print("[green]Audio generated. Playing with mpv...[/green]")
        try:
            subprocess.run(
                ["mpv", "--no-video", audio_file.name],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except FileNotFoundError:
            console.print("[red]mpv not found. Install mpv to play audio.[/red]")
        except subprocess.CalledProcessError as e:
            console.print(f"[red]mpv playback error: {e}[/red]")

    def cmd_status(self, args):
        """Show current state."""
        table = Table(title="Current State")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Voice", self.selected_voice['voice_description'] if self.selected_voice else "[dim]<none>[/dim]")
        table.add_row("Text", self.input_text or "[dim]<none>[/dim]")
        table.add_row("Options", str(self.voice_options) if self.voice_options else "[dim]<none>[/dim]")
        console.print(table)
        self._show_filters()

    def cmd_help(self, args):
        """Show help."""
        table = Table(title="Commands")
        table.add_column("Command", style="cyan bold")
        table.add_column("Description")

        cmds = [
            ("voices [page]", "List voices (paginated)"),
            ("next / prev", "Next/previous page"),
            ("filter <field> <value>", "Filter voices (service, gender, language, locale, name)"),
            ("filter <field>", "Clear a single filter"),
            ("filter", "Show active filters"),
            ("clearfilters", "Clear all filters"),
            ("select <index>", "Select a voice by index number"),
            ("text <input>", "Set input text for TTS"),
            ("options", "List available options for selected voice"),
            ("set <option> <value>", "Set a voice option"),
            ("clear <option>", "Clear one voice option"),
            ("clearoptions", "Clear all voice options"),
            ("play", "Generate audio and play with mpv"),
            ("status", "Show current state"),
            ("help", "Show this help"),
            ("quit / exit", "Exit the REPL"),
        ]
        for cmd, desc in cmds:
            table.add_row(cmd, desc)
        console.print(table)

    def get_completer(self):
        commands = [
            'voices', 'next', 'prev', 'filter', 'clearfilters',
            'select', 'text', 'options', 'set', 'clear', 'clearoptions',
            'play', 'status', 'help', 'quit', 'exit',
        ]
        return WordCompleter(commands, ignore_case=True)

    def run(self):
        self.initialize()

        session = PromptSession(completer=self.get_completer())
        self.cmd_help([])

        dispatch = {
            'voices': self.cmd_voices,
            'next': self.cmd_next,
            'prev': self.cmd_prev,
            'filter': self.cmd_filter,
            'clearfilters': self.cmd_clearfilters,
            'select': self.cmd_select,
            'text': self.cmd_text,
            'options': self.cmd_options,
            'set': self.cmd_set,
            'clear': self.cmd_clear,
            'clearoptions': self.cmd_clearoptions,
            'play': self.cmd_play,
            'status': self.cmd_status,
            'help': self.cmd_help,
        }

        while True:
            try:
                line = session.prompt("tts> ")
            except (EOFError, KeyboardInterrupt):
                break

            line = line.strip()
            if not line:
                continue

            try:
                parts = shlex.split(line)
            except ValueError:
                parts = line.split()

            cmd = parts[0].lower()
            args = parts[1:]

            if cmd in ('quit', 'exit'):
                break

            handler = dispatch.get(cmd)
            if handler:
                handler(args)
            else:
                console.print(f"[red]Unknown command: {cmd}. Type 'help' for commands.[/red]")

        console.print("[dim]Goodbye.[/dim]")


@app.command()
def main():
    """TTS Voice Explorer - interactive REPL for testing text-to-speech."""
    repl = TTSRepl()
    repl.run()


if __name__ == "__main__":
    app()
