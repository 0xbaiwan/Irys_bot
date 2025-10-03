import random
import time

from typing import Optional
from eth_abi import encode
from eth_typing import HexStr

from core.onchain.wallet import Web3Wallet
from models.bot import GameType
from models.onchain import IrysGameContract
from web3.types import TxParams


class IrysGamesModule(Web3Wallet):
    def __init__(self, private_key: str, rpc_url: str, proxy: str = None):
        super().__init__(private_key, rpc_url, proxy)
        self.proxy = proxy

    async def get_play_balance(self) -> Optional[float]:
        contract_address = IrysGameContract.address
        method_id = "0x47734892"

        encoded_address = encode(
            ["address"],
            [self.to_checksum_address(self.wallet_address)]
        ).hex()
        data = method_id + encoded_address

        call: TxParams = {
            "to": self.to_checksum_address(contract_address),
            "data": HexStr(data),
        }

        raw_balance = await self.eth.call(call)
        balance = int(raw_balance.hex(), 16)

        return float(self.from_wei(balance, "ether"))


    async def deposit_tokens(self, amount: float) -> tuple[bool, str]:
        try:
            nonce = await self.eth.get_transaction_count(self.wallet_address)
            value = self.to_wei(amount, "ether")
            data = "0xd0e30db0"  # deposit()
            to = "0xBC41F2B6BdFCB3D87c3d5E8b37fD02C56B69ccaC"

            chain_id = await self.eth.chain_id

            tx: TxParams = {
                "from": self.wallet_address,
                "to": to,
                "value": value,
                "data": HexStr(data),
                "nonce": nonce,
                "chainId": chain_id,
                "gasPrice": await self.eth.gas_price,
            }

            gas_estimate = await self.eth.estimate_gas(tx)
            tx["gas"] = int(gas_estimate * 1.2)

            await self.check_trx_availability(tx)
            return await self._process_transaction(tx)

        except Exception as error:
            return False, str(error)


    async def authorize_payment(self) -> tuple[str, str, int]:
        ts = int(time.time() * 1000)
        message = f"我授权支付 0.001 IRYS 以在 Irys Arcade 玩游戏。\n    \n玩家: {self.wallet_address}\n金额: 0.001 IRYS\n时间戳: {ts}\n\n此签名确认我拥有此钱包并授权支付。"

        signature = await self.get_signature(message)
        return message, signature, ts


    async def complete_payment(self, initial_ts: int, score: int, session_id: str, game_type: GameType) -> tuple[str, str, int]:
        complete_at_ts = initial_ts + random.randint(2, 10) * 60 * 1000
        message = f"我在 Irys Arcade 完成了 {game_type} 游戏。\n    \n玩家: {self.wallet_address}\n游戏: {game_type}\n分数: {score}\n会话: {session_id}\n时间戳: {complete_at_ts}\n\n此签名确认我拥有此钱包并完成了此游戏。"

        signature = await self.get_signature(message)
        return message, signature, complete_at_ts

