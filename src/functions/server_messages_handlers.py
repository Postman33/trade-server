from src.models.message_types import ServerMessages, ClientMessages

import json


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


def format_success_info(message):
    return json.dumps({
        'messageType': ServerMessages.SuccessInfo.value,
        'message': message
    })


def format_error_info(reason):
    return json.dumps({
        'messageType': ServerMessages.ErrorInfo.value,
        'message': reason
    })


def format_market_data_update(data):
    return json.dumps({
        'messageType': ServerMessages.MarketDataUpdate.value,
        'message': data.__dict__
    })


def format_quotes_info(data):
    serialized_quotes = [quote.__dict__ for quote in data]
    return json.dumps({
        'messageType': ServerMessages.QuotesInfo.value,
        'message': serialized_quotes
    })


def format_order_info(data):
    serialized_orders = [serialize_order(order) for order in data]
    return json.dumps({
        'messageType': ServerMessages.OrderInfo.value,
        'message': serialized_orders
    })


def format_current_quotes(data):
    return json.dumps({
        'messageType': ServerMessages.CurrentQuotes.value,
        'message': data.__dict__
    })
