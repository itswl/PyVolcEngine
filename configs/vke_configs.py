#!/usr/bin/env python
# -*- coding: utf-8 -*-


# 共享的VPC ID配置
VPC_ID = 'vpc-22j75iztkwo3k7r2qr1czeq8b'

# 共享的子网ID配置，用不同请手动修改
SUBNET_IDS = [
    'subnet-5gfoskjvbhts73inqkkgo6ow',
    'subnet-3qd8s8xald8n47prml147n61j',
    'subnet-22j75kf4du3gg7r2qr1mupd66'
]

# 共享的安全组ID配置
SECURITY_GROUP_IDS = ['sg-22j75j5qo8u0w7r2qr1r5yieo']

# 实例类型配置
INSTANCE_TYPES = {
    'node-default': ['ecs.c3a.4xlarge'],  # 默认配置
    'node-edge': ['ecs.c3a.2xlarge'],     # edge 节点配置
}

# VKE集群配置列表
CLUSTER_CONFIGS = [
    {
        'name': 'ns-hs-sh-dev-k8s',
        'description': '',
        'kubernetes_version': '1.28',
        'vpc_id': VPC_ID,
        'delete_protection_enabled': True,
        
        # 集群网络配置
        'cluster_config': {
            'subnet_ids': SUBNET_IDS,
            'api_server_public_access_enabled': True,
            'api_server_public_access_config': {
                'public_access_network_config': {
                    'billing_type': 3,
                    'bandwidth': 10,
                    'isp': 'BGP'
                }
            },
            'resource_public_access_default_enabled': True
        },
        
        # Pod网络配置
        'pods_config': {
            'pod_network_mode': 'VpcCniShared',
            'vpc_cni_config': {
                'subnet_ids': SUBNET_IDS,
                'trunk_eni_enabled': False
            }
        },
        
        # Service网络配置
        'services_config': {
            'service_cidrsv4': ['172.28.0.0/17']
        },
        
        # Kubernetes配置
        'kubernetes_config': {
            'cluster_domain': 'cluster.local',
            'control_plane_config': {
                'kube_api_server_config': {
                    'admission_plugins': {
                        'always_pull_images': True
                    }
                }
            }
        },
        
        # 节点池配置
        'node_pools': [
            # 通用计算节点池 - 自动伸缩
            {
                'name': 'auto-pool',
                'auto_scaling': {
                    'enabled': True,
                    'max_replicas': 10,
                    'min_replicas': 1,
                    'desired_replicas': 1,
                    'priority': 10,
                    'subnet_policy': 'ZoneBalance'
                },
                'node_config': {
                    'instance_charge_type': 'PostPaid',
                    'instance_type_ids': INSTANCE_TYPES['node-default'],
                    'subnet_ids': SUBNET_IDS,
                    'security': {
                        'security_group_ids': SECURITY_GROUP_IDS,
                        'security_strategies': ['Hids'],
                        'password': 'TnNAU2hlbnpoZW4yMDI0'
                    },
                    'system_volume': {
                        'size': 100,
                        'type': 'ESSD_PL0'
                    },
                    'data_volumes': [
                        {
                            'size': 400,
                            'type': 'ESSD_PL0',
                            # 'file_system': 'Xfs',
                            # 'mount_point': '/var/lib/containerd,/var/lib/kubelet'
                        }
                    ],
                    'initialize_script': 'SGVsbG8gZnJvbSBub2RlIGluaXRpYWxpemF0aW9u',
                    'additional_container_storage_enabled': True,
                    'name_prefix': 'auto',
                    'tags': [
                        {
                            'key': 'pool-type',
                            'value': 'node-default'
                        }
                    ]
                },
                'kubernetes_config': {
                    'labels': [
                        {
                            'key': 'node-role',
                            'value': 'worker'
                        },
                        {
                            'key': 'workload-type',
                            'value': 'general'
                        }
                    ],
                    'taints': [],
                    'cordon': False
                },
                'tags': [
                    {
                        'key': 'purpose',
                        'value': 'general-compute'
                    }
                ]
            },
            
            # 通用计算节点池 - 固定节点数
            {
                'name': 'default-pool',
                'auto_scaling': {
                    'enabled': False,
                    'max_replicas': 10,
                    'min_replicas': 2,
                    'desired_replicas': 2,
                    'priority': 10,
                    'subnet_policy': 'ZoneBalance'
                },
                'node_config': {
                    'instance_charge_type': 'PrePaid',
                    'instance_type_ids': INSTANCE_TYPES['node-default'],
                    'subnet_ids': SUBNET_IDS,
                    'security': {
                        'security_group_ids': SECURITY_GROUP_IDS,
                        'security_strategies': ['Hids'],
                        'password': 'TnNAU2hlbnpoZW4yMDI0'
                    },
                    'system_volume': {
                        'size': 100,
                        'type': 'ESSD_PL0'
                    },
                    'data_volumes': [
                        {
                            'size': 400,
                            'type': 'ESSD_PL0',
                            # 'file_system': 'Xfs',
                            # 'mount_point': '/var/lib/containerd,/var/lib/kubelet'
                        }
                    ],
                    'initialize_script': 'SGVsbG8gZnJvbSBub2RlIGluaXRpYWxpemF0aW9u',
                    'additional_container_storage_enabled': True,
                    'name_prefix': 'default',
                    'tags': [
                        {
                            'key': 'pool-type',
                            'value': 'node-default'
                        }
                    ]
                },
                'kubernetes_config': {
                    'labels': [
                        {
                            'key': 'node-role',
                            'value': 'worker'
                        },
                        {
                            'key': 'workload-type',
                            'value': 'general'
                        }
                    ],
                    'taints': [],
                    'cordon': False
                },
                'tags': [
                    {
                        'key': 'purpose',
                        'value': 'general-compute'
                    }
                ]
            },
            
            # edge 节点池
            {
                'name': 'edge-pool',
                'auto_scaling': {
                    'enabled': True,
                    'max_replicas': 5,
                    'min_replicas': 1,
                    'desired_replicas': 2,
                    'priority': 20,
                    'subnet_policy': 'ZoneBalance'
                },
                'node_config': {
                    'instance_charge_type': 'PostPaid',
                    'instance_type_ids': INSTANCE_TYPES['node-edge'],
                    'subnet_ids': SUBNET_IDS,
                    'security': {
                        'security_group_ids': SECURITY_GROUP_IDS,
                        'security_strategies': ['Hids'],
                        'password': 'TnNAU2hlbnpoZW4yMDI0'
                    },
                    'system_volume': {
                        'size': 40,
                        'type': 'ESSD_PL0'
                    },
                    'data_volumes': [
                        {
                            'size': 100,
                            'type': 'ESSD_PL0',
                            # 'file_system': 'Xfs',
                            # 'mount_point': '/var/lib/containerd,/var/lib/kubelet'
                        }
                    ],
                    'initialize_script': 'SGVsbG8gZnJvbSBub2RlIGluaXRpYWxpemF0aW9u',
                    'additional_container_storage_enabled': True,
                    'name_prefix': 'edge',
                    'tags': [
                        {
                            'key': 'pool-type',
                            'value': 'node-edge-optimized'
                        }
                    ]
                },
                'kubernetes_config': {
                    'labels': [
                        {
                            'key': 'node-role',
                            'value': 'worker'
                        },
                        {
                            'key': 'workload-type',
                            'value': 'node-edge-intensive'
                        }
                    ],
                    'taints': [
                        {
                            'key': 'bind-eip',
                            'value': 'yes',
                            'effect': 'NoSchedule'
                        }
                    ],
                    'cordon': False
                },
                'tags': [
                    {
                        'key': 'purpose',
                        'value': 'node-edge-optimized'
                    }
                ]
            }
        ]
    }
]