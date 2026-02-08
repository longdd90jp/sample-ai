import asyncio
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport

async def main():
    transport = StreamableHttpTransport(url="http://localhost:8000/mcp")
    client = Client(transport)

    async with client:
        # gọi tool process_data
        result = await client.call_tool("process_data", {"input": "sample"})
        print(result)

if __name__ == "__main__":
    asyncio.run(main())
