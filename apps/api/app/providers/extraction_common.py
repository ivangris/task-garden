from __future__ import annotations


class ExtractionProviderError(RuntimeError):
    def __init__(self, reason: str, message: str) -> None:
        super().__init__(message)
        self.reason = reason
        self.message = message


class ProviderUnavailableError(ExtractionProviderError):
    def __init__(self, message: str = "The extraction provider is unavailable.") -> None:
        super().__init__("provider_unavailable", message)


class ProviderTimeoutError(ExtractionProviderError):
    def __init__(self, message: str = "The extraction provider timed out.") -> None:
        super().__init__("provider_timeout", message)


class MalformedStructuredOutputError(ExtractionProviderError):
    def __init__(self, message: str = "The extraction provider returned malformed structured output.") -> None:
        super().__init__("malformed_output", message)


class EmptyExtractionResponseError(ExtractionProviderError):
    def __init__(self, message: str = "The extraction provider returned an empty response.") -> None:
        super().__init__("empty_response", message)


class LowSignalExtractionError(ExtractionProviderError):
    def __init__(self, message: str = "The extraction provider returned too little actionable structure.") -> None:
        super().__init__("low_signal_response", message)
