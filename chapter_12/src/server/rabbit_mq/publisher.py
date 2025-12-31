import os
import asyncio
import json

from rabbit_mq.rabbitmq_client import RabbitmqClient

# Load environment variables
from dotenv import load_dotenv
server_home_dir = os.getenv("PWD")    # Equal to 'os.getcwd()'
config_env = f"{server_home_dir}/config/config.env"
load_dotenv(config_env)


async def main():
    # Configure the queue to publish to (use one of your existing queues)
    demo_queue = os.getenv("RABBITMQ_QUEUE_DEMO", "demo_queue")
    
    if not demo_queue:
        print("Error: RABBITMQ_QUEUE_FASTAPI_TO_ORCH not set in .env")
        return

    # Initialize publisher service
    publisher = RabbitmqClient(
        client_name="publisher",
        input_queue=demo_queue
    )
    
    try:
        # Connect to RabbitMQ
        await publisher.connect()

        # Sample message data
        message_data = {
            "job_id": "test-123",  
            "action": "test_publish",
            "timestamp": asyncio.get_event_loop().time(),
            "prompt": "Hello from publisher!",
            "metadata": {"test": True, "version": "1.0"}
        }

        # Publish the message
        await publisher.publish_message(
            routing_key=demo_queue,
            data=message_data,
            correlation_id="test-12345"  # Optional: for tracking messages
        )

    except Exception as e:
        print(f"Publish failed: {str(e)}")
    finally:
        # Clean up connection
        await publisher.close()

if __name__ == "__main__":
    asyncio.run(main())

