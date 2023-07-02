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