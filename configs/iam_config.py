"""火山引擎 IAM 配置文件

本配置文件包含IAM用户和用户组的配置信息：
- 用户配置：包含用户的团队归属、显示名称、用户名和认证方式
- 用户组配置：包含各团队的用户组信息

作者: IAM Team
日期: 2024
"""

# 用户信息配置
# teams字段是一个列表，支持用户同时属于多个团队
# auth_type可以是："password"（仅密码登录）、"access_key"（仅访问密钥）、"both"（两者都需要）或"none"（都不需要）
# password字段是可选的，如果不设置则使用默认密码
USER_CONFIG = [
    {"teams": ["product"], "display_name": "产品经理-张三", "user_name": "prod1", "auth_type": "password"},
    {"teams": ["development"], "display_name": "开发工程师-李四", "user_name": "dev1", "auth_type": "both", "password": "Dev2024@Li4"},
    {"teams": ["development"], "display_name": "开发工程师-王五", "user_name": "dev2", "auth_type": "both", "password": "Dev2024@Wang5"},
    {"teams": ["development", "ops"], "display_name": "开发工程师-赵六", "user_name": "dev3", "auth_type": "both"},
    {"teams": ["development"], "display_name": "开发工程师-孙七", "user_name": "dev4", "auth_type": "both"},
    {"teams": ["product", "development"], "display_name": "产品经理-周八", "user_name": "prod2", "auth_type": "none"},
    {"teams": ["ops", "development"], "display_name": "运维工程师-郑十", "user_name": "ops2", "auth_type": "access_key"},
]

# 用户组配置
# 定义各团队的用户组信息，包括描述、显示名称和用户组名称
TEAM_GROUPS = {
    "product": {
        "description": "产品团队用户组 - 用于管理产品团队成员的权限",
        "display_name": "产品团队",
        "user_group_name": "pm-team",
        "policies": ["ReadOnlyAccess", "TicketFullAccess"]
    },
    "development": {
        "description": "开发团队用户组 - 用于管理开发团队成员的权限",
        "display_name": "开发团队",
        "user_group_name": "dev-team",
        "policies": ["ReadOnlyAccess",  "TicketFullAccess", "VKEInnerFullAccess", "VeFaaSFullAccess", "DbwFullAccess"]
    },
    "ops": {
        "description": "运维团队用户组 - 用于管理运维团队成员的权限",
        "display_name": "运维团队",
        "user_group_name": "ops-team",
        "policies": ["AdministratorAccess"]
    }
}

# 默认密码配置
DEFAULT_PASSWORD = "DefaultPassword123!"

# 密钥存储目录配置
SECRET_DIR = "./logs/secrets"