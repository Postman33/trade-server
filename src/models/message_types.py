from enum import Enum


class ClientMessages(Enum):
    SubscribeMarketData = 1
    UnsubscribeMarketData = 2
    GetOrderInfo = 3
    GetCurrentQuotes = 4
    PlaceOrder = 5
    CancelOrder = 6
    GetOrderByIdInfo = 7


class ServerMessages(Enum):
    SuccessInfo = 1
    ErrorInfo = 2
    CurrentQuotes = 3
    MarketDataUpdate = 4
    QuotesInfo = 5
    OrderInfo = 6