import asyncio
import websockets
import uuid
import json
import random
import datetime
import sqlite3

# Список активных подписок на котировки
subscriptions = {}

# Список активных заявок
orders = {}


class Quote:
    def __init__(self, bid, offer, min_amount, max_amount):
        self.bid = bid
        self.offer = offer
        self.min_amount = min_amount
        self.max_amount = max_amount


class Order:
    def __init__(self, order_id, timestamp, instrument, side, price, volume, status, last_changed):
        self.order_id = order_id
        self.timestamp = timestamp
        self.instrument = instrument
        self.side = side
        self.price = price
        self.volume = volume
        self.status = status
        self.last_changed = last_changed


def serialize_order(order):
    return {
        'order_id': order.order_id,
        'timestamp': order.timestamp,
        'instrument': order.instrument,
        'side': order.side,
        'price': order.price,
        'volume': order.volume,
        'status': order.status,
        "last_changed": order.last_changed
    }


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


async def get_order_info(websocket):
    orders_info = get_orders_info()  # Получение информации о заявках
    await websocket.send(format_order_info(orders_info))


async def get_current_quotes(websocket, data):
    instrument = data['instrument']
    quote = get_quote(instrument)  # Функция для получения текущих котировок по инструменту
    await websocket.send(format_current_quotes(quote))


async def place_order(websocket, data):
    order_id = str(uuid.uuid4())
    timestamp = str(datetime.datetime.now())
    instrument = data['instrument']
    side = data['side']
    price = data['price']
    volume = data['volume']
    status = 'Active'
    create_order(order_id, timestamp, instrument, side, price, volume, status)
    await websocket.send(format_success_info(order_id))


async def cancel_order(websocket, data):
    order_id = data['orderId']
    if cancel_existing_order(order_id):
        await websocket.send(format_success_info(order_id))
    else:
        await websocket.send(format_error_info('Order not found'))


async def get_order_id_info(websocket, data):
    instrument = data['instrument']
    orders_info = get_orders_info_by_instrument(instrument)
    await websocket.send(format_order_info(orders_info))


def format_success_info(message):
    return json.dumps({
        'messageType': 'SuccessInfo',
        'message': message
    })


def format_error_info(reason):
    return json.dumps({
        'messageType': 'ErrorInfo',
        'message': reason
    })


def format_market_data_update(data):
    return json.dumps({
        'messageType': 'MarketDataUpdate',
        'message': data.__dict__
    })


def format_order_info(data):
    serialized_orders = [serialize_order(order) for order in data]
    return json.dumps({
        'messageType': 'OrderInfo',
        'message': serialized_orders
    })


def format_current_quotes(data):
    return json.dumps({
        'messageType': 'CurrentQuotes',
        'message': data.__dict__
    })


def get_quote(instrument):
    conn = sqlite3.connect('quotes.db')
    cursor = conn.cursor()

    cursor.execute(f"SELECT * FROM quotes WHERE instrument = '{instrument}' ORDER BY timestamp DESC LIMIT 1")
    row = cursor.fetchone()

    if row:
        _, timestamp, bid, offer, min_amount, max_amount = row
        return Quote(bid=str(bid), offer=offer, min_amount=min_amount, max_amount=max_amount)

    conn.close()


def create_order(order_id, timestamp, instrument, side, price, volume, status):
    conn = sqlite3.connect('orders.db')
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS orders
                      (order_id TEXT, timestamp TEXT, instrument TEXT, side TEXT,
                       price REAL, volume REAL, status TEXT)''')

    cursor.execute(
        f"INSERT INTO orders (order_id, timestamp, instrument, side, price, volume, status, last_changed) "
        f"VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (order_id, timestamp, instrument, side, price, volume, status, timestamp)
    )

    conn.commit()
    conn.close()


def cancel_existing_order(order_id):
    conn = sqlite3.connect('orders.db')
    cursor = conn.cursor()

    cursor.execute(f"SELECT * FROM orders WHERE order_id = '{order_id}'")
    row = cursor.fetchone()

    if row:
        status = row[6]
        if status == 'Active':
            timestamp = str(datetime.datetime.now())
            cursor.execute(
                f"UPDATE orders SET status = 'Cancelled', last_changed = '{timestamp}' WHERE order_id = '{order_id}'")

            conn.commit()
            conn.close()
            return True

    conn.close()
    return False


def get_orders_info():
    conn = sqlite3.connect('orders.db')
    cursor = conn.cursor()

    cursor.execute(f"SELECT * FROM orders")
    rows = cursor.fetchall()

    orders_info = []
    for row in rows:
        order_id, timestamp, instrument, side, price, volume, status, last_changed = row
        order = Order(order_id, timestamp, instrument, side, price, volume, status, last_changed)
        orders_info.append(order)
        print(last_changed)
    conn.close()
    return orders_info


def get_orders_info_by_instrument(instrument):
    conn = sqlite3.connect('orders.db')
    cursor = conn.cursor()

    cursor.execute(f"SELECT * FROM orders WHERE instrument = '{instrument}'")
    rows = cursor.fetchall()

    orders_info = []
    for row in rows:
        order_id, timestamp, _, side, price, volume, status, last_changed = row
        order = Order(order_id, timestamp, instrument, side, price, volume, status, last_changed)
        orders_info.append(order)
    print(orders_info)
    conn.close()
    return orders_info


async def handle_message(websocket, message):
    message_type = message['messageType']
    if message_type == 'SubscribeMarketData':
        await subscribe_market_data(websocket, message['message'])
    elif message_type == 'UnsubscribeMarketData':
        await unsubscribe_market_data(websocket)
    elif message_type == 'GetOrderInfo':
        await get_order_info(websocket)
    elif message_type == 'GetCurrentQuotes':
        await get_current_quotes(websocket, message['message'])
    elif message_type == 'PlaceOrder':
        await place_order(websocket, message['message'])
    elif message_type == 'CancelOrder':
        await cancel_order(websocket, message['message'])
    elif message_type == 'GetOrderByIdInfo':
        await get_order_id_info(websocket, message['message'])
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
    except websockets.exceptions.ConnectionClosedError:
        await unsubscribe_market_data(websocket)


async def market_data_publisher():
    while True:
        for subscription_id, subscription in subscriptions.items():

            instrument = subscription['instrument']
            quote = get_quote(instrument)
            message = format_market_data_update(quote)

            try:
                await subscription['websocket'].send(message)
            except:
                continue
        await asyncio.sleep(1)


async def update_quotes():
    while True:
        for instrument in ['IM', 'TG', 'BJ']:
            current_quote = get_quote(instrument)
            if current_quote is None:
                current_price = 60
            else:
                current_price = float(current_quote.offer)

            current_price += random.uniform(-0.5, 0.5)
            current_price = max(0, min(100, current_price))  # Ограничиваем цену между 0 и 100
            new_bid = str(current_price)
            new_offer = current_price

            conn = sqlite3.connect('quotes.db')
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
    conn = sqlite3.connect('orders.db')

    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS orders
                      (order_id TEXT, timestamp TEXT, instrument TEXT, side TEXT,
                       price REAL, volume REAL, status TEXT, last_changed TEXT)''')
    cursor.execute(f"SELECT * FROM orders WHERE instrument = '{instrument}' AND status = 'Active'")
    rows = cursor.fetchall()

    for row in rows:
        order_id, timestamp, _, side, price, volume, _,last_changed = row
        price = float(price)

        if side == 'Buy' and price >= current_price:
            cursor.execute(
                f"UPDATE orders SET status = 'Filled', last_changed = '{timestamp}' WHERE order_id = '{order_id}'")
        elif side == 'Sell' and price <= current_price:
            cursor.execute(
                f"UPDATE orders SET status = 'Filled', last_changed = '{timestamp}' WHERE order_id = '{order_id}'")

    conn.commit()
    conn.close()


start_server = websockets.serve(consumer, 'localhost', 8765)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.ensure_future(market_data_publisher())
asyncio.ensure_future(update_quotes())
asyncio.get_event_loop().run_forever()
