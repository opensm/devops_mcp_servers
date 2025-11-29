from common.loger import logger


class DataBaseException(Exception):
    """
    数据处理异常
    """

    def __init__(self, message):
        super().__init__(message)
        self.message = "【工作流数据处理异常】" + message
        logger.error(self.message)


class DataTypeError(DataBaseException):
    """
    数据类型错误
    """

    def __init__(self, message):
        super().__init__(message)
        self.message = "【工作流数据类型异常】" + message
        logger.debug(self.message)


class DataValueError(DataBaseException):
    """
    数据值错误
    """

    def __init__(self, message):
        super().__init__(message)
        self.message = "【工作流数据值异常】" + message
        logger.error(self.message)


class DataKeyError(DataBaseException):
    """
    数据键错误
    """

    def __init__(self, message):
        super().__init__(message)
        self.message = "【工作流数据键异常】" + message
        logger.error(self.message)


class FormatException(Exception):
    """
    数据格式错误
    """

    def __init__(self, message):
        super().__init__(message)
        self.message = "【工作流数据格式异常】" + message
        logger.error(self.message)


class DataNOtFound(DataBaseException):
    """
    数据不存在
    """

    def __init__(self, message):
        super().__init__(message)
        self.message = "【工作流数据不存在】" + message
        logger.debug(self.message)
