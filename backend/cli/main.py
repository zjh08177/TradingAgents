from typing import Optional
import datetime
import typer
from pathlib import Path
from functools import wraps
from rich.console import Console
from rich.panel import Panel
from rich.spinner import Spinner
from rich.live import Live
from rich.columns import Columns
from rich.markdown import Markdown
from rich.layout import Layout
from rich.text import Text
from rich.live import Live
from rich.table import Table
from collections import deque
import time
from rich.tree import Tree
from rich import box
from rich.align import Align
from rich.rule import Rule

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG
from cli.models import AnalystType
from cli.utils import *

console = Console()

app = typer.Typer(
    name="TradingAgents",
    help="TradingAgents CLI: Multi-Agents LLM Financial Trading Framework",
    add_completion=True,  # Enable shell completion
)


# Create a deque to store recent messages with a maximum length
class MessageBuffer:
    def __init__(self, max_length=100):
        self.messages = deque(maxlen=max_length)
        self.tool_calls = deque(maxlen=max_length)
        self.current_report = None
        self.final_report = None  # Store the complete final report
        self.agent_status = {
            # Analyst Team
            "Market Analyst": "pending",
            "Social Analyst": "pending",
            "News Analyst": "pending",
            "Fundamentals Analyst": "pending",
            # Research Team
            "Bull Researcher": "pending",
            "Bear Researcher": "pending",
            "Research Manager": "pending",
            # Trading Team
            "Trader": "pending",
            # Risk Management Team
            "Risky Analyst": "pending",
            "Neutral Analyst": "pending",
            "Safe Analyst": "pending",
            # Portfolio Management Team
            "Portfolio Manager": "pending",
        }
        self.current_agent = None
        self.report_sections = {
            "market_report": None,
            "sentiment_report": None,
            "news_report": None,
            "fundamentals_report": None,
            "investment_plan": None,
            "trader_investment_plan": None,
            "final_trade_decision": None,
        }

    def add_message(self, message_type, content):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.messages.append((timestamp, message_type, content))

    def add_tool_call(self, tool_name, args):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.tool_calls.append((timestamp, tool_name, args))

    def update_agent_status(self, agent, status):
        if agent in self.agent_status:
            self.agent_status[agent] = status
            self.current_agent = agent

    def update_report_section(self, section_name, content):
        if section_name in self.report_sections:
            self.report_sections[section_name] = content
            self._update_current_report()

    def _update_current_report(self):
        # For the panel display, only show the most recently updated section
        latest_section = None
        latest_content = None

        # Find the most recently updated section
        for section, content in self.report_sections.items():
            if content is not None:
                latest_section = section
                latest_content = content
               
        if latest_section and latest_content:
            # Format the current section for display
            section_titles = {
                "market_report": "Market Analysis",
                "sentiment_report": "Social Sentiment",
                "news_report": "News Analysis",
                "fundamentals_report": "Fundamentals Analysis",
                "investment_plan": "Research Team Decision",
                "trader_investment_plan": "Trading Team Plan",
                "final_trade_decision": "Portfolio Management Decision",
            }
            self.current_report = (
                f"### {section_titles[latest_section]}\n{latest_content}"
            )

        # Update the final complete report
        self._update_final_report()

    def _update_final_report(self):
        report_parts = []

        # Analyst Team Reports
        if any(
            self.report_sections[section]
            for section in [
                "market_report",
                "sentiment_report",
                "news_report",
                "fundamentals_report",
            ]
        ):
            report_parts.append("## Analyst Team Reports")
            if self.report_sections["market_report"]:
                report_parts.append(
                    f"### Market Analysis\n{self.report_sections['market_report']}"
                )
            if self.report_sections["sentiment_report"]:
                report_parts.append(
                    f"### Social Sentiment\n{self.report_sections['sentiment_report']}"
                )
            if self.report_sections["news_report"]:
                report_parts.append(
                    f"### News Analysis\n{self.report_sections['news_report']}"
                )
            if self.report_sections["fundamentals_report"]:
                report_parts.append(
                    f"### Fundamentals Analysis\n{self.report_sections['fundamentals_report']}"
                )

        # Research Team Reports
        if self.report_sections["investment_plan"]:
            report_parts.append("## Research Team Decision")
            report_parts.append(f"{self.report_sections['investment_plan']}")

        # Trading Team Reports
        if self.report_sections["trader_investment_plan"]:
            report_parts.append("## Trading Team Plan")
            report_parts.append(f"{self.report_sections['trader_investment_plan']}")

        # Portfolio Management Decision
        if self.report_sections["final_trade_decision"]:
            report_parts.append("## Portfolio Management Decision")
            report_parts.append(f"{self.report_sections['final_trade_decision']}")

        self.final_report = "\n\n".join(report_parts) if report_parts else None


message_buffer = MessageBuffer()


def create_layout():
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="main"),
        Layout(name="footer", size=3),
    )
    layout["main"].split_column(
        Layout(name="upper", ratio=3), Layout(name="analysis", ratio=5)
    )
    layout["upper"].split_row(
        Layout(name="progress", ratio=2), Layout(name="messages", ratio=3)
    )
    return layout


def update_display(layout, spinner_text=None):
    # Header with welcome message
    layout["header"].update(
        Panel(
            "[bold green]Welcome to TradingAgents CLI[/bold green]\n"
            "[dim]© [Tauric Research](https://github.com/TauricResearch)[/dim]",
            title="Welcome to TradingAgents",
            border_style="green",
            padding=(1, 2),
            expand=True,
        )
    )

    # Progress panel showing agent status
    progress_table = Table(
        show_header=True,
        header_style="bold magenta",
        show_footer=False,
        box=box.SIMPLE_HEAD,  # Use simple header with horizontal lines
        title=None,  # Remove the redundant Progress title
        padding=(0, 2),  # Add horizontal padding
        expand=True,  # Make table expand to fill available space
    )
    progress_table.add_column("Team", style="cyan", justify="center", width=20)
    progress_table.add_column("Agent", style="green", justify="center", width=20)
    progress_table.add_column("Status", style="yellow", justify="center", width=20)

    # Group agents by team
    teams = {
        "Analyst Team": [
            "Market Analyst",
            "Social Analyst",
            "News Analyst",
            "Fundamentals Analyst",
        ],
        "Research Team": ["Bull Researcher", "Bear Researcher", "Research Manager"],
        "Trading Team": ["Trader"],
        "Risk Management": ["Risky Analyst", "Neutral Analyst", "Safe Analyst"],
        "Portfolio Management": ["Portfolio Manager"],
    }

    for team, agents in teams.items():
        # Add first agent with team name
        first_agent = agents[0]
        status = message_buffer.agent_status[first_agent]
        if status == "in_progress":
            spinner = Spinner(
                "dots", text="[blue]in_progress[/blue]", style="bold cyan"
            )
            status_cell = spinner
        else:
            status_color = {
                "pending": "yellow",
                "completed": "green",
                "error": "red",
            }.get(status, "white")
            status_cell = f"[{status_color}]{status}[/{status_color}]"
        progress_table.add_row(team, first_agent, status_cell)

        # Add remaining agents in team
        for agent in agents[1:]:
            status = message_buffer.agent_status[agent]
            if status == "in_progress":
                spinner = Spinner(
                    "dots", text="[blue]in_progress[/blue]", style="bold cyan"
                )
                status_cell = spinner
            else:
                status_color = {
                    "pending": "yellow",
                    "completed": "green",
                    "error": "red",
                }.get(status, "white")
                status_cell = f"[{status_color}]{status}[/{status_color}]"
            progress_table.add_row("", agent, status_cell)

        # Add horizontal line after each team
        progress_table.add_row("─" * 20, "─" * 20, "─" * 20, style="dim")

    layout["progress"].update(
        Panel(progress_table, title="Progress", border_style="cyan", padding=(1, 2))
    )

    # Messages panel showing recent messages and tool calls
    messages_table = Table(
        show_header=True,
        header_style="bold magenta",
        show_footer=False,
        expand=True,  # Make table expand to fill available space
        box=box.MINIMAL,  # Use minimal box style for a lighter look
        show_lines=True,  # Keep horizontal lines
        padding=(0, 1),  # Add some padding between columns
    )
    messages_table.add_column("Time", style="cyan", width=8, justify="center")
    messages_table.add_column("Type", style="green", width=10, justify="center")
    messages_table.add_column(
        "Content", style="white", no_wrap=False, ratio=1
    )  # Make content column expand

    # Combine tool calls and messages
    all_messages = []

    # Add tool calls
    for timestamp, tool_name, args in message_buffer.tool_calls:
        # Truncate tool call args if too long
        if isinstance(args, str) and len(args) > 100:
            args = args[:97] + "..."
        all_messages.append((timestamp, "Tool", f"{tool_name}: {args}"))

    # Add regular messages
    for timestamp, msg_type, content in message_buffer.messages:
        # Convert content to string if it's not already
        content_str = content
        if isinstance(content, list):
            # Handle list of content blocks (Anthropic format)
            text_parts = []
            for item in content:
                if isinstance(item, dict):
                    if item.get('type') == 'text':
                        text_parts.append(item.get('text', ''))
                    elif item.get('type') == 'tool_use':
                        text_parts.append(f"[Tool: {item.get('name', 'unknown')}]")
                else:
                    text_parts.append(str(item))
            content_str = ' '.join(text_parts)
        elif not isinstance(content_str, str):
            content_str = str(content)
            
        # Truncate message content if too long
        if len(content_str) > 200:
            content_str = content_str[:197] + "..."
        all_messages.append((timestamp, msg_type, content_str))

    # Sort by timestamp
    all_messages.sort(key=lambda x: x[0])

    # Calculate how many messages we can show based on available space
    # Start with a reasonable number and adjust based on content length
    max_messages = 12  # Increased from 8 to better fill the space

    # Get the last N messages that will fit in the panel
    recent_messages = all_messages[-max_messages:]

    # Add messages to table
    for timestamp, msg_type, content in recent_messages:
        # Format content with word wrapping
        wrapped_content = Text(content, overflow="fold")
        messages_table.add_row(timestamp, msg_type, wrapped_content)

    if spinner_text:
        messages_table.add_row("", "Spinner", spinner_text)

    # Add a footer to indicate if messages were truncated
    if len(all_messages) > max_messages:
        messages_table.footer = (
            f"[dim]Showing last {max_messages} of {len(all_messages)} messages[/dim]"
        )

    layout["messages"].update(
        Panel(
            messages_table,
            title="Messages & Tools",
            border_style="blue",
            padding=(1, 2),
        )
    )

    # Analysis panel showing current report
    if message_buffer.current_report:
        layout["analysis"].update(
            Panel(
                Markdown(message_buffer.current_report),
                title="Current Report",
                border_style="green",
                padding=(1, 2),
            )
        )
    else:
        layout["analysis"].update(
            Panel(
                "[italic]Waiting for analysis report...[/italic]",
                title="Current Report",
                border_style="green",
                padding=(1, 2),
            )
        )

    # Footer with statistics
    tool_calls_count = len(message_buffer.tool_calls)
    llm_calls_count = sum(
        1 for _, msg_type, _ in message_buffer.messages if msg_type == "Reasoning"
    )
    reports_count = sum(
        1 for content in message_buffer.report_sections.values() if content is not None
    )

    stats_table = Table(show_header=False, box=None, padding=(0, 2), expand=True)
    stats_table.add_column("Stats", justify="center")
    stats_table.add_row(
        f"Tool Calls: {tool_calls_count} | LLM Calls: {llm_calls_count} | Generated Reports: {reports_count}"
    )

    layout["footer"].update(Panel(stats_table, border_style="grey50"))


def get_user_selections():
    """Get user ticker selection with simplified interface and sensible defaults."""
    # Display ASCII art welcome message
    with open("./cli/static/welcome.txt", "r") as f:
        welcome_ascii = f.read()

    # Create welcome box content
    welcome_content = f"{welcome_ascii}\n"
    welcome_content += "[bold green]TradingAgents: Multi-Agents LLM Financial Trading Framework - CLI[/bold green]\n\n"
    welcome_content += "[bold]Workflow Steps:[/bold]\n"
    welcome_content += "I. Analyst Team → II. Research Team → III. Trader → IV. Risk Management → V. Portfolio Management\n\n"
    welcome_content += (
        "[dim]Built by [Tauric Research](https://github.com/TauricResearch)[/dim]"
    )

    # Create and center the welcome box
    welcome_box = Panel(
        welcome_content,
        border_style="green",
        padding=(1, 2),
        title="Welcome to TradingAgents",
        subtitle="Multi-Agents LLM Financial Trading Framework",
    )
    console.print(Align.center(welcome_box))
    console.print()  # Add a blank line after the welcome box

    # Simplified input - only ask for ticker symbol
    ticker_box = Panel(
        "[bold]Enter Ticker Symbol[/bold]\n[dim]Enter the stock ticker you want to analyze (e.g., AAPL, TSLA, SPY)[/dim]\n[dim]Default: SPY[/dim]",
        border_style="blue",
        padding=(1, 2)
    )
    console.print(ticker_box)
    selected_ticker = get_ticker()

    # Use sensible defaults for all other parameters
    analysis_date = datetime.datetime.now().strftime("%Y-%m-%d")
    selected_analysts = [AnalystType.MARKET, AnalystType.SOCIAL, AnalystType.NEWS, AnalystType.FUNDAMENTALS]
    selected_research_depth = 5
    selected_llm_provider = "openai"
    backend_url = "https://api.openai.com/v1"
    selected_shallow_thinker = "gpt-4o"
    selected_deep_thinker = "o3"

    # Display the configuration being used
    config_info = f"""[bold green]Configuration:[/bold green]
• [bold]Ticker:[/bold] {selected_ticker}
• [bold]Date:[/bold] {analysis_date} (latest trading day)
• [bold]Analysts:[/bold] All analysts (Market, Social, News, Fundamentals)
• [bold]Research Depth:[/bold] Deep (5 rounds of debate)
• [bold]LLM Provider:[/bold] OpenAI
• [bold]Quick Thinking:[/bold] GPT-4o
• [bold]Deep Thinking:[/bold] o3

[dim]Starting analysis with optimized settings...[/dim]"""

    console.print(Panel(config_info, border_style="green", padding=(1, 2), title="Analysis Configuration"))
    console.print()

    return {
        "ticker": selected_ticker,
        "analysis_date": analysis_date,
        "analysts": selected_analysts,
        "research_depth": selected_research_depth,
        "llm_provider": selected_llm_provider.lower(),
        "backend_url": backend_url,
        "shallow_thinker": selected_shallow_thinker,
        "deep_thinker": selected_deep_thinker,
    }


def get_ticker():
    """Get ticker symbol from user input."""
    ticker = typer.prompt("", default="SPY")
    return ticker.strip().upper()


def get_analysis_date():
    """Get the analysis date from user input."""
    while True:
        date_str = typer.prompt(
            "", default=datetime.datetime.now().strftime("%Y-%m-%d")
        )
        try:
            # Validate date format and ensure it's not in the future
            analysis_date = datetime.datetime.strptime(date_str, "%Y-%m-%d")
            if analysis_date.date() > datetime.datetime.now().date():
                console.print("[red]Error: Analysis date cannot be in the future[/red]")
                continue
            return date_str
        except ValueError:
            console.print(
                "[red]Error: Invalid date format. Please use YYYY-MM-DD[/red]"
            )


def display_complete_report(final_state):
    """Display the complete analysis report with team-based panels."""
    console.print("\n[bold green]Complete Analysis Report[/bold green]\n")

    # I. Analyst Team Reports
    analyst_reports = []

    # Market Analyst Report
    if final_state.get("market_report"):
        analyst_reports.append(
            Panel(
                Markdown(final_state["market_report"]),
                title="Market Analyst",
                border_style="blue",
                padding=(1, 2),
            )
        )

    # Social Analyst Report
    if final_state.get("sentiment_report"):
        analyst_reports.append(
            Panel(
                Markdown(final_state["sentiment_report"]),
                title="Social Analyst",
                border_style="blue",
                padding=(1, 2),
            )
        )

    # News Analyst Report
    if final_state.get("news_report"):
        analyst_reports.append(
            Panel(
                Markdown(final_state["news_report"]),
                title="News Analyst",
                border_style="blue",
                padding=(1, 2),
            )
        )

    # Fundamentals Analyst Report
    if final_state.get("fundamentals_report"):
        analyst_reports.append(
            Panel(
                Markdown(final_state["fundamentals_report"]),
                title="Fundamentals Analyst",
                border_style="blue",
                padding=(1, 2),
            )
        )

    if analyst_reports:
        console.print(
            Panel(
                Columns(analyst_reports, equal=True, expand=True),
                title="I. Analyst Team Reports",
                border_style="cyan",
                padding=(1, 2),
            )
        )

    # II. Research Team Reports
    if final_state.get("investment_debate_state"):
        research_reports = []
        debate_state = final_state["investment_debate_state"]

        # Bull Researcher Analysis
        if debate_state.get("bull_history"):
            research_reports.append(
                Panel(
                    Markdown(debate_state["bull_history"]),
                    title="Bull Researcher",
                    border_style="blue",
                    padding=(1, 2),
                )
            )

        # Bear Researcher Analysis
        if debate_state.get("bear_history"):
            research_reports.append(
                Panel(
                    Markdown(debate_state["bear_history"]),
                    title="Bear Researcher",
                    border_style="blue",
                    padding=(1, 2),
                )
            )

        # Research Manager Decision
        if debate_state.get("judge_decision"):
            research_reports.append(
                Panel(
                    Markdown(debate_state["judge_decision"]),
                    title="Research Manager",
                    border_style="blue",
                    padding=(1, 2),
                )
            )

        if research_reports:
            console.print(
                Panel(
                    Columns(research_reports, equal=True, expand=True),
                    title="II. Research Team Decision",
                    border_style="magenta",
                    padding=(1, 2),
                )
            )

    # III. Trading Team Reports
    if final_state.get("trader_investment_plan"):
        console.print(
            Panel(
                Panel(
                    Markdown(final_state["trader_investment_plan"]),
                    title="Trader",
                    border_style="blue",
                    padding=(1, 2),
                ),
                title="III. Trading Team Plan",
                border_style="yellow",
                padding=(1, 2),
            )
        )

    # IV. Risk Management Team Reports
    if final_state.get("risk_debate_state"):
        risk_reports = []
        risk_state = final_state["risk_debate_state"]

        # Aggressive (Risky) Analyst Analysis
        if risk_state.get("risky_history"):
            risk_reports.append(
                Panel(
                    Markdown(risk_state["risky_history"]),
                    title="Aggressive Analyst",
                    border_style="blue",
                    padding=(1, 2),
                )
            )

        # Conservative (Safe) Analyst Analysis
        if risk_state.get("safe_history"):
            risk_reports.append(
                Panel(
                    Markdown(risk_state["safe_history"]),
                    title="Conservative Analyst",
                    border_style="blue",
                    padding=(1, 2),
                )
            )

        # Neutral Analyst Analysis
        if risk_state.get("neutral_history"):
            risk_reports.append(
                Panel(
                    Markdown(risk_state["neutral_history"]),
                    title="Neutral Analyst",
                    border_style="blue",
                    padding=(1, 2),
                )
            )

        if risk_reports:
            console.print(
                Panel(
                    Columns(risk_reports, equal=True, expand=True),
                    title="IV. Risk Management Team Decision",
                    border_style="red",
                    padding=(1, 2),
                )
            )

        # V. Portfolio Manager Decision
        if risk_state.get("judge_decision"):
            console.print(
                Panel(
                    Panel(
                        Markdown(risk_state["judge_decision"]),
                        title="Portfolio Manager",
                        border_style="blue",
                        padding=(1, 2),
                    ),
                    title="V. Portfolio Manager Decision",
                    border_style="green",
                    padding=(1, 2),
                )
            )


def update_research_team_status(status):
    """Update status for all research team members and trader."""
    research_team = ["Bull Researcher", "Bear Researcher", "Research Manager", "Trader"]
    for agent in research_team:
        message_buffer.update_agent_status(agent, status)

def extract_content_string(content):
    """Extract string content from various message formats."""
    if isinstance(content, str):
        return content
    elif isinstance(content, list):
        # Handle Anthropic's list format
        text_parts = []
        for item in content:
            if isinstance(item, dict):
                if item.get('type') == 'text':
                    text_parts.append(item.get('text', ''))
                elif item.get('type') == 'tool_use':
                    text_parts.append(f"[Tool: {item.get('name', 'unknown')}]")
            else:
                text_parts.append(str(item))
        return ' '.join(text_parts)
    else:
        return str(content)

def get_user_selections_advanced():
    """Get all user selections with advanced configuration options."""
    # Display ASCII art welcome message
    with open("./cli/static/welcome.txt", "r") as f:
        welcome_ascii = f.read()

    # Create welcome box content
    welcome_content = f"{welcome_ascii}\n"
    welcome_content += "[bold green]TradingAgents: Multi-Agents LLM Financial Trading Framework - CLI (Advanced Mode)[/bold green]\n\n"
    welcome_content += "[bold]Workflow Steps:[/bold]\n"
    welcome_content += "I. Analyst Team → II. Research Team → III. Trader → IV. Risk Management → V. Portfolio Management\n\n"
    welcome_content += (
        "[dim]Built by [Tauric Research](https://github.com/TauricResearch)[/dim]"
    )

    # Create and center the welcome box
    welcome_box = Panel(
        welcome_content,
        border_style="green",
        padding=(1, 2),
        title="Welcome to TradingAgents - Advanced Mode",
        subtitle="Multi-Agents LLM Financial Trading Framework",
    )
    console.print(Align.center(welcome_box))
    console.print()  # Add a blank line after the welcome box

    # Create a boxed questionnaire for each step
    def create_question_box(title, prompt, default=None):
        box_content = f"[bold]{title}[/bold]\n"
        box_content += f"[dim]{prompt}[/dim]"
        if default:
            box_content += f"\n[dim]Default: {default}[/dim]"
        return Panel(box_content, border_style="blue", padding=(1, 2))

    # Step 1: Ticker symbol
    console.print(
        create_question_box(
            "Step 1: Ticker Symbol", "Enter the ticker symbol to analyze", "SPY"
        )
    )
    selected_ticker = get_ticker()

    # Step 2: Analysis date
    default_date = datetime.datetime.now().strftime("%Y-%m-%d")
    console.print(
        create_question_box(
            "Step 2: Analysis Date",
            "Enter the analysis date (YYYY-MM-DD)",
            default_date,
        )
    )
    analysis_date = get_analysis_date()

    # Step 3: Select analysts
    console.print(
        create_question_box(
            "Step 3: Analysts Team", "Select your LLM analyst agents for the analysis"
        )
    )
    selected_analysts = select_analysts()
    console.print(
        f"[green]Selected analysts:[/green] {', '.join(analyst.value for analyst in selected_analysts)}"
    )

    # Step 4: Research depth
    console.print(
        create_question_box(
            "Step 4: Research Depth", "Select your research depth level"
        )
    )
    selected_research_depth = select_research_depth()

    # Step 5: OpenAI backend
    console.print(
        create_question_box(
            "Step 5: LLM Provider", "Select which service to talk to"
        )
    )
    selected_llm_provider, backend_url = select_llm_provider()
    
    # Step 6: Thinking agents
    console.print(
        create_question_box(
            "Step 6: Thinking Agents", "Select your thinking agents for analysis"
        )
    )
    selected_shallow_thinker = select_shallow_thinking_agent(selected_llm_provider)
    selected_deep_thinker = select_deep_thinking_agent(selected_llm_provider)

    return {
        "ticker": selected_ticker,
        "analysis_date": analysis_date,
        "analysts": selected_analysts,
        "research_depth": selected_research_depth,
        "llm_provider": selected_llm_provider.lower(),
        "backend_url": backend_url,
        "shallow_thinker": selected_shallow_thinker,
        "deep_thinker": selected_deep_thinker,
    }


def run_analysis(advanced_mode=False):
    # Get user selections based on mode
    if advanced_mode:
        selections = get_user_selections_advanced()
    else:
        selections = get_user_selections()

    # Create config with selected research depth
    config = DEFAULT_CONFIG.copy()
    config["max_debate_rounds"] = selections["research_depth"]
    config["max_risk_discuss_rounds"] = selections["research_depth"]
    config["quick_think_llm"] = selections["shallow_thinker"]
    config["deep_think_llm"] = selections["deep_thinker"]
    config["backend_url"] = selections["backend_url"]
    config["llm_provider"] = selections["llm_provider"].lower()

    # Initialize the graph
    graph = TradingAgentsGraph(
        [analyst.value for analyst in selections["analysts"]], config=config, debug=True
    )

    # Create result directory
    results_dir = Path(config["results_dir"]) / selections["ticker"] / selections["analysis_date"]
    results_dir.mkdir(parents=True, exist_ok=True)
    report_dir = results_dir / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    log_file = results_dir / "message_tool.log"
    log_file.touch(exist_ok=True)

    def save_message_decorator(obj, func_name):
        func = getattr(obj, func_name)
        @wraps(func)
        def wrapper(*args, **kwargs):
            func(*args, **kwargs)
            timestamp, message_type, content = obj.messages[-1]
            content = content.replace("\n", " ")  # Replace newlines with spaces
            with open(log_file, "a") as f:
                f.write(f"{timestamp} [{message_type}] {content}\n")
        return wrapper
    
    def save_tool_call_decorator(obj, func_name):
        func = getattr(obj, func_name)
        @wraps(func)
        def wrapper(*args, **kwargs):
            func(*args, **kwargs)
            timestamp, tool_name, args = obj.tool_calls[-1]
            args_str = ", ".join(f"{k}={v}" for k, v in args.items())
            with open(log_file, "a") as f:
                f.write(f"{timestamp} [Tool Call] {tool_name}({args_str})\n")
        return wrapper

    def save_report_section_decorator(obj, func_name):
        func = getattr(obj, func_name)
        @wraps(func)
        def wrapper(section_name, content):
            func(section_name, content)
            if section_name in obj.report_sections and obj.report_sections[section_name] is not None:
                content = obj.report_sections[section_name]
                if content:
                    file_name = f"{section_name}.md"
                    with open(report_dir / file_name, "w") as f:
                        f.write(content)
        return wrapper

    message_buffer.add_message = save_message_decorator(message_buffer, "add_message")
    message_buffer.add_tool_call = save_tool_call_decorator(message_buffer, "add_tool_call")
    message_buffer.update_report_section = save_report_section_decorator(message_buffer, "update_report_section")

    # Now start the display layout
    layout = create_layout()

    with Live(layout, refresh_per_second=4) as live:
        # Initial display
        update_display(layout)

        # Add initial messages
        message_buffer.add_message("System", f"Selected ticker: {selections['ticker']}")
        message_buffer.add_message(
            "System", f"Analysis date: {selections['analysis_date']}"
        )
        message_buffer.add_message(
            "System",
            f"Selected analysts: {', '.join(analyst.value for analyst in selections['analysts'])}",
        )
        update_display(layout)

        # Reset agent statuses
        for agent in message_buffer.agent_status:
            message_buffer.update_agent_status(agent, "pending")

        # Reset report sections
        for section in message_buffer.report_sections:
            message_buffer.report_sections[section] = None
        message_buffer.current_report = None
        message_buffer.final_report = None

        # Update agent status to in_progress for the first analyst
        first_analyst = f"{selections['analysts'][0].value.capitalize()} Analyst"
        message_buffer.update_agent_status(first_analyst, "in_progress")
        update_display(layout)

        # Create spinner text
        spinner_text = (
            f"Analyzing {selections['ticker']} on {selections['analysis_date']}..."
        )
        update_display(layout, spinner_text)

        # Initialize state and get graph args
        init_agent_state = graph.propagator.create_initial_state(
            selections["ticker"], selections["analysis_date"]
        )
        args = graph.propagator.get_graph_args()

        # Stream the analysis
        trace = []
        for chunk in graph.graph.stream(init_agent_state, **args):
            # Handle the new parallel execution structure
            messages_found = False
            
            # Check for messages in the old format (for backward compatibility)
            if "messages" in chunk and len(chunk["messages"]) > 0:
                messages_found = True
                last_message = chunk["messages"][-1]
                
                # Extract message content and type
                if hasattr(last_message, "content"):
                    content = extract_content_string(last_message.content)  # Use the helper function
                    msg_type = "Reasoning"
                else:
                    content = str(last_message)
                    msg_type = "System"

                # Add message to buffer
                message_buffer.add_message(msg_type, content)                

                # If it's a tool call, add it to tool calls
                if hasattr(last_message, "tool_calls"):
                    for tool_call in last_message.tool_calls:
                        # Handle both dictionary and object tool calls
                        if isinstance(tool_call, dict):
                            message_buffer.add_tool_call(
                                tool_call["name"], tool_call["args"]
                            )
                        else:
                            message_buffer.add_tool_call(tool_call.name, tool_call.args)
            
            # Check for messages in the new parallel execution format
            else:
                # Look for messages in analyst channels
                message_channels = ["market_messages", "social_messages", "news_messages", "fundamentals_messages"]
                
                for node_name, node_data in chunk.items():
                    if isinstance(node_data, dict):
                        for channel in message_channels:
                            if channel in node_data and node_data[channel]:
                                messages_found = True
                                # Get the last message from this channel
                                last_message = node_data[channel][-1]
                                
                                # Extract message content and type
                                if hasattr(last_message, "content"):
                                    content = extract_content_string(last_message.content)
                                    msg_type = f"{channel.replace('_messages', '').title()} Analyst"
                                else:
                                    content = str(last_message)
                                    msg_type = f"{channel.replace('_messages', '').title()} System"

                                # Add message to buffer
                                message_buffer.add_message(msg_type, content)                

                                # If it's a tool call, add it to tool calls
                                if hasattr(last_message, "tool_calls"):
                                    for tool_call in last_message.tool_calls:
                                        # Handle both dictionary and object tool calls
                                        if isinstance(tool_call, dict):
                                            message_buffer.add_tool_call(
                                                tool_call["name"], tool_call["args"]
                                            )
                                        else:
                                            message_buffer.add_tool_call(tool_call.name, tool_call.args)
                                
                                # Only process the first message channel found to avoid duplicates
                                break
                    if messages_found:
                        break
            
            # Continue with the rest of the processing (reports, etc.)
            if True:  # Always process chunk for reports regardless of messages

                # Update reports and agent status based on chunk content
                # Analyst Team Reports
                if "market_report" in chunk and chunk["market_report"]:
                    message_buffer.update_report_section(
                        "market_report", chunk["market_report"]
                    )
                    message_buffer.update_agent_status("Market Analyst", "completed")
                    # Set next analyst to in_progress
                    if "social" in selections["analysts"]:
                        message_buffer.update_agent_status(
                            "Social Analyst", "in_progress"
                        )

                if "sentiment_report" in chunk and chunk["sentiment_report"]:
                    message_buffer.update_report_section(
                        "sentiment_report", chunk["sentiment_report"]
                    )
                    message_buffer.update_agent_status("Social Analyst", "completed")
                    # Set next analyst to in_progress
                    if "news" in selections["analysts"]:
                        message_buffer.update_agent_status(
                            "News Analyst", "in_progress"
                        )

                if "news_report" in chunk and chunk["news_report"]:
                    message_buffer.update_report_section(
                        "news_report", chunk["news_report"]
                    )
                    message_buffer.update_agent_status("News Analyst", "completed")
                    # Set next analyst to in_progress
                    if "fundamentals" in selections["analysts"]:
                        message_buffer.update_agent_status(
                            "Fundamentals Analyst", "in_progress"
                        )

                if "fundamentals_report" in chunk and chunk["fundamentals_report"]:
                    message_buffer.update_report_section(
                        "fundamentals_report", chunk["fundamentals_report"]
                    )
                    message_buffer.update_agent_status(
                        "Fundamentals Analyst", "completed"
                    )
                    # Set all research team members to in_progress
                    update_research_team_status("in_progress")

                # Research Team - Handle Investment Debate State
                if (
                    "investment_debate_state" in chunk
                    and chunk["investment_debate_state"]
                ):
                    debate_state = chunk["investment_debate_state"]

                    # Update Bull Researcher status and report
                    if "bull_history" in debate_state and debate_state["bull_history"]:
                        # Keep all research team members in progress
                        update_research_team_status("in_progress")
                        # Extract latest bull response
                        bull_responses = debate_state["bull_history"].split("\n")
                        latest_bull = bull_responses[-1] if bull_responses else ""
                        if latest_bull:
                            message_buffer.add_message("Reasoning", latest_bull)
                            # Update research report with bull's latest analysis
                            message_buffer.update_report_section(
                                "investment_plan",
                                f"### Bull Researcher Analysis\n{latest_bull}",
                            )

                    # Update Bear Researcher status and report
                    if "bear_history" in debate_state and debate_state["bear_history"]:
                        # Keep all research team members in progress
                        update_research_team_status("in_progress")
                        # Extract latest bear response
                        bear_responses = debate_state["bear_history"].split("\n")
                        latest_bear = bear_responses[-1] if bear_responses else ""
                        if latest_bear:
                            message_buffer.add_message("Reasoning", latest_bear)
                            # Update research report with bear's latest analysis
                            message_buffer.update_report_section(
                                "investment_plan",
                                f"{message_buffer.report_sections['investment_plan']}\n\n### Bear Researcher Analysis\n{latest_bear}",
                            )

                    # Update Research Manager status and final decision
                    if (
                        "judge_decision" in debate_state
                        and debate_state["judge_decision"]
                    ):
                        # Keep all research team members in progress until final decision
                        update_research_team_status("in_progress")
                        message_buffer.add_message(
                            "Reasoning",
                            f"Research Manager: {debate_state['judge_decision']}",
                        )
                        # Update research report with final decision
                        message_buffer.update_report_section(
                            "investment_plan",
                            f"{message_buffer.report_sections['investment_plan']}\n\n### Research Manager Decision\n{debate_state['judge_decision']}",
                        )
                        # Mark all research team members as completed
                        update_research_team_status("completed")
                        # Set first risk analyst to in_progress
                        message_buffer.update_agent_status(
                            "Risky Analyst", "in_progress"
                        )

                # Trading Team
                if (
                    "trader_investment_plan" in chunk
                    and chunk["trader_investment_plan"]
                ):
                    message_buffer.update_report_section(
                        "trader_investment_plan", chunk["trader_investment_plan"]
                    )
                    # Set first risk analyst to in_progress
                    message_buffer.update_agent_status("Risky Analyst", "in_progress")

                # Risk Management Team - Handle Risk Debate State
                if "risk_debate_state" in chunk and chunk["risk_debate_state"]:
                    risk_state = chunk["risk_debate_state"]

                    # Update Risky Analyst status and report
                    if (
                        "current_risky_response" in risk_state
                        and risk_state["current_risky_response"]
                    ):
                        message_buffer.update_agent_status(
                            "Risky Analyst", "in_progress"
                        )
                        message_buffer.add_message(
                            "Reasoning",
                            f"Risky Analyst: {risk_state['current_risky_response']}",
                        )
                        # Update risk report with risky analyst's latest analysis only
                        message_buffer.update_report_section(
                            "final_trade_decision",
                            f"### Risky Analyst Analysis\n{risk_state['current_risky_response']}",
                        )

                    # Update Safe Analyst status and report
                    if (
                        "current_safe_response" in risk_state
                        and risk_state["current_safe_response"]
                    ):
                        message_buffer.update_agent_status(
                            "Safe Analyst", "in_progress"
                        )
                        message_buffer.add_message(
                            "Reasoning",
                            f"Safe Analyst: {risk_state['current_safe_response']}",
                        )
                        # Update risk report with safe analyst's latest analysis only
                        message_buffer.update_report_section(
                            "final_trade_decision",
                            f"### Safe Analyst Analysis\n{risk_state['current_safe_response']}",
                        )

                    # Update Neutral Analyst status and report
                    if (
                        "current_neutral_response" in risk_state
                        and risk_state["current_neutral_response"]
                    ):
                        message_buffer.update_agent_status(
                            "Neutral Analyst", "in_progress"
                        )
                        message_buffer.add_message(
                            "Reasoning",
                            f"Neutral Analyst: {risk_state['current_neutral_response']}",
                        )
                        # Update risk report with neutral analyst's latest analysis only
                        message_buffer.update_report_section(
                            "final_trade_decision",
                            f"### Neutral Analyst Analysis\n{risk_state['current_neutral_response']}",
                        )

                    # Update Portfolio Manager status and final decision
                    if "judge_decision" in risk_state and risk_state["judge_decision"]:
                        message_buffer.update_agent_status(
                            "Portfolio Manager", "in_progress"
                        )
                        message_buffer.add_message(
                            "Reasoning",
                            f"Portfolio Manager: {risk_state['judge_decision']}",
                        )
                        # Update risk report with final decision only
                        message_buffer.update_report_section(
                            "final_trade_decision",
                            f"### Portfolio Manager Decision\n{risk_state['judge_decision']}",
                        )
                        # Mark risk analysts as completed
                        message_buffer.update_agent_status("Risky Analyst", "completed")
                        message_buffer.update_agent_status("Safe Analyst", "completed")
                        message_buffer.update_agent_status(
                            "Neutral Analyst", "completed"
                        )
                        message_buffer.update_agent_status(
                            "Portfolio Manager", "completed"
                        )

                # Update the display
                update_display(layout)

            trace.append(chunk)

        # Get final state and decision
        final_state = trace[-1]
        
        # Extract the final trade decision from the correct location
        final_trade_decision = None
        if "Risk Judge" in final_state and "final_trade_decision" in final_state["Risk Judge"]:
            final_trade_decision = final_state["Risk Judge"]["final_trade_decision"]
        elif "final_trade_decision" in final_state:
            final_trade_decision = final_state["final_trade_decision"]
        
        if final_trade_decision:
            decision = graph.process_signal(final_trade_decision)
        else:
            decision = "No trade decision available"

        # Update all agent statuses to completed
        for agent in message_buffer.agent_status:
            message_buffer.update_agent_status(agent, "completed")

        message_buffer.add_message(
            "Analysis", f"Completed analysis for {selections['analysis_date']}"
        )

        # Update final report sections
        for section in message_buffer.report_sections.keys():
            if section in final_state:
                message_buffer.update_report_section(section, final_state[section])

        # Display the complete final report
        display_complete_report(final_state)

        # Save the final complete report and decision
        # Save the final trade decision
        if final_trade_decision:
            decision_file = results_dir / "final_trade_decision.md"
            with open(decision_file, "w") as f:
                f.write(f"# Final Trading Decision\n\n")
                f.write(f"**Ticker:** {selections['ticker']}\n")
                f.write(f"**Analysis Date:** {selections['analysis_date']}\n")
                f.write(f"**Decision:** {decision}\n\n")
                f.write("## Raw Decision Text\n\n")
                f.write(final_trade_decision)
        
        # Save the complete final report
        complete_report_file = results_dir / "complete_analysis_report.md"
        with open(complete_report_file, "w") as f:
            f.write(f"# Complete Analysis Report\n\n")
            f.write(f"**Ticker:** {selections['ticker']}\n")
            f.write(f"**Analysis Date:** {selections['analysis_date']}\n")
            f.write(f"**Analysis Time:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Add analyst reports
            if final_state.get("market_report"):
                f.write("## Market Analysis\n\n")
                f.write(final_state["market_report"])
                f.write("\n\n")
            
            if final_state.get("sentiment_report"):
                f.write("## Social Media Sentiment Analysis\n\n")
                f.write(final_state["sentiment_report"])
                f.write("\n\n")
            
            if final_state.get("news_report"):
                f.write("## News Analysis\n\n")
                f.write(final_state["news_report"])
                f.write("\n\n")
            
            if final_state.get("fundamentals_report"):
                f.write("## Fundamentals Analysis\n\n")
                f.write(final_state["fundamentals_report"])
                f.write("\n\n")
            
            # Add research team analysis
            if final_state.get("investment_debate_state"):
                debate_state = final_state["investment_debate_state"]
                f.write("## Investment Research Analysis\n\n")
                
                if debate_state.get("bull_history"):
                    f.write("### Bull Researcher Analysis\n\n")
                    f.write(debate_state["bull_history"])
                    f.write("\n\n")
                
                if debate_state.get("bear_history"):
                    f.write("### Bear Researcher Analysis\n\n")
                    f.write(debate_state["bear_history"])
                    f.write("\n\n")
                
                if debate_state.get("judge_decision"):
                    f.write("### Research Manager Decision\n\n")
                    f.write(debate_state["judge_decision"])
                    f.write("\n\n")
            
            # Add trading analysis
            if final_state.get("trader_investment_plan"):
                f.write("## Trading Plan\n\n")
                f.write(final_state["trader_investment_plan"])
                f.write("\n\n")
            
            # Add risk analysis
            if final_state.get("risk_debate_state"):
                risk_state = final_state["risk_debate_state"]
                f.write("## Risk Management Analysis\n\n")
                
                if risk_state.get("risky_history"):
                    f.write("### Aggressive Risk Analysis\n\n")
                    f.write(risk_state["risky_history"])
                    f.write("\n\n")
                
                if risk_state.get("safe_history"):
                    f.write("### Conservative Risk Analysis\n\n")
                    f.write(risk_state["safe_history"])
                    f.write("\n\n")
                
                if risk_state.get("neutral_history"):
                    f.write("### Neutral Risk Analysis\n\n")
                    f.write(risk_state["neutral_history"])
                    f.write("\n\n")
                
                if risk_state.get("judge_decision"):
                    f.write("### Risk Manager Final Decision\n\n")
                    f.write(risk_state["judge_decision"])
                    f.write("\n\n")
            
            # Add final decision
            if final_trade_decision:
                f.write("## Final Trading Decision\n\n")
                f.write(f"**Decision:** {decision}\n\n")
                f.write("### Detailed Decision\n\n")
                f.write(final_trade_decision)
        
        # Save final state as JSON for programmatic access
        final_state_file = results_dir / "final_state.json"
        with open(final_state_file, "w") as f:
            import json
            # Convert final_state to JSON-serializable format
            json_state = {}
            for key, value in final_state.items():
                try:
                    json.dumps(value)  # Test if it's JSON serializable
                    json_state[key] = value
                except:
                    json_state[key] = str(value)  # Convert to string if not serializable
            json.dump(json_state, f, indent=2)
        
        print(f"\n✅ Analysis complete! Results saved to: {results_dir}")
        print(f"📄 Complete report: {complete_report_file}")
        print(f"🎯 Final decision: {decision_file}")
        print(f"📊 Final state: {final_state_file}")

        update_display(layout)


@app.command()
def analyze(
    advanced: bool = typer.Option(
        False, 
        "--advanced", 
        "-a", 
        help="Use advanced configuration mode with full customization options"
    ),
    streaming: bool = typer.Option(
        False,
        "--streaming",
        "-s", 
        help="Enable real-time streaming of analysis reports as they're generated"
    )
):
    """Run trading analysis with simplified or advanced configuration."""
    if streaming:
        run_analysis_streaming(advanced_mode=advanced)
    else:
        run_analysis(advanced_mode=advanced)


@app.command()
def stream(
    advanced: bool = typer.Option(
        False, 
        "--advanced", 
        "-a", 
        help="Use advanced configuration mode with full customization options"
    )
):
    """Run real-time streaming trading analysis."""
    run_analysis_streaming(advanced_mode=advanced)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    advanced: bool = typer.Option(
        False, 
        "--advanced", 
        "-a", 
        help="Use advanced configuration mode with full customization options"
    ),
    streaming: bool = typer.Option(
        False,
        "--streaming",
        "-s", 
        help="Enable real-time streaming of analysis reports as they're generated"
    )
):
    """TradingAgents CLI: Multi-Agents LLM Financial Trading Framework"""
    if ctx.invoked_subcommand is None:
        # Default behavior - run analysis
        if streaming:
            run_analysis_streaming(advanced_mode=advanced)
        else:
            run_analysis(advanced_mode=advanced)


class StreamingMessageBuffer(MessageBuffer):
    """Enhanced MessageBuffer for real-time content streaming"""
    
    def __init__(self, max_length=100):
        super().__init__(max_length)
        self.streaming_content = {
            "current_agent": None,
            "current_content": "",
            "content_buffer": "",
            "last_streamed_length": 0
        }
        self.content_callbacks = []
    
    def add_content_callback(self, callback):
        """Add a callback to be called when new content is streamed"""
        self.content_callbacks.append(callback)
    
    def stream_content(self, agent_name, content_chunk):
        """Stream content in real-time"""
        self.streaming_content["current_agent"] = agent_name
        self.streaming_content["content_buffer"] += content_chunk
        
        # Call registered callbacks with new content
        for callback in self.content_callbacks:
            callback(agent_name, content_chunk, self.streaming_content["content_buffer"])
    
    def finalize_streaming_content(self, section_name):
        """Finalize the streaming content into a report section"""
        if self.streaming_content["content_buffer"]:
            self.update_report_section(section_name, self.streaming_content["content_buffer"])
            self.streaming_content["content_buffer"] = ""
            self.streaming_content["last_streamed_length"] = 0


def create_streaming_layout():
    """Create layout optimized for streaming content"""
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="main"),
        Layout(name="footer", size=3),
    )
    layout["main"].split_column(
        Layout(name="upper", ratio=2),
        Layout(name="streaming_content", ratio=4),
        Layout(name="analysis", ratio=3)
    )
    layout["upper"].split_row(
        Layout(name="progress", ratio=2), Layout(name="messages", ratio=3)
    )
    return layout


def update_streaming_display(layout, streaming_buffer, spinner_text=None):
    """Update display with streaming content"""
    # Update header
    layout["header"].update(
        Panel(
            "[bold green]Welcome to TradingAgents CLI[/bold green]\n"
            "[dim]© [Tauric Research](https://github.com/TauricResearch)[/dim]",
            title="Welcome to TradingAgents",
            border_style="green",
        )
    )

    # Update progress panel using streaming_buffer
    progress_table = Table(show_header=False, box=box.MINIMAL)
    progress_table.add_column("Agent", style="cyan", no_wrap=True)
    progress_table.add_column("Status", style="magenta")

    for agent, status in streaming_buffer.agent_status.items():
        if status == "completed":
            status_icon = "✅"
        elif status == "in_progress":
            status_icon = "🔄"
        else:
            status_icon = "⏳"
        progress_table.add_row(agent, f"{status_icon} {status.title()}")

    layout["progress"].update(
        Panel(
            progress_table,
            title="Agent Progress",
            border_style="blue"
        )
    )

    # Update messages panel using streaming_buffer
    messages_content = []
    for timestamp, msg_type, content in list(streaming_buffer.messages)[-10:]:  # Show last 10 messages
        messages_content.append(f"[dim]{timestamp}[/dim] [{msg_type}] {content}")

    if spinner_text:
        messages_content.append(f"[yellow]⚡ {spinner_text}[/yellow]")

    layout["messages"].update(
        Panel(
            "\n".join(messages_content),
            title="Recent Messages",
            border_style="yellow"
        )
    )
    
    # Add streaming content panel
    if streaming_buffer.streaming_content["current_agent"] and streaming_buffer.streaming_content["content_buffer"]:
        agent_name = streaming_buffer.streaming_content["current_agent"]
        content = streaming_buffer.streaming_content["content_buffer"]
        
        # Limit display content to prevent overwhelming the terminal
        display_content = content[-2000:] if len(content) > 2000 else content
        if len(content) > 2000:
            display_content = "...\n" + display_content
        
        streaming_panel = Panel(
            Markdown(display_content),
            title=f"🔴 Live: {agent_name}",
            border_style="red",
            expand=True
        )
        layout["streaming_content"].update(streaming_panel)
    else:
        layout["streaming_content"].update(
            Panel(
                "[dim]Waiting for content to stream...[/dim]",
                title="📡 Streaming Content",
                border_style="dim"
            )
        )

    # Update analysis panel using streaming_buffer
    if streaming_buffer.current_report:
        layout["analysis"].update(
            Panel(
                Markdown(streaming_buffer.current_report),
                title="Latest Report Section", 
                border_style="green"
            )
        )
    else:
        layout["analysis"].update(
            Panel(
                "[dim]Analysis reports will appear here...[/dim]",
                title="Analysis Reports",
                border_style="dim"
            )
        )

    # Footer with instructions
    layout["footer"].update(
        Panel(
            "[bold]TradingAgents Streaming Analysis[/bold] | Press Ctrl+C to stop",
            style="bold white on blue"
        )
    )


def update_research_team_status_streaming(streaming_buffer, status):
    """Update all research team agent statuses for streaming"""
    research_agents = ["Bull Researcher", "Bear Researcher", "Research Manager"]
    for agent in research_agents:
        streaming_buffer.update_agent_status(agent, status)


def run_analysis_streaming(advanced_mode=False):
    """
    Streaming version of run_analysis that delivers reports in real-time
    """
    # Get user selections based on mode
    if advanced_mode:
        selections = get_user_selections_advanced()
    else:
        selections = get_user_selections()

    # Create config with selected research depth
    config = DEFAULT_CONFIG.copy()
    config["max_debate_rounds"] = selections["research_depth"]
    config["max_risk_discuss_rounds"] = selections["research_depth"]
    config["quick_think_llm"] = selections["shallow_thinker"]
    config["deep_think_llm"] = selections["deep_thinker"]
    config["backend_url"] = selections["backend_url"]
    config["llm_provider"] = selections["llm_provider"].lower()

    # Initialize the graph
    graph = TradingAgentsGraph(
        [analyst.value for analyst in selections["analysts"]], config=config, debug=True
    )

    # Create result directory
    results_dir = Path(config["results_dir"]) / selections["ticker"] / selections["analysis_date"]
    results_dir.mkdir(parents=True, exist_ok=True)
    report_dir = results_dir / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    log_file = results_dir / "message_tool.log"
    log_file.touch(exist_ok=True)

    # Use streaming message buffer instead of regular one
    streaming_buffer = StreamingMessageBuffer()

    def save_message_decorator(obj, func_name):
        func = getattr(obj, func_name)
        @wraps(func)
        def wrapper(*args, **kwargs):
            func(*args, **kwargs)
            timestamp, message_type, content = obj.messages[-1]
            content = content.replace("\n", " ")  # Replace newlines with spaces
            with open(log_file, "a") as f:
                f.write(f"{timestamp} [{message_type}] {content}\n")
        return wrapper
    
    def save_tool_call_decorator(obj, func_name):
        func = getattr(obj, func_name)
        @wraps(func)
        def wrapper(*args, **kwargs):
            func(*args, **kwargs)
            timestamp, tool_name, args = obj.tool_calls[-1]
            args_str = ", ".join(f"{k}={v}" for k, v in args.items())
            with open(log_file, "a") as f:
                f.write(f"{timestamp} [Tool Call] {tool_name}({args_str})\n")
        return wrapper

    def save_report_section_decorator(obj, func_name):
        func = getattr(obj, func_name)
        @wraps(func)
        def wrapper(section_name, content):
            func(section_name, content)
            if section_name in obj.report_sections and obj.report_sections[section_name] is not None:
                content = obj.report_sections[section_name]
                if content:
                    file_name = f"{section_name}.md"
                    with open(report_dir / file_name, "w") as f:
                        f.write(content)
        return wrapper

    streaming_buffer.add_message = save_message_decorator(streaming_buffer, "add_message")
    streaming_buffer.add_tool_call = save_tool_call_decorator(streaming_buffer, "add_tool_call")
    streaming_buffer.update_report_section = save_report_section_decorator(streaming_buffer, "update_report_section")

    # Create streaming layout
    layout = create_streaming_layout()

    # Agent mapping for streaming
    agent_mapping = {
        "market": "Market Analyst",
        "social": "Social Media Analyst", 
        "news": "News Analyst",
        "fundamentals": "Fundamentals Analyst",
        "bull": "Bull Researcher",
        "bear": "Bear Researcher", 
        "research_manager": "Research Manager",
        "trader": "Trading Team",
        "risky": "Risky Analyst",
        "safe": "Safe Analyst",
        "neutral": "Neutral Analyst",
        "portfolio": "Portfolio Manager"
    }

    with Live(layout, refresh_per_second=8) as live:  # Higher refresh rate for streaming
        # Initial display
        update_streaming_display(layout, streaming_buffer)

        # Add initial messages
        streaming_buffer.add_message("System", f"Selected ticker: {selections['ticker']}")
        streaming_buffer.add_message(
            "System", f"Analysis date: {selections['analysis_date']}"
        )
        streaming_buffer.add_message(
            "System",
            f"Selected analysts: {', '.join(analyst.value for analyst in selections['analysts'])}",
        )
        update_streaming_display(layout, streaming_buffer)

        # Reset agent statuses
        for agent in streaming_buffer.agent_status:
            streaming_buffer.update_agent_status(agent, "pending")

        # Reset report sections
        for section in streaming_buffer.report_sections:
            streaming_buffer.report_sections[section] = None
        streaming_buffer.current_report = None
        streaming_buffer.final_report = None

        # Update agent status to in_progress for the first analyst
        first_analyst = f"{selections['analysts'][0].value.capitalize()} Analyst"
        streaming_buffer.update_agent_status(first_analyst, "in_progress")
        update_streaming_display(layout, streaming_buffer)

        # Create spinner text
        spinner_text = (
            f"Analyzing {selections['ticker']} on {selections['analysis_date']}..."
        )
        update_streaming_display(layout, streaming_buffer, spinner_text)

        # Initialize state and get graph args
        init_agent_state = graph.propagator.create_initial_state(
            selections["ticker"], selections["analysis_date"]
        )
        args = graph.propagator.get_graph_args()

        # Stream the analysis with real-time content delivery
        trace = []
        current_streaming_agent = None
        
        for chunk in graph.graph.stream(init_agent_state, **args):
            if len(chunk["messages"]) > 0:
                # Get the last message from the chunk
                last_message = chunk["messages"][-1]

                # Extract message content and type
                if hasattr(last_message, "content"):
                    content = extract_content_string(last_message.content)
                    msg_type = "Reasoning"
                    
                    # Detect which agent is currently speaking and stream content
                    agent_detected = None
                    for key, agent_name in agent_mapping.items():
                        if any(keyword in content.lower() for keyword in [key, agent_name.lower()]):
                            agent_detected = agent_name
                            break
                    
                    # If we detected an agent or have ongoing streaming
                    if agent_detected or current_streaming_agent:
                        if agent_detected and agent_detected != current_streaming_agent:
                            # New agent started - finalize previous and start new
                            if current_streaming_agent:
                                section_map = {
                                    "Market Analyst": "market_report",
                                    "Social Media Analyst": "sentiment_report", 
                                    "News Analyst": "news_report",
                                    "Fundamentals Analyst": "fundamentals_report",
                                    "Research Manager": "investment_plan",
                                    "Trading Team": "trader_investment_plan",
                                    "Portfolio Manager": "final_trade_decision"
                                }
                                if current_streaming_agent in section_map:
                                    streaming_buffer.finalize_streaming_content(section_map[current_streaming_agent])
                            
                            current_streaming_agent = agent_detected
                            streaming_buffer.update_agent_status(agent_detected, "in_progress")
                        
                        # Stream the content in real-time
                        if current_streaming_agent:
                            streaming_buffer.stream_content(current_streaming_agent, content + "\n")
                
                else:
                    content = str(last_message)
                    msg_type = "System"

                # Add message to buffer
                streaming_buffer.add_message(msg_type, content[:200] + "..." if len(content) > 200 else content)

                # Handle tool calls
                if hasattr(last_message, "tool_calls"):
                    for tool_call in last_message.tool_calls:
                        if isinstance(tool_call, dict):
                            streaming_buffer.add_tool_call(
                                tool_call["name"], tool_call["args"]
                            )
                        else:
                            streaming_buffer.add_tool_call(tool_call.name, tool_call.args)

                # Handle section completions and agent status updates
                # Analyst Team Reports
                if "market_report" in chunk and chunk["market_report"]:
                    streaming_buffer.update_report_section("market_report", chunk["market_report"])
                    streaming_buffer.update_agent_status("Market Analyst", "completed")
                    current_streaming_agent = None
                    if "social" in [a.value for a in selections["analysts"]]:
                        streaming_buffer.update_agent_status("Social Media Analyst", "in_progress")

                if "sentiment_report" in chunk and chunk["sentiment_report"]:
                    streaming_buffer.update_report_section("sentiment_report", chunk["sentiment_report"])
                    streaming_buffer.update_agent_status("Social Media Analyst", "completed")
                    current_streaming_agent = None
                    if "news" in [a.value for a in selections["analysts"]]:
                        streaming_buffer.update_agent_status("News Analyst", "in_progress")

                if "news_report" in chunk and chunk["news_report"]:
                    streaming_buffer.update_report_section("news_report", chunk["news_report"])
                    streaming_buffer.update_agent_status("News Analyst", "completed")
                    current_streaming_agent = None
                    if "fundamentals" in [a.value for a in selections["analysts"]]:
                        streaming_buffer.update_agent_status("Fundamentals Analyst", "in_progress")

                if "fundamentals_report" in chunk and chunk["fundamentals_report"]:
                    streaming_buffer.update_report_section("fundamentals_report", chunk["fundamentals_report"])
                    streaming_buffer.update_agent_status("Fundamentals Analyst", "completed")
                    current_streaming_agent = None
                    update_research_team_status_streaming(streaming_buffer, "in_progress")

                # Research Team - Handle Investment Debate State with streaming
                if "investment_debate_state" in chunk and chunk["investment_debate_state"]:
                    debate_state = chunk["investment_debate_state"]

                    if "bull_history" in debate_state and debate_state["bull_history"]:
                        update_research_team_status_streaming(streaming_buffer, "in_progress")
                        bull_responses = debate_state["bull_history"].split("\n")
                        latest_bull = bull_responses[-1] if bull_responses else ""
                        if latest_bull:
                            streaming_buffer.stream_content("Bull Researcher", latest_bull + "\n")

                    if "bear_history" in debate_state and debate_state["bear_history"]:
                        update_research_team_status_streaming(streaming_buffer, "in_progress")
                        bear_responses = debate_state["bear_history"].split("\n")
                        latest_bear = bear_responses[-1] if bear_responses else ""
                        if latest_bear:
                            streaming_buffer.stream_content("Bear Researcher", latest_bear + "\n")

                    if "judge_decision" in debate_state and debate_state["judge_decision"]:
                        streaming_buffer.stream_content("Research Manager", debate_state["judge_decision"] + "\n")
                        streaming_buffer.finalize_streaming_content("investment_plan")
                        update_research_team_status_streaming(streaming_buffer, "completed")
                        streaming_buffer.update_agent_status("Risky Analyst", "in_progress")
                        current_streaming_agent = None

                # Trading Team with streaming
                if "trader_investment_plan" in chunk and chunk["trader_investment_plan"]:
                    streaming_buffer.update_report_section("trader_investment_plan", chunk["trader_investment_plan"])
                    streaming_buffer.update_agent_status("Risky Analyst", "in_progress")
                    current_streaming_agent = None

                # Risk Management Team with streaming
                if "risk_debate_state" in chunk and chunk["risk_debate_state"]:
                    risk_state = chunk["risk_debate_state"]

                    if "current_risky_response" in risk_state and risk_state["current_risky_response"]:
                        streaming_buffer.update_agent_status("Risky Analyst", "in_progress")
                        streaming_buffer.stream_content("Risky Analyst", risk_state["current_risky_response"] + "\n")

                    if "current_safe_response" in risk_state and risk_state["current_safe_response"]:
                        streaming_buffer.update_agent_status("Safe Analyst", "in_progress")
                        streaming_buffer.stream_content("Safe Analyst", risk_state["current_safe_response"] + "\n")

                    if "current_neutral_response" in risk_state and risk_state["current_neutral_response"]:
                        streaming_buffer.update_agent_status("Neutral Analyst", "in_progress")
                        streaming_buffer.stream_content("Neutral Analyst", risk_state["current_neutral_response"] + "\n")

                    if "judge_decision" in risk_state and risk_state["judge_decision"]:
                        streaming_buffer.stream_content("Portfolio Manager", risk_state["judge_decision"] + "\n")
                        streaming_buffer.finalize_streaming_content("final_trade_decision")
                        
                        # Mark all risk team as completed
                        streaming_buffer.update_agent_status("Risky Analyst", "completed")
                        streaming_buffer.update_agent_status("Safe Analyst", "completed")
                        streaming_buffer.update_agent_status("Neutral Analyst", "completed")
                        streaming_buffer.update_agent_status("Portfolio Manager", "completed")
                        current_streaming_agent = None

                # Update the display with streaming content
                update_streaming_display(layout, streaming_buffer)

            trace.append(chunk)

        # Finalize any remaining streaming content
        if current_streaming_agent:
            section_map = {
                "Market Analyst": "market_report",
                "Social Media Analyst": "sentiment_report", 
                "News Analyst": "news_report",
                "Fundamentals Analyst": "fundamentals_report",
                "Research Manager": "investment_plan",
                "Trading Team": "trader_investment_plan",
                "Portfolio Manager": "final_trade_decision"
            }
            if current_streaming_agent in section_map:
                streaming_buffer.finalize_streaming_content(section_map[current_streaming_agent])

        # Get final state and decision
        final_state = trace[-1]
        # Extract the final trade decision from the correct location
        final_trade_decision = None
        if "Risk Judge" in final_state and "final_trade_decision" in final_state["Risk Judge"]:
            final_trade_decision = final_state["Risk Judge"]["final_trade_decision"]
        elif "final_trade_decision" in final_state:
            final_trade_decision = final_state["final_trade_decision"]
        
        if final_trade_decision:
            decision = graph.process_signal(final_trade_decision)
        else:
            decision = "No trade decision available"

        # Update all agent statuses to completed
        for agent in streaming_buffer.agent_status:
            streaming_buffer.update_agent_status(agent, "completed")

        streaming_buffer.add_message(
            "Analysis", f"Completed streaming analysis for {selections['analysis_date']}"
        )

        # Update final report sections
        for section in streaming_buffer.report_sections.keys():
            if section in final_state:
                streaming_buffer.update_report_section(section, final_state[section])

        # Display the complete final report
        display_complete_report(final_state)

        # Save the final complete report and decision
        # Save the final trade decision
        if final_trade_decision:
            decision_file = results_dir / "final_trade_decision.md"
            with open(decision_file, "w") as f:
                f.write(f"# Final Trading Decision\n\n")
                f.write(f"**Ticker:** {selections['ticker']}\n")
                f.write(f"**Analysis Date:** {selections['analysis_date']}\n")
                f.write(f"**Decision:** {decision}\n\n")
                f.write("## Raw Decision Text\n\n")
                f.write(final_trade_decision)
        
        # Save the complete final report
        complete_report_file = results_dir / "complete_analysis_report.md"
        with open(complete_report_file, "w") as f:
            f.write(f"# Complete Analysis Report\n\n")
            f.write(f"**Ticker:** {selections['ticker']}\n")
            f.write(f"**Analysis Date:** {selections['analysis_date']}\n")
            f.write(f"**Analysis Time:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Add analyst reports
            if final_state.get("market_report"):
                f.write("## Market Analysis\n\n")
                f.write(final_state["market_report"])
                f.write("\n\n")
            
            if final_state.get("sentiment_report"):
                f.write("## Social Media Sentiment Analysis\n\n")
                f.write(final_state["sentiment_report"])
                f.write("\n\n")
            
            if final_state.get("news_report"):
                f.write("## News Analysis\n\n")
                f.write(final_state["news_report"])
                f.write("\n\n")
            
            if final_state.get("fundamentals_report"):
                f.write("## Fundamentals Analysis\n\n")
                f.write(final_state["fundamentals_report"])
                f.write("\n\n")
            
            # Add research team analysis
            if final_state.get("investment_debate_state"):
                debate_state = final_state["investment_debate_state"]
                f.write("## Investment Research Analysis\n\n")
                
                if debate_state.get("bull_history"):
                    f.write("### Bull Researcher Analysis\n\n")
                    f.write(debate_state["bull_history"])
                    f.write("\n\n")
                
                if debate_state.get("bear_history"):
                    f.write("### Bear Researcher Analysis\n\n")
                    f.write(debate_state["bear_history"])
                    f.write("\n\n")
                
                if debate_state.get("judge_decision"):
                    f.write("### Research Manager Decision\n\n")
                    f.write(debate_state["judge_decision"])
                    f.write("\n\n")
            
            # Add trading analysis
            if final_state.get("trader_investment_plan"):
                f.write("## Trading Plan\n\n")
                f.write(final_state["trader_investment_plan"])
                f.write("\n\n")
            
            # Add risk analysis
            if final_state.get("risk_debate_state"):
                risk_state = final_state["risk_debate_state"]
                f.write("## Risk Management Analysis\n\n")
                
                if risk_state.get("risky_history"):
                    f.write("### Aggressive Risk Analysis\n\n")
                    f.write(risk_state["risky_history"])
                    f.write("\n\n")
                
                if risk_state.get("safe_history"):
                    f.write("### Conservative Risk Analysis\n\n")
                    f.write(risk_state["safe_history"])
                    f.write("\n\n")
                
                if risk_state.get("neutral_history"):
                    f.write("### Neutral Risk Analysis\n\n")
                    f.write(risk_state["neutral_history"])
                    f.write("\n\n")
                
                if risk_state.get("judge_decision"):
                    f.write("### Risk Manager Final Decision\n\n")
                    f.write(risk_state["judge_decision"])
                    f.write("\n\n")
            
            # Add final decision
            if final_trade_decision:
                f.write("## Final Trading Decision\n\n")
                f.write(f"**Decision:** {decision}\n\n")
                f.write("### Detailed Decision\n\n")
                f.write(final_trade_decision)
        
        # Save final state as JSON for programmatic access
        final_state_file = results_dir / "final_state.json"
        with open(final_state_file, "w") as f:
            import json
            # Convert final_state to JSON-serializable format
            json_state = {}
            for key, value in final_state.items():
                try:
                    json.dumps(value)  # Test if it's JSON serializable
                    json_state[key] = value
                except:
                    json_state[key] = str(value)  # Convert to string if not serializable
            json.dump(json_state, f, indent=2)
        
        print(f"\n✅ Analysis complete! Results saved to: {results_dir}")
        print(f"📄 Complete report: {complete_report_file}")
        print(f"🎯 Final decision: {decision_file}")
        print(f"📊 Final state: {final_state_file}")

        update_streaming_display(layout, streaming_buffer)


if __name__ == "__main__":
    app()
