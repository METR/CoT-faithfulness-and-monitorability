import asyncio
import os
from typing import Any

import anyio
from anthropic import AsyncAnthropic
from anyio.streams.memory import MemoryObjectReceiveStream
from dotenv import load_dotenv
from inspect_ai.model import GenerateConfig
from inspect_ai.model._providers._anthropic_batch import AnthropicBatcher
from inspect_ai.model._providers.util.batch import Batch, BatchRequest


async def _receive_and_print(batch_id: str, stream: MemoryObjectReceiveStream[Any]):
    _ = await stream.receive()
    print(f"Received message for {batch_id}")


async def download_batch_results():
    # Load environment variables
    load_dotenv()

    # Initialize the Anthropic client
    client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    # The batch ID you want to download
    batch_id = "msgbatch_01KxGrRr7ZZHoAQZsniSpPE8"

    while True:
        requests: dict[str, BatchRequest[Any]] = {}
        streams: dict[str, MemoryObjectReceiveStream[Any]] = {}

        with open("custom_ids.txt", "r") as f:
            for line in f:
                custom_id = line.strip()
                print(custom_id + " added to requests")
                stream = anyio.create_memory_object_stream[Any](max_buffer_size=100)
                requests[custom_id] = BatchRequest(
                    request={},
                    result_stream=stream[0],
                )
                streams[custom_id] = stream[1]

        batch = Batch[Any](
            id=batch_id,
            requests=requests,
        )

        batcher = AnthropicBatcher(client, GenerateConfig())
        await asyncio.gather(
            batcher._handle_batch_result(batch, True),  # pyright: ignore[reportPrivateUsage]
            *[
                _receive_and_print(batch_id, stream)
                for batch_id, stream in streams.items()
            ],
        )


if __name__ == "__main__":
    asyncio.run(download_batch_results())
