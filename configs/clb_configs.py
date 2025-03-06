# -*- coding: utf-8 -*-

"""
CLB（负载均衡）实例配置
"""

# CLB实例配置列表
clb_configs = [
    {
        'name': 'public-clb-1',
        'subnet_id': 'subnet-22jqp154rgum87r2qr1lfsh2i',  # 替换为实际的子网ID
        'type': 'public',
        'load_balancer_spec': 'small_2',
        'description': '公网负载均衡实例1',
        'eip': {
            'bandwidth': 10,
            'eip_billing_type': 2
        }
    },
    {
        'name': 'public-clb-2',
        'subnet_id': 'subnet-22jqp154rgum87r2qr1lfsh2i',  # 替换为实际的子网ID
        'type': 'public',
        'load_balancer_spec': 'medium_1',
        'description': '公网负载均衡实例2',
        'eip': {
            'bandwidth': 100,
            'eip_billing_type': 2
        }
    }
]