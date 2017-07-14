import pika
import pytest
import six
import tornado

from newrelic.api.background_task import background_task

from conftest import (QUEUE, QUEUE_2, EXCHANGE, EXCHANGE_2, CORRELATION_ID,
        REPLY_TO, HEADERS, BODY)
from testing_support.fixtures import (capture_transaction_metrics,
        validate_transaction_metrics, validate_tt_collector_json,
        function_not_called, override_application_settings)
from testing_support.settings import rabbitmq_settings


DB_SETTINGS = rabbitmq_settings()

_message_broker_tt_params = {
    'queue_name': QUEUE,
    'routing_key': QUEUE,
    'correlation_id': CORRELATION_ID,
    'reply_to': REPLY_TO,
    'headers': HEADERS.copy(),
}


class MyIOLoop(tornado.ioloop.IOLoop.configured_class()):
    def handle_callback_exception(self, *args, **kwargs):
        raise


tornado.ioloop.IOLoop.configure(MyIOLoop)

parametrized_connection = pytest.mark.parametrize('ConnectionClass',
        [pika.SelectConnection, pika.TornadoConnection])


_test_select_conn_basic_get_inside_txn_metrics = [
    ('MessageBroker/RabbitMQ/Exchange/Produce/Named/%s' % EXCHANGE, None),
    ('MessageBroker/RabbitMQ/Exchange/Consume/Named/%s' % EXCHANGE, 1),
]

if six.PY3:
    _test_select_conn_basic_get_inside_txn_metrics.append(
        (('Function/test_pika_async_connection_consume:'
          'test_async_connection_basic_get_inside_txn.'
          '<locals>.on_message'), 1))
else:
    _test_select_conn_basic_get_inside_txn_metrics.append(
        ('Function/test_pika_async_connection_consume:on_message', 1))


@parametrized_connection
@validate_transaction_metrics(
        ('test_pika_async_connection_consume:'
                'test_async_connection_basic_get_inside_txn'),
        scoped_metrics=_test_select_conn_basic_get_inside_txn_metrics,
        rollup_metrics=_test_select_conn_basic_get_inside_txn_metrics,
        background_task=True)
@validate_tt_collector_json(message_broker_params=_message_broker_tt_params)
@background_task()
def test_async_connection_basic_get_inside_txn(producer, ConnectionClass):
    def on_message(channel, method_frame, header_frame, body):
        assert method_frame
        assert body == BODY
        channel.basic_ack(method_frame.delivery_tag)
        channel.close()
        connection.close()
        connection.ioloop.stop()

    def on_open_channel(channel):
        channel.basic_get(callback=on_message, queue=QUEUE)

    def on_open_connection(connection):
        connection.channel(on_open_channel)

    connection = ConnectionClass(
            pika.ConnectionParameters(DB_SETTINGS['host']),
            on_open_callback=on_open_connection)

    try:
        connection.ioloop.start()
    except:
        connection.close()
        connection.ioloop.stop()
        raise


@parametrized_connection
def test_select_connection_basic_get_outside_txn(producer, ConnectionClass):
    metrics_list = []

    @capture_transaction_metrics(metrics_list)
    def test_basic_get():
        def on_message(channel, method_frame, header_frame, body):
            assert method_frame
            assert body == BODY
            channel.basic_ack(method_frame.delivery_tag)
            channel.close()
            connection.close()
            connection.ioloop.stop()

        def on_open_channel(channel):
            channel.basic_get(callback=on_message, queue=QUEUE)

        def on_open_connection(connection):
            connection.channel(on_open_channel)

        connection = ConnectionClass(
                pika.ConnectionParameters(DB_SETTINGS['host']),
                on_open_callback=on_open_connection)

        try:
            connection.ioloop.start()
        except:
            connection.close()
            connection.ioloop.stop()
            raise

    test_basic_get()

    # Confirm that no metrics have been created. This is because no background
    # task should be created for basic_get actions.
    assert not metrics_list


_test_select_conn_basic_get_inside_txn_no_callback_metrics = [
    ('MessageBroker/RabbitMQ/Exchange/Produce/Named/%s' % EXCHANGE, None),
    ('MessageBroker/RabbitMQ/Exchange/Consume/Named/%s' % EXCHANGE, None),
]


@parametrized_connection
@validate_transaction_metrics(
    ('test_pika_async_connection_consume:'
            'test_async_connection_basic_get_inside_txn_no_callback'),
    scoped_metrics=_test_select_conn_basic_get_inside_txn_no_callback_metrics,
    rollup_metrics=_test_select_conn_basic_get_inside_txn_no_callback_metrics,
    background_task=True)
@validate_tt_collector_json(message_broker_params=_message_broker_tt_params)
@background_task()
def test_async_connection_basic_get_inside_txn_no_callback(producer,
        ConnectionClass):
    def on_open_channel(channel):
        channel.basic_get(callback=None, queue=QUEUE)
        channel.close()
        connection.close()
        connection.ioloop.stop()

    def on_open_connection(connection):
        connection.channel(on_open_channel)

    connection = ConnectionClass(
            pika.ConnectionParameters(DB_SETTINGS['host']),
            on_open_callback=on_open_connection)

    try:
        connection.ioloop.start()
    except:
        connection.close()
        connection.ioloop.stop()
        raise


_test_async_connection_basic_get_empty_metrics = [
    ('MessageBroker/RabbitMQ/Exchange/Produce/Named/%s' % EXCHANGE, None),
    ('MessageBroker/RabbitMQ/Exchange/Consume/Named/%s' % EXCHANGE, None),
]


@parametrized_connection
@validate_transaction_metrics(
        ('test_pika_async_connection_consume:'
                'test_async_connection_basic_get_empty'),
        scoped_metrics=_test_async_connection_basic_get_empty_metrics,
        rollup_metrics=_test_async_connection_basic_get_empty_metrics,
        background_task=True)
@validate_tt_collector_json(message_broker_params=_message_broker_tt_params)
@background_task()
def test_async_connection_basic_get_empty(ConnectionClass):
    QUEUE = 'test_async_empty'

    def on_message(channel, method_frame, header_frame, body):
        assert False, body.decode('UTF-8')

    def on_open_channel(channel):
        channel.basic_get(callback=on_message, queue=QUEUE)
        channel.close()
        connection.close()
        connection.ioloop.stop()

    def on_open_connection(connection):
        connection.channel(on_open_channel)

    connection = ConnectionClass(
            pika.ConnectionParameters(DB_SETTINGS['host']),
            on_open_callback=on_open_connection)

    try:
        connection.ioloop.start()
    except:
        connection.close()
        connection.ioloop.stop()
        raise


_test_select_conn_basic_consume_in_txn_metrics = [
    ('MessageBroker/RabbitMQ/Exchange/Produce/Named/%s' % EXCHANGE, None),
    ('MessageBroker/RabbitMQ/Exchange/Consume/Named/%s' % EXCHANGE, None),
]

if six.PY3:
    _test_select_conn_basic_consume_in_txn_metrics.append(
        (('Function/test_pika_async_connection_consume:'
          'test_async_connection_basic_consume_inside_txn.'
          '<locals>.on_message'), 1))
else:
    _test_select_conn_basic_consume_in_txn_metrics.append(
        ('Function/test_pika_async_connection_consume:on_message', 1))


@parametrized_connection
@validate_transaction_metrics(
        ('test_pika_async_connection_consume:'
                'test_async_connection_basic_consume_inside_txn'),
        scoped_metrics=_test_select_conn_basic_consume_in_txn_metrics,
        rollup_metrics=_test_select_conn_basic_consume_in_txn_metrics,
        background_task=True)
@validate_tt_collector_json(message_broker_params=_message_broker_tt_params)
@background_task()
def test_async_connection_basic_consume_inside_txn(producer, ConnectionClass):
    def on_message(channel, method_frame, header_frame, body):
        assert hasattr(method_frame, '_nr_start_time')
        assert body == BODY
        channel.basic_ack(method_frame.delivery_tag)
        channel.close()
        connection.close()
        connection.ioloop.stop()

    def on_open_channel(channel):
        channel.basic_consume(on_message, QUEUE)

    def on_open_connection(connection):
        connection.channel(on_open_channel)

    connection = ConnectionClass(
            pika.ConnectionParameters(DB_SETTINGS['host']),
            on_open_callback=on_open_connection)

    try:
        connection.ioloop.start()
    except:
        connection.close()
        connection.ioloop.stop()
        raise


_test_select_conn_basic_consume_two_exchanges = [
    ('MessageBroker/RabbitMQ/Exchange/Produce/Named/%s' % EXCHANGE, None),
    ('MessageBroker/RabbitMQ/Exchange/Consume/Named/%s' % EXCHANGE, None),
    ('MessageBroker/RabbitMQ/Exchange/Produce/Named/%s' % EXCHANGE_2, None),
    ('MessageBroker/RabbitMQ/Exchange/Consume/Named/%s' % EXCHANGE_2, None),
]

if six.PY3:
    _test_select_conn_basic_consume_two_exchanges.append(
        (('Function/test_pika_async_connection_consume:'
          'test_async_connection_basic_consume_two_exchanges.'
          '<locals>.on_message_1'), 1))
    _test_select_conn_basic_consume_two_exchanges.append(
        (('Function/test_pika_async_connection_consume:'
          'test_async_connection_basic_consume_two_exchanges.'
          '<locals>.on_message_2'), 1))
else:
    _test_select_conn_basic_consume_two_exchanges.append(
        ('Function/test_pika_async_connection_consume:on_message_1', 1))
    _test_select_conn_basic_consume_two_exchanges.append(
        ('Function/test_pika_async_connection_consume:on_message_2', 1))


@parametrized_connection
@validate_transaction_metrics(
        ('test_pika_async_connection_consume:'
                'test_async_connection_basic_consume_two_exchanges'),
        scoped_metrics=_test_select_conn_basic_consume_two_exchanges,
        rollup_metrics=_test_select_conn_basic_consume_two_exchanges,
        background_task=True)
@background_task()
def test_async_connection_basic_consume_two_exchanges(producer, producer_2,
        ConnectionClass):
    global events_received
    events_received = 0

    def on_message_1(channel, method_frame, header_frame, body):
        channel.basic_ack(method_frame.delivery_tag)
        assert hasattr(method_frame, '_nr_start_time')
        assert body == BODY

        global events_received
        events_received += 1

        if events_received == 2:
            channel.close()
            connection.close()
            connection.ioloop.stop()

    def on_message_2(channel, method_frame, header_frame, body):
        channel.basic_ack(method_frame.delivery_tag)
        assert hasattr(method_frame, '_nr_start_time')
        assert body == BODY

        global events_received
        events_received += 1

        if events_received == 2:
            channel.close()
            connection.close()
            connection.ioloop.stop()

    def on_open_channel(channel):
        channel.basic_consume(on_message_1, QUEUE)
        channel.basic_consume(on_message_2, QUEUE_2)

    def on_open_connection(connection):
        connection.channel(on_open_channel)

    connection = ConnectionClass(
            pika.ConnectionParameters(DB_SETTINGS['host']),
            on_open_callback=on_open_connection)

    try:
        connection.ioloop.start()
    except:
        connection.close()
        connection.ioloop.stop()
        raise


# This should not create a transaction
@function_not_called('newrelic.core.stats_engine',
                'StatsEngine.record_transaction')
@override_application_settings({'debug.record_transaction_failure': True})
def test_tornado_connection_basic_consume_outside_transaction(producer):
    def on_message(channel, method_frame, header_frame, body):
        assert hasattr(method_frame, '_nr_start_time')
        assert body == BODY
        channel.basic_ack(method_frame.delivery_tag)
        channel.close()
        connection.close()
        connection.ioloop.stop()

    def on_open_channel(channel):
        channel.basic_consume(on_message, QUEUE)

    def on_open_connection(connection):
        connection.channel(on_open_channel)

    connection = pika.TornadoConnection(
            pika.ConnectionParameters(DB_SETTINGS['host']),
            on_open_callback=on_open_connection)

    try:
        connection.ioloop.start()
    except:
        connection.close()
        connection.ioloop.stop()
        raise


if six.PY3:
    _test_select_connection_consume_outside_txn_metrics = [
        (('Function/test_pika_async_connection_consume:'
          'test_select_connection_basic_consume_outside_transaction.'
          '<locals>.on_message'), 1)]
else:
    _test_select_connection_consume_outside_txn_metrics = [
        ('Function/test_pika_async_connection_consume:on_message', 1)]


# This should create a transaction
@validate_transaction_metrics(
        'Named/%s' % EXCHANGE,
        scoped_metrics=_test_select_connection_consume_outside_txn_metrics,
        rollup_metrics=_test_select_connection_consume_outside_txn_metrics,
        background_task=True,
        group='Message/RabbitMQ/Exchange')
def test_select_connection_basic_consume_outside_transaction(producer):
    def on_message(channel, method_frame, header_frame, body):
        assert hasattr(method_frame, '_nr_start_time')
        assert body == BODY
        channel.basic_ack(method_frame.delivery_tag)
        channel.close()
        connection.close()
        connection.ioloop.stop()

    def on_open_channel(channel):
        channel.basic_consume(on_message, QUEUE)

    def on_open_connection(connection):
        connection.channel(on_open_channel)

    connection = pika.SelectConnection(
            pika.ConnectionParameters(DB_SETTINGS['host']),
            on_open_callback=on_open_connection)

    try:
        connection.ioloop.start()
    except:
        connection.close()
        connection.ioloop.stop()
        raise