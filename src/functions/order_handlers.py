import datetime
import sqlite3
import uuid

from src.models.order import Order
from src.functions.server_messages_handlers import *


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


def create_order(order_id, timestamp, instrument, side, price, volume, status):
    conn = sqlite3.connect('md.db')
    cursor = conn.cursor()
    cursor.execute(
        f"INSERT INTO orders (order_id, timestamp, instrument, side, price, volume, status, last_changed) "
        f"VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (order_id, timestamp, instrument, side, price, volume, status, timestamp)
    )
    conn.commit()
    conn.close()


def cancel_existing_order(order_id):
    conn = sqlite3.connect('md.db')
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
    conn = sqlite3.connect('md.db')
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM orders")
    rows = cursor.fetchall()
    orders_info = []
    for row in rows:
        order_id, timestamp, instrument, side, price, volume, status, last_changed = row
        order = Order(order_id, timestamp, instrument, side, price, volume, status, last_changed)
        orders_info.append(order)
    conn.close()
    return orders_info


def get_orders_info_by_instrument(instrument):
    conn = sqlite3.connect('md.db')
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


async def get_order_info(websocket):
    orders_info = get_orders_info()  # Получение информации о заявках
    await websocket.send(format_order_info(orders_info))
