from src.core.settings.config import settings
from opensearchpy import AWSV4SignerAuth
import boto3

async def setup_aws_auth():
    """Setup authentication for OpenSearch Serverless (AOSS) only."""
    session = boto3.Session()
    credentials = session.get_credentials()
    if not credentials:
        raise ValueError("No AWS credentials found - ensure IAM roles are configured or provide explicit credentials")
    # Always use 'aoss' for OpenSearch Serverless
    service = 'aoss'
    return AWSV4SignerAuth(credentials, settings.aws_region, service)