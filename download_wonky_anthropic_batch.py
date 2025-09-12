import asyncio
import os

from anthropic import AsyncAnthropic
from dotenv import load_dotenv


async def download_batch_results():
    # Load environment variables
    load_dotenv()

    # Initialize the Anthropic client
    client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    # The batch ID you want to download
    batch_id = "msgbatch_01KxGrRr7ZZHoAQZsniSpPE8"

    try:
        while True:
            # Retrieve the batch results
            async for _ in await client.messages.batches.results(batch_id):
                print(".", end="", flush=True)
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(download_batch_results())
