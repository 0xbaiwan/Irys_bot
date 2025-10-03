import asyncio
import random

from typing import List, Any, Set, Optional, Callable
from loguru import logger

from core.modules.executor import ModuleExecutor
from loader import config, file_operations, semaphore, proxy_manager
from models import Account
from utils import Progress
from console import Console
from database import initialize_database, Accounts


class ApplicationManager:
    def __init__(self):
        self.accounts_with_initial_delay: Set[str] = set()
        self.module_map = {
            "request_tokens_from_faucet": (config.accounts_to_request_tokens, self._execute_module_for_accounts),
            "top_up_game_balance": (config.accounts_to_top_up_game_balance, self._execute_module_for_accounts),
            "play_games": (config.accounts_to_play_games, self._execute_module_for_accounts),
            "mint_omnihub_nft": (config.accounts_to_mint_nft, self._execute_module_for_accounts),
            "all_in_one": (config.accounts_for_all_in_one, self._execute_module_for_accounts),
        }

    @staticmethod
    async def initialize() -> None:
        logger.info(f"正在初始化数据库..")
        await initialize_database()
        logger.success(f"数据库已初始化")
        await file_operations.setup_files()

    async def _execute_module_for_accounts(
        self, accounts: List[Account], module_name: str
    ) -> list[Any]:
        progress = Progress(len(accounts))

        if module_name == "export_stats":
            await file_operations.setup_stats()

        tasks = []
        for account in accounts:
            executor = ModuleExecutor(account)
            module_func = getattr(executor, f"_process_{module_name}")
            tasks.append(self._safe_execute_module(account, module_func, progress))

        return await asyncio.gather(*tasks)

    async def _safe_execute_module(
            self, account: Account, module_func: Callable, progress: Progress
    ) -> Optional[dict]:
        try:
            async with semaphore:
                if (
                    config.attempts_and_delay_settings.delay_before_start.min > 0
                    and config.attempts_and_delay_settings.delay_before_start.max > 0
                ):
                    if account.wallet_address not in self.accounts_with_initial_delay:
                        random_delay = random.randint(
                            config.attempts_and_delay_settings.delay_before_start.min,
                            config.attempts_and_delay_settings.delay_before_start.max
                        )
                        logger.info(
                            f"账户: {account.wallet_address} | 初始延迟设置为 {random_delay} 秒 | 将在 {random_delay} 秒后开始执行"
                        )
                        self.accounts_with_initial_delay.add(account.wallet_address)
                        await asyncio.sleep(random_delay)

                result = await module_func()
                if module_func.__name__ != "_process_farm":
                    progress.increment()
                    logger.debug(f"进度: {progress.processed}/{progress.total}")

                return result

        except Exception as e:
            logger.error(f"处理账户 {account.wallet_address} 时发生错误: {str(e)}")
            return {"success": False, "error": str(e)}


    @staticmethod
    async def _clean_accounts_proxies() -> None:
        logger.info("正在清理所有账户代理..")
        try:
            cleared_count = await Accounts().clear_all_accounts_proxies()
            logger.success(f"成功清理了 {cleared_count} 个账户的代理")

        except Exception as e:
            logger.error(f"清理账户代理时发生错误: {str(e)}")

    async def run(self) -> None:
        last_chosen_module = None
        while True:
            if config.loop_settings.enable_loop and last_chosen_module:
                # If looping is enabled and a module was previously chosen, reuse it
                config.module = last_chosen_module
                logger.info(f"循环模式已启用。将再次执行模块: {config.module}")
            else:
                # Otherwise, display console and let user choose
                await Console().build()
                last_chosen_module = config.module # Store the chosen module

            if config.module == "clean_accounts_proxies":
                await self._clean_accounts_proxies()
                if not config.loop_settings.enable_loop: # Only pause if not looping
                    input("\n按 Enter 键继续...")
                continue

            if config.module not in self.module_map:
                logger.error(f"未知模块: {config.module}")
                break

            proxy_manager.load_proxy(config.proxies)
            accounts, process_func = self.module_map[config.module]

            if config.application_settings.shuffle_accounts:
                random.shuffle(accounts)

            if not accounts:
                logger.error(f"模块 {config.module} 没有账户")
                if not config.loop_settings.enable_loop: # Only pause if not looping
                    input("\n按 Enter 键继续...")
                continue

            await self._execute_module_for_accounts(accounts, config.module)

            if config.loop_settings.enable_loop:
                if config.loop_settings.loop_interval_seconds > 0:
                    delay = config.loop_settings.loop_interval_seconds
                    logger.info(f"所有账户任务已完成。将在 {delay} 秒后再次执行模块: {config.module}")
                    await asyncio.sleep(delay)
                else:
                    logger.info(f"所有账户任务已完成。循环模式已启用，但未设置循环间隔时间。 সন")
            else:
                input("\n按 Enter 键继续...")
