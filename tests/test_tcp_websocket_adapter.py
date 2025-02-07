import asyncio
import pytest
import websockets
from tcp_websocket_adapter import TCPWebSocketAdapter

TCP_HOST = "localhost"
TCP_PORT = 4242
WS_HOST = "localhost"
WS_PORT = 5050


@pytest.fixture
async def mock_tcp_server():
    """Creates a fake TCP server to test against."""
    clients = []

    async def handle_client(reader, writer):
        clients.append(writer)
        try:
            while data := await reader.read(1024):
                for client in clients:
                    if client is not writer:
                        client.write(data)
                        await client.drain()
        except asyncio.CancelledError:
            pass
        finally:
            clients.remove(writer)
            writer.close()
            await writer.wait_closed()

    server = await asyncio.start_server(handle_client, TCP_HOST, TCP_PORT)
    yield server
    server.close()
    await server.wait_closed()

@pytest.fixture
async def bridge():
    """Creates the bridge and starts it."""
    bridge = TCPWebSocketAdapter(TCP_HOST, TCP_PORT, WS_HOST, WS_PORT)
    bridge.start()
    await asyncio.sleep(1)
    yield bridge
    await bridge.stop()


@pytest.mark.asyncio
async def test_start_stop(bridge):
    """Test if the WebSocket server starts and stops correctly."""
    assert bridge._ws_server is not None
    assert bridge._ws_server_runner_task is not None

    await bridge.stop()
    assert bridge._ws_server is None
    assert bridge._ws_server_runner_task is None

@pytest.mark.asyncio
async def test_client_disconnects(bridge):
    """Test if the bridge handles client disconnections properly."""
    async with websockets.connect(f"ws://{WS_HOST}:{WS_PORT}") as ws:
        pass

    await asyncio.sleep(0.5)
    assert bridge._ws_server is not None


@pytest.mark.asyncio
async def test_tcp_to_websocket(mock_tcp_server, bridge):
    """Test if a TCP message is received on the WebSocket."""
    async with websockets.connect(f"ws://{WS_HOST}:{WS_PORT}") as ws:
        reader, writer = await asyncio.open_connection(TCP_HOST, TCP_PORT)

        message = b"Hello from TCP\r\n"
        writer.write(message)
        await writer.drain()

        received = await ws.recv()
        assert received == message.strip()

        writer.close()
        await writer.wait_closed()


@pytest.mark.asyncio
async def test_websocket_to_tcp(mock_tcp_server, bridge):
    """Test if a WebSocket message is received on the TCP server."""
    reader, writer = await asyncio.open_connection(TCP_HOST, TCP_PORT)

    async with websockets.connect(f"ws://{WS_HOST}:{WS_PORT}") as ws:
        message = "Hello from WebSocket"
        await ws.send(message)

        received = await reader.read(len(message) + 2)  # +2 for \r\n
        assert received == message.encode() + b'\r\n'

    writer.close()
    await writer.wait_closed()


@pytest.mark.asyncio
async def test_tcp_message_sent_to_multiple_ws_clients(mock_tcp_server, bridge):
    """Test if a TCP message is received and forwarded to multiple WebSocket clients."""

    async with websockets.connect(f"ws://{WS_HOST}:{WS_PORT}") as ws1:
        async with websockets.connect(f"ws://{WS_HOST}:{WS_PORT}") as ws2:
            reader, writer = await asyncio.open_connection(TCP_HOST, TCP_PORT)

            message = b"Hello from TCP\r\n"
            writer.write(message)
            await writer.drain()

            await asyncio.sleep(0.1)

            received_ws1 = await ws1.recv()
            received_ws2 = await ws2.recv()

            assert received_ws1.strip() == message.strip()
            assert received_ws2.strip() == message.strip()

            writer.close()
            await writer.wait_closed()