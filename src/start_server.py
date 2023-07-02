import asyncio

import websockets

from src.main import init, consumer, market_data_publisher, update_quotes

init()
start_server = websockets.serve(consumer, 'localhost', 8765)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.ensure_future(market_data_publisher())
asyncio.ensure_future(update_quotes())
asyncio.get_event_loop().run_forever()
