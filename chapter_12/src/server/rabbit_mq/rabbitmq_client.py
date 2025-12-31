import os
import json
import asyncio
import aio_pika
import traceback

from typing import Optional, Callable, Awaitable
from dotenv import load_dotenv

from logger.logger import Logger



class RabbitmqConnection:
    _instance: Optional["RabbitmqConnection"] = None
    _connection: Optional[aio_pika.Connection] = None
    _channel: Optional[aio_pika.Channel] = None

    def __new__(cls):
        # Singleton pattern: reuse 1 connection/channel across one OS process.
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    

    def __init__(self):
        self.logger = Logger("rabbit_mq").getLogger()
        self.is_connection_created = False

        try:
            # Load environment variables
            server_home_dir = os.getenv("PWD")    # Equal to 'os.getcwd()'
            config_env = f"{server_home_dir}/config/config.env"
            load_dotenv(config_env)

            debug_msg = f"RabbitmqConnection(), RabbitmqConnection initialized successfully."
            self.logger.debug(debug_msg)

        except Exception as e:
            warn_msg = f"RabbitmqConnection(), Failed to initialize RabbitmqConnection, error message: '{str(e)}'."
            self.logger.warning(warn_msg)



    async def connect(self):
        """Initialize RabbitMQ connection/channel (call once at startup)"""
        if self._connection and not self._connection.is_closed:
            debug_msg = f"connect(), Reuse existing connection."
            self.logger.debug(debug_msg)
            return  
        
        try:
            connection_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")

            # Connect to RabbitMQ (robust = auto-reconnect on failure)
            self._connection = await aio_pika.connect_robust(
                url=connection_url,
                timeout=30  # Avoid connection timeouts
            )

            # Create a channel (1 channel per app is sufficient for dev/prod)
            self._channel = await self._connection.channel()

            # Declare queues (idempotent: safe to call multiple times)
            await self._declare_queues()

            debug_msg = f"connect(), RabbitMQ connection '{connection_url}' is established."
            self.logger.debug(debug_msg)

        except ConnectionError as e:
            warn_msg = f"connect(), Could not connect to RabbitMQ. Check if the server is running."
            self.logger.warning(warn_msg)

        except aio_pika.exceptions.AMQPConnectionError as e:
            warn_msg = f"connect(), AMQP specific connection error: '{str(e)}'."
            self.logger.warning(warn_msg)

        except Exception as e:
            warn_msg = f"connect(), An unexpected error occurred: '{str(e)}'."
            self.logger.warning(warn_msg)


    async def _declare_queues(self):
        """Declare all required queues (match your workflow)"""
        queues = [
            os.getenv("RABBITMQ_QUEUE_FASTAPI_TO_ORCH"),
            os.getenv("RABBITMQ_QUEUE_ORCH_TO_FASTAPI")
        ]
        for queue_name in queues:
            if queue_name:  # Ensure queue name is not None
                await self._channel.declare_queue(
                    queue_name,
                    durable=True  # Persist queue across RabbitMQ restarts
                )


    @property
    def channel(self) -> aio_pika.Channel:
        """
        Get the active RabbitMQ channel with initialization check.
        """
        if not self._connection or self._connection.is_closed:
            if self.is_connection_created:
                warn_msg = "channel(), RabbitMQ connection not established. Call connect() first."
                self.logger.warning(warn_msg)
            else:
                self.is_connection_created = True
            return None

        if not self._channel or self._channel.is_closed:
            # Attempt to recreate channel if connection exists but channel is closed
            try:
                # Run synchronous channel creation (since properties can't be async)
                loop = asyncio.get_event_loop()
                self._channel = loop.run_until_complete(self._connection.channel())
                loop.run_until_complete(self._declare_queues())
                self.logger.debug("channel(), Recreated RabbitMQ channel")
                
            except Exception as e:
                warn_msg = f"channel(), Failed to recreate channel: '{str(e)}'"
                self.logger.warning(warn_msg)
                return None

        return self._channel


    async def close(self):
        """
        Cleanup connection on shutdown.
        """
        if self._connection and not self._connection.is_closed:
            try:
                await self._connection.close()
                debug_msg = f"close(), RabbitMQ connection has been successfully closed."
                self.logger.debug(debug_msg)

            except Exception as e:
                warn_msg = f"close(), Following exception was thrown when closing RabbitMQ connection: \n"
                warn_msg += f"\t '{str(e)}'."
                self.logger.warning(warn_msg)



class RabbitmqClient:
    def __init__(
            self, 
            client_name: str="",
            input_queue: str=""
        ):
        self.client_name = client_name.strip()
        self.input_queue = input_queue
        self.connection = RabbitmqConnection()
        self.consumer_tag = None
        self.logger = None

        try:
            self.logger = Logger("rabbit_mq").getLogger()
            debug_msg = f"RabbitmqClient(), rabbitmq client '{self.client_name}' initialized successfully."
            self.logger.debug(debug_msg)

        except Exception as e:
            warn_msg = f"RabbitmqClient(), Failed to initialize rabbitmq client '{self.client_name}', \n"
            warn_msg += f"\t '{str(e)}'."
            self.logger.warning(warn_msg)
        

    async def connect(self):
        """
        Connect to RabbitMQ using the singleton connection.
        """
        await self.connection.connect()



    async def start_consuming(
            self, 
            message_handler: Callable[[aio_pika.IncomingMessage], Awaitable[None]]
        ):
        """
        Start consuming messages from the input queue
        """
        try:
            if not self.connection.channel:
                warn_msg = f"start_consuming(), RabbitMQ channel not available, ensure connect() completed successfully."
                self.logger.warning(warn_msg)
                return
            
            # Declare the queue 
            queue = await self.connection.channel.declare_queue(
                self.input_queue,
                durable=True
            )

            self.consumer_tag = await queue.consume(
                callback=message_handler,
                no_ack=False  # Manual ack (via message.process())
            )
            debug_msg = f"start_consuming(), rabbitmq client '{self.client_name}' started, \n"
            debug_msg += f" creating a consumer with tag '{self.consumer_tag}',"
            debug_msg += f" listening to the messages on queue '{self.input_queue}'."
            self.logger.debug(debug_msg)

        except Exception as e:
            warn_msg = f"start_consuming(), Fail to start the rabbitmq client '{self.client_name}' "
            warn_msg == f"with message queue '{self.input_queue}'. Exception: '{str(e)}'."
            self.logger.warning(warn_msg)


    async def stop_consuming(self):
        """Stop consuming messages using the stored consumer_tag"""
        if not self.consumer_tag or not self.connection.channel:
            self.logger.debug("stop_consuming(), No active consumer to cancel")
            return

        try:
            # Get the queue instance again (since we need it to cancel consumption)
            queue = await self.connection.channel.get_queue(self.input_queue)
            
            # Cancel the consumer using the queue's cancel method
            await queue.cancel(self.consumer_tag)
            
            self.logger.debug(
                f"stop_consuming(), Consumer '{self.consumer_tag}' "
                f"on queue '{self.input_queue}' canceled successfully"
            )
            self.consumer_tag = None  # Clear the tag after cancellation

        except aio_pika.exceptions.QueueNotFound:
            self.logger.warning(f"stop_consuming(), Queue '{self.input_queue}' not found")
        except Exception as e:
            self.logger.warning(
                f"stop_consuming(), Failed to cancel consumer '{self.consumer_tag}': {str(e)}"
            )


    async def publish_message(
            self, 
            routing_key: str, 
            data: dict, 
            correlation_id: Optional[str] = None
        ):
        """
        Publish a message to a specified queue.
        """
        await self.connection.channel.default_exchange.publish(
            aio_pika.Message(
                body=json.dumps(data).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                correlation_id=correlation_id
            ),
            routing_key=routing_key
        )

        debug_msg = f"publish_message(), Message is successfully published to '{routing_key}' "
        debug_msg += f"(correlation ID: {correlation_id})."

        data_str = json.dumps(data, ensure_ascii=False, indent=2)
        debug_msg += f"Following is the message: \n{data_str}\n"
        self.logger.debug(debug_msg)



    async def close(self):
        """
        Stop consuming and close the connection.
        """
        if self.consumer_tag and self.connection.channel:
            # Terminate the consumer if active
            await self.stop_consuming()
            
        await self.connection.close()
        debug_msg = f"close(), rabbitmq client '{self.client_name}' is successfully closed."
        self.logger.debug(debug_msg)