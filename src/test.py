import json
from unittest.mock import MagicMock, patch

from src.functions.order_handlers import cancel_existing_order, create_order
from src.main import format_success_info, format_error_info, process_orders
from src.models.message_types import *
from unittest.mock import call


def test_format_success_info():
    message = 'Success message'
    expected_output = {
        'messageType': ServerMessages.SuccessInfo.value,
        'message': message

    }

    assert format_success_info(message) == json.dumps(expected_output)


def test_format_error_info():
    reason = 'Error reason'
    expected_output = {
        'messageType': ServerMessages.ErrorInfo.value,
        'message': reason
    }

    assert format_error_info(reason) == json.dumps(expected_output)


@patch('main.sqlite3.connect')
def test_create_order(mock_connect):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_connect.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor

    order_id = '75'
    timestamp = '2023-07-01 00:00:00'
    instrument = 'Instrument1'
    side = 'Buy'
    price = 100.0
    volume = 1.0
    status = 'Active'

    create_order(order_id, timestamp, instrument, side, price, volume, status)

    mock_connect.assert_called_once_with('md.db')
    mock_conn.cursor.assert_called_once()
    mock_cursor.execute.assert_called_once_with(
        f"INSERT INTO orders (order_id, timestamp, instrument, side, price, volume, status, last_changed) "
        f"VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (order_id, timestamp, instrument, side, price, volume, status, timestamp)
    )
    mock_conn.commit.assert_called_once()
    mock_conn.close.assert_called_once()


@patch('main.sqlite3.connect')
def test_cancel_existing_order(mock_connect):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_connect.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor

    mock_cursor.fetchone.return_value = ['order_id', 'timestamp', 'instrument', 'side', 'price', 'volume', 'Active',
                                         'last_changed']

    order_id = '1'

    result = cancel_existing_order(order_id)

    mock_connect.assert_called_once()
    mock_conn.cursor.assert_called_once_with()
    mock_cursor.execute.assert_called()
    # Проверьте, что функция execute вызывалась дважды и проверьте, соответствуют ли SQL-запросы ожиданиям
    assert mock_cursor.execute.call_count == 2
    assert mock_cursor.execute.call_args_list[0] == call(f"SELECT * FROM orders WHERE order_id = '{order_id}'")
    assert 'UPDATE orders SET status = \'Cancelled\'' in mock_cursor.execute.call_args_list[1][0][0]


@patch('main.sqlite3.connect')
def test_cancel_existing_order_failed(mock_connect):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_connect.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor

    mock_cursor.fetchone.return_value = None

    order_id = '1'

    result = cancel_existing_order(order_id)

    mock_connect.assert_called_once()
    mock_conn.cursor.assert_called_once_with()
    mock_cursor.execute.assert_called_with(f"SELECT * FROM orders WHERE order_id = '{order_id}'")
    mock_conn.close.assert_called_once()
    assert result is False


@patch('main.sqlite3.connect')
def test_process_orders(mock_connect):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_connect.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor

    instrument = 'TM'
    current_price = 100.0

    mock_cursor.fetchall.return_value = [
        ('order_id1', '2023-07-01 00:00:00', instrument, 'Buy', 106.0, 1.0, 'Active', '2023-07-01 00:00:00'),
        ('order_id2', '2023-07-01 00:00:00', instrument, 'Sell', 98.0, 1.0, 'Active', '2023-07-01 00:00:00'),
        ('order_id3', '2023-07-01 00:00:00', instrument, 'Buy', 95, 1.0, 'Active', '2023-07-01 00:00:00'),
        ('order_id4', '2023-07-01 00:00:00', instrument, 'Sell', 105.0, 1.0, 'Active', '2023-07-01 00:00:00'),
    ]

    process_orders(instrument, current_price)

    # Проверяем, что connect был вызван
    mock_connect.assert_called_once_with('md.db')
    # Проверяем, что cursor был вызван
    mock_conn.cursor.assert_called_once()
    # Проверяем вызов SELECT запроса
    mock_cursor.execute.assert_any_call(f"SELECT * FROM orders WHERE instrument = '{instrument}' AND status = 'Active'")

    # Проверяем, что UPDATE вызван дважды (для покупки и продажи)
    assert mock_cursor.execute.call_count == 3

    update_calls = [call for call in mock_cursor.execute.call_args_list if 'UPDATE' in call[0][0]]
    assert len(update_calls) == 2

    # Проверяем, что UPDATE был вызван с правильными параметрами
    for call in update_calls:
        assert "UPDATE orders SET status = 'Filled'" in call[0][0]
        assert "WHERE order_id = 'order_id1'" in call[0][0] or "WHERE order_id = 'order_id2'" in call[0][0]

    # Проверяем, что commit был вызван
    mock_conn.commit.assert_called_once()
    # Проверяем, что close был вызван
    mock_conn.close.assert_called_once()
