import asyncio
from enum import Enum

import websockets
import uuid
import json
import random
import datetime
import sqlite3

from src.functions.order_handlers import cancel_order, get_order_id_info, get_order_info, place_order
from src.functions.quote_handlers import get_quotes, get_quote, get_current_quotes
from src.functions.server_messages_handlers import format_market_data_update, format_error_info, format_quotes_info, \
    format_success_info
from src.models.message_types import ClientMessages

# Список активных подписок на котировки
subscriptions = {}


async def subscribe_market_data(websocket, data):
    instrument = data['instrument']
    subscription_id = str(uuid.uuid4())
    subscriptions[subscription_id] = {
        'websocket': websocket,
        'instrument': instrument
    }
    await websocket.send(format_success_info(subscription_id))


async def unsubscribe_market_data(websocket):
    for subscription_id, subscription in subscriptions.items():
        if subscription['websocket'] == websocket:
            del subscriptions[subscription_id]
            break


def init():
    conn = sqlite3.connect('md.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS orders
                      (order_id TEXT, timestamp TEXT, instrument TEXT, side TEXT,
                       price REAL, volume REAL, status TEXT, last_changed TEXT)''')
    conn.commit()
    conn.close()

    conn = sqlite3.connect('md.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS quotes
                            (timestamp TEXT, instrument TEXT, bid REAL, offer REAL, min_amount REAL, max_amount REAL)''')
    conn.commit()
    conn.close()


message_handlers = dict({
    ClientMessages.SubscribeMarketData.value: {
        'handler': subscribe_market_data,
        'websocketOnl': False
    },
    ClientMessages.UnsubscribeMarketData.value:
        {
            'handler': unsubscribe_market_data,
            'websocketOnl': True
        },

    ClientMessages.GetOrderInfo.value:
        {
            'handler': get_order_info,
            'websocketOnl': True
        },
    ClientMessages.GetCurrentQuotes:
        {
            'handler': get_current_quotes,
            'websocketOnl': False
        },
    ClientMessages.PlaceOrder.value:
        {
            'handler': place_order,
            'websocketOnl': False
        },
    ClientMessages.CancelOrder.value:
        {
            'handler': cancel_order,
            'websocketOnl': False
        },
    ClientMessages.GetOrderByIdInfo.value:
        {
            'handler': get_order_id_info,
            'websocketOnl': False
        },
})


async def handle_message(websocket, message):
    message_type = message['messageType']
    handler = message_handlers.get(message_type)
    if handler:
        if handler['websocketOnl']:
            await handler['handler'](websocket)
        else:
            await handler['handler'](websocket, message.get('message'))
    else:
        await websocket.send(format_error_info('Invalid message type'))


async def consumer(websocket, path):
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                await handle_message(websocket, data)
            except json.JSONDecodeError:
                await websocket.send(format_error_info('Invalid JSON format'))
    except websockets.ConnectionClosedError:
        await unsubscribe_market_data(websocket)


async def market_data_publisher():
    while True:
        for subscription_id, subscription in subscriptions.items():

            instrument = subscription['instrument']
            quote = get_quote(instrument)
            quotes = get_quotes(instrument)
            message = format_market_data_update(quote)

            try:
                await subscription['websocket'].send(message)
                await subscription['websocket'].send(format_quotes_info(quotes))
            except:
                continue
        await asyncio.sleep(1)


async def update_quotes():
    while True:
        for instrument in ['IM', 'TG', 'BJ']:
            current_quote = get_quote(instrument)
            if current_quote is None:
                current_price = 60
                new_offer = 150
            else:
                current_price = float(current_quote.bid)
                new_offer = float(current_quote.offer)

            current_price += random.uniform(-0.5, 0.5)
            current_price = max(0, min(100, current_price))  # Ограничиваем цену между 0 и 100

            new_bid = str(current_price)

            new_offer += random.uniform(-5, 5)
            new_offer = max(0, min(250, new_offer))

            conn = sqlite3.connect('md.db')
            cursor = conn.cursor()
            timestamp = str(datetime.datetime.now())
            cursor.execute(
                f"INSERT INTO quotes (instrument, timestamp, bid, offer, min_amount, max_amount) "
                f"VALUES (?, ?, ?, ?, ?, ?)",
                (instrument, timestamp, new_bid, new_offer, 0, 0)
            )
            conn.commit()
            conn.close()

            process_orders(instrument, current_price)

        await asyncio.sleep(1)


def process_orders(instrument, current_price):
    conn = sqlite3.connect('md.db')
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM orders WHERE instrument = '{instrument}' AND status = 'Active'")
    rows = cursor.fetchall()
    for row in rows:
        order_id, timestamp, _, side, price, volume, _, last_changed = row
        price = float(price)
        timestamp_upd = str(datetime.datetime.now())
        if side == 'Buy' and price >= current_price:
            cursor.execute(
                f"UPDATE orders SET status = 'Filled', last_changed = '{timestamp_upd}' WHERE order_id = '{order_id}'")
        elif side == 'Sell' and price <= current_price:
            cursor.execute(
                f"UPDATE orders SET status = 'Filled', last_changed = '{timestamp_upd}' WHERE order_id = '{order_id}'")
    conn.commit()
    conn.close()


