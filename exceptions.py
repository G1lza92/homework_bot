class SendMessageFail(Exception):
    """Исключение отправки сообщения."""

    pass


class APIResponseStatusException(Exception):
    """Исключение сбоя запроса к API."""

    pass


class UnknownStatusException(Exception):
    """Исключение неизвестного статуса домашней работы."""

    pass
