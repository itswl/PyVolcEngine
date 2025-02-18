# coding: utf-8

from __future__ import absolute_import

import volcenginesdkredis
from whitelist_base_manager import WhitelistBaseManager

class RedisWhitelistManager(WhitelistBaseManager):
    """Redis服务的白名单管理类

    继承自WhitelistBaseManager，实现Redis服务特定的白名单操作。
    """

    def __init__(self):
        super().__init__()
        self.api = volcenginesdkredis
        self.client_api = self.api.REDISApi()
