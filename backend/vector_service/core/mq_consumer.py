import pika
import json
import threading
import asyncio
from loguru import logger
from backend.shared.core.config import settings
from backend.vector_service.services.vector_service import VectorService
from backend.shared.rpc import vector_pb2


class RabbitMQConsumer:
    """
    Vector Service 内部的 RabbitMQ 消费者，用于处理向量化任务。
    """
    def __init__(self):
        self.connection = None
        self.channel = None
        self.vector_service = VectorService()
        self.loop = None

    def connect(self):
        """
        连接 RabbitMQ 并开始消费。
        """
        try:
            credentials = pika.PlainCredentials(
                settings.RABBITMQ_DEFAULT_USER, settings.RABBITMQ_DEFAULT_PASS
            )
            parameters = pika.ConnectionParameters(
                host=settings.RABBITMQ_HOST,
                port=settings.RABBITMQ_PORT,
                credentials=credentials,
            )
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            self.channel.queue_declare(queue="embedding_queue", durable=True)
            self.channel.basic_qos(prefetch_count=1)
            self.channel.basic_consume(
                queue="embedding_queue", on_message_callback=self.on_message
            )
            logger.info("RabbitMQ Consumer connected")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            # Retry logic could be added here
            raise

    def on_message(self, ch, method, properties, body):
        """
        处理 RabbitMQ 消息，调用 VectorService.Upsert 进行向量化。
        """
        try:
            message = json.loads(body)
            logger.info(f"Received message: {message.get('id', 'unknown')}")

            metadata = message.get("metadata", {})
            str_metadata = {k: str(v) for k, v in metadata.items()}

            request = vector_pb2.UpsertRequest(
                id=message["id"], text=message["text"], metadata=str_metadata
            )

            # 安全地调用异步 Upsert 方法
            if self.loop and self.loop.is_running():
                future = asyncio.run_coroutine_threadsafe(
                    self.vector_service.Upsert(request, None), self.loop
                )
                try:
                    response = future.result(timeout=30)  # Wait for result with timeout
                    
                    if response.success:
                        ch.basic_ack(delivery_tag=method.delivery_tag)
                        logger.info(f"Processed message: {message['id']}")
                    else:
                        logger.error(f"Failed to process message: {response.error}")
                        ch.basic_ack(
                            delivery_tag=method.delivery_tag
                        )  # Ack to remove from queue
                except Exception as e:
                    logger.error(f"Error waiting for Upsert result: {e}")
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
            else:
                logger.error("Event loop is not running")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    def start(self, loop):
        """
        启动消费者循环。
        """
        self.loop = loop
        self.connect()
        logger.info("Starting RabbitMQ Consumer loop...")
        self.channel.start_consuming()

    def run_in_thread(self, loop):
        """
        在独立线程中运行消费者。
        """
        thread = threading.Thread(target=self.start, args=(loop,))
        thread.daemon = True
        thread.start()
        return thread
