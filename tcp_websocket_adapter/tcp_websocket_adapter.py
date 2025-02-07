import asyncio
import logging
import websockets
from asyncio import StreamReader, StreamWriter

class TCPWebSocketAdapter:
    """
    A class that adapts TCP and WebSocket connections, forwarding messages between them.

    This class listens for incoming WebSocket connections and forwards data between a TCP server
    and WebSocket clients. It also forwards messages from WebSocket clients to the TCP server.

    Attributes:
        tcp_host (str): The host address of the TCP server.
        tcp_port (int): The port number of the TCP server.
        ws_host (str): The host address for the WebSocket server (default is 'localhost').
        ws_port (int): The port number for the WebSocket server (default is 5050).
        buffer_size (int): The size of the buffer used to read data from the TCP connection.
        _ws_server (websockets.serve): The WebSocket server instance.
        _ws_server_runner_task (asyncio.Task): The task for running the WebSocket server.
    """

    def __init__(self, tcp_host, tcp_port, ws_host='localhost', ws_port=5050, buffer_size=1024):
        """
        Initializes the TCPWebSocketAdapter with the specified parameters.

        Args:
            tcp_host (str): The host address of the TCP server.
            tcp_port (int): The port number of the TCP server.
            ws_host (str): The host address for the WebSocket server. Default is 'localhost'.
            ws_port (int): The port number for the WebSocket server. Default is 5050.
            buffer_size (int): The size of the buffer for reading data from the TCP connection. Default is 1024.
        """
        self.tcp_host = tcp_host
        self.tcp_port = tcp_port
        self.ws_host = ws_host
        self.ws_port = ws_port
        self.buffer_size = buffer_size
        self._ws_server = None
        self._ws_server_runner_task = None

    @staticmethod
    def setup_logging(level=logging.INFO):
        """
        Configures logging for the application.

        This method allows users to set the logging level and format for the logs.

        Args:
            level (int): The logging level. Default is logging.INFO. You can use logging.DEBUG, logging.WARNING, etc.
        """
        logging.basicConfig(level=level, format="%(asctime)s - %(levelname)s - %(message)s")

    async def _forward_tcp_to_ws(self, reader: StreamReader, websocket):
        """
        Reads data from the TCP connection and forwards it to the WebSocket client.

        Args:
            reader (StreamReader): The reader used to read data from the TCP connection.
            websocket (websockets.WebSocketClientProtocol): The WebSocket connection to forward the data to.
        """
        buffer = bytearray()
        try:
            logging.info(f"Started forwarding from TCP {self.tcp_host}:{self.tcp_port} to WS {self.ws_host}:{self.ws_port}")
            while True:
                data = await reader.read(self.buffer_size)
                if not data:
                    logging.info("TCP connection closed by peer")
                    break

                buffer.extend(data)
                while b'\r\n' in buffer:
                    message, _, buffer = buffer.partition(b'\r\n')
                    logging.info(f"TCP -> WS: {message!r}")
                    try:
                        await websocket.send(message)
                    except websockets.exceptions.ConnectionClosed:
                        logging.warning("WebSocket client disconnected during forwarding")
                        break  # Stop forwarding if WebSocket is closed

        except (asyncio.CancelledError, websockets.exceptions.ConnectionClosed):
            logging.warning("Error during TCP to WebSocket forwarding")
        finally:
            logging.info("TCP connection handler exited")

    async def _forward_ws_to_tcp(self, websocket, writer: StreamWriter):
        """
        Reads data from the WebSocket client and forwards it to the TCP connection.

        Args:
            websocket (websockets.WebSocketClientProtocol): The WebSocket connection to read data from.
            writer (StreamWriter): The writer used to write data to the TCP connection.
        """
        try:
            logging.info(f"Started forwarding from WS {self.ws_host}:{self.ws_port} to TCP {self.tcp_host}:{self.tcp_port}")
            async for message in websocket:
                if isinstance(message, str):
                    message = message.encode()
                logging.info(f"WS -> TCP: {message!r}")
                writer.write(message + b'\r\n')
                await writer.drain()
        except (asyncio.CancelledError, websockets.exceptions.ConnectionClosed):
            logging.warning("Error during WebSocket to TCP forwarding")
        finally:
            logging.info("WebSocket connection handler exited")
            writer.close()
            await writer.wait_closed()

    async def _handle_ws_connection(self, websocket):
        """
        Handles an incoming WebSocket connection, creates TCP connection, and starts forwarding tasks.

        Args:
            websocket (websockets.WebSocketClientProtocol): The WebSocket connection to handle.
        """
        try:
            logging.info(f"New WebSocket connection established.")
            reader, writer = await asyncio.open_connection(self.tcp_host, self.tcp_port)

            # Start forwarding tasks for both TCP to WS and WS to TCP
            forward_tcp_task = asyncio.create_task(self._forward_tcp_to_ws(reader, websocket))
            forward_ws_task = asyncio.create_task(self._forward_ws_to_tcp(websocket, writer))
            await asyncio.gather(forward_tcp_task, forward_ws_task)

        except asyncio.CancelledError:
            logging.warning("WebSocket connection task cancelled unexpectedly")
        except Exception as e:
            logging.error(f"Error in WebSocket connection handling: {e}")
        finally:
            logging.info(f"WebSocket client disconnected")

    async def _ws_server_runner(self):
        """
        Starts the WebSocket server and keeps it running.
        This method will handle incoming WebSocket connections and delegate message forwarding.
        """
        try:
            self._ws_server = await websockets.serve(self._handle_ws_connection, self.ws_host, self.ws_port)
            logging.info(f"WebSocket server started at ws://{self.ws_host}:{self.ws_port}")
            await self._ws_server.wait_closed()
        except Exception as e:
            logging.error(f"Error starting WebSocket server: {e}")

    def start(self):
        """
        Starts the WebSocket server in the background.

        This method creates a background task to run the WebSocket server.
        """
        if not self._ws_server_runner_task or self._ws_server_runner_task.done():
            self._ws_server_runner_task = asyncio.create_task(self._ws_server_runner())
            logging.info("Server started successfully.")

    async def stop(self):
        """
        Stops the WebSocket server gracefully.

        This method closes the WebSocket server and cancels the background task associated with it.
        """
        if self._ws_server:
            self._ws_server.close()
            await self._ws_server.wait_closed()
            logging.info("Server stopped gracefully.")

        if self._ws_server_runner_task:
            self._ws_server_runner_task.cancel()
            try:
                await self._ws_server_runner_task
            except asyncio.CancelledError:
                logging.info("WebSocket server task was cancelled.")

        self._ws_server = None
        self._ws_server_runner_task = None
        logging.info("Server resources cleaned up.")
