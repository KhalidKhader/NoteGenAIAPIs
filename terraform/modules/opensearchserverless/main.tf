resource "aws_opensearchserverless_collection" "main" {
  name        = var.collection_name
  type        = "VECTORSEARCH"
  description = var.description

  depends_on = [aws_opensearchserverless_security_policy.encryption]
}

resource "aws_opensearchserverless_vpc_endpoint" "main" {
  name               = "${var.collection_name}-vpce"
  vpc_id             = var.vpc_id
  subnet_ids         = var.subnet_ids
  security_group_ids = var.security_group_ids
}

resource "aws_opensearchserverless_security_policy" "main" {
  name        = "${var.collection_name}-network"
  type        = "network"
  description = "Allow VPC or public access to the collection"
  policy      = jsonencode([
    {
      Rules = [
        {
          ResourceType = "collection",
          Resource     = ["collection/${aws_opensearchserverless_collection.main.name}"]
        }
      ],
      AllowFromPublic = var.allow_from_public,
      SourceVPCEs     = var.allow_from_public == false && var.vpc_id != null ? [aws_opensearchserverless_vpc_endpoint.main.id] : []
    }
  ])

  depends_on = [aws_opensearchserverless_vpc_endpoint.main]
}

resource "aws_opensearchserverless_security_policy" "encryption" {
  name        = "${var.collection_name}-enc"
  type        = "encryption"
  description = "Encryption policy for OpenSearch Serverless collection"
  policy = jsonencode({
    Rules = [
      {
        ResourceType = "collection"
        Resource     = ["collection/${var.collection_name}"]
      }
    ],
    AWSOwnedKey = true
  })
} 