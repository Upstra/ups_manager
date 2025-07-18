from redis import Redis
from dotenv import load_dotenv
from os import environ as env

from data_retriever.cache_element import deserialize_element, VCenterElement, deserialize_vcenter, VMwareElement

load_dotenv()

VCENTER = "metrics:vcenter"
ELEMENTS = "metrics:elements"
METRICS = "metrics:metrics"

class CacheException(Exception):
    def __init__(self, message):
        self.message = message

class Cache:
    def __init__(self):
        try:
            host = env.get('REDIS_HOST')
            port = int(env.get('REDIS_PORT'))
            password = env.get('REDIS_PASSWORD')
            username = env.get('REDIS_USERNAME')

            self._redis = Redis(
                host=host,
                port=port,
                password=password,
                username=username,
                decode_responses=True
            )
            self._redis.ping()
        except Exception as e:
            raise CacheException(f"Failed to connect to Redis: {e}") from e

    def get_elements(self) -> list[VMwareElement]:
        """
        Get all VMware elements that we need to get metrics from
        Returns:
            (list[VMwareElement]): The VMware elements that we need to get metrics from
        Raises:
            CacheException: If an error occured while getting VMware elements
        """
        try:
            return [deserialize_element(element) for element in self._redis.lrange(ELEMENTS, 0, -1)]
        except Exception as e:
            raise CacheException(f"Failed to get elements from Redis: {e}") from e

    def get_vcenter(self) -> VCenterElement:
        """
        Get `VCenter` element from Redis
        Returns:
            (VCenterElement): The `VCenter` element from Redis, or None if it doesn't exist
        Raises:
            CacheException: If an error occured while getting vCenter element
        """
        try:
            return deserialize_vcenter(self._redis.get(VCENTER))
        except Exception as e:
            raise CacheException(f"Failed to get vCenter from Redis: {e}") from e

    def set_metrics(self, element: str, metrics: str):
        """
        Set the metrics of a VMware element
        Args:
            element (str): The serialized JSON `VMwareElement`
            metrics (str): The serialized JSON of the metrics of the element
        Raises:
            CacheException: If an error occured while setting metrics
        """
        try:
            self._redis.hset(METRICS, element, metrics)
        except Exception as e:
            raise CacheException(f"Failed to push metrics to Redis: {e}") from e
