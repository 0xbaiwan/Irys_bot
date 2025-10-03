from models import OperationResult


def operation_failed(pk_or_mnemonic: str, data: dict = None) -> OperationResult:
    return OperationResult(
        pk_or_mnemonic=pk_or_mnemonic,
        data=data,
        status=False,
    )


def operation_success(pk_or_mnemonic: str, data: dict = None) -> OperationResult:
    return OperationResult(
        pk_or_mnemonic=pk_or_mnemonic,
        data=data,
        status=True,
    )


def validate_error(error: Exception) -> str:
    error_message = str(error).lower()

    if "operation timed out after" in error_message:
        return "服务器未及时响应"

    elif (
        "curl: (7)" in error_message
        or "curl: (28)" in error_message
        or "curl: (16)" in error_message
        or "connect tunnel failed" in error_message
    ):
        return "代理失败" if "connect tunnel failed" not in error_message else f"连接失败: {error_message}"

    elif "timed out" in error_message or "operation timed out" in error_message:
        return "连接超时"

    elif "empty document" in error_message or "expecting value" in error_message:
        return "收到空响应"

    elif (
            "curl: (35)" in error_message
            or "curl: (97)" in error_message
            or "eof" in error_message
            or "curl: (56)" in error_message
            or "ssl" in error_message
    ):
        return "SSL 错误。如果此类错误很多，请尝试安装证书。"

    elif "417 Expectation Failed" in error_message:
        return "417 预期失败"

    elif "unsuccessful tunnel" in error_message:
        return "TLS 隧道不成功"

    elif "connection error" in error_message:
        return "连接错误"

    else:
        return error_message
