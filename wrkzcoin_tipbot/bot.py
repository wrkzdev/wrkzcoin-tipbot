import asyncio
import click
import discord
import mongoengine
from discord.ext import commands

import sys
sys.path.append("..")
import models, store, daemonrpc_client
from config import config

COIN_DIGITS = 100
COIN_REPR = 'WRKZ'

bot_description = f"Tip {COIN_REPR} to other users on your server."
bot_help_register = "Register or change your deposit address."
bot_help_info = "Get your account's info."
bot_help_withdraw = f"Withdraw {COIN_REPR} from your balance."
bot_help_balance = f"Check your {COIN_REPR} balance."
bot_help_botbalance = f"Check (only) bot {COIN_REPR} balance."
bot_help_tip = f"Give {COIN_REPR} to a user from your balance."
bot_help_height = f"Show {COIN_REPR} current block height."
bot_help_nethash = f"Show {COIN_REPR} network hashrate."
bot_help_diff = f"Show {COIN_REPR} current difficulty."
bot_help_supply = f"Show {COIN_REPR} circulating supply."
bot_help_stats = f"Show summary {COIN_REPR}: height, difficulty, etc."

bot = commands.Bot(command_prefix='.')
EMOJI_ERROR = "\u274C"
EMOJI_MONEYFACE = "\u1F911"

@bot.event
async def on_ready():
    print('Ready!')
    print(bot.user.name)
    print(bot.user.id)


@bot.command(pass_context=True, help=bot_help_info)
async def info(context: commands.Context):
    user = store.register_user(context.message.author.id)
    if (user.user_wallet_address is None):
        await bot.send_message(
            context.message.author, f'**[💁 ACCOUNT INFO]**\n\n'
            f'👛 Deposit Address: `{user.balance_wallet_address}`\n\n'
            f'👛 Registered Wallet: `NONE, Please register.`')	
    else:
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
        f'💰 Available: {wallet.actual_balance / COIN_DIGITS:.2f} '
        f'{COIN_REPR}\n'
        f'👛 Pending: {wallet.locked_balance / COIN_DIGITS:.2f} '
        f'{COIN_REPR}\n')

@bot.command(pass_context=True, help=bot_help_botbalance)
async def botbalance(context: commands.Context, member: discord.Member):
    if (member.bot == False):
        await bot.add_reaction(context.message, EMOJI_ERROR)
        await bot.send_message(
            context.message.author, 'Only for bot!!!')
    else:
        user = store.register_user(member.id)
        wallet = store.get_user_wallet(user.user_id)
        balance_actual = '{:,.2f}'.format(wallet.actual_balance / COIN_DIGITS)
        balance_locked = '{:,.2f}'.format(wallet.locked_balance / COIN_DIGITS)
        await bot.send_message(
            context.message.author, f'**[💰 INFO BOT {member.name}\'s BALANCE]**\n\n'
            f'👛 Deposit Address: `{user.balance_wallet_address}`\n'
            f'💰 Available: {balance_actual} '
            f'{COIN_REPR}\n'
            f'👛 Pending: {balance_locked} '
            f'{COIN_REPR}\n')

@bot.command(pass_context=True, name='register', aliases=['registerwallet', 'reg', 'updatewallet'], help=bot_help_register)
async def register(context: commands.Context, wallet_address: str):
    user_id = context.message.author.id
    existing_user: models.User = models.User.objects(user_id=user_id).first()

    if (len(wallet_address) != 98) :
        await bot.add_reaction(context.message, EMOJI_ERROR)
        await bot.send_message(context.message.author,
                        f'🛑 Invalid address:\n'
                        f'`{wallet_address}`')
        return

    if not re.match(r'Wrkz[a-zA-Z0-9]{94,}', wallet_address.strip()):
        await bot.add_reaction(context.message, EMOJI_ERROR)
        await bot.send_message(context.message.author,
                        f'🛑 Invalid address:\n'
                        f'`{wallet_address}`')

    if existing_user:
        prev_address = existing_user.user_wallet_address
        existing_user = store.register_user(existing_user.user_id,
                                            user_wallet=wallet_address)
        if prev_address:
            await bot.add_reaction(context.message, EMOJI_MONEYFACE)
            await bot.send_message(
                context.message.author,
                f'Your deposit address has been changed from:\n'
                f'`{prev_address}`\n to\n '
                f'`{existing_user.user_wallet_address}`')
            return

    user = (existing_user or
            store.register_user(user_id, user_wallet=wallet_address))
    await bot.add_reaction(context.message, EMOJI_MONEYFACE)
    await bot.send_message(context.message.author,
                           f'You have been registered.\n'
                           f'You can send your deposits to '
                           f'`{user.balance_wallet_address}` and your '
                           f'balance will be available once confirmed.')


@bot.command(pass_context=True, help=bot_help_withdraw)
async def withdraw(context: commands.Context, amount: float):
    user: models.User = models.User.objects(
        user_id=context.message.author.id).first()
    real_amount = int(amount * COIN_DIGITS)

    if not user.user_wallet_address:
        await bot.send_message(
            context.message.author,
            f'You do not have a withdrawal address, please use '
            f'`.register <wallet_address>` to register.')
        return

    user_balance_wallet: models.Wallet = models.Wallet.objects(
        wallet_address=user.balance_wallet_address).first()

    if real_amount + config.tx_fee >= user_balance_wallet.actual_balance:
        await bot.add_reaction(context.message, EMOJI_ERROR)
        await bot.send_message(context.message.author,
                               f'🛑 Insufficient balance to withdraw '
                               f'{real_amount / COIN_DIGITS:.2f} '
                               f'{COIN_REPR}.')
        return

    if real_amount > config.max_tx_amount:
        await bot.add_reaction(context.message, EMOJI_ERROR)
        await bot.send_message(
            context.message.author,
                f'🛑 Transactions cannot be bigger than '
                f'{config.max_tx_amount / COIN_DIGITS:.2f} '
                f'{COIN_REPR}')
        return
    elif real_amount < config.min_tx_amount:
        await bot.add_reaction(context.message, EMOJI_ERROR)
        await bot.send_message(
            context.message.author,
                f'🛑 Transactions cannot be lower than '
                f'{config.min_tx_amount / COIN_DIGITS:.2f} '
                f'{COIN_REPR}')
        return

    withdrawal = store.withdraw(user, real_amount)
    if (withdrawal is not None):
        await bot.add_reaction(context.message, EMOJI_MONEYFACE)
        await bot.send_message(
            context.message.author,
                f'💰 You have withdrawn {real_amount / COIN_DIGITS:.2f} '
                f'{COIN_REPR}.\n'
                f'Transaction hash: `{withdrawal.tx_hash}`')
    else:
        await bot.add_reaction(context.message, EMOJI_ERROR)


@bot.command(pass_context=True, help=bot_help_tip)
async def tip(context: commands.Context, amount: float,
              member: discord.Member = None):

    if (str(context.message.channel.type).lower() == "private"):
        await bot.reply('🛑 This command can not be in private.')
        return
    ## If multiple mentions
    if (len(context.message.mentions) > 1):
        await _tip(context, amount, None, None)
        return

    user_from: models.User = models.User.objects(
        user_id=context.message.author.id).first()
    user_to: models.User = store.register_user(member.id)
    real_amount = int(amount * COIN_DIGITS)

    user_from_wallet: models.Wallet = models.Wallet.objects(
        wallet_address=user_from.balance_wallet_address).first()

    if real_amount + config.tx_fee >= user_from_wallet.actual_balance:
        await bot.add_reaction(context.message, EMOJI_ERROR)
        await bot.send_message(context.message.author,
                        f'🛑 Insufficient balance to send tip of '
                        f'{real_amount / COIN_DIGITS:.2f} '
                        f'{COIN_REPR} to {member.mention}.')
        return

    if real_amount > config.max_tx_amount:
        await bot.add_reaction(context.message, EMOJI_ERROR)
        await bot.send_message(context.message.author,
                        f'🛑 Transactions cannot be bigger than '
                        f'{config.max_tx_amount / COIN_DIGITS:.2f} '
                        f'{COIN_REPR}.')
        return
    elif real_amount < config.min_tx_amount:
        await bot.add_reaction(context.message, EMOJI_ERROR)
        await bot.send_message(context.message.author,
                        f'🛑 Transactions cannot be smaller than '
                        f'{config.min_tx_amount / COIN_DIGITS:.2f} '
                        f'{COIN_REPR}.')
        return

    tip = store.send_tip(user_from, user_to, real_amount)
    if (tip is not None):
        tipAmount = '{:,.2f}'.format(real_amount / COIN_DIGITS)
        await bot.add_reaction(context.message, EMOJI_MONEYFACE)
        await bot.send_message(
            context.message.author,
                        f'💰💖 Tip of {tipAmount} '
                        f'{COIN_REPR} '
                        f'was sent to `{member.name}`\n'
                        f'Transaction hash: `{tip.tx_hash}`')
        await bot.send_message(
            member,
                        f'💰 You got a tip of {tipAmount} '
                        f'{COIN_REPR} from `{context.message.author.name}`\n'
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
    await bot.reply(f'*[CIRCULATING SUPPLY]* `{supply}{COIN_REPR}`\n')

@bot.command(pass_context=True, help=bot_help_stats)
async def stats(context: commands.Context):
    supply = daemonrpc_client.getsupply()
    difficulty = daemonrpc_client.getdiff()
    hashrate = daemonrpc_client.gethashrate()
    height = daemonrpc_client.getheight()
    await bot.reply(f'\n*[NETWORK HEIGHT]* `{height}`\n'
                    f'*[CIRCULATING SUPPLY]* `{supply}{COIN_REPR}`\n'
                    f'*[CURRENT DIFFICULTY]* `{difficulty}`\n'
                    f'*[NETWORK HASH RATE]* `{hashrate}`\n')

@register.error
async def register_error(error, _: commands.Context):
    pass


@info.error
async def info_error(error, _: commands.Context):
    pass

@balance.error
async def botbalance_error(error, _: commands.Context):
    pass

@balance.error
async def balance_error(error, _: commands.Context):
    pass


@withdraw.error
async def withdraw_error(error, _: commands.Context):
    pass


@tip.error
async def tip_error(error, _: commands.Context):
    pass


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

## Multiple tip
async def _tip(context: commands.Context, amount,
               sender: discord.User=None,
               receiver: discord.User=None):
    user_from: models.User = models.User.objects(
        user_id=context.message.author.id).first()

    if not sender:  # regular tip
        sender = context.message.author

    if not receiver:
        tipees = context.message.mentions
    else:
        tipees = [receiver, ]

    try:
        real_amount = int(round(float(amount) * COIN_DIGITS))
    except:
        await bot.send_message(context.message.author,
                                "Amount must be a number.")
        return

    if real_amount > config.max_tx_amount:
        await bot.add_reaction(context.message, EMOJI_ERROR)
        await bot.send_message(context.message.author,
                        f'🛑 Transactions cannot be bigger than '
                        f'{config.max_tx_amount / COIN_DIGITS:.2f} '
                        f'{COIN_REPR}.')
        return
    elif real_amount < config.min_tx_amount:
        await bot.add_reaction(context.message, EMOJI_ERROR)
        await bot.send_message(context.message.author,
                        f'🛑 Transactions cannot be smaller than '
                        f'{config.min_tx_amount / COIN_DIGITS:.2f} '
                        f'{COIN_REPR}.')
        return

    destinations = []
    listMembers = tipees

    memids = [] ## list of member ID
    for member in listMembers:
        #print(member.name) # you'll just print out Member objects your way.
        if (context.message.author.id != member.id) :
            user_to: models.User = store.register_user(member.id)
            memids.append(user_to)

    for desti in memids:
        destinations.append({"address":desti.balance_wallet_address,"amount":real_amount})

    ActualSpend = real_amount * len(memids) + config.tx_fee
    user_from_wallet: models.Wallet = models.Wallet.objects(
        wallet_address=user_from.balance_wallet_address).first()
    #print(str(amount)) #10.0
    #print(str(real_amount)) #1000
    if ActualSpend + config.tx_fee >= user_from_wallet.actual_balance:
        await bot.add_reaction(context.message, EMOJI_ERROR)
        await bot.send_message(context.message.author,
                        f'🛑 Insufficient balance to send total tip of '
                        f'{ActualSpend / COIN_DIGITS:.2f} '
                        f'{COIN_REPR}.')
        return

    if ActualSpend > config.max_tx_amount:
        await bot.add_reaction(context.message, EMOJI_ERROR)
        await bot.send_message(context.message.author,
                        f'🛑 Total transactions cannot be bigger than '
                        f'{config.max_tx_amount / COIN_DIGITS:.2f} '
                        f'{COIN_REPR}.')
        return
    elif real_amount < config.min_tx_amount:
        print('ActualSpend: '+str(ActualSpend))
        await bot.add_reaction(context.message, EMOJI_ERROR)
        await bot.send_message(context.message.author,
                        f'🛑 Total transactions cannot be smaller than '
                        f'{config.min_tx_amount / COIN_DIGITS:.2f} '
                        f'{COIN_REPR}.')
        return

    #print(destinations)
    tip = store.send_tipall(user_from, destinations, real_amount)

    await bot.add_reaction(context.message, EMOJI_MONEYFACE)
    await bot.send_message(
        context.message.author,
                    f'💰💖 Total tip of {ActualSpend / COIN_DIGITS:.2f} '
                    f'{COIN_REPR} '
                    f'was sent to ({len(destinations)}) members.\n'
                    f'Transaction hash: `{tip.tx_hash}`\n'
                    f'Each: `{real_amount / COIN_DIGITS:.2f}{COIN_REPR}`'
                    f'Total spending: `{ActualSpend / COIN_DIGITS:.2f}{COIN_REPR}`')
    for member in context.message.mentions:
        #print(member.name) # you'll just print out Member objects your way.
        if (context.message.author.id != member.id) :
            if (member.bot == False):
                await bot.send_message(
                    member,
                        f'💰 You got a tip of {real_amount / COIN_DIGITS:.2f} '
                        f'{COIN_REPR} from `{context.message.author.name}`\n'
                        f'Transaction hash: `{tip.tx_hash}`')
    return

if __name__ == '__main__':
    main()

