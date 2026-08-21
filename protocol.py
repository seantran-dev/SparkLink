import struct


class Protocol:

    @staticmethod
    def encode(message):
        """
        Convert a string message into a framed byte sequence.

        Format:

            [4-byte message length][message bytes]
        """

        data = message.encode("utf-8")

        length = struct.pack(
            "!I",
            len(data)
        )

        return length + data

    @staticmethod
    def receive(sock):
        """
        Receive exactly one complete message
        from a TCP socket.

        Returns:
            str | None
        """

        # -----------------------------------------------------
        # Receive the 4-byte message length
        # -----------------------------------------------------

        header = Protocol._receive_exact(
            sock,
            4
        )

        if header is None:
            return None

        length = struct.unpack(
            "!I",
            header
        )[0]

        # -----------------------------------------------------
        # Receive the actual message
        # -----------------------------------------------------

        data = Protocol._receive_exact(
            sock,
            length
        )

        if data is None:
            return None

        return data.decode("utf-8")

    @staticmethod
    def _receive_exact(sock, amount):
        """
        Receive exactly `amount` bytes.

        TCP may split one message across multiple
        recv() calls, so we keep receiving until
        we have everything.
        """

        data = bytearray()

        while len(data) < amount:

            chunk = sock.recv(
                amount - len(data)
            )

            if not chunk:
                return None

            data.extend(chunk)

        return bytes(data)