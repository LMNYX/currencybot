import discord
import os
import requests
import json
import re
from datetime import datetime, timedelta

ENVRATE = os.getenv("DEFAULT_CURRENCY").split(',')
ENVTOKEN = os.getenv('DISORD_TOKEN')
ENVPREFIX = os.getenv('BOT_PREFIX')
CURRENCYREGEX = r"(\d+\.?\d*)(k*)? ?(\w+)"

with open('currencies.json') as f:
    currencies = json.load(f)

def find_currency(currency):
    if not currency.strip():
        return None
    
    currency = currency.lower()
    
    for c in currencies:
        if c['cc'] == currency:
            return c
        if any([re.match(alias, currency) for alias in c['aliases']]):
            return c
    return None

def does_text_contain_currency(text):
    for c in currencies:
        if c['cc'] in text:
            return c
    return False

def get_cur_exchange_rate(cur1, cur2):
    r = requests.get('https://duckduckgo.com/js/spice/currency/1/{}/{}'.format(cur1, cur2))

    if (r.status_code != 200):
        return False

    try:
        unwrapped_response = r.text[r.text.find('\n') + 1 : r.text.rfind('\n') - 2]
        json_response = json.loads(unwrapped_response)
        value = json_response['to'][0]['mid']
    except:
        return False
    return value

async def shit_broke(message):
    await message.reply("Shit broke. You're either brainded or blame [DuckDuckGo](https://duckduckgo.com).")
    return True

class MyClient(discord.Client):
    async def on_ready(self):
        print(f'Logged on as {self.user}!')

    async def on_message(self, message):
        
        if message.author == self.user:
            return
        
        message.content = re.sub(r'\<(a\:)?\:?\@?\w+(\:\d+)?\>', '', message.content).lower()

        print(f"{message.author}: {message.content}", end='')

        if message.content.startswith(ENVPREFIX):
            print(' (command)', end='')
            command = message.content.split()[0][1:]
            if command == "convert":
                args = message.content.split()[1:]
                if len(args) == 3:
                    amount = args[0]
                    currency = args[1]
                    to_currency = args[2]
                    converted = get_cur_exchange_rate(
                        currency,
                        to_currency
                    )
                    if (not converted):
                        await shit_broke(message)
                        return
                    print(amount)
                    print(converted)
                    total_value = float(amount) * float(converted)
                    await message.reply(f'{amount} {currency.upper()} is ~{round(total_value, 3)} {to_currency.upper()}.')
                else:
                    await message.reply('Invalid arguments')
            return

        matches = re.finditer(CURRENCYREGEX, message.content, re.MULTILINE)
        print('')

        currency_data = []

        for matchNum, match in enumerate(matches, start=1):
            amount_unwrapped = float(match.group(1))
            amount_k = len(match.group(2)) if match.group(2) else 0
            currency = find_currency(match.group(3))
            
            if (amount_k > 0):
                amount_unwrapped = amount_unwrapped * (1000 * amount_k)
            
            exchange_rate = get_cur_exchange_rate(currency['cc'], ENVRATE[0])
            if (not exchange_rate):
                await shit_broke(message)
                return
            total_value = amount_unwrapped * exchange_rate

            currency_data.append('{} **{}** is {} **{}**'.format(
                amount_unwrapped,
                currency['cc'].upper(),
                round(total_value, 3),
                find_currency(ENVRATE[0])['cc'].upper()
            ))
        

        if (len(currency_data) < 1):
            return
        
        response_text = "### <a:DinkDonk:956632861899886702> {} currency mentions found.\n".format(len(currency_data))

        for k, v in enumerate(currency_data):
            response_text += '{}. {}'.format(k+1, v)
        
        await message.reply(response_text)

            
intents = discord.Intents.default()
intents.message_content = True

client = MyClient(intents=intents)
client.run(ENVTOKEN)
