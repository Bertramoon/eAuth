from typing import Optional, Union

from apiflask.validators import ValidationError, Validator

from ..utils.tool import is_ip


class IP(Validator):
    default_error_message = "Invalid ip address: {input}."

    def __init__(
        self,
        *,
        only_str: Optional[bool] = True,
        error: Optional[str] = None,
    ):
        self.only_str = only_str
        self.error = error

    def _repr_args(self) -> str:
        return f"only_str={self.only_str}"

    def _format_error(self, value: Union[str, int], message: str) -> str:
        return (self.error or message).format(input=value)

    def __call__(self, value: Union[str, int]) -> Union[str, int]:
        error_message = self.error or self.default_error_message
        if not isinstance(value, (str, int)) or not is_ip(value):
            raise ValidationError(self._format_error(value, error_message))

        return value
