#!/bin/bash

# Search Infrastructure Setup Script
# Auto Bot Solutions Forum - Elasticsearch Cluster Setup

set -e

echo "Setting up Search Infrastructure for Auto Bot Solutions Forum..."

# Configuration
ELASTICSEARCH_VERSION="7.17.9"
ELASTICSEARCH_HOME="/opt/elasticsearch"
ELASTICSEARCH_USER="elasticsearch"
ELASTICSEARCH_GROUP="elasticsearch"
ELASTICSEARCH_PORT="9200"
ELASTICSEARCH_CLUSTER_NAME="forum-search"
ELASTICSEARCH_NODE_NAME="forum-search-node-1"

# Create directories
echo "Creating Elasticsearch directories..."
mkdir -p $ELASTICSEARCH_HOME
mkdir -p /var/log/elasticsearch
mkdir -p /var/lib/elasticsearch
mkdir -p /etc/elasticsearch
mkdir -p /opt/search/monitoring
mkdir -p /opt/search/backup

# Set permissions
echo "Setting permissions..."
chmod 755 $ELASTICSEARCH_HOME
chmod 755 /var/log/elasticsearch
chmod 755 /var/lib/elasticsearch
chmod 755 /etc/elasticsearch
chmod 755 /opt/search

# Create Elasticsearch user if it doesn't exist
echo "Creating Elasticsearch user..."
if ! id "$ELASTICSEARCH_USER" &>/dev/null; then
    useradd -m -s /bin/bash $ELASTICSEARCH_USER
    echo "Elasticsearch user created successfully"
else
    echo "Elasticsearch user already exists"
fi

# Install Java
echo "Installing Java..."
apt-get update
apt-get install -y openjdk-11-jdk
apt-get install -y curl wget gnupg2

# Set JAVA_HOME
echo "Setting JAVA_HOME..."
echo "export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64" >> /etc/environment
echo "export PATH=\$PATH:\$JAVA_HOME/bin" >> /etc/environment
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64

# Download and install Elasticsearch
echo "Downloading and installing Elasticsearch..."
cd /tmp
wget https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-$ELASTICSEARCH_VERSION-linux-x86_64.tar.gz
tar -xzf elasticsearch-$ELASTICSEARCH_VERSION-linux-x86_64.tar.gz
mv elasticsearch-$ELASTICSEARCH_VERSION $ELASTICSEARCH_HOME

# Set ownership
echo "Setting ownership..."
chown -R $ELASTICSEARCH_USER:$ELASTICSEARCH_GROUP $ELASTICSEARCH_HOME
chown -R $ELASTICSEARCH_USER:$ELASTICSEARCH_GROUP /var/log/elasticsearch
chown -R $ELASTICSEARCH_USER:$ELASTICSEARCH_GROUP /var/lib/elasticsearch
chown -R $ELASTICSEARCH_USER:$ELASTICSEARCH_GROUP /etc/elasticsearch

# Configure Elasticsearch
echo "Configuring Elasticsearch..."
cat > /etc/elasticsearch/elasticsearch.yml << EOF
# Elasticsearch Configuration
cluster.name: $ELASTICSEARCH_CLUSTER_NAME
node.name: $ELASTICSEARCH_NODE_NAME

# Network settings
network.host: 0.0.0.0
http.port: $ELASTICSEARCH_PORT
transport.tcp.port: 9300

# Discovery settings
discovery.type: single-node

# Path settings
path.data: /var/lib/elasticsearch
path.logs: /var/log/elasticsearch

# Memory settings
bootstrap.memory_lock: true

# Security settings
xpack.security.enabled: false
xpack.monitoring.enabled: true
xpack.monitoring.collection.enabled: true

# Index settings
action.auto_create_index: "+*"
action.destructive_requires_name: true

# Performance settings
thread_pool.write.queue_size: 1000
thread_pool.search.queue_size: 1000

# Search settings
search.max_buckets: 10000
search.max_clause_count: 1024

# Indexing settings
index.refresh_interval: 1s
index.number_of_shards: 1
index.number_of_replicas: 0

# Logging settings
logger.level: INFO
logger.org.elasticsearch: WARN
EOF

# Configure JVM options
echo "Configuring JVM options..."
cat > $ELASTICSEARCH_HOME/config/jvm.options << EOF
## JVM configuration

# Xms represents the initial size of total heap space
# Xmx represents the maximum size of total heap space

-Xms1g
-Xmx1g

################################################################
## Expert settings
################################################################
## All settings below this section are considered
## expert settings. Don't mess with them unless you
## are an expert!

################################################################
## GC configuration
################################################################
-XX:+UseG1GC
-XX:MaxGCPauseMillis=200
-XX:InitiatingHeapOccupancyPercent=45

################################################################
## Directory settings
################################################################
-XX:+AlwaysPreTouch
-XX:+HeapDumpOnOutOfMemoryError
-XX:HeapDumpPath=/var/log/elasticsearch
-XX:ErrorFile=/var/log/elasticsearch/hs_err_pid%p.log

################################################################
## JMX settings
################################################################
-XX:+UnlockCommercialFeatures
-XX:+UseCompressedOops

################################################################
## Performance settings
################################################################
-XX:+UseStringDeduplication
-XX:+UseCompressedOops
-XX:+UseG1GC
-XX:MaxGCPauseMillis=200
-XX:InitiatingHeapOccupancyPercent=45

################################################################
## Diagnostic settings
################################################################
-XX:+PrintGCDetails
-XX:+PrintGCTimeStamps
-XX:+PrintGCDateStamps
-XX:+UseGCLogFileRotation
-XX:NumberOfGCLogFiles=10
-XX:GCLogFileSize=64M
-XX:+UseCompressedOops
-XX:+UseG1GC
-XX:MaxGCPauseMillis=200
-XX:InitiatingHeapOccupancyPercent=45
EOF

# Create systemd service file
echo "Creating systemd service file..."
cat > /etc/systemd/system/elasticsearch.service << EOF
[Unit]
Description=Elasticsearch
Documentation=https://www.elastic.co
Wants=network-online.target
After=network-online.target

[Service]
Type=notify
RuntimeDirectory=elasticsearch
PrivateTmp=true
Environment=ES_HOME=$ELASTICSEARCH_HOME
Environment=ES_PATH_CONF=/etc/elasticsearch
Environment=PID_DIR=/var/run/elasticsearch
WorkingDirectory=$ELASTICSEARCH_HOME
User=$ELASTICSEARCH_USER
Group=$ELASTICSEARCH_GROUP

ExecStart=$ELASTICSEARCH_HOME/bin/elasticsearch
StandardOutput=journal
StandardError=inherit
LimitNOFILE=65535
LimitNPROC=32768
LimitAS=infinity
LimitFSIZE=infinity
KillSignal=SIGTERM
KillSendSIGKILL=no
SuccessExitStatus=143
TimeoutStopSec=0

# Allow Elasticsearch to access protected files
ProtectSystem=full
ReadWriteDirectories=/var/lib/elasticsearch
ReadWriteDirectories=/var/log/elasticsearch
ReadWriteDirectories=/etc/elasticsearch

[Install]
WantedBy=multi-user.target
EOF

# Set system limits
echo "Setting system limits..."
cat >> /etc/security/limits.conf << EOF
$ELASTICSEARCH_USER soft nofile 65535
$ELASTICSEARCH_USER hard nofile 65535
$ELASTICSEARCH_USER soft memlock unlimited
$ELASTICSEARCH_USER hard memlock unlimited
EOF

cat >> /etc/sysctl.conf << EOF
vm.max_map_count=262144
vm.swappiness=1
EOF

# Apply system limits
sysctl -p

# Enable and start Elasticsearch service
echo "Enabling and starting Elasticsearch service..."
systemctl daemon-reload
systemctl enable elasticsearch
systemctl start elasticsearch

# Wait for Elasticsearch to start
echo "Waiting for Elasticsearch to start..."
sleep 30

# Check if Elasticsearch is running
if curl -s http://localhost:$ELASTICSEARCH_PORT > /dev/null; then
    echo "Elasticsearch is running successfully"
else
    echo "Elasticsearch failed to start"
    exit 1
fi

# Install Kibana for monitoring
echo "Installing Kibana..."
cd /tmp
wget https://artifacts.elastic.co/downloads/kibana/kibana-$ELASTICSEARCH_VERSION-linux-x86_64.tar.gz
tar -xzf kibana-$ELASTICSEARCH_VERSION-linux-x86_64.tar.gz
mv kibana-$ELASTICSEARCH_VERSION-linux-x86_64 /opt/kibana

# Configure Kibana
echo "Configuring Kibana..."
cat > /etc/kibana/kibana.yml << EOF
# Kibana Configuration
server.host: "0.0.0.0"
server.port: 5601
elasticsearch.hosts: ["http://localhost:$ELASTICSEARCH_PORT"]
elasticsearch.username: ""
elasticsearch.password: ""

# Monitoring settings
monitoring.ui.container.elasticsearch.enabled: true
monitoring.ui.container.logstash.enabled: true
EOF

# Create Kibana systemd service
echo "Creating Kibana systemd service..."
cat > /etc/systemd/system/kibana.service << EOF
[Unit]
Description=Kibana
Documentation=https://www.elastic.co
Wants=network-online.target
After=network-online.target

[Service]
Type=notify
RuntimeDirectory=kibana
PrivateTmp=true
Environment=KIBANA_HOME=/opt/kibana
WorkingDirectory=/opt/kibana
User=$ELASTICSEARCH_USER
Group=$ELASTICSEARCH_GROUP

ExecStart=/opt/kibana/bin/kibana
StandardOutput=journal
StandardError=inherit
LimitNOFILE=65535
LimitNPROC=32768
LimitAS=infinity
LimitFSIZE=infinity
KillSignal=SIGTERM
KillSendSIGKILL=no
SuccessExitStatus=143
TimeoutStopSec=0

[Install]
WantedBy=multi-user.target
EOF

# Enable and start Kibana
echo "Enabling and starting Kibana..."
systemctl daemon-reload
systemctl enable kibana
systemctl start kibana

# Create search indexes
echo "Creating search indexes..."
sleep 10

# Create forum posts index
curl -X PUT "localhost:$ELASTICSEARCH_PORT/forum_posts" -H 'Content-Type: application/json' -d'
{
  "settings": {
    "number_of_shards": 1,
    "number_of_replicas": 0,
    "refresh_interval": "1s"
  },
  "mappings": {
    "properties": {
      "id": {
        "type": "integer"
      },
      "title": {
        "type": "text",
        "analyzer": "standard",
        "fields": {
          "keyword": {
            "type": "keyword"
          }
        }
      },
      "content": {
        "type": "text",
        "analyzer": "english"
      },
      "author": {
        "type": "text",
        "analyzer": "standard",
        "fields": {
          "keyword": {
            "type": "keyword"
          }
        }
      },
      "author_id": {
        "type": "integer"
      },
      "category": {
        "type": "keyword"
      },
      "tags": {
        "type": "keyword"
      },
      "created_at": {
        "type": "date",
        "format": "yyyy-MM-dd HH:mm:ss||strict_date_optional_time"
      },
      "updated_at": {
        "type": "date",
        "format": "yyyy-MM-dd HH:mm:ss||strict_date_optional_time"
      },
      "views_count": {
        "type": "integer"
      },
      "comments_count": {
        "type": "integer"
      },
      "votes_count": {
        "type": "integer"
      },
      "status": {
        "type": "keyword"
      }
    }
  }
}'

# Create users index
curl -X PUT "localhost:$ELASTICSEARCH_PORT/users" -H 'Content-Type: application/json' -d'
{
  "settings": {
    "number_of_shards": 1,
    "number_of_replicas": 0,
    "refresh_interval": "1s"
  },
  "mappings": {
    "properties": {
      "id": {
        "type": "integer"
      },
      "username": {
        "type": "text",
        "analyzer": "standard",
        "fields": {
          "keyword": {
            "type": "keyword"
          }
        }
      },
      "email": {
        "type": "keyword"
      },
      "first_name": {
        "type": "text",
        "analyzer": "standard",
        "fields": {
          "keyword": {
            "type": "keyword"
          }
        }
      },
      "last_name": {
        "type": "text",
        "analyzer": "standard",
        "fields": {
          "keyword": {
            "type": "keyword"
          }
        }
      },
      "bio": {
        "type": "text",
        "analyzer": "english"
      },
      "location": {
        "type": "text",
        "analyzer": "standard",
        "fields": {
          "keyword": {
            "type": "keyword"
          }
        }
      },
      "website": {
        "type": "keyword"
      },
      "created_at": {
        "type": "date",
        "format": "yyyy-MM-dd HH:mm:ss||strict_date_optional_time"
      },
      "last_login": {
        "type": "date",
        "format": "yyyy-MM-dd HH:mm:ss||strict_date_optional_time"
      },
      "is_active": {
        "type": "boolean"
      },
      "roles": {
        "type": "keyword"
      }
    }
  }
}'

# Create forum comments index
curl -X PUT "localhost:$ELASTICSEARCH_PORT/forum_comments" -H 'Content-Type: application/json' -d'
{
  "settings": {
    "number_of_shards": 1,
    "number_of_replicas": 0,
    "refresh_interval": "1s"
  },
  "mappings": {
    "properties": {
      "id": {
        "type": "integer"
      },
      "content": {
        "type": "text",
        "analyzer": "english"
      },
      "author": {
        "type": "text",
        "analyzer": "standard",
        "fields": {
          "keyword": {
            "type": "keyword"
          }
        }
      },
      "author_id": {
        "type": "integer"
      },
      "post_id": {
        "type": "integer"
      },
      "created_at": {
        "type": "date",
        "format": "yyyy-MM-dd HH:mm:ss||strict_date_optional_time"
      },
      "updated_at": {
        "type": "date",
        "format": "yyyy-MM-dd HH:mm:ss||strict_date_optional_time"
      },
      "votes_count": {
        "type": "integer"
      },
      "status": {
        "type": "keyword"
      }
    }
  }
}'

# Create search analytics index
curl -X PUT "localhost:$ELASTICSEARCH_PORT/search_analytics" -H 'Content-Type: application/json' -d'
{
  "settings": {
    "number_of_shards": 1,
    "number_of_replicas": 0,
    "refresh_interval": "1s"
  },
  "mappings": {
    "properties": {
      "query_id": {
        "type": "keyword"
      },
      "query_text": {
        "type": "text",
        "analyzer": "standard"
      },
      "user_id": {
        "type": "integer"
      },
      "session_id": {
        "type": "keyword"
      },
      "ip_address": {
        "type": "ip"
      },
      "user_agent": {
        "type": "text",
        "analyzer": "keyword"
      },
      "search_type": {
        "type": "keyword"
      },
      "index_name": {
        "type": "keyword"
      },
      "results_count": {
        "type": "integer"
      },
      "execution_time_ms": {
        "type": "float"
      },
      "timestamp": {
        "type": "date",
        "format": "yyyy-MM-dd HH:mm:ss||strict_date_optional_time"
      },
      "filters": {
        "type": "object"
      },
      "sort": {
        "type": "object"
      }
    }
  }
}'

# Install search monitoring tools
echo "Installing search monitoring tools..."
pip3 install elasticsearch==7.17.9
pip3 install elasticsearch-py==7.17.9
pip3 install prometheus-client==0.11.0
pip3 install grafana-api==1.0.3

# Create monitoring configuration
echo "Creating monitoring configuration..."
cat > /opt/search/monitoring/prometheus.yml << EOF
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "/opt/search/monitoring/rules/*.yml"

scrape_configs:
  - job_name: 'elasticsearch'
    static_configs:
      - targets: ['localhost:9200']
    metrics_path: '/_prometheus/metrics'
    scrape_interval: 15s

  - job_name: 'kibana'
    static_configs:
      - targets: ['localhost:5601']
    metrics_path: '/api/status/metrics'
    scrape_interval: 15s
EOF

# Create search backup configuration
echo "Creating backup configuration..."
cat > /opt/search/backup/backup-config.yml << EOF
# Elasticsearch Backup Configuration
backup:
  enabled: true
  schedule: "0 2 * * *"  # Daily at 2 AM
  retention_days: 30
  compression: true
  
  repositories:
    - name: "local_backup"
      type: "fs"
      settings:
        location: "/opt/search/backup/local"
        compress: true
    
    - name: "s3_backup"
      type: "s3"
      settings:
        bucket: "forum-search-backup"
        region: "us-east-1"
        base_path: "elasticsearch"
        compress: true
  
  indices:
    - "forum_posts"
    - "users"
    - "forum_comments"
    - "search_analytics"
  
  snapshots:
    name_pattern: "forum-search-snapshot-%Y%m%d-%H%M%S"
    include_global_state: true
    wait_for_completion: true
EOF

# Create search performance optimization script
echo "Creating performance optimization script..."
cat > /opt/search/performance-optimization.py << 'EOF'
#!/usr/bin/env python3
"""
Search Performance Optimization Script
Auto Bot Solutions Forum
"""

import sys
import time
import logging
from elasticsearch import Elasticsearch

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def optimize_search_performance():
    """Optimize Elasticsearch performance"""
    es = Elasticsearch(['localhost:9200'])
    
    optimizations = [
        # Optimize index settings
        {
            "index.refresh_interval": "5s",
            "index.number_of_replicas": 0,
            "index.translog.flush_threshold_size": "512mb"
        },
        
        # Optimize thread pools
        {
            "thread_pool.write.queue_size": 1000,
            "thread_pool.search.queue_size": 1000,
            "thread_pool.management.queue_size": 500
        },
        
        # Optimize cache settings
        {
            "indices.queries.cache.size": "10%",
            "indices.fielddata.cache.size": "30%"
        }
    ]
    
    for optimization in optimizations:
        try:
            es.cluster.put_settings(body={"persistent": optimization})
            logger.info(f"Applied optimization: {optimization}")
        except Exception as e:
            logger.error(f"Failed to apply optimization {optimization}: {e}")

if __name__ == "__main__":
    optimize_search_performance()
EOF

chmod +x /opt/search/performance-optimization.py

# Run performance optimization
echo "Running performance optimization..."
python3 /opt/search/performance-optimization.py

echo "Search Infrastructure setup completed successfully!"
echo ""
echo "Services running:"
echo "  - Elasticsearch: http://localhost:9200"
echo "  - Kibana: http://localhost:5601"
echo ""
echo "Indexes created:"
echo "  - forum_posts"
echo "  - users"
echo "  - forum_comments"
echo "  - search_analytics"
echo ""
echo "Next steps:"
echo "1. Configure your application to use Elasticsearch at http://localhost:9200"
echo "2. Set up Kibana dashboards at http://localhost:5601"
echo "3. Configure search monitoring with Prometheus"
echo "4. Set up backup schedule"
echo ""
echo "Search Infrastructure is ready for use!"
