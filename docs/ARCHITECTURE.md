# Wine-O Architecture (draft)

High-level overview:
- Mobile (Flutter) captures images, performs lightweight preprocessing, and uploads to backend or AI edge service.
- Backend (FastAPI) provides auth, user, collections, and orchestration for AI & 3D services.
- AI services (PyTorch, YOLOv8, SAM, EasyOCR, CLIP) run as separate GPU-enabled microservices.
- 3D-engine (Unity + toolchain) performs reconstruction and exports GLB assets to object storage/CDN.
- Storage: PostgreSQL for relational data, Redis for caching, Elasticsearch + Pinecone for search and embeddings.
- Infra: AWS EKS, S3, CloudFront, RDS, ECR, Terraform for IaC, GitHub Actions for CI/CD.

This document will expand as modules are implemented.
