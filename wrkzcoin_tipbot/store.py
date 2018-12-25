from datetime import datetime

import sys
sys.path.append("..")
import models, wallet

def register_user(user_id: str, user_wallet: str = None) -> models.User:
    existing_user: models.User = models.User.objects(user_id=user_id).first()
    if existing_user:
        if not user_wallet:
            return existing_user

        existing_user.user_wallet_address = user_wallet
        existing_user.save()
        return existing_user

    balance_address = wallet.register()
    user_model = models.User(user_id=user_id, user_wallet_address=user_wallet,
                             balance_wallet_address=balance_address)
    user_model.save()
    models.Wallet(wallet_address=balance_address).save()
    return user_model


def get_user_wallet(user_id: str) -> models.Wallet:
    user: models.User = models.User.objects(user_id=user_id).first()
    user_wallet: models.Wallet = models.Wallet.objects(
        wallet_address=user.balance_wallet_address).first()
    return user_wallet


def send_tip(user_from: models.User, user_to: models.User,
             amount: int) -> models.Tip:
    tip = models.Tip(from_user=user_from, to_user=user_to, amount=amount,
                     date=datetime.utcnow())

    tx_hash = wallet.send_transaction(user_from.balance_wallet_address,
                                      user_to.balance_wallet_address, amount)

    tip.tx_hash = tx_hash
    tip.save()

    return tip

def send_tipall(user_from: models.User, user_tos,
             amount: int) -> models.TipAll:
    tip = models.TipAll(from_user=user_from, amount=amount,
                     date=datetime.utcnow())

    tx_hash = wallet.send_transactionall(user_from.balance_wallet_address,
                                      user_tos)

    tip.tx_hash = tx_hash
    tip.save()
    return tip

def withdraw(user: models.User, amount: int) -> models.Withdrawal:
    withdrawal = models.Withdrawal(user=user, amount=amount,
                                   date=datetime.utcnow())

    tx_hash = wallet.send_transaction(user.balance_wallet_address,
                                      user.user_wallet_address, amount)

    withdrawal.tx_hash = tx_hash
    withdrawal.save()

    return withdrawal


def update_balances():
    print('Updating all wallet balances')
    wallets = models.Wallet.objects
    wallet_addresses = [w.wallet_address for w in wallets]
    balances = wallet.get_all_balances(wallet_addresses)
    for address, details in balances.items():
        try:
            wallet_doc: models.Wallet = models.Wallet.objects(
                wallet_address=address).first()
            wallet_doc.actual_balance = details['availableBalance']
            wallet_doc.locked_balance = details['lockedAmount']
            wallet_doc.save()
            print(f'Updated wallet {wallet_doc.wallet_address}')
        except Exception as e:
            print(e)
