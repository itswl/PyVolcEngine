# -*- coding: utf-8 -*-

"""
CLB（负载均衡）实例配置
"""

# CLB实例配置列表
clb_configs = [
    {
        'name': 'eve-cn-prod-clb',
        'subnet_id': 'subnet-3qd8s8xald8n47prml147n61j',  # 替换为实际的子网ID
        'type': 'public',
        'load_balancer_spec': 'medium_1',
        'description': '',
        'eip': {
            'bandwidth': 50,
            'eip_billing_type': 3 # 按量付费，实际流量
        }
    },    
    {
        'name': 'eve-cn-infra-prod-clb-livekit-server-turn',
        'subnet_id': 'subnet-3qd8s8xald8n47prml147n61j',  # 替换为实际的子网ID
        'type': 'public',
        'load_balancer_spec': 'small_2',
        'description': '',
        'eip': {
            'bandwidth': 50,
            'eip_billing_type': 3 # 按量付费，实际流量
        }
    }
]