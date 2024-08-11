import logging
from abc import abstractmethod, ABC
from typing import Optional

from flask import current_app

from .email import send_mail

logger = logging.getLogger(__name__)


class MessageUtil(ABC):
    """
    审计日志接口。需要注意的是，每个接口只能有一个input和output schema实现该接口，否则出现多个schema相互覆盖的情况就可能会得到不符合预期的结果
    """

    @abstractmethod
    def send(self, *, sender, receiver, title, message, **kwargs):
        pass


class EmailMessageUtil(MessageUtil):
    def send(self, sender: Optional[str], receiver: str, title: str, message: str, **kwargs):
        domain_only = current_app.config.get("MAIL_DOMAIN_ONLY")
        if not isinstance(receiver, str) or (
                domain_only and receiver and not (receiver.count('@') == 1 and receiver.split('@')[-1] == domain_only)):
            logger.warning(f"[send email] Failed to send email because of only support domain from {domain_only}"
                           f" but the receiver is {receiver}")
            return
        send_mail(title, receiver, message, **kwargs)


message_util = EmailMessageUtil()
