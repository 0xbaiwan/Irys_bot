import os
import sys
import time

import inquirer
from art import text2art
from colorama import Fore, Style
from inquirer.themes import GreenPassion

from loader import config
from sys import exit

from rich.console import Console as RichConsole
from rich.panel import Panel
from rich.table import Table
from rich import box
from rich.text import Text

from database import Accounts

sys.path.append(os.path.realpath("."))


class Console:
    MODULES = (
        "📦 一体化",
        "🔑 从水龙头请求代币",
        "💎 充值游戏余额",
        "🎮 玩游戏",
        "📥 铸造 OmniHub NFT",
        "",
        "🧹 清理账户代理",
        "❌ 退出",
    )
    MODULES_DATA = {
        "📦 一体化": "all_in_one",
        "🔑 从水龙头请求代币": "request_tokens_from_faucet",
        "💎 充值游戏余额": "top_up_game_balance",
        "🎮 玩游戏": "play_games",
        "📥 铸造 OmniHub NFT": "mint_omnihub_nft",
        "🧹 清理账户代理": "clean_accounts_proxies",
        "❌ 退出": "exit",
    }

    def __init__(self):
        self.rich_console = RichConsole()

    def show_dev_info(self):
        os.system("cls" if os.name == "nt" else "clear")
        self.show_loading_animation()

        title = text2art("Irys Bot", font="small")
        styled_title = Text(title, style="bold cyan")

        version = Text("版本: 1.0.0", style="blue")
        github = Text("GitHub: https://github.com/0xbaiwan/Irys_bot", style="green")

        dev_panel = Panel(
            Text.assemble(styled_title, "\n", version, "\n", github),
            border_style="yellow",
            expand=False,
            title="[bold green]欢迎[/bold green]",
            subtitle="[italic]由 0xbaiwan 提供支持[/italic]",
        )

        self.rich_console.print(dev_panel)
        print()

    def show_loading_animation(self):
        with self.rich_console.status("[bold green]加载中...", spinner="dots"):
            time.sleep(1.5)

    @staticmethod
    def prompt(data: list):
        answers = inquirer.prompt(data, theme=GreenPassion())
        return answers

    def get_module(self):
        questions = [
            inquirer.List(
                "module",
                message=Fore.LIGHTBLACK_EX + "选择模块" + Style.RESET_ALL,
                choices=self.MODULES,
            ),
        ]

        answers = self.prompt(questions)
        return answers.get("module")

    async def display_info(self):
        main_table = Table(title="配置概览", box=box.ROUNDED, show_lines=True)

        # 账户表格
        accounts_table = Table(box=box.SIMPLE)
        accounts_table.add_column("参数", style="cyan")
        accounts_table.add_column("值", style="magenta")

        accounts_table.add_row("一体化账户", str(len(config.accounts_for_all_in_one)))
        accounts_table.add_row("玩游戏账户", str(len(config.accounts_to_play_games)))
        accounts_table.add_row("充值游戏余额账户", str(len(config.accounts_to_top_up_game_balance)))
        accounts_table.add_row("请求代币账户", str(len(config.accounts_to_request_tokens)))
        accounts_table.add_row("铸造 NFT 账户", str(len(config.accounts_to_mint_nft)))
        accounts_table.add_row("代理", str(len(config.proxies)))

        main_table.add_column("部分")
        main_table.add_row("[bold]文件信息[/bold]", accounts_table)

        panel = Panel(
            main_table,
            expand=False,
            border_style="green",
            title="[bold yellow]系统信息[/bold yellow]",
            subtitle="[italic]使用数字键选择模块[/italic]",
        )
        self.rich_console.print(panel)

    async def build(self) -> str | None:
        try:
            self.show_dev_info()
            await self.display_info()

            module = self.get_module()
            config.module = self.MODULES_DATA[module]

            if config.module == "exit":
                with self.rich_console.status(
                        "[bold red]正在关闭...", spinner="dots"
                ):
                    time.sleep(1)
                self.rich_console.print("[bold red]再见! 👋[/bold red]")
                exit(0)

            return config.module

        except KeyboardInterrupt:
            self.rich_console.print(
                "\n[bold red]用户中断。正在退出...[/bold red]"
            )
            exit(0)
