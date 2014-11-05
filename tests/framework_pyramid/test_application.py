import pytest

from testing_support.fixtures import (validate_transaction_metrics,
    validate_transaction_errors, override_application_settings)

from newrelic.packages import six

def target_application():
    # We need to delay Pyramid application creation because of ordering
    # issues whereby the agent needs to be initialised before Pyramid is
    # imported and the routes configured. Normally pytest only runs the
    # global fixture which will initialise the agent after each test
    # file is imported, which is too late. We also can't do application
    # creation within a function as Pyramid relies on view handlers being
    # at global scope, so import it from a separate module.

    from _test_application import _test_application
    return _test_application

_test_application_index_scoped_metrics = [
        ('Python/WSGI/Application', 1),
        ('Python/WSGI/Response', 1),
        ('Python/WSGI/Finalize', 1),
        ('Function/pyramid.router:Router.__call__', 1),
        ('Function/_test_application:home_view', 1)]

@validate_transaction_errors(errors=[])
@validate_transaction_metrics('_test_application:home_view',
        scoped_metrics=_test_application_index_scoped_metrics)
def test_application_index():
    application = target_application()
    response = application.get('')
    response.mustcontain('INDEX RESPONSE')

_test_not_found_as_exception_response_scoped_metrics = [
        ('Python/WSGI/Application', 1),
        ('Python/WSGI/Response', 1),
        ('Python/WSGI/Finalize', 1),
        ('Function/pyramid.router:Router.__call__', 1),
        ('Function/pyramid.httpexceptions:default_exceptionresponse_view', 1),
        ('Function/_test_application:not_found_exception_response', 1)]

@validate_transaction_errors(errors=[])
#@validate_transaction_metrics('_test_application:not_found_exception_response',
#        scoped_metrics=_test_not_found_as_exception_response_scoped_metrics)
@validate_transaction_metrics(
        'pyramid.httpexceptions:default_exceptionresponse_view',
        scoped_metrics=_test_not_found_as_exception_response_scoped_metrics)
def test_not_found_as_exception_response():
    application = target_application()
    application.get('/nf1', status=404)

_test_not_found_raises_NotFound_scoped_metrics = [
        ('Python/WSGI/Application', 1),
        ('Python/WSGI/Response', 1),
        ('Python/WSGI/Finalize', 1),
        ('Function/pyramid.router:Router.__call__', 1),
        ('Function/pyramid.httpexceptions:default_exceptionresponse_view', 1),
        ('Function/_test_application:raise_not_found', 1)]

@validate_transaction_errors(errors=[])
#@validate_transaction_metrics('_test_application:raise_not_found',
#        scoped_metrics=_test_not_found_raises_NotFound_scoped_metrics)
@validate_transaction_metrics(
        'pyramid.httpexceptions:default_exceptionresponse_view',
        scoped_metrics=_test_not_found_raises_NotFound_scoped_metrics)
def test_application_not_found_raises_NotFound():
    application = target_application()
    application.get('/nf2', status=404)

_test_not_found_returns_NotFound_scoped_metrics = [
        ('Python/WSGI/Application', 1),
        ('Python/WSGI/Response', 1),
        ('Python/WSGI/Finalize', 1),
        ('Function/pyramid.router:Router.__call__', 1),
        ('Function/_test_application:return_not_found', 1)]

@validate_transaction_errors(errors=[])
@validate_transaction_metrics('_test_application:return_not_found',
        scoped_metrics=_test_not_found_returns_NotFound_scoped_metrics)
def test_application_not_found_returns_NotFound():
    application = target_application()
    application.get('/nf3', status=404)

_test_unexpected_exception_scoped_metrics = [
        ('Python/WSGI/Application', 1),
        ('Function/pyramid.router:Router.__call__', 1),
        ('Function/_test_application:error', 1)]

if six.PY3:
    _test_unexpected_exception_errors = ['builtins:RuntimeError']
else:
    _test_unexpected_exception_errors = ['exceptions:RuntimeError']

@validate_transaction_errors(
        errors=_test_unexpected_exception_errors)
@validate_transaction_metrics('_test_application:error',
        scoped_metrics=_test_unexpected_exception_scoped_metrics)
def test_application_unexpected_exception():
    application = target_application()
    with pytest.raises(RuntimeError):
        application.get('/error', status=500)

_test_redirect_scoped_metrics = [
        ('Python/WSGI/Application', 1),
        ('Python/WSGI/Response', 1),
        ('Python/WSGI/Finalize', 1),
        ('Function/pyramid.router:Router.__call__', 1),
        ('Function/pyramid.httpexceptions:default_exceptionresponse_view', 1),
        ('Function/_test_application:redirect', 1)]

@validate_transaction_errors(errors=[])
#@validate_transaction_metrics('_test_application:redirect',
#        scoped_metrics=_test_redirect_scoped_metrics)
@validate_transaction_metrics(
        'pyramid.httpexceptions:default_exceptionresponse_view',
        scoped_metrics=_test_redirect_scoped_metrics)
def test_application_redirect():
    application = target_application()
    application.get('/redirect', status=302)

_test_resource_get_scoped_metrics = [
        ('Python/WSGI/Application', 1),
        ('Python/WSGI/Response', 1),
        ('Python/WSGI/Finalize', 1),
        ('Function/pyramid.router:Router.__call__', 1),
        ('Function/_test_application:RestView', 1),
        ('Function/_test_application:RestView.get', 1)]

@validate_transaction_errors(errors=[])
@validate_transaction_metrics('_test_application:RestView.get',
        scoped_metrics=_test_resource_get_scoped_metrics)
def test_application_rest_get():
    application = target_application()
    response = application.get('/rest')
    response.mustcontain('Called GET')

_test_resource_post_scoped_metrics = [
        ('Python/WSGI/Application', 1),
        ('Python/WSGI/Response', 1),
        ('Python/WSGI/Finalize', 1),
        ('Function/pyramid.router:Router.__call__', 1),
        ('Function/_test_application:RestView', 2),
        ('Function/_test_application:RestView.post', 1)]

@validate_transaction_errors(errors=[])
@validate_transaction_metrics('_test_application:RestView.post',
        scoped_metrics=_test_resource_post_scoped_metrics)
def test_application_rest_post():
    application = target_application()
    response = application.post('/rest') # Raises PredicateMismatch
    response.mustcontain('Called POST')

_test_html_insertion_settings = {
    'browser_monitoring.enabled': True,
    'browser_monitoring.auto_instrument': True,
    'js_agent_loader': u'<!-- NREUM HEADER -->',
}

@override_application_settings(_test_html_insertion_settings)
def test_html_insertion():
    application = target_application()
    response = application.get('/html_insertion', status=200)

    # The 'NREUM HEADER' value comes from our override for the header.
    # The 'NREUM.info' value comes from the programmatically generated
    # footer added by the agent.

    response.mustcontain('NREUM HEADER', 'NREUM.info')