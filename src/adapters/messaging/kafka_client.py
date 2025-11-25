from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from src.core.config import settings
import json
import asyncio

class KafkaClient:
    producer: AIOKafkaProducer = None

    async def start(self):
        self.producer = AIOKafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        await self.producer.start()
        print("Kafka Producer started")

    async def stop(self):
        if self.producer:
            await self.producer.stop()
            print("Kafka Producer stopped")

    async def send_message(self, topic: str, message: dict):
        if not self.producer:
            raise Exception("Kafka Producer not initialized")
        await self.producer.send_and_wait(topic, message)

    async def consume(self, topic: str):
        consumer = AIOKafkaConsumer(
            topic,
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            group_id="router_group"
        )
        await consumer.start()
        try:
            async for msg in consumer:
                yield msg
        finally:
            await consumer.stop()

kafka_client = KafkaClient()

async def get_kafka_producer():
    if not kafka_client.producer:
        await kafka_client.start()
    return kafka_client
