# 白名单配置
whitelist_config = {
    "whitelists": [
        {
            "name": "lan",
            "ip_list": ["127.0.0.0/8","10.0.0.0/8","100.64.0.0/10","172.16.0.0/12","192.168.0.0/16"],
            "description": "默认白名单配置",
            "type": "IPv4"
        },
        {
            "name": "wan_office",
            "ip_list": ["OFFICE_IP"],
            "description": "办公网络白名单",
            "type": "IPv4"
        },
        {
            "name": "wan_server",
            "ip_list": ["IP_PLACEHOLDER_1", "IP_PLACEHOLDER_2", "IP_PLACEHOLDER_3"],
            "description": "公网网络白名单",
            "type": "IPv4"
        }
    ]
}