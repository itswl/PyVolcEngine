# 白名单配置
whitelist_config = {
    "whitelists": [
        {
            "name": "default-whitelist",
            "ip_list": ["0.0.0.0/0"],
            "description": "默认白名单配置",
            "type": "IPv4"
        },
        {
            "name": "office-whitelist",
            "ip_list": ["192.168.1.0/24", "192.168.2.0/24"],
            "description": "办公网络白名单",
            "type": "IPv4"
        },
        {
            "name": "vpc-whitelist",
            "ip_list": ["172.16.0.0/16"],
            "description": "VPC网络白名单",
            "type": "IPv4"
        }
    ]
}