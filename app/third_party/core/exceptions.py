class ThirdPartyRequestException(Exception):
    """
    产品级别：第三方接口请求异常。
    """
    def __init__(self, message: str):
        super().__init__(message)