from unittest.mock import Mock

import pytest

from fastopenapi.core.types import RequestData
from fastopenapi.routers.common import RequestEnvelope
from fastopenapi.routers.django.extractors import DjangoAsyncRequestDataExtractor


class TestDjangoAsyncRequestDataExtractor:

    @pytest.mark.asyncio
    async def test_get_body_calls_sync_method(self):
        """Test async body extraction calls sync method"""
        request = Mock()
        request.body = b'{"key": "value"}'

        result = await DjangoAsyncRequestDataExtractor._get_body(request)

        assert result == {"key": "value"}

    @pytest.mark.asyncio
    async def test_get_form_data_calls_sync_method(self):
        """Test async form data extraction calls sync method"""
        request = Mock()
        request.POST = Mock()
        request.POST.keys = Mock(return_value=["field"])
        request.POST.getlist = Mock(return_value=["value"])

        result = await DjangoAsyncRequestDataExtractor._get_form_data(request)

        assert result == {"field": "value"}

    @pytest.mark.asyncio
    async def test_get_files_calls_sync_method(self):
        """Test async files extraction calls sync method"""
        request = Mock()

        result = await DjangoAsyncRequestDataExtractor._get_files(request)

        assert result == {}

    @pytest.mark.asyncio
    async def test_extract_request_data_full(self):
        """Test full async request data extraction"""
        request = Mock()
        request.path_params = {"id": "123"}
        request.GET = Mock()
        request.GET.keys = Mock(return_value=["param"])
        request.GET.getlist = Mock(return_value=["value"])
        request.headers = {"Content-Type": "application/json"}
        request.COOKIES = {"session": "abc"}
        request.body = b'{"data": "test"}'
        request.POST = Mock()
        request.POST.keys = Mock(return_value=["form_field"])
        request.POST.getlist = Mock(return_value=["form_value"])

        env = RequestEnvelope(request=request, path_params=None)

        result = await DjangoAsyncRequestDataExtractor.extract_request_data(env)

        assert isinstance(result, RequestData)
        assert result.path_params == {"id": "123"}
        assert result.query_params == {"param": "value"}
        assert result.headers == {"content-type": "application/json"}
        assert result.cookies == {"session": "abc"}
        assert result.body == {"data": "test"}
        assert result.form_data == {"form_field": "form_value"}
        assert result.files == {}
