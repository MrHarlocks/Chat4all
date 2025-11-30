import os
import sys

# Add project root to python path
sys.path.append(os.getcwd())

from kafka.admin import KafkaAdminClient, NewPartitions
from src.core.config import settings

def add_partitions():
    print(f"Connecting to Kafka at {settings.KAFKA_BOOTSTRAP_SERVERS}...")
    try:
        admin_client = KafkaAdminClient(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            client_id='admin_client'
        )
        
        # Check current partitions first? 
        # create_partitions expects a dict of topic -> NewPartitions
        # NewPartitions(total_count=N) where N must be > current count
        
        topic_partitions = {settings.KAFKA_TOPIC_MESSAGES: NewPartitions(total_count=4)}
        
        print(f"Attempting to increase partitions for {settings.KAFKA_TOPIC_MESSAGES} to 4...")
        admin_client.create_partitions(topic_partitions)
        print("Partitions increased to 4 successfully.")
        
    except Exception as e:
        print(f"Operation result: {e}")

if __name__ == "__main__":
    add_partitions()
