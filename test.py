import json

import pytest
import asyncio
from unittest.mock import MagicMock, patch
from sqlite3 import Error as SQLiteError
from main import format_success_info, format_error_info, create_order, cancel_existing_order

from unittest.mock import call

def test_format_success_info():
    message = 'Success message'
    expected_output = {
        'messageType': 'SuccessInfo',
        'message': message

    }

    assert format_success_info(message) == json.dumps(expected_output)

def test_format_error_info():
    reason = 'Error reason'
    expected_output = {
        'messageType': 'ErrorInfo',
        'message': reason
    }

    assert format_error_info(reason) == json.dumps(expected_output)


@patch('main.sqlite3.connect')  # Замените 'your_script' на имя вашего скрипта
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

    mock_connect.assert_called_once()
    mock_conn.cursor.assert_called_once()
    mock_cursor.execute.assert_called_once()
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


@patch('main.sqlite3.connect')  # Замените 'your_script' на имя вашего скрипта
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