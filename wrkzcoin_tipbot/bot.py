import asyncio
import click
import discord
import mongoengine
from discord.ext import commands

import sys
sys.path.append("..")
import models, store, daemonrpc_client
from config import config

WRKZCOIN_DIGITS = 100
WRKZCOIN_REPR = 'WRKZ'

bot_description = f"Tip {WRKZCOIN_REPR} to other users on your server."
bot_help_register = "Register or change your deposit address."
bot_help_info = "Get your account's info."
bot_help_withdraw = f"Withdraw {WRKZCOIN_REPR} from your balance."
bot_help_balance = f"Check your {WRKZCOIN_REPR} balance."
bot_help_tip = f"Give {WRKZCOIN_REPR} to a user from your balance."
bot_help_height = f"Get {WRKZCOIN_REPR} current block height."
bot_help_nethash = f"Get {WRKZCOIN_REPR} network hashrate."
bot_help_diff = f"Get {WRKZCOIN_REPR} current difficulty."
bot_help_supply = f"Get {WRKZCOIN_REPR} circulating supply."

bot = commands.Bot(command_prefix='.')

@bot.event
async def on_ready():
    print('Ready!')
    print(bot.user.name)
    print(bot.user.id)


@bot.command(pass_context=True, help=bot_help_info)
async def info(context: commands.Context):
    user = store.register_user(context.message.author.id)
    await bot.send_message(
        context.message.author, f'**[💁 ACCOUNT INFO]**\n\n'
        f'👛 Deposit Address: `{user.balance_wallet_address}`\n\n'
        f'👛 Registered Wallet: `{user.user_wallet_address}`')


@bot.command(pass_context=True, help=bot_help_balance)
async def balance(context: commands.Context):
    user = store.register_user(context.message.author.id)
    wallet = store.get_user_wallet(user.user_id)
    await bot.send_message(
        context.message.author, '**[💰 YOUR BALANCE]**\n\n'
        f'💰 Available: {wallet.actual_balance / WRKZCOIN_DIGITS:.2f} '
        f'{WRKZCOIN_REPR}\n'
        f'👛 Pending: {wallet.locked_balance / WRKZCOIN_DIGITS:.2f} '
        f'{WRKZCOIN_REPR}\n')


@bot.command(pass_context=True, help=bot_help_register)
async def register(context: commands.Context, wallet_address: str):
    user_id = context.message.author.id

    existing_user: models.User = models.User.objects(user_id=user_id).first()
    if existing_user:
        prev_address = existing_user.user_wallet_address
        existing_user = store.register_user(existing_user.user_id,
                                            user_wallet=wallet_address)
        if prev_address:
            await bot.send_message(
                context.message.author,
                f'Your deposit address has been changed from:\n'
                f'`{prev_address}`\n to\n '
                f'`{existing_user.user_wallet_address}`')
            return

    user = (existing_user or
            store.register_user(user_id, user_wallet=wallet_address))

    await bot.send_message(context.message.author,
                           f'You have been registered.\n'
                           f'You can send your deposits to '
                           f'`{user.balance_wallet_address}` and your '
                           f'balance will be available once confirmed.')


@bot.command(pass_context=True, help=bot_help_withdraw)
async def withdraw(context: commands.Context, amount: float):
    user: models.User = models.User.objects(
        user_id=context.message.author.id).first()
    real_amount = int(amount * WRKZCOIN_DIGITS)

    if not user.user_wallet_address:
        await bot.send_message(
            context.message.author,
            f'You do not have a withdrawal address, please use '
            f'`.register <wallet_address>` to register.')
        return

    user_balance_wallet: models.Wallet = models.Wallet.objects(
        wallet_address=user.balance_wallet_address).first()

    if real_amount + config.tx_fee >= user_balance_wallet.actual_balance:
        await bot.send_message(context.message.author,
                               f'🛑 Insufficient balance to withdraw '
                               f'{real_amount / WRKZCOIN_DIGITS:.2f} '
                               f'{WRKZCOIN_REPR}.')
        return

    if real_amount > config.max_tx_amount:
        await bot.reply(f'🛑 Transactions cannot be bigger than '
                        f'{config.max_tx_amount / WRKZCOIN_DIGITS:.2f} '
                        f'{WRKZCOIN_REPR}')
        return
    elif real_amount < config.min_tx_amount:
        await bot.reply(f'🛑 Transactions cannot be lower than '
                        f'{config.min_tx_amount / WRKZCOIN_DIGITS:.2f} '
                        f'{WRKZCOIN_REPR}')
        return

    withdrawal = store.withdraw(user, real_amount)
    await bot.send_message(
        context.message.author,
        f'💰 You have withdrawn {real_amount / WRKZCOIN_DIGITS:.2f} '
        f'{WRKZCOIN_REPR}.\n'
        f'Transaction hash: `{withdrawal.tx_hash}`')


@bot.command(pass_context=True, help=bot_help_tip)
async def tip(context: commands.Context, member: discord.Member,
              amount: float):
    user_from: models.User = models.User.objects(
        user_id=context.message.author.id).first()
    user_to: models.User = store.register_user(member.id)
    real_amount = int(amount * WRKZCOIN_DIGITS)

    user_from_wallet: models.Wallet = models.Wallet.objects(
        wallet_address=user_from.balance_wallet_address).first()

    if real_amount + config.tx_fee >= user_from_wallet.actual_balance:
        await bot.reply(f'🛑 Insufficient balance to send tip of '
                        f'{real_amount / WRKZCOIN_DIGITS:.2f} '
                        f'{WRKZCOIN_REPR} to {member.mention}.')
        return

    if real_amount > config.max_tx_amount:
        await bot.reply(f'🛑 Transactions cannot be bigger than '
                        f'{config.max_tx_amount / WRKZCOIN_DIGITS:.2f} '
                        f'{WRKZCOIN_REPR}.')
        return
    elif real_amount < config.min_tx_amount:
        await bot.reply(f'🛑 Transactions cannot be smaller than '
                        f'{config.min_tx_amount / WRKZCOIN_DIGITS:.2f} '
                        f'{WRKZCOIN_REPR}.')
        return

    tip = store.send_tip(user_from, user_to, real_amount)

    await bot.reply(f'💰💖 Tip of {real_amount / WRKZCOIN_DIGITS:.2f} '
                    f'{WRKZCOIN_REPR} '
                    f'was sent to {member.mention}\n'
                    f'Transaction hash: `{tip.tx_hash}`')


@bot.command(pass_context=True, help=bot_help_height)
async def height(context: commands.Context):
    height = daemonrpc_client.getheight()
    await bot.reply(f'*[NETWORK HEIGHT]* `{height}`\n')

@bot.command(pass_context=True, help=bot_help_nethash)
async def hash(context: commands.Context):
    hashrate = daemonrpc_client.gethashrate()
    await bot.reply(f'*[NETWORK HASH RATE]* `{hashrate}`\n')

@bot.command(pass_context=True, help=bot_help_diff)
async def diff(context: commands.Context):
    difficulty = daemonrpc_client.getdiff()
    await bot.reply(f'*[CURRENT DIFFICULTY]* `{difficulty}`\n')

@bot.command(pass_context=True, help=bot_help_supply)
async def supply(context: commands.Context):
    supply = daemonrpc_client.getsupply()
    await bot.reply(f'*[CIRCULATING SUPPLY]* `{supply}{WRKZCOIN_REPR}`\n')

@register.error
async def register_error(error, _: commands.Context):
    await handle_errors(error)


@info.error
async def info_error(error, _: commands.Context):
    await handle_errors(error)


@balance.error
async def balance_error(error, _: commands.Context):
    await handle_errors(error)


@withdraw.error
async def withdraw_error(error, _: commands.Context):
    await handle_errors(error)


@tip.error
async def tip_error(error, _: commands.Context):
    await handle_errors(error)


async def handle_errors(error):
    if isinstance(error, commands.BadArgument):
        await bot.say(f'Invalid arguments provided.')
    else:
        await bot.say(f'Error.')


async def update_balance_wallets():
    while not bot.is_closed:
        store.update_balances()
        await asyncio.sleep(config.wallet_balance_update_interval)


@click.command()
def main():
    mongoengine.connect(db=config.database.db, host=config.database.host,
                        port=config.database.port,
                        username=config.database.user,
                        password=config.database.password)
    bot.loop.create_task(update_balance_wallets())
    bot.run(config.discord.token)


if __name__ == '__main__':
    main()

