# Copyright 2010 New Relic, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import pytest
import openai
from conftest import (  # pylint: disable=E0611
    disabled_ai_monitoring_settings,
    disabled_ai_monitoring_streaming_settings,
)
from testing_support.fixtures import (
    reset_core_stats_engine,
    validate_attributes,
    validate_custom_event_count,
)
from testing_support.validators.validate_custom_events import validate_custom_events
from testing_support.validators.validate_transaction_metrics import (
    validate_transaction_metrics,
)

from newrelic.api.background_task import background_task
from newrelic.api.transaction import add_custom_attribute
from conftest import llm_token_count_callback_success, llm_token_count_callback_negative_return_val, llm_token_count_callback_non_int_return_val
from newrelic.api.ml_model import set_llm_token_count_callback

disabled_custom_insights_settings = {"custom_insights_events.enabled": False}

_test_openai_chat_completion_messages = (
    {"role": "system", "content": "You are a scientist."},
    {"role": "user", "content": "What is 212 degrees Fahrenheit converted to Celsius?"},
)

chat_completion_recorded_events = [
    (
        {"type": "LlmChatCompletionSummary"},
        {
            "id": None,  # UUID that varies with each run
            "appName": "Python Agent Test (mlmodel_openai)",
            "llm.conversation_id": "my-awesome-id",
            "llm.foo": "bar",
            "transaction_id": "transaction-id",
            "span_id": None,
            "trace_id": "trace-id",
            "request_id": "49dbbffbd3c3f4612aa48def69059ccd",
            "api_key_last_four_digits": "sk-CRET",
            "duration": None,  # Response time varies each test run
            "request.model": "gpt-3.5-turbo",
            "response.model": "gpt-3.5-turbo-0613",
            "response.organization": "new-relic-nkmd8b",
            "request.temperature": 0.7,
            "request.max_tokens": 100,
            "response.choices.finish_reason": "stop",
            "response.headers.llmVersion": "2020-10-01",
            "response.headers.ratelimitLimitRequests": 200,
            "response.headers.ratelimitLimitTokens": 40000,
            "response.headers.ratelimitResetTokens": "90ms",
            "response.headers.ratelimitResetRequests": "7m12s",
            "response.headers.ratelimitRemainingTokens": 39940,
            "response.headers.ratelimitRemainingRequests": 199,
            "vendor": "openAI",
            "ingest_source": "Python",
            "response.number_of_messages": 3,
        },
    ),
    (
        {"type": "LlmChatCompletionMessage"},
        {
            "id": "chatcmpl-87sb95K4EF2nuJRcTs43Tm9ntTemv-0",
            "appName": "Python Agent Test (mlmodel_openai)",
            "llm.conversation_id": "my-awesome-id",
            "llm.foo": "bar",
            "request_id": "49dbbffbd3c3f4612aa48def69059ccd",
            "span_id": None,
            "trace_id": "trace-id",
            "transaction_id": "transaction-id",
            "content": "You are a scientist.",
            "role": "system",
            "completion_id": None,
            "sequence": 0,
            "response.model": "gpt-3.5-turbo-0613",
            "vendor": "openAI",
            "ingest_source": "Python",
        },
    ),
    (
        {"type": "LlmChatCompletionMessage"},
        {
            "id": "chatcmpl-87sb95K4EF2nuJRcTs43Tm9ntTemv-1",
            "appName": "Python Agent Test (mlmodel_openai)",
            "llm.conversation_id": "my-awesome-id",
            "llm.foo": "bar",
            "request_id": "49dbbffbd3c3f4612aa48def69059ccd",
            "span_id": None,
            "trace_id": "trace-id",
            "transaction_id": "transaction-id",
            "content": "What is 212 degrees Fahrenheit converted to Celsius?",
            "role": "user",
            "completion_id": None,
            "sequence": 1,
            "response.model": "gpt-3.5-turbo-0613",
            "vendor": "openAI",
            "ingest_source": "Python",
        },
    ),
    (
        {"type": "LlmChatCompletionMessage"},
        {
            "id": "chatcmpl-87sb95K4EF2nuJRcTs43Tm9ntTemv-2",
            "appName": "Python Agent Test (mlmodel_openai)",
            "llm.conversation_id": "my-awesome-id",
            "llm.foo": "bar",
            "request_id": "49dbbffbd3c3f4612aa48def69059ccd",
            "span_id": None,
            "trace_id": "trace-id",
            "transaction_id": "transaction-id",
            "content": "212 degrees Fahrenheit is equal to 100 degrees Celsius.",
            "role": "assistant",
            "completion_id": None,
            "sequence": 2,
            "response.model": "gpt-3.5-turbo-0613",
            "vendor": "openAI",
            "is_response": True,
            "ingest_source": "Python",
        },
    ),
]


@reset_core_stats_engine()
@validate_custom_events(chat_completion_recorded_events)
# One summary event, one system message, one user message, and one response message from the assistant
@validate_custom_event_count(count=4)
@validate_transaction_metrics(
    name="test_chat_completion_stream:test_openai_chat_completion_sync_in_txn_with_llm_metadata",
    custom_metrics=[
        ("Supportability/Python/ML/OpenAI/%s" % openai.__version__, 1),
    ],
    background_task=True,
)
@validate_attributes("agent", ["llm"])
@background_task()
def test_openai_chat_completion_sync_in_txn_with_llm_metadata(set_trace_info):
    set_trace_info()
    add_custom_attribute("llm.conversation_id", "my-awesome-id")
    add_custom_attribute("llm.foo", "bar")
    add_custom_attribute("non_llm_attr", "python-agent")

    generator = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=_test_openai_chat_completion_messages,
        temperature=0.7,
        max_tokens=100,
        stream=True,
    )
    for resp in generator:
        assert resp


chat_completion_recorded_events_no_llm_metadata = [
    (
        {"type": "LlmChatCompletionSummary"},
        {
            "id": None,  # UUID that varies with each run
            "appName": "Python Agent Test (mlmodel_openai)",
            "transaction_id": "transaction-id",
            "span_id": None,
            "trace_id": "trace-id",
            "request_id": "49dbbffbd3c3f4612aa48def69059ccd",
            "api_key_last_four_digits": "sk-CRET",
            "duration": None,  # Response time varies each test run
            "request.model": "gpt-3.5-turbo",
            "response.model": "gpt-3.5-turbo-0613",
            "response.organization": "new-relic-nkmd8b",
            "request.temperature": 0.7,
            "request.max_tokens": 100,
            "response.choices.finish_reason": "stop",
            "response.headers.llmVersion": "2020-10-01",
            "response.headers.ratelimitLimitRequests": 200,
            "response.headers.ratelimitLimitTokens": 40000,
            "response.headers.ratelimitResetTokens": "90ms",
            "response.headers.ratelimitResetRequests": "7m12s",
            "response.headers.ratelimitRemainingTokens": 39940,
            "response.headers.ratelimitRemainingRequests": 199,
            "vendor": "openAI",
            "ingest_source": "Python",
            "response.number_of_messages": 3,
        },
    ),
    (
        {"type": "LlmChatCompletionMessage"},
        {
            "id": "chatcmpl-87sb95K4EF2nuJRcTs43Tm9ntTemv-0",
            "appName": "Python Agent Test (mlmodel_openai)",
            "request_id": "49dbbffbd3c3f4612aa48def69059ccd",
            "span_id": None,
            "trace_id": "trace-id",
            "transaction_id": "transaction-id",
            "content": "You are a scientist.",
            "role": "system",
            "completion_id": None,
            "sequence": 0,
            "response.model": "gpt-3.5-turbo-0613",
            "vendor": "openAI",
            "ingest_source": "Python",
        },
    ),
    (
        {"type": "LlmChatCompletionMessage"},
        {
            "id": "chatcmpl-87sb95K4EF2nuJRcTs43Tm9ntTemv-1",
            "appName": "Python Agent Test (mlmodel_openai)",
            "request_id": "49dbbffbd3c3f4612aa48def69059ccd",
            "span_id": None,
            "trace_id": "trace-id",
            "transaction_id": "transaction-id",
            "content": "What is 212 degrees Fahrenheit converted to Celsius?",
            "role": "user",
            "completion_id": None,
            "sequence": 1,
            "response.model": "gpt-3.5-turbo-0613",
            "vendor": "openAI",
            "ingest_source": "Python",
        },
    ),
    (
        {"type": "LlmChatCompletionMessage"},
        {
            "id": "chatcmpl-87sb95K4EF2nuJRcTs43Tm9ntTemv-2",
            "appName": "Python Agent Test (mlmodel_openai)",
            "request_id": "49dbbffbd3c3f4612aa48def69059ccd",
            "span_id": None,
            "trace_id": "trace-id",
            "transaction_id": "transaction-id",
            "content": "212 degrees Fahrenheit is equal to 100 degrees Celsius.",
            "role": "assistant",
            "completion_id": None,
            "sequence": 2,
            "response.model": "gpt-3.5-turbo-0613",
            "vendor": "openAI",
            "is_response": True,
            "ingest_source": "Python",
        },
    ),
]


@reset_core_stats_engine()
@validate_custom_events(chat_completion_recorded_events_no_llm_metadata)
# One summary event, one system message, one user message, and one response message from the assistant
@validate_custom_event_count(count=4)
@validate_transaction_metrics(
    "test_chat_completion_stream:test_openai_chat_completion_sync_in_txn_no_llm_metadata",
    scoped_metrics=[("Llm/completion/OpenAI/create", 1)],
    rollup_metrics=[("Llm/completion/OpenAI/create", 1)],
    background_task=True,
)
@background_task()
def test_openai_chat_completion_sync_in_txn_no_llm_metadata(set_trace_info):
    set_trace_info()
    generator = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=_test_openai_chat_completion_messages,
        temperature=0.7,
        max_tokens=100,
        stream=True,
    )
    for resp in generator:
        assert resp


chat_completion_token_recorded_events = [
    (
        {"type": "LlmChatCompletionSummary"},
        {
            "id": None,  # UUID that varies with each run
            "appName": "Python Agent Test (mlmodel_openai)",
            "llm.conversation_id": "my-awesome-id",
            "llm.foo": "bar",
            "transaction_id": "transaction-id",
            "span_id": None,
            "trace_id": "trace-id",
            "request_id": "49dbbffbd3c3f4612aa48def69059ccd",
            "api_key_last_four_digits": "sk-CRET",
            "duration": None,  # Response time varies each test run
            "request.model": "gpt-3.5-turbo",
            "response.model": "gpt-3.5-turbo-0613",
            "response.organization": "new-relic-nkmd8b",
            "request.temperature": 0.7,
            "request.max_tokens": 100,
            "response.choices.finish_reason": "stop",
            "response.headers.llmVersion": "2020-10-01",
            "response.headers.ratelimitLimitRequests": 200,
            "response.headers.ratelimitLimitTokens": 40000,
            "response.headers.ratelimitResetTokens": "90ms",
            "response.headers.ratelimitResetRequests": "7m12s",
            "response.headers.ratelimitRemainingTokens": 39940,
            "response.headers.ratelimitRemainingRequests": 199,
            "vendor": "openAI",
            "ingest_source": "Python",
            "response.number_of_messages": 3,
        },
    ),
    (
        {"type": "LlmChatCompletionMessage"},
        {
            "id": "chatcmpl-87sb95K4EF2nuJRcTs43Tm9ntTemv-0",
            "appName": "Python Agent Test (mlmodel_openai)",
            "llm.conversation_id": "my-awesome-id",
            "llm.foo": "bar",
            "token_count": 105,
            "request_id": "49dbbffbd3c3f4612aa48def69059ccd",
            "span_id": None,
            "trace_id": "trace-id",
            "transaction_id": "transaction-id",
            "content": "You are a scientist.",
            "role": "system",
            "completion_id": None,
            "sequence": 0,
            "response.model": "gpt-3.5-turbo-0613",
            "vendor": "openAI",
            "ingest_source": "Python",
        },
    ),
    (
        {"type": "LlmChatCompletionMessage"},
        {
            "id": "chatcmpl-87sb95K4EF2nuJRcTs43Tm9ntTemv-1",
            "appName": "Python Agent Test (mlmodel_openai)",
            "llm.conversation_id": "my-awesome-id",
            "llm.foo": "bar",
            "token_count": 105,
            "request_id": "49dbbffbd3c3f4612aa48def69059ccd",
            "span_id": None,
            "trace_id": "trace-id",
            "transaction_id": "transaction-id",
            "content": "What is 212 degrees Fahrenheit converted to Celsius?",
            "role": "user",
            "completion_id": None,
            "sequence": 1,
            "response.model": "gpt-3.5-turbo-0613",
            "vendor": "openAI",
            "ingest_source": "Python",
        },
    ),
    (
        {"type": "LlmChatCompletionMessage"},
        {
            "id": "chatcmpl-87sb95K4EF2nuJRcTs43Tm9ntTemv-2",
            "appName": "Python Agent Test (mlmodel_openai)",
            "llm.conversation_id": "my-awesome-id",
            "llm.foo": "bar",
            "token_count": 105,
            "request_id": "49dbbffbd3c3f4612aa48def69059ccd",
            "span_id": None,
            "trace_id": "trace-id",
            "transaction_id": "transaction-id",
            "content": "212 degrees Fahrenheit is equal to 100 degrees Celsius.",
            "role": "assistant",
            "completion_id": None,
            "sequence": 2,
            "response.model": "gpt-3.5-turbo-0613",
            "vendor": "openAI",
            "is_response": True,
            "ingest_source": "Python",
        },
    ),
]


@pytest.mark.parametrize("llm_token_callback", [llm_token_count_callback_success, llm_token_count_callback_negative_return_val, llm_token_count_callback_non_int_return_val])
@reset_core_stats_engine()
def test_openai_chat_completion_sync_with_token_count_callback(set_trace_info, llm_token_callback):
    if llm_token_callback.__name__ == "llm_token_count_callback_success":
        expected_events = chat_completion_recorded_events
    else:
        expected_events = chat_completion_recorded_events

    @validate_custom_event_count(count=4)
    @validate_custom_events(expected_events)
    @validate_transaction_metrics(
        "test_chat_completion_stream:test_openai_chat_completion_sync_with_token_count_callback.<locals>._test",
        scoped_metrics=[("Llm/completion/OpenAI/create", 1)],
        rollup_metrics=[("Llm/completion/OpenAI/create", 1)],
        background_task=True,
    )
    @validate_attributes("agent", ["llm"])
    @background_task()
    def _test():
        set_trace_info()
        add_custom_attribute("llm.conversation_id", "my-awesome-id")
        add_custom_attribute("llm.foo", "bar")
        add_custom_attribute("non_llm_attr", "python-agent")

        generator = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=_test_openai_chat_completion_messages,
            temperature=0.7,
            max_tokens=100,
            stream=True,
        )
        for resp in generator:
            assert resp

    _test()


@disabled_ai_monitoring_streaming_settings
@reset_core_stats_engine()
@validate_custom_event_count(count=0)
@validate_transaction_metrics(
    "test_chat_completion_stream:test_openai_chat_completion_sync_ai_monitoring_streaming_disabled",
    custom_metrics=[
        ("Supportability/Python/ML/OpenAI/%s" % openai.__version__, 1),
        ("Supportability/Python/ML/Streaming/Disabled", 1),
    ],
    scoped_metrics=[("Llm/completion/OpenAI/create", 1)],
    rollup_metrics=[("Llm/completion/OpenAI/create", 1)],
    background_task=True,
)
@background_task()
def test_openai_chat_completion_sync_ai_monitoring_streaming_disabled():
    add_custom_attribute("llm.conversation_id", "my-awesome-id")
    openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=_test_openai_chat_completion_messages,
        temperature=0.7,
        max_tokens=100,
        stream=True,
    )


@reset_core_stats_engine()
@validate_custom_event_count(count=0)
def test_openai_chat_completion_sync_outside_txn():
    add_custom_attribute("llm.conversation_id", "my-awesome-id")
    openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=_test_openai_chat_completion_messages,
        temperature=0.7,
        max_tokens=100,
        stream=True,
    )


@disabled_ai_monitoring_settings
@reset_core_stats_engine()
@validate_custom_event_count(count=0)
@background_task()
def test_openai_chat_completion_sync_ai_monitoring_disabled():
    add_custom_attribute("llm.conversation_id", "my-awesome-id")
    openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=_test_openai_chat_completion_messages,
        temperature=0.7,
        max_tokens=100,
        stream=True,
    )


@reset_core_stats_engine()
@validate_custom_events(chat_completion_recorded_events_no_llm_metadata)
@validate_custom_event_count(count=4)
@validate_transaction_metrics(
    "test_chat_completion_stream:test_openai_chat_completion_async_no_llm_metadata",
    scoped_metrics=[("Llm/completion/OpenAI/acreate", 1)],
    rollup_metrics=[("Llm/completion/OpenAI/acreate", 1)],
    background_task=True,
)
@background_task()
def test_openai_chat_completion_async_no_llm_metadata(loop, set_trace_info):
    set_trace_info()

    async def consumer():
        generator = await openai.ChatCompletion.acreate(
            model="gpt-3.5-turbo",
            messages=_test_openai_chat_completion_messages,
            temperature=0.7,
            max_tokens=100,
            stream=True,
        )
        async for resp in generator:
            assert resp

    loop.run_until_complete(consumer())


@reset_core_stats_engine()
@validate_custom_events(chat_completion_recorded_events)
@validate_custom_event_count(count=4)
@validate_transaction_metrics(
    "test_chat_completion_stream:test_openai_chat_completion_async_with_llm_metadata",
    scoped_metrics=[("Llm/completion/OpenAI/acreate", 1)],
    rollup_metrics=[("Llm/completion/OpenAI/acreate", 1)],
    background_task=True,
)
@validate_transaction_metrics(
    name="test_chat_completion_stream:test_openai_chat_completion_async_with_llm_metadata",
    custom_metrics=[
        ("Supportability/Python/ML/OpenAI/%s" % openai.__version__, 1),
    ],
    background_task=True,
)
@validate_attributes("agent", ["llm"])
@background_task()
def test_openai_chat_completion_async_with_llm_metadata(loop, set_trace_info):
    set_trace_info()
    add_custom_attribute("llm.conversation_id", "my-awesome-id")
    add_custom_attribute("llm.foo", "bar")
    add_custom_attribute("non_llm_attr", "python-agent")

    async def consumer():
        generator = await openai.ChatCompletion.acreate(
            model="gpt-3.5-turbo",
            messages=_test_openai_chat_completion_messages,
            temperature=0.7,
            max_tokens=100,
            stream=True,
        )
        async for resp in generator:
            assert resp

    loop.run_until_complete(consumer())


@pytest.mark.parametrize("llm_token_callback", [llm_token_count_callback_success, llm_token_count_callback_negative_return_val, llm_token_count_callback_non_int_return_val])
@reset_core_stats_engine()
def test_openai_chat_completion_async_with_token_count_callback(set_trace_info, loop, llm_token_callback):
    if llm_token_callback.__name__ == "llm_token_count_callback_success":
        expected_events = chat_completion_token_recorded_events
    else:
        expected_events = chat_completion_recorded_events

    @validate_custom_event_count(count=4)
    @validate_custom_events(expected_events)
    @validate_transaction_metrics(
        "test_chat_completion_stream:test_openai_chat_completion_async_with_token_count_callback.<locals>._test",
        scoped_metrics=[("Llm/completion/OpenAI/acreate", 1)],
        rollup_metrics=[("Llm/completion/OpenAI/acreate", 1)],
        background_task=True,
    )
    @validate_attributes("agent", ["llm"])
    @background_task()
    def _test():
        set_trace_info()
        add_custom_attribute("llm.conversation_id", "my-awesome-id")
        add_custom_attribute("llm.foo", "bar")
        add_custom_attribute("non_llm_attr", "python-agent")

        async def consumer():
            generator = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=_test_openai_chat_completion_messages,
                temperature=0.7,
                max_tokens=100,
                stream=True,
            )
            async for resp in generator:
                assert resp

        loop.run_until_complete(consumer())

    _test()

@disabled_ai_monitoring_streaming_settings
@reset_core_stats_engine()
@validate_custom_event_count(count=0)
@validate_transaction_metrics(
    name="test_chat_completion_stream:test_openai_chat_completion_async_ai_monitoring_streaming_disabled",
    custom_metrics=[
        ("Supportability/Python/ML/OpenAI/%s" % openai.__version__, 1),
        ("Supportability/Python/ML/Streaming/Disabled", 1),
    ],
    scoped_metrics=[("Llm/completion/OpenAI/acreate", 1)],
    rollup_metrics=[("Llm/completion/OpenAI/acreate", 1)],
    background_task=True,
)
@background_task()
def test_openai_chat_completion_async_ai_monitoring_streaming_disabled(loop):
    async def consumer():
        generator = await openai.ChatCompletion.acreate(
            model="gpt-3.5-turbo",
            messages=_test_openai_chat_completion_messages,
            temperature=0.7,
            max_tokens=100,
            stream=True,
        )
        async for resp in generator:
            assert resp

    loop.run_until_complete(consumer())


@reset_core_stats_engine()
@validate_custom_event_count(count=0)
def test_openai_chat_completion_async_outside_transaction(loop):
    async def consumer():
        generator = await openai.ChatCompletion.acreate(
            model="gpt-3.5-turbo",
            messages=_test_openai_chat_completion_messages,
            temperature=0.7,
            max_tokens=100,
            stream=True,
        )
        async for resp in generator:
            assert resp

    loop.run_until_complete(consumer())


@disabled_ai_monitoring_settings
@reset_core_stats_engine()
@validate_custom_event_count(count=0)
@background_task()
def test_openai_chat_completion_async_ai_monitoring_disabled(loop):
    async def consumer():
        generator = await openai.ChatCompletion.acreate(
            model="gpt-3.5-turbo",
            messages=_test_openai_chat_completion_messages,
            temperature=0.7,
            max_tokens=100,
            stream=True,
        )
        async for resp in generator:
            assert resp

    loop.run_until_complete(consumer())


def test_openai_chat_completion_functions_marked_as_wrapped_for_sdk_compatibility():
    assert openai.ChatCompletion._nr_wrapped
    assert openai.util.convert_to_openai_object._nr_wrapped