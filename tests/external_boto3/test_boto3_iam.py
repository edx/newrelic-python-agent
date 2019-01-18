import sys
import uuid

import boto3
import moto

from newrelic.api.background_task import background_task
from testing_support.fixtures import (validate_transaction_metrics,
        validate_tt_segment_params, override_application_settings)
from testing_support.validators.validate_span_events import (
        validate_span_events)

MOTO_VERSION = tuple(int(v) for v in moto.__version__.split('.'))

# patch earlier versions of moto to support py37
if sys.version_info >= (3, 7) and MOTO_VERSION <= (1, 3, 1):
    import re
    moto.packages.responses.responses.re._pattern_type = re.Pattern

AWS_ACCESS_KEY_ID = 'AAAAAAAAAAAACCESSKEY'
AWS_SECRET_ACCESS_KEY = 'AAAAAASECRETKEY'

TEST_USER = 'python-agent-test-%s' % uuid.uuid4()

_iam_scoped_metrics = [
    ('External/iam.amazonaws.com/botocore/POST', 3),
]

_iam_rollup_metrics = [
    ('External/all', 3),
    ('External/allOther', 3),
    ('External/iam.amazonaws.com/all', 3),
    ('External/iam.amazonaws.com/botocore/POST', 3),
]


@override_application_settings({'distributed_tracing.enabled': True})
@validate_span_events(expected_agents=('aws.requestId',), count=3)
@validate_span_events(exact_agents={'aws.operation': 'CreateUser'}, count=1)
@validate_span_events(exact_agents={'aws.operation': 'GetUser'}, count=1)
@validate_span_events(exact_agents={'aws.operation': 'DeleteUser'}, count=1)
@validate_tt_segment_params(present_params=('aws.requestId',))
@validate_transaction_metrics(
        'test_boto3_iam:test_iam',
        scoped_metrics=_iam_scoped_metrics,
        rollup_metrics=_iam_rollup_metrics,
        background_task=True)
@background_task()
@moto.mock_iam
def test_iam():
    iam = boto3.client(
            'iam',
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    )

    # Create user
    resp = iam.create_user(UserName=TEST_USER)
    assert resp['ResponseMetadata']['HTTPStatusCode'] == 200

    # Get the user
    resp = iam.get_user(UserName=TEST_USER)
    assert resp['ResponseMetadata']['HTTPStatusCode'] == 200
    assert resp['User']['UserName'] == TEST_USER

    # Delete the user
    resp = iam.delete_user(UserName=TEST_USER)
    assert resp['ResponseMetadata']['HTTPStatusCode'] == 200
