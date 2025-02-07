
# TCP to WebSocket Adapter

A Python library that acts as a bridge between a TCP server and WebSocket clients. This adapter listens for incoming WebSocket connections and forwards data between a TCP server and connected WebSocket clients, as well as forwards messages from WebSocket clients to the TCP server.

## Why I Created This

I created this library because I needed a way to connect to an old device that only supports a TCP socket connection, but I wanted to interact with it via WebSocket (for use with a browser-based client). Since no straightforward solution existed for this problem, I built this library to bridge the gap between TCP socket and WebSocket communication. If you're facing the same challenge, this adapter might be just what you need!

## Features

- Bridges TCP communication to WebSocket clients.
- Forwards WebSocket messages to a TCP server.
- Configurable buffer size and host/port parameters.
- Supports handling multiple WebSocket clients.
- Graceful start/stop of WebSocket server and TCP connection.

## Installation (Soon)

You can install the package from PyPI via `pip`:

```bash
pip install tcp-websocket-adapter
```

Alternatively, you can clone the repository and install it locally:

```bash
git clone https://github.com/your-username/tcp-websocket-adapter.git
cd tcp-websocket-adapter
pip install .
```

## Usage

Here’s how to use the adapter in your Python project:

### Example:

```python
import asyncio
from tcp_websocket_adapter import TCPWebSocketAdapter

# Initialize the adapter with TCP server details and WebSocket server settings
adapter = TCPWebSocketAdapter(tcp_host='localhost', tcp_port=12345, ws_host='localhost', ws_port=5050)

# Start the WebSocket server
adapter.start()

# Optionally, set logging level
TCPWebSocketAdapter.setup_logging(logging.DEBUG)

# Run the event loop
try:
    asyncio.get_event_loop().run_forever()
except KeyboardInterrupt:
    pass
finally:
    # Gracefully stop the server
    asyncio.run(adapter.stop())
```

## Configuration

- `tcp_host`: Host of the TCP server (e.g., `'localhost'`).
- `tcp_port`: Port of the TCP server (e.g., `12345`).
- `ws_host`: Host for the WebSocket server (default is `'localhost'`).
- `ws_port`: Port for the WebSocket server (default is `5050`).
- `buffer_size`: Buffer size used for reading data from the TCP connection (default is `1024`).

## Logging

The library uses Python's built-in `logging` module to output logs. You can configure the logging level using the `setup_logging` method.

```python
TCPWebSocketAdapter.setup_logging(logging.DEBUG)
```

Log messages will include the timestamp, log level, and message.

## Testing

To run the unit tests for the package, use the following command:

```bash
pytest
```

Make sure you have `pytest` installed (you can install it with `pip install pytest`).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributions

Contributions are welcome! Please fork this repository and create a pull request with your improvements or fixes.

## Contact

If you have any questions or issues with the adapter, feel free to reach out or open an issue on GitHub.

- GitHub: [https://github.com/jokicjovan/TCP-WebSocket-Adapter](https://github.com/jokicjovan/TCP-WebSocket-Adapter)
