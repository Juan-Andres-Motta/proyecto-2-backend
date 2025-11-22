from abc import ABC, abstractmethod


class SQSEventPublisherPort(ABC):
    """Port for publishing events directly to SQS queues."""

    @abstractmethod
    async def publish_routes_generated(self) -> None:
        """
        Publish delivery_routes_generated void event to BFF queue.

        This is a trigger event for UI to refetch data.
        """
        pass
