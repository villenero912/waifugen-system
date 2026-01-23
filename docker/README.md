# JAV Automation System - Docker Infrastructure

This directory contains all Docker-related configuration files, deployment scripts, and infrastructure components for the JAV Automation System. The system is designed to run on a cloud VPS with containerized services for production automation, video generation, subscriber management, and monitoring.

## Directory Structure

```
docker/
├── Dockerfile                    # Main application Dockerfile
├── Dockerfile.chat_api           # FastAPI-based chat automation service
├── Dockerfile.karaoke            # Karaoke generation system
├── init.sql                      # PostgreSQL database schema
├── deploy.sh                     # Standard deployment script
├── deploy_secure.sh              # Secure deployment with enhanced security
└── scripts/
    ├── load_env.sh              # Environment variable loader
    ├── produce.sh               # Video production pipeline script
    ├── setup.sh                 # Quick setup script for VPS
    └── setup_env.sh             # Secure API key configuration
```

## Service Overview

The Docker infrastructure orchestrates multiple services that work together to provide a complete automation solution:

The PostgreSQL database serves as the primary data storage layer, containing the complete schema for Phase 1 content generation tracking, Phase 2 subscriber management, revenue analytics, and DM automation. The database uses optimized indexes for high-performance queries across subscriber data, engagement metrics, and content performance analytics. All database ports are bound to localhost only, preventing external access and ensuring data security.

Redis provides caching and session management capabilities, configured with a maximum memory limit of 512MB and the allkeys-lru eviction policy. This ensures efficient memory usage while maintaining fast access to frequently used data. Redis is also bound to localhost only for security.

N8N serves as the workflow automation engine, connecting all services through visual workflows. It stores its data in PostgreSQL and provides a web interface for creating and managing automation pipelines. The n8n_workflows directory can contain pre-built workflow templates that are mounted read-only into the container.

Grafana provides the monitoring dashboard interface, connecting to Prometheus for metrics visualization. Pre-configured dashboards and data sources can be mounted through the provisioning directories. The Grafana container includes plugins for clock panels and JSON data sources.

Prometheus handles metrics collection and storage, with a configurable retention period (default 15 days). It scrapes metrics from all services including the Node Exporter for system-level metrics. The monitoring/prometheus directory contains the Prometheus configuration and alert rules.

Node Exporter collects system-level metrics including CPU usage, memory utilization, disk I/O, and network statistics. These metrics feed into Prometheus for monitoring and alerting.

Nginx acts as the reverse proxy and load balancer, routing traffic to internal services while providing SSL termination, gzip compression, and rate limiting. The configuration includes security headers and upstream definitions for all services.

Watchtower provides automatic container updates by monitoring running containers and rebuilding them when new images are available. It sends notifications via Slack when updates occur and includes a read-only Docker socket for security.

## Quick Start Guide

To deploy the system for the first time, begin by ensuring Docker and Docker Compose are installed on your server. The deploy_secure.sh script includes automatic Docker installation if needed, but having it pre-installed is recommended for faster deployment.

Navigate to the project root directory and execute the secure deployment script with elevated privileges. The script will perform system requirements checks, generate secure passwords, create the environment configuration file, and start all containers. Review the generated .env file and update the API keys with your actual credentials for QWEN, A2E, and any platform-specific integrations.

```bash
cd /path/to/waifugen_system
sudo ./docker/deploy_secure.sh
```

After deployment, access the various services through their respective endpoints. The N8N workflow interface is available at http://your-server/api/, Grafana dashboards at http://your-server/grafana/, and Prometheus metrics at http://your-server/prometheus/. A health check endpoint is available at http://your-server/health for load balancer health monitoring.

## Configuration Files

The deployment process creates a comprehensive .env file containing all necessary configuration. This file should be protected carefully as it contains sensitive credentials. The file is automatically generated with secure random passwords for database and Redis authentication, as well as JWT and encryption keys for application security.

Critical configuration sections include the database configuration block defining PostgreSQL connection parameters, the Redis configuration for caching, security keys for token generation and data encryption, API keys for external services like QWEN (AI processing) and A2E (video generation), platform credentials for TikTok, Instagram, YouTube, Facebook, and Discord integrations, and monitoring settings for Prometheus retention and alerting.

To modify configuration after initial deployment, edit the .env file and restart the affected containers using docker-compose restart service-name. For database-related changes, you may need to rebuild and restart the postgres container.

## Database Schema

The init.sql file contains the complete PostgreSQL schema supporting both Phase 1 and Phase 2 functionality. Phase 1 tables include users for authentication, generated_content for tracking produced videos, platform_credentials for encrypted API storage, revenue_records for monetization tracking, system_metrics for performance monitoring, and proxy_usage for geographic distribution management.

Phase 2 tables expand functionality with subscriber management including the main phase2_subscribers table, subscription_tier_history for tracking upgrades and downgrades, ppv_purchases for pay-per-view content tracking, dm_sequences and dm_messages for automation workflows, subscriber_engagement for daily activity metrics, content_consumption for viewing behavior analysis, and winback_campaigns for churn recovery.

Revenue and analytics tables include revenue_transactions for detailed transaction logging, daily_revenue_summary for platform-level aggregation, monthly_analytics for KPI tracking, and kpi_dashboard for comprehensive performance metrics. Automation tables contain dm_templates for reusable message templates, automation_campaigns for marketing campaigns, and campaign_performance for tracking results.

Japanese platform-specific tables handle FC2 and Fantia integration with dedicated data structures for each platform's unique metrics and content types. The schema includes optimized indexes for common query patterns and views for simplifying frequent analytics queries.

## Deployment Scripts

The deploy.sh script provides standard deployment functionality including system requirements verification, project structure creation, environment file generation with secure passwords, Nginx configuration, and container startup. This script is suitable for development and testing environments.

The deploy_secure.sh script enhances security through additional validation checks, stricter password requirements, read-only Docker socket mounting for Watchtower, enhanced rate limiting configuration, and comprehensive security headers in Nginx. This script is recommended for production deployments.

The scripts/ directory contains utility scripts for various operations. The load_env.sh script sources environment variables from the .env file for use in shell sessions. The produce.sh script provides the video production pipeline interface for creating Phase 1 and Phase 2 content, including karaoke generation capabilities. The setup.sh script performs initial system configuration including dependency installation, firewall setup, and Docker configuration creation. The setup_env.sh script provides secure API key configuration with hidden input prompts.

## Security Considerations

All deployment scripts automatically generate secure passwords for database authentication, Redis, and Grafana admin access. These passwords are stored in the .env file which must be protected through file permissions (chmod 600 .env) and should never be committed to version control.

Database ports (PostgreSQL 5432, Redis 6379) are bound to 127.0.0.1 only, preventing external network access to these services. All external traffic routes through Nginx which provides an additional security layer with rate limiting and security headers.

The Watchtower container mounts the Docker socket read-only to prevent container escape attacks while still allowing image updates. All application containers run as non-root users where possible to minimize the impact of potential vulnerabilities.

API keys and platform credentials should be updated from placeholder values before production deployment. The scripts perform basic validation but cannot detect all configuration errors. Regular security audits of the .env file and running services are recommended.

## Resource Allocation

The Docker Compose configuration includes resource limits optimized for a 4 vCPU, 16 GB RAM server. PostgreSQL is allocated up to 4GB memory with 2GB reservation, Redis is limited to 1GB, N8N can use up to 2GB, Grafana and Prometheus each have 1GB limits, and Nginx with Watchtower share the remaining 256MB allocation.

For servers with different specifications, adjust these limits in the docker-compose.yml file. Monitor actual resource usage through Grafana dashboards and adjust limits based on observed patterns. Under-provisioned services may experience performance degradation, while over-provisioning wastes resources that could be allocated to content generation workloads.

## Monitoring and Alerting

Prometheus collects metrics from all services with a default retention period of 15 days. The configuration includes pre-defined alert rules for high CPU usage (above 80%) and high memory usage (above 85%). Alert destinations can be configured through the SLACK_WEBHOOK_URL environment variable for Slack notifications.

Grafana dashboards provide visualization of system health, content production metrics, subscriber growth, and revenue analytics. The initial dashboard configuration can be extended with custom panels for specific operational requirements. Prometheus targets and Grafana data sources are automatically provisioned through configuration files in the monitoring directories.

The Node Exporter collects host-level metrics including CPU, memory, disk, network, and system load averages. These metrics enable capacity planning and help identify resource bottlenecks before they impact service availability.

## Troubleshooting

If containers fail to start, first check Docker logs using docker-compose logs service-name to identify error messages. Common issues include incorrect API keys preventing application startup, insufficient system resources for container memory limits, port conflicts when services are already running on the same ports, and permission issues with mounted volumes.

For database connectivity issues, verify the POSTGRES_PASSWORD in .env matches what the postgres container expects. The container automatically creates the initial database and user from environment variables. If the database volume becomes corrupted, remove the volume with docker-compose down -v and rebuild to start with a fresh database.

Network connectivity problems between containers indicate network configuration issues. All services connect through the jav_network bridge network with DNS-based service discovery. Verify container names match the connection strings in application configuration.

Performance issues often relate to resource constraints. Monitor actual resource usage through Grafana and adjust container limits accordingly. The FFmpeg threads and parallel render settings in .env significantly impact video generation performance and should be tuned based on available CPU cores.

## Maintenance Tasks

Regular maintenance ensures system reliability and security. Weekly tasks include reviewing container logs for errors, checking Prometheus alerts for performance degradation, and verifying backup completion status. Monthly tasks include reviewing and rotating API keys if compromised, updating base images for security patches through Watchtower, and analyzing capacity trends for infrastructure planning.

Database backups should be configured through the BACKUP_* environment variables. The system supports scheduled backups with compression and encryption. Store backups in a separate location from the primary data volume to protect against data loss.

To update the system, push code changes to the repository and let Watchtower automatically rebuild and restart containers. For major updates, manually run docker-compose up -d --build to ensure proper service restart order and verify functionality before completing the update.

## Support and Documentation

For additional documentation, refer to the main project README.md in the project root directory. The n8n workflows directory may contain pre-built automation templates with documentation on their usage. API documentation for individual services can be accessed through their respective health check endpoints which return service status and available endpoints.

For issues or questions, check the logs directory for application logs and the docker-compose logs output for container-level error messages. Common issues and their solutions are documented in the project's issue tracker.
