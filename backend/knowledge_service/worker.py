import sys
import os
import pika
import json
import grpc
import time
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from backend.shared.core.config import settings
from backend.shared.rpc import vector_pb2, vector_pb2_grpc
from backend.shared.core.discovery import registry
from loguru import logger
import random


def consume():
    """
    独立知识库 Worker。
    从 RabbitMQ 消费消息并通过 gRPC 调用向量服务。
    注意：这是向量服务内部消费者的替代方案。
    """
    logger.info("Starting Knowledge Worker...")

    # 连接RabbitMQ
    credentials = pika.PlainCredentials(
        settings.RABBITMQ_DEFAULT_USER, settings.RABBITMQ_DEFAULT_PASS
    )
    parameters = pika.ConnectionParameters(
        host=settings.RABBITMQ_HOST,
        port=settings.RABBITMQ_PORT,
        credentials=credentials,
    )

    # RabbitMQ 连接重试逻辑
    while True:
        try:
            connection = pika.BlockingConnection(parameters)
            break
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}. Retrying in 5s...")
            time.sleep(5)

    channel = connection.channel()
    channel.queue_declare(queue="embedding_queue", durable=True)

    # 连接向量服务 gRPC (通过 Nacos 服务发现)
    target = "localhost:50051"  # Default fallback
    try:
        instances = registry.get_service("vector-service")
        hosts = instances.get("hosts", []) if isinstance(instances, dict) else instances
        healthy = [
            i for i in hosts if i.get("healthy", True) and i.get("enabled", True)
        ]
        if healthy:
            inst = random.choice(healthy)
            target = f"{inst['ip']}:{inst['port']}"
            logger.info(f"Discovered Vector Service at {target}")
        else:
            logger.warning("No healthy Vector Service found in Nacos, using default.")
    except Exception as e:
        logger.error(f"Failed to discover Vector Service: {e}")

    logger.info(f"Connecting to Vector Service at {target}...")
    channel_grpc = grpc.insecure_channel(target)
    stub = vector_pb2_grpc.VectorServiceStub(channel_grpc)

    def callback(ch, method, properties, body):
        """
        RabbitMQ 消息回调函数。
        """
        try:
            message = json.loads(body)
            logger.info(f"Processing chunk: {message['id']}")

            # 调用向量服务进行 Upsert 操作
            request = vector_pb2.UpsertRequest(
                id=message["id"], text=message["text"], metadata=message["metadata"]
            )

            response = stub.Upsert(request)

            if response.success:
                logger.info(f"Successfully indexed chunk {message['id']}")
                ch.basic_ack(delivery_tag=method.delivery_tag)
            else:
                logger.error(f"Failed to index chunk {message['id']}: {response.error}")

                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue="embedding_queue", on_message_callback=callback)

    logger.info("Knowledge Worker is waiting for messages...")
    channel.start_consuming()


if __name__ == "__main__":
    consume()
