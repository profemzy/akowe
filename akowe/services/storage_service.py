import os
import uuid
from datetime import datetime, timedelta
from typing import Tuple

from azure.storage.blob import BlobServiceClient, ContainerClient, generate_blob_sas, BlobSasPermissions


class StorageService:
    """Service for handling file uploads to Azure Blob Storage"""
    
    @staticmethod
    def get_blob_service_client() -> BlobServiceClient:
        """Get Azure Blob Service client from connection string"""
        connection_string = os.environ.get('AZURE_STORAGE_CONNECTION_STRING')
        if not connection_string:
            raise ValueError("Azure Storage connection string not found in environment variables")
            
        return BlobServiceClient.from_connection_string(connection_string)
    
    @staticmethod
    def get_container_client(container_name: str) -> ContainerClient:
        """Get container client for the specified container"""
        blob_service_client = StorageService.get_blob_service_client()
        return blob_service_client.get_container_client(container_name)
    
    @staticmethod
    def upload_file(file_data, container_name: str) -> Tuple[str, str]:
        """Upload a file to Azure Blob Storage
        
        Args:
            file_data: File data from request.files
            container_name: Container name in Azure Storage
            
        Returns:
            Tuple containing (blob_name, blob_url)
        """
        try:
            # Create a unique blob name
            original_filename = file_data.filename
            file_extension = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
            blob_name = f"{uuid.uuid4()}.{file_extension}" if file_extension else f"{uuid.uuid4()}"
            
            # Get container client and upload the file
            container_client = StorageService.get_container_client(container_name)
            
            # Check if container exists, create if it doesn't
            try:
                container_client.get_container_properties()
            except Exception:
                blob_service_client = StorageService.get_blob_service_client()
                blob_service_client.create_container(container_name)
            
            # Upload the file
            blob_client = container_client.get_blob_client(blob_name)
            blob_client.upload_blob(file_data)
            
            # Get the URL
            blob_url = blob_client.url
            
            return blob_name, blob_url
        
        except Exception as e:
            raise Exception(f"Failed to upload file to Azure Storage: {str(e)}")
    
    @staticmethod
    def delete_file(blob_name: str, container_name: str) -> None:
        """Delete a file from Azure Blob Storage
        
        Args:
            blob_name: Name of the blob to delete
            container_name: Container name in Azure Storage
        """
        try:
            container_client = StorageService.get_container_client(container_name)
            blob_client = container_client.get_blob_client(blob_name)
            blob_client.delete_blob()
        except Exception as e:
            raise Exception(f"Failed to delete file from Azure Storage: {str(e)}")
    
    @staticmethod
    def generate_sas_url(blob_name: str, container_name: str, expiry_hours: int = 1) -> str:
        """Generate a SAS URL for temporary access to a blob
        
        Args:
            blob_name: Name of the blob
            container_name: Container name in Azure Storage
            expiry_hours: Number of hours until the SAS token expires
            
        Returns:
            SAS URL for the blob
        """
        try:
            # Get connection string from environment
            connection_string = os.environ.get('AZURE_STORAGE_CONNECTION_STRING')
            if not connection_string:
                raise ValueError("Azure Storage connection string not found in environment variables")
            
            # Extract account name and key from connection string
            # Connection string format: DefaultEndpointsProtocol=https;AccountName=xxx;AccountKey=xxx;EndpointSuffix=core.windows.net
            conn_parts = dict(part.split('=', 1) for part in connection_string.split(';') if '=' in part)
            account_name = conn_parts.get('AccountName')
            account_key = conn_parts.get('AccountKey')
            
            if not account_name or not account_key:
                raise ValueError("Account name or key not found in connection string")
            
            # Generate SAS token
            sas_token = generate_blob_sas(
                account_name=account_name,
                container_name=container_name,
                blob_name=blob_name,
                account_key=account_key,
                permission=BlobSasPermissions(read=True),
                expiry=datetime.utcnow() + timedelta(hours=expiry_hours)
            )
            
            # Create blob URL
            endpoint = f"https://{account_name}.blob.core.windows.net"
            blob_url = f"{endpoint}/{container_name}/{blob_name}?{sas_token}"
            
            return blob_url
        
        except Exception as e:
            raise Exception(f"Failed to generate SAS URL: {str(e)}")
