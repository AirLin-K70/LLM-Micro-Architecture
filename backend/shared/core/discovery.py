import socket
import logging
from nacos import NacosClient
from backend.shared.core.config import settings

logger = logging.getLogger(__name__)

# 动态修改 NacosClient 的 get_access_token 方法，如果没有用户名密码则跳过认证获取 token
original_get_access_token = NacosClient.get_access_token


def patched_get_access_token(self, force_refresh=False):
    """
    如果未提供用户名或密码，则跳过获取 access token 的过程，
    避免在无认证模式下的 Nacos 服务中报错。
    """
    if not self.username or not self.password:
        return
    return original_get_access_token(self, force_refresh)


NacosClient.get_access_token = patched_get_access_token


class NacosRegistry:
    """
    Nacos 服务注册与发现客户端封装。
    负责将当前服务注册到 Nacos Server，以及查询其他服务实例。
    """

    def __init__(self):
        self.server_addresses = settings.NACOS_SERVER_ADDR
        self.namespace = settings.NACOS_NAMESPACE

        if not self.namespace:
            self.namespace = None

        username = settings.NACOS_USERNAME
        password = settings.NACOS_PASSWORD

        if not username:
            username = None
        if not password:
            password = None

        self.client = NacosClient(
            self.server_addresses,
            namespace=self.namespace,
            username=username,
            password=password,
        )

    def register_service(
        self, service_name: str, host: str, port: int, group_name: str = "DEFAULT_GROUP"
    ):
        """
        注册服务实例到 Nacos。
        :param service_name: 服务名称
        :param host: 服务主机 IP
        :param port: 服务端口
        :param group_name: 分组名称
        """
        try:
            # 注册实例，并设置较短的心跳间隔以确保服务稳定性
            self.client.add_naming_instance(
                service_name,
                host,
                port,
                group_name=group_name,
                heartbeat_interval=5,
            )
            logger.info(
                f"Successfully registered service {service_name} at {host}:{port}"
            )
        except Exception as e:
            logger.error(f"Failed to register service {service_name}: {e}")

    def deregister_service(
        self, service_name: str, host: str, port: int, group_name: str = "DEFAULT_GROUP"
    ):
        """
        从 Nacos 注销服务实例。
        通常在服务关闭时调用。
        """
        try:
            self.client.remove_naming_instance(
                service_name, host, port, group_name=group_name
            )
            logger.info(f"Successfully deregistered service {service_name}")
        except Exception as e:
            logger.error(f"Failed to deregister service {service_name}: {e}")

    def get_service(self, service_name: str, group_name: str = "DEFAULT_GROUP"):
        """
        获取指定服务的实例列表。
        :return: 服务实例列表
        """
        try:
            return self.client.list_naming_instance(service_name, group_name=group_name)
        except Exception as e:
            logger.error(f"Failed to get service {service_name}: {e}")
            return []


def get_local_ip():
    """
    获取本机局域网 IP 地址。
    通过建立一个 UDP 连接（不会实际发送数据）来自动选择合适的网卡 IP。
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # 尝试连接一个公网地址（这里用的是保留地址），系统会自动分配出口 IP
        s.connect(("10.255.255.255", 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = "127.0.0.1"
    finally:
        s.close()
    return IP


# 全局单例注册对象
registry = NacosRegistry()
