from __future__ import absolute_import

import volcenginesdkrdspostgresql
from whitelist_base_manager import WhitelistBaseManager

class PostgreSQLWhitelistManager(WhitelistBaseManager):
    """PostgreSQL白名单管理类
    这个类继承自WhitelistBaseManager，提供了PostgreSQL数据库的白名单管理功能。
    """

    def __init__(self):
        super().__init__()
        self.api = volcenginesdkrdspostgresql
        self.client_api = self.volcenginesdkrdspostgresql.RDSPOSTGRESQLApi()
