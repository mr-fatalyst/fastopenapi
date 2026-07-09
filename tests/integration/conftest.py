import pytest

from tests.integration.clients import CLIENT_FACTORIES

VARIANTS = list(CLIENT_FACTORIES)


@pytest.fixture(params=VARIANTS)
def client(request):
    factory = CLIENT_FACTORIES[request.param]
    try:
        instance = factory()
    except ImportError as exc:
        pytest.skip(f"{request.param}: framework not installed ({exc})")
    try:
        yield instance
    finally:
        instance.close()
