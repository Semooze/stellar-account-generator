import asyncio
import math
import sys
from datetime import datetime, time
from decimal import Decimal

import aiohttp
from stellar_base.builder import Builder
from stellar_base.keypair import Keypair


FRIENDBOT_URL = "https://friendbot.stellar.org"
STELLAR_TEST_URL = "https://horizon-testnet.stellar.org"


async def fund_with_friend_bot(address):
    url = f"{FRIENDBOT_URL}/?addr={address}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return True if resp.status == 200 else False


async def create_tmp_account() -> Keypair:
    kp = Keypair.random()
    created = await fund_with_friend_bot(kp.address().decode())
    if not created:
        return None, None
    return kp.address().decode(), kp.seed().decode()


async def merge_account(main_address, tmp_address, tmp_seed):
    account = Builder(address=tmp_address, secret=tmp_seed)
    account.append_account_merge_op(destination=main_address)
    account.sign()
    return account.gen_xdr()


async def submit_transaction(xdr):
    url = f"{STELLAR_TEST_URL}/transactions"
    async with aiohttp.ClientSession() as session:
        data = {"tx": xdr.decode()}
        async with session.post(url, data=data) as resp:
            return resp


async def add_trust(seed):
    builder = Builder(secret=seed)
    builder.append_trust_op(destination=sys.argv[3], code="HOT")
    builder.sign()
    result = builder.submit()
    return result


async def pay_hot(address):
    builder = Builder(secret="[insert secret seed]")
    builder.append_payment_op(destination=address, asset_issuer=sys.argv[3], asset_code="HOT", amount=sys.argv[4])
    builder.sign()
    result = builder.submit()
    return result



async def create_account(xlm):
    kp = Keypair.random()
    public_key = kp.address().decode()
    seed = kp.seed().decode()
    print(public_key, seed)
    result = await fund_with_friend_bot(public_key)
    print(result)
    if Decimal(xlm) < 10000:
        return print("Wrong arguments money should at least 10000.")

    NUMBER_OF_ACCOUNT = math.floor((Decimal(xlm) - 10000) / 10000)
    count = 0

    if len(sys.argv) >= 4:
        await add_trust(seed)
    if len(sys.argv) == 5:
        await pay_hot(public_key)

    if Decimal(xlm) == 10000:
        return public_key, seed

    # print(NUMBER_OF_ACCOUNT, count)

    while True:
        print(count)
        tmp_address, tmp_seed = await create_tmp_account()
        if not tmp_address:
            continue
        xdr = await merge_account(public_key, tmp_address, tmp_seed)
        result = await submit_transaction(xdr)
        if result.status != 200:
            continue
        count += 1
        if count == NUMBER_OF_ACCOUNT:
            break
    return public_key, seed


if __name__ == "__main__":
    print(
        "args\n1 number of account that want to create\n2 amount of money that want in new address\n3 issuer of trust when want trust HOT\n4 amount of HOT"
    )
    if len(sys.argv) <= 1:
        print("Please insert amount of XLM as an argument")
    else:
        now = datetime.now()
        loop = asyncio.get_event_loop()
        for i in range(0, int(sys.argv[1])):
            result = loop.run_until_complete(create_account(sys.argv[2]))
            if isinstance(result, tuple):
                print(*result)
            else:
                print(result)
        loop.close()
        wait_until = datetime.now()
        print(f"Time use :{wait_until - now}")
    print("Finished!")
