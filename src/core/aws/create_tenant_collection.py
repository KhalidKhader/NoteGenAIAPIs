import boto3
import json
import asyncio
from typing import Dict, Any
from opensearchpy import OpenSearch, RequestsHttpConnection
from .opensearch_conversation_rag_service import ConversationRAGService
from .setup_aws_auth import setup_aws_auth

from src.core.settings.config import settings
from src.core.settings.logging import logger

async def create_tenant_collection(collection_name: str, clinic_id: str) -> Dict[str, Any]:
    """Create a new tenant collection with all required policies."""
    # Create a temporary RAG service instance for initialization
    rag_service = ConversationRAGService()
    await rag_service.initialize()

    try:
        aoss = boto3.client('opensearchserverless', region_name=settings.aws_region)
        
        # Generate short policy names (max 32 chars)
        policy_prefix = collection_name[:28]  # Leave room for suffixes
        
        # 1. Create encryption policy (if not exists)
        encryption_policy = {
            "Rules": [{
                "ResourceType": "collection",
                "Resource": [f"collection/{collection_name}"]
            }],
            "AWSOwnedKey": True
        }
        
        try:
            aoss.create_security_policy(
                name=f"{policy_prefix}-enc",
                policy=json.dumps(encryption_policy),
                type='encryption',
                description=f'Encryption policy for {collection_name}'
            )
            logger.info(f"Created encryption policy for {collection_name}")
        except aoss.exceptions.ConflictException:
            logger.info(f"Encryption policy already exists for {collection_name}")
        
        # 2. Create network policy (if not exists)
        network_policy = [{
            "Description": f"Network policy for {collection_name}",
            "Rules": [
                {
                    "ResourceType": "collection",
                    "Resource": [f"collection/{collection_name}"]
                }
            ],
            "AllowFromPublic": True
        }]
        
        try:
            aoss.create_security_policy(
                name=f"{policy_prefix}-net",
                policy=json.dumps(network_policy),
                type='network',
                description=f'Network policy for {collection_name}'
            )
            logger.info(f"Created network policy for {collection_name}")
        except aoss.exceptions.ConflictException:
            logger.info(f"Network policy already exists for {collection_name}")
        
        # 3. Create data access policy (if not exists)
        # Get caller identity for proper ARN
        sts = boto3.client('sts')
        account_id = sts.get_caller_identity()['Account']
        
        data_policy = [{
            "Rules": [
                {
                    "Resource": [
                        f"index/{collection_name}/*"
                    ],
                    "Permission": [
                        "aoss:CreateIndex",
                        "aoss:DeleteIndex",
                        "aoss:UpdateIndex",
                        "aoss:DescribeIndex",
                        "aoss:ReadDocument",
                        "aoss:WriteDocument"
                    ],
                    "ResourceType": "index"
                },
                {
                    "Resource": [
                        f"collection/{collection_name}"
                    ],
                    "Permission": [
                        "aoss:CreateCollectionItems",
                        "aoss:DeleteCollectionItems",
                        "aoss:UpdateCollectionItems",
                        "aoss:DescribeCollectionItems"
                    ],
                    "ResourceType": "collection"
                }
            ],
            "Principal": [
                f"arn:aws:iam::{account_id}:root"  # Grant access to the entire AWS account
            ]
        }]
        
        try:
            aoss.create_access_policy(
                name=f"te-{policy_prefix}",
                policy=json.dumps(data_policy),
                type='data',
                description=f'Data access policy for {collection_name}'
            )
            logger.info(f"Created access policy for {collection_name}")
        except aoss.exceptions.ConflictException:
            logger.info(f"Access policy already exists for {collection_name}")
        
        # 4. Create collection
        try:
            response = aoss.create_collection(
                name=collection_name,
                type='VECTORSEARCH',
                description=f'Tenant collection for clinic {clinic_id}'
            )
            
            collection_id = response['createCollectionDetail']['id']
            logger.info(f"Created collection {collection_name}")
            
            # 5. Return immediately without waiting for ACTIVE status
            # This makes response time < 1 second
            return {
                'collection_id': collection_id,
                'status': 'CREATING',
                'message': 'Collection created successfully. It will be active within 1-2 minutes.',
                'endpoint': 'Will be available when collection is active'
            }
            
        except aoss.exceptions.ConflictException:
            logger.error(f"Collection {collection_name} already exists")
            raise Exception(f"Collection {collection_name} already exists")
        
    except Exception as e:
        error_msg = f"Failed to create tenant collection {collection_name}: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)