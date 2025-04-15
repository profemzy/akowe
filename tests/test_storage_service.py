import os
import unittest
from unittest.mock import Mock, patch, MagicMock
from io import BytesIO
from akowe.services.storage_service import StorageService


class MockBlobClient:
    def __init__(self, url='https://test.blob.core.windows.net/test/test.jpg'):
        self.url = url
    
    def upload_blob(self, data):
        return None
    
    def delete_blob(self):
        return None


class MockContainerClient:
    def __init__(self, container_name='test'):
        self.container_name = container_name
    
    def get_blob_client(self, blob_name):
        return MockBlobClient()
    
    def get_container_properties(self):
        return {}


class MockBlobServiceClient:
    def __init__(self, account_name='testaccount'):
        self.account_name = account_name
        self._credential = Mock()
        self._credential.account_key = 'testkey'
    
    def get_container_client(self, container_name):
        return MockContainerClient(container_name)
    
    def get_blob_client(self, container, blob):
        return MockBlobClient()
    
    def create_container(self, container_name):
        return MockContainerClient(container_name)


class TestStorageService(unittest.TestCase):
    
    @patch('os.environ.get')
    @patch('akowe.services.storage_service.BlobServiceClient')
    def test_get_blob_service_client(self, mock_blob_service_client, mock_environ_get):
        # Setup mocks
        mock_environ_get.return_value = 'test_connection_string'
        mock_blob_service_client.from_connection_string.return_value = 'test_client'
        
        # Call method
        result = StorageService.get_blob_service_client()
        
        # Assert
        mock_environ_get.assert_called_with('AZURE_STORAGE_CONNECTION_STRING')
        mock_blob_service_client.from_connection_string.assert_called_with('test_connection_string')
        self.assertEqual(result, 'test_client')
    
    @patch('akowe.services.storage_service.StorageService.get_blob_service_client')
    def test_get_container_client(self, mock_get_blob_service_client):
        # Setup mocks
        mock_service_client = Mock()
        mock_container_client = Mock()
        mock_service_client.get_container_client.return_value = mock_container_client
        mock_get_blob_service_client.return_value = mock_service_client
        
        # Call method
        result = StorageService.get_container_client('test_container')
        
        # Assert
        mock_get_blob_service_client.assert_called_once()
        mock_service_client.get_container_client.assert_called_with('test_container')
        self.assertEqual(result, mock_container_client)
    
    @patch('akowe.services.storage_service.StorageService.get_container_client')
    @patch('uuid.uuid4')
    def test_upload_file(self, mock_uuid4, mock_get_container_client):
        # Setup mocks
        mock_uuid4.return_value = 'test_uuid'
        mock_container_client = MockContainerClient()
        mock_get_container_client.return_value = mock_container_client
        
        # Create mock file
        mock_file = Mock()
        mock_file.filename = 'test.jpg'
        mock_file.read = lambda: b'test_content'
        
        # Call method
        blob_name, blob_url = StorageService.upload_file(mock_file, 'test_container')
        
        # Assert
        self.assertEqual(blob_name, 'test_uuid.jpg')
        self.assertEqual(blob_url, 'https://test.blob.core.windows.net/test/test.jpg')
    
    @patch('akowe.services.storage_service.StorageService.get_container_client')
    def test_delete_file(self, mock_get_container_client):
        # Setup mocks
        mock_container_client = MockContainerClient()
        mock_get_container_client.return_value = mock_container_client
        
        # Call method
        StorageService.delete_file('test.jpg', 'test_container')
        
        # Assert success if no exception raised
        self.assertTrue(True)
    
    @patch('os.environ.get')
    @patch('akowe.services.storage_service.BlobServiceClient')
    @patch('akowe.services.storage_service.generate_blob_sas')
    def test_generate_sas_url(self, mock_generate_blob_sas, mock_blob_service_client, mock_environ_get):
        # Setup mocks
        mock_environ_get.return_value = 'test_connection_string'
        mock_service_client = MockBlobServiceClient()
        mock_blob_service_client.from_connection_string.return_value = mock_service_client
        mock_generate_blob_sas.return_value = 'test_sas_token'
        
        # Call method
        result = StorageService.generate_sas_url('test.jpg', 'test_container')
        
        # Assert
        self.assertEqual(result, 'https://test.blob.core.windows.net/test/test.jpg?test_sas_token')
