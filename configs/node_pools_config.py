#!/usr/bin/env python
# -*- coding: utf-8 -*-

# 多节点池配置
NODE_POOLS_CONFIG = {
    # 计算密集型节点池
    'compute': {
        'name': 'compute-nodepool',
        'auto_scaling': {
            'enabled': True,
            'max_replicas': 10,
            'min_replicas': 2,
            'desired_replicas': 2,
            'priority': 10,
            'subnet_policy': 'ZoneBalance'
        },
        'node_config': {
            'instance_type_ids': ['ecs.c3a.4xlarge'],  # 高性能计算实例
            'subnet_ids': [
                'subnet-13g1aq29zgfls3n6nu564lbef',
                'subnet-miw612h20t8g5smt1bwxqbot',
                'subnet-miw5w8uc3zeo5smt1bwme4wm'
            ],
            'security': {
                'security_group_ids': ['sg-13g1afdiyhqf43n6nu4yijbgc'],
                'security_strategies': ['Hids']
            },
            'system_volume': {
                'size': 100,
                'type': 'ESSD_PL0'
            },
            'data_volumes': [{
                'size': 200,
                'type': 'ESSD_PL0'
            }],
            'initialize_script': 'SGVsbG8gZnJvbSBub2RlIGluaXRpYWxpemF0aW9u',
            'additional_container_storage_enabled': True,
            'name_prefix': 'compute',
            'tags': [{
                'key': 'node-type',
                'value': 'compute'
            }]
        },
        'kubernetes_config': {
            'labels': [
                {
                    'key': 'node-role',
                    'value': 'compute'
                },
                {
                    'key': 'workload-type',
                    'value': 'compute-intensive'
                }
            ],
            'taints': [{
                'key': 'dedicated',
                'value': 'compute',
                'effect': 'NoSchedule'
            }],
            'cordon': False
        }
    },
    
    # 内存密集型节点池
    'memory': {
        'name': 'memory-nodepool',
        'auto_scaling': {
            'enabled': True,
            'max_replicas': 8,
            'min_replicas': 2,
            'desired_replicas': 2,
            'priority': 20,
            'subnet_policy': 'ZoneBalance'
        },
        'node_config': {
            'instance_type_ids': ['ecs.c3a.4xlarge'],  # 内存优化实例
            'subnet_ids': [
                'subnet-13g1aq29zgfls3n6nu564lbef',
                'subnet-miw612h20t8g5smt1bwxqbot',
                'subnet-miw5w8uc3zeo5smt1bwme4wm'
            ],
            'security': {
                'security_group_ids': ['sg-13g1afdiyhqf43n6nu4yijbgc'],
                'security_strategies': ['Hids']
            },
            'system_volume': {
                'size': 100,
                'type': 'ESSD_PL0'
            },
            'data_volumes': [{
                'size': 300,
                'type': 'ESSD_PL0',
            }],
            'initialize_script': 'SGVsbG8gZnJvbSBub2RlIGluaXRpYWxpemF0aW9u',
            'additional_container_storage_enabled': True,
            'name_prefix': 'memory',
            'tags': [{
                'key': 'node-type',
                'value': 'memory'
            }]
        },
        'kubernetes_config': {
            'labels': [
                {
                    'key': 'node-role',
                    'value': 'memory'
                },
                {
                    'key': 'workload-type',
                    'value': 'memory-intensive'
                }
            ],
            'taints': [{
                'key': 'dedicated',
                'value': 'memory',
                'effect': 'NoSchedule'
            }],
            'cordon': False
        }
    },
    
    # 通用型节点池
    'general': {
        'name': 'general-nodepool',
        'auto_scaling': {
            'enabled': True,
            'max_replicas': 5,
            'min_replicas': 1,
            'desired_replicas': 2,
            'priority': 30,
            'subnet_policy': 'ZoneBalance'
        },
        'node_config': {
            'instance_type_ids': ['ecs.c3a.4xlarge'],  # 通用型实例
            'subnet_ids': [
                'subnet-13g1aq29zgfls3n6nu564lbef',
                'subnet-miw612h20t8g5smt1bwxqbot',
                'subnet-miw5w8uc3zeo5smt1bwme4wm'
            ],
            'security': {
                'security_group_ids': ['sg-13g1afdiyhqf43n6nu4yijbgc'],
                'security_strategies': ['Hids']
            },
            'system_volume': {
                'size': 100,
                'type': 'ESSD_PL0'
            },
            'data_volumes': [{
                'size': 200,
                'type': 'ESSD_PL0'
            }],
            'initialize_script': 'SGVsbG8gZnJvbSBub2RlIGluaXRpYWxpemF0aW9u',
            'additional_container_storage_enabled': True,
            'name_prefix': 'general',
            'tags': [{
                'key': 'node-type',
                'value': 'general'
            }]
        },
        'kubernetes_config': {
            'labels': [
                {
                    'key': 'node-role',
                    'value': 'general'
                },
                {
                    'key': 'workload-type',
                    'value': 'general-purpose'
                }
            ],
            'taints': [],
            'cordon': False
        }
    }
}