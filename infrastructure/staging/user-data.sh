#!/bin/bash
set -e

# Update system
dnf update -y

# Install Docker
dnf install -y docker

# Start Docker service
systemctl start docker
systemctl enable docker

# Add ec2-user to docker group
usermod -aG docker ec2-user

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Install AWS CLI v2 (already included in Amazon Linux 2023)
# aws --version

# Install git
dnf install -y git

# Create directory for application
mkdir -p /home/ec2-user/app
chown ec2-user:ec2-user /home/ec2-user/app

# Log completion
echo "EC2 instance initialization completed at $(date)" > /var/log/user-data.log
