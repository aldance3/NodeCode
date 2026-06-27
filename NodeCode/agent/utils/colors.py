"""
utils/colors.py - Terminal color helpers using colorama
"""

from colorama import Fore, Style, init

init(autoreset=True)


def user_prompt(text: str) -> str:
    return f"{Fore.CYAN}{Style.BRIGHT}{text}{Style.RESET_ALL}"


def assistant_prefix() -> str:
    return f"{Fore.GREEN}{Style.BRIGHT}AI:{Style.RESET_ALL} "


def tool_running(name: str, server: str) -> str:
    return f"{Fore.YELLOW}  ⚙  Running {Style.BRIGHT}{name}{Style.NORMAL} [{server}]...{Style.RESET_ALL}"


def tool_done(name: str, elapsed: float, exit_code: str = "") -> str:
    code_str = f"  exit={exit_code}" if exit_code else ""
    return f"{Fore.GREEN}  ✓  {name} completed in {elapsed:.2f}s{code_str}{Style.RESET_ALL}"


def tool_error(name: str, error: str) -> str:
    return f"{Fore.RED}  ✗  {name} error: {error}{Style.RESET_ALL}"


def info(text: str) -> str:
    return f"{Fore.BLUE}{text}{Style.RESET_ALL}"


def error(text: str) -> str:
    return f"{Fore.RED}{Style.BRIGHT}ERROR:{Style.NORMAL} {text}{Style.RESET_ALL}"


def dim(text: str) -> str:
    return f"{Style.DIM}{text}{Style.RESET_ALL}"
