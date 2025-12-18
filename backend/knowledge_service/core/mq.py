import pika
import json
from backend.shared.core.config import settings


class RabbitMQProducer:
    """
    RabbitMQ 生产者封装类。
    """

    def __init__(self):
        self.connection = None
        self.channel = None

    def connect(self):
        """
        建立 RabbitMQ 连接。
        """
        if not self.connection or self.connection.is_closed:
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
            # 声明队列，确保其存在
            self.channel.queue_declare(queue="embedding_queue", durable=True)

    def publish(self, message: dict):
        """
        发送消息到队列。
        """
        try:
            if not self.connection or self.connection.is_closed:
                self.connect()

            self.channel.basic_publish(
                exchange="",
                routing_key="embedding_queue",
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # make message persistent (消息持久化)
                ),
            )
        except (pika.exceptions.ConnectionClosed, pika.exceptions.StreamLostError):
            # 连接断开时重试一次
            self.connect()
            self.channel.basic_publish(
                exchange="",
                routing_key="embedding_queue",
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,
                ),
            )


producer = RabbitMQProducer()
