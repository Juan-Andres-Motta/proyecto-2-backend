- ECR Repo with Lifecycle Policy
  - Repository Name: my-ecr-repo
  - Lifecycle Policy:
    - Rule 1: Retain only the latest 4 images, delete older ones


- ECS Cluster
  - Cluster Name: medisupply-cluster
  - Capacity Providers: FARGATE, FARGATE_SPOT (The cheapest option)
  - 1 task per microservice (max replica 2)
  - Services should connect using ECS Service Connect for internal communication
  - ALB for external access to services

- RDS
  - PostgreSQL Free Tier
  - Create the module, but do not use it in terraform main file
  - BD per service (except BFF & test-service)
  - Ensure IAM roles and security groups are configured for secure access

- Deployment Strategy
  - Use Blue/Green deployment strategy for zero-downtime deployments, 10min linear deployment
  - Do not use CodeDeploy, use only ECS features
  - Configure health checks and alarms for monitoring
  - In case of failure, automatically rollback to the previous stable version (5% error threshold)
  

