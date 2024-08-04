from abc import abstractmethod, ABC
from .email import send_mail


class MessageUtil(ABC):
    """
    审计日志接口。需要注意的是，每个接口只能有一个input和output schema实现该接口，否则出现多个schema相互覆盖的情况就可能会得到不符合预期的结果
    """

    @abstractmethod
    def send(self, *, sender, receiver, title, message, **kwargs):
        pass


class EmailMessageUtil(MessageUtil):
    def send(self, sender, receiver, title, message, **kwargs):
        send_mail(title, receiver, message, **kwargs)


message_util = EmailMessageUtil()
