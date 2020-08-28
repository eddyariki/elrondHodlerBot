import telebot
import json
import threading
import time
import requests
import sys
from encrypt import Encryption
from dbmanager import DBManager

file_loc = ""
with open(file_loc + "config.json", "r") as cg:
    config = json.load(cg)


"""
--------------------------------------------------------------------------
Setup
--------------------------------------------------------------------------
"""

bot = telebot.TeleBot(config["token"], parse_mode="Markdown")
accepted_groups = config['accepted_groups']
bot_address = config['bot_address']
crypto = Encryption("")
db = DBManager(file_loc+"data/test.db")
d = db.get_all()

"""
--------------------------------------------------------------------------
Bot Message Handlers
--------------------------------------------------------------------------
"""

def check_auth(message):
    for id in accepted_groups:
        try:
            bot.get_chat_member(int(id),message.from_user.id)
            print("In group")
            return True
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


@bot.message_handler(commands=['start'])
def command_start(message):
    args = message.text.split(" ")
    if(len(args)>1):
        if(args[1]=="register"):
            if(check_auth(message)):
                user_id = str(message.from_user.id)
                encrypted, key = crypto.encrypt(user_id)
                print(encrypted)
                bot.send_message(message.chat.id, f"Here is your encrypted user_id: \n\n{encrypted}\n\n{key}\n\nWhat to do: \nGo to your Elrond Wallet and send a tiny amount of eGLD to the address: \n{bot_address}\n\n!Important! in the data box send the encrypted user id\n\nOnce the transaction is sent, come back here and do /transaction _____________ and put transaction hash there.", parse_mode='None')
            else:
                bot.send_message(message.chat.id, "You are not in the group")
    else:
        bot.send_message(message.chat.id, config["welcome"])


@bot.message_handler(commands=['transaction'])
def command_tx(message):
    args = message.text.split(" ")
    if(len(args)>1):
        tx_id = args[1]
        key = args[2]
        r = requests.get("https://api.elrond.com/transaction/" + tx_id)
        if(r.status_code==200):
            data = r.json()
            tx = data['data']['transaction']
            if(tx['status']=='executed'):
                sender = tx['sender']
                receiver = tx['receiver']
                if(receiver == bot_address):
                    data = tx['data']
                    print(data)
                    print(type(data))

                    user_id=crypto.decrypt(data, key)
                    for id in accepted_groups:
                        try:
                            chat_mem=bot.get_chat_member(int(id),int(user_id))
                            print("In group")
                            utc_time = int(time.time())
                            db.insert(str(sender), str(tx_id), utc_time)
                            bot.send_message(message.chat.id,"Success!!!: " + chat_mem.user.first_name)
                        except Exception as e:
                            print(e)

@bot.message_handler(commands=['verify'])
def command_verify(message):
    args = message.text.split(" ")
    if(len(args)>2):
        wallet_address = args[1]
        key = args[2]
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
                        print(data)
                        print(type(data))
                        user_id=crypto.decrypt(data, key)
                        for id in accepted_groups:
                            try:
                                chat_mem=bot.get_chat_member(int(id),int(user_id))
                                print("In group")
                                bot.send_message(message.chat.id,"Verified! You are VERIFIED!: " + chat_mem.user.first_name)
                            except Exception as e:
                                print(e)
        

print("polling")
bot.polling()
