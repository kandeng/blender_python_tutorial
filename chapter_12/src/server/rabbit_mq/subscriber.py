import asyncio
import json
import os
from aio_pika import IncomingMessage
from rabbitmq_service import RabbitMQService

# Load environment variables
from dotenv import load_dotenv
server_home_dir = os.getenv("PWD")    # Equal to 'os.getcwd()'
config_env = f"{server_home_dir}/config/config.env"
load_dotenv(config_env)




async def message_handler(message: IncomingMessage):
    """Handle incoming messages from RabbitMQ"""
    try:
        # Process the message
        async with message.process():  # Acknowledges message on exit
            data = json.loads(message.body.decode())
            print("\nReceived message:")
            print(f"Correlation ID: {message.correlation_id}")
            print(f"Body: {json.dumps(data, indent=2)}")
            
    except json.JSONDecodeError:
        print("Failed to decode JSON message")
    except Exception as e:
        print(f"Error processing message: {str(e)}")


async def main():
    # target_queue = os.getenv("RABBITMQ_QUEUE_FASTAPI_TO_ORCH", "fastapi_to_orch")
    target_queue = os.getenv("RABBITMQ_QUEUE_TEST_SUBSCRIBER", "test_subscriber")
    
    if not target_queue:
        print("Error: RABBITMQ_QUEUE_FASTAPI_TO_ORCH not set in .env")
        return

    subscriber = RabbitMQService(
        service_name="subscriber",
        input_queue=target_queue
    )
    
    try:
        await subscriber.connect()

        # Start consuming with the correct method
        await subscriber.start_consuming(message_handler)
        
        # Keep the service running
        while subscriber.connection.channel:
            await asyncio.sleep(10)
        
        await subscriber.close()


    except KeyboardInterrupt:
        print("\nStopping subscriber...")
    except Exception as e:
        print(f"Subscription failed: {str(e)}")
    finally:
        await subscriber.close()

if __name__ == "__main__":
    asyncio.run(main())