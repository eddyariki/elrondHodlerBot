import telebot
import json
import threading
import time
from datetime import datetime
import requests
import sys
from encrypt import Encryption
from dbmanager import DBManager
from signal import signal, SIGINT

file_loc = ""
with open(file_loc + "config.json", "r") as cg:
    config = json.load(cg)


"""
--------------------------------------------------------------------------
Setup
--------------------------------------------------------------------------
"""

bot = telebot.TeleBot(config["token"], parse_mode="Markdown")
accepted_group = config['accepted_group']
bot_address = config['bot_address']
crypto = Encryption("")
db = DBManager(file_loc+"data/test.db")

how_to = """
[1]. Send transaction

*TO*: Bot's address

*MESSAGE*: Encrypted user ID

*FEE*: Fee changes with message size, make sure you adjust. 


[2]. Confirm transaction and verify

Do /verifytx transaction_hash

[3]. Successful

If decryption is successful, username matches, and user is in whitelisted group:

-Wallet Address

-Transaction Hash

-Timestamp

Will be stored in database. 

[4]. Optional:

Do /verify wallet_address

This will verify ownership of wallet and send it to groupchat to prove it to members.

[5]. See group's value

Do /totalvalue in the groupchat to see total value
"""



"""
--------------------------------------------------------------------------
Bot Message Handlers
--------------------------------------------------------------------------
"""

def check_auth(message):

    try:
        user = bot.get_chat_member(int(accepted_group),message.from_user.id)
        if(user):
            return user.status !="left"
        else:
            return False
    except Exception as e:
        print(e)
    return False


@bot.inline_handler(func=lambda query:True)
def query_text(inline_query):
    print("Received inline")
    bot.answer_inline_query(
        inline_query.id,
        [],
        cache_time=0, 
        is_personal=True, 
        switch_pm_text="Register Wallet Address? (PM mode)",
        switch_pm_parameter="register"
    )

@bot.message_handler(commands=['groupinfo'])
def command_groupinfo(message):
    print(message.chat.id)

@bot.message_handler(commands=['start'])
def command_start(message):
    args = message.text.split(" ")
    if(len(args)>1):
        if(args[1]=="register"):
            if(message.chat.type!="private"):
                bot.delete_message(message.chat.id, message.message_id)
                bot.send_message(message.chat.id, "Do not invoke this here! This is to be done in private.")
                return
            if(check_auth(message)):
                bot.send_message(message.chat.id, how_to, parse_mode='Markdown')
                #Encrypt username
                user_id = str(message.from_user.id)
                encrypted = crypto.encrypt(user_id)
                bot.send_message(message.chat.id, "-\n✅*[your encrypted user_id]✅:*\n-",parse_mode='Markdown')
                bot.send_message(message.chat.id, f"{encrypted}",parse_mode='None')
                bot.send_message(message.chat.id, "-\n🧾*[bot's address to send to]🧾:*\n-", parse_mode='Markdown')
                bot.send_message(message.chat.id, f"{bot_address}", parse_mode='None')
            else:
                bot.send_message(message.chat.id, "You are not in the group")
    else:
        if(message.chat.type!="private"):
            bot.send_message(message.chat.id, "Type in @elrondHodlerBot in the message field.")
            return
        bot.send_message(message.chat.id, config["welcome"], parse_mode='None')


@bot.message_handler(commands=['verifytx'])
def command_tx(message):
   
    if(message.chat.type!="private"):
        bot.delete_message(message.chat.id, message.message_id)
        bot.send_message(message.chat.id, "Do not invoke this here! This is to be done in private.")
        return
    if(check_auth(message)):
        try:
            # print(message)
            new_message = message.text.replace("\n", " ")
            args = " ".join(new_message.split()).split(" ")
            
            if(len(args)>1):
                tx_id = args[1]
                
                r = requests.get("https://api.elrond.com/transaction/" + tx_id)
                if(r.status_code==200):
                    data = r.json()
                    tx = data['data']['transaction']
                    if(tx['status']=='executed'):
                        sender = tx['sender']
                        receiver = tx['receiver']
                        if(receiver == bot_address):
                            data = tx['data']
                            user_id=crypto.decrypt(data)
                            try:
                                chat_mem=bot.get_chat_member(int(accepted_group),int(user_id))
                                if(chat_mem.user.id==message.from_user.id):
                                    utc_time = int(time.time())
                                    db.insert(str(sender), str(tx_id), utc_time)
                                    db.backup(file_loc+"backup")
                                    bot.send_message(message.chat.id,f"""
Success✅ Stored:

Wallet Address:

{str(sender)}

Transaction ID:

{str(tx_id)}

Timestamp UTC:
({datetime.fromtimestamp(utc_time)})
""", parse_mode="None")                    
                                else:
                                    bot.send_message(message.chat.id, "This user is not you.")
                            except Exception as e:
                                bot.send_message(message.chat.id, "Something went wrong with verifying transaction.")
                        else:
                            bot.send_message(message.chat.id, "You sent to the wrong address...?")
                    else:
                        bot.send_message(message.chat.id, "Transaction did not execute. Got gas?")
                else:
                    bot.send_message(message.chat.id, f"Error code: {r.status_code}\nTry again in a few minutes.")
            else:
                bot.send_message(message.chat.id, "Send a the transaction_hash", parse_mode="None")
        except Exception as e:
            print(e)
    else:
         bot.send_message(message.chat.id, "You are not in group.", parse_mode="None")


@bot.message_handler(commands=['verify'])
def command_verify(message):
    if(message.chat.type!="private"):
        bot.delete_message(message.chat.id, message.message_id)
        bot.send_message(message.chat.id, "Do not invoke this here! This is to be done in private.")
        return
    if(check_auth(message)):
        d = db.get_all()
        chat_size = bot.get_chat_members_count(int(accepted_group))
        percent = len(d)/float(chat_size)
        if(percent<0.5):
            bot.send_message(message.chat.id, "In order to protect anonymity, this command will not be available until there are enough addresses listed.")
            return
        try:
            new_message = message.text.replace("\n", " ")
            args = " ".join(new_message.split()).split(" ")
            if(len(args)>1):
                wallet_address = args[1]
                results = db.get_address(wallet_address)
                if(len(results)>0):
                    stored_address = results[0]
                    tx_id = stored_address[2]
                    r = requests.get("https://api.elrond.com/transaction/" + tx_id)
                    if(r.status_code==200):
                        data = r.json()
                        tx = data['data']['transaction']
                        if(tx['status']=='executed'):
                            receiver = tx['receiver']
                            if(receiver == bot_address):
                                data = tx['data']
                                user_id=crypto.decrypt(data)
                                try:
                                    chat_mem=bot.get_chat_member(int(accepted_group),int(user_id))
                                    if(chat_mem.user.id == message.from_user.id):
                                        r1 = requests.get("https://api.elrond.com/address/" + wallet_address + "/balance")
                                        balance=False
                                        if(r1.status_code==200):
                                            balance_raw = float(r1.json()['data']['balance'])/10**21
                                            balance = "{:,.18f}".format(float(r1.json()['data']['balance'])/10**18)
                                        if(balance):
                                            payload = {"symbol":"EGLDUSDT"}
                                            r2 = requests.get("https://api.binance.com/api/v3/" + "ticker/price", params=payload)
                                            if(r2.status_code==200):
                                                price_usd_data = float(r2.json()['price'])*1000
                                            verification_message= f"""👨‍⚖️ Wallet Verified ✅

By: @{chat_mem.user.username}
Name: {chat_mem.user.first_name} {chat_mem.user.last_name}

Wallet Address:
{wallet_address}

Balance:
{balance}eGLD

Value:
${'{:,.2f}'.format(balance_raw * price_usd_data)}
"""
                                            bot.send_message(int(accepted_group),verification_message, parse_mode='None')
                                            bot.send_message(message.chat.id,verification_message, parse_mode='None')
                                            bot.send_message(message.chat.id,"Message sent to groupchat.", parse_mode='None')
                                        else:
                                            bot.send_message(message.chat.id, "Could not find wallet.")
                                    else:
                                        bot.send_message(message.chat.id, "This user is not you.")
                                except Exception as e:
                                    bot.send_message(message.chat.id, "Something went wrong with verifying transaction.\nCheck ecryption key")
                else:
                    bot.send_message(message.chat.id, "Could not find wallet. Check address again.")
            else:
                bot.send_message(message.chat.id, "Send your transaction_hash", parse_mode='None')
        except Exception as e:
            print(e)
    else:
        bot.send_message(message.chat.id, "You are not in group.")
        
@bot.message_handler(commands=['totalvalue'])
def command_total(message):
    if(check_auth(message)):
        d = db.get_all()
        chat_size = bot.get_chat_members_count(int(accepted_group))
        percent = len(d)/float(chat_size)
        if(percent<0.5):
            bot.send_message(message.chat.id, "In order to protect anonymity, this command will not be available until there are enough addresses listed.")
            return
        balances = 0
        for wallets in d:
            address = wallets[1]
            r1 = requests.get("https://api.elrond.com/address/" + address + "/balance")
            if(r1.status_code==200):
                balance_raw = float(r1.json()['data']['balance'])/10**18
                balances+=balance_raw
        payload = {"symbol":"ERDUSDT"}
        r2 = requests.get("https://api.binance.com/api/v3/" + "ticker/price", params=payload)
        if(r2.status_code==200):
            price_usd_data = float(r2.json()['price'])*1000
        total_usd = "{:,.2f}".format(price_usd_data * balances)
        bot.send_message(message.chat.id, f"""
Group's total hodlings:
{balances}eGLD

Value:
${total_usd}
""")
    else:
        bot.send_message(message.chat.id, "You are not in group.")


def signal_handler(signal_received, frame):
    print("Exiting....")
    exit(0)

def main():
    signal(SIGINT, signal_handler)
    while True:
        try:
            print("Starting Bot Polling...", "info")
            bot.polling()
        except Exception as e:
            print(f"Bot polling error: {e.args}", "error")
            bot.stop_polling()
            time.sleep(10)


if __name__ == "__main__":
    main()