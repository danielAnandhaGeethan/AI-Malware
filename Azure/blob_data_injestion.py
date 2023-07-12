from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
import utils.utils as utils

def upload_files_to_blob_storage(hash, file_type, image_type):
    # Connect to Azure Blob Storage
    connect_str = 'DefaultEndpointsProtocol=https;AccountName=malwarebistorage;AccountKey=ng2g0h2ddtFsgdHvU4+xo9zJZQPnsICkvkGfupcDL/tEKhEoAItnaHaDX5ctYK5174yGXDduK2i0+AStuiFb2Q==;EndpointSuffix=core.windows.net'
    blob_service_client = BlobServiceClient.from_connection_string(connect_str)

    # Create a container
    container_name = 'bicont'
    container_client = blob_service_client.get_container_client(container_name)

    # Upload image file to blob storage
    image_path = utils.TEMP_PATH + f"/image/{image_type}/" + hash + '.png'
    upload_path = hash + '.png'
    blob_client = blob_service_client.get_blob_client(container=container_name, blob='images/' + upload_path)
    with open(image_path, "rb") as data:
        blob_client.upload_blob(data)

    # Upload exe file to blob storage
    exe_path = utils.TEMP_PATH + f"/malware/{file_type}/" + hash + '.exe'
    upload_path = hash + '.exe'
    blob_client = blob_service_client.get_blob_client(container=container_name, blob='exe/' + upload_path)
    with open(exe_path, "rb") as data:
        blob_client.upload_blob(data)

    # Upload json file to blob storage
    json_path = utils.TEMP_PATH + f"/cuckoo/" + hash + '.json'
    upload_path = hash + '.json'
    blob_client = blob_service_client.get_blob_client(container=container_name, blob='json/' + upload_path)
    with open(json_path, "rb") as data:
        blob_client.upload_blob(data)

    print('Files uploaded successfully!')

# Example usage
if __name__ == '__main__':
    upload_files_to_blob_storage('putty', 'exe', "BB")