class AcmeBaseError(Exception):
    pass


class AcmeError(AcmeBaseError):
    def __init__(self, detail: str) -> None:
        pass
    pass


class UnknownAcmeError(AcmeError):
    def __init__(self, type_: str, detail: str) -> None:
        self.type_ = type_
        self.detail = detail


class ErrorResponse(AcmeBaseError):
    def __init__(
            self,
            http_status: int,
            http_headers,
            http_body: bytes,
    ) -> None:
        self.http_status = http_status
        self.http_headers = http_headers
        self.http_body = http_body
        super().__init__(http_status, http_headers, http_body)


class ProtocolError(AcmeBaseError):
    def __init__(
            self,
            message,
            http_status,
            http_headers,
            http_body: bytes,
    ) -> None:
        self.message = message
        self.http_status = http_status
        self.http_headers = http_headers
        self.http_body = http_body
        super().__init__(message, http_status, http_headers, http_body)
