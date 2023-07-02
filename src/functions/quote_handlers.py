import sqlite3

from src.models.quote import Quote
from src.functions.server_messages_handlers import *


def get_quote(instrument):
    conn = sqlite3.connect('md.db')
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM quotes WHERE instrument = '{instrument}' ORDER BY timestamp DESC LIMIT 1")
    row = cursor.fetchone()

    if row:
        _, timestamp, bid, offer, min_amount, max_amount = row
        return Quote(bid=str(bid), offer=offer, min_amount=min_amount, max_amount=max_amount, timestamp=timestamp)

    conn.close()


def get_quotes(instrument):
    conn = sqlite3.connect('md.db')
    cursor = conn.cursor()

    cursor.execute(f"SELECT * FROM quotes WHERE instrument = '{instrument}' ORDER BY timestamp DESC LIMIT 25")
    rows = cursor.fetchall()

    quotes = []
    for row in rows:
        tm, instrument, bid, offer, min_amount, max_amount = row
        quote = Quote(bid=str(bid), offer=offer, min_amount=min_amount, max_amount=max_amount, timestamp=tm)
        quotes.append(quote)

    conn.close()
    return quotes


async def get_current_quotes(websocket, data):
    instrument = data['instrument']
    quote = get_quote(instrument)  # Функция для получения текущих котировок по инструменту
    await websocket.send(format_current_quotes(quote))
