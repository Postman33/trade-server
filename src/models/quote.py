class Quote:
    def __init__(self, bid, offer, min_amount, max_amount, timestamp=None):
        self.bid = bid
        self.offer = offer
        self.min_amount = min_amount
        self.max_amount = max_amount
        self.timestamp = timestamp