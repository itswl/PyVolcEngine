#!/usr/bin/env python
# -*- coding: utf-8 -*-


# 共享的VPC ID配置
VPC_ID = 'vpc-13g1af5mu1iio3n6nu4i4sqzp'

# 共享的子网ID配置，用不同请手动修改
SUBNET_IDS = [
    'subnet-13g1aq29zgfls3n6nu564lbef',
    'subnet-miw612h20t8g5smt1bwxqbot',
    'subnet-miw5w8uc3zeo5smt1bwme4wm'
]

# 共享的安全组ID配置
SECURITY_GROUP_IDS = ['sg-13g1afdiyhqf43n6nu4yijbgc']

# 实例类型配置
INSTANCE_TYPES = {
    'compute': ['ecs.c3a.4xlarge'],  # 计算型实例
    'memory': ['ecs.c3a.2xlarge'],  # 内存优化型实例
    'general': ['ecs.c3a.4xlarge'],  # 通用型实例
    'production': ['ecs.c3a.4xlarge']  # 生产环境实例
}

# VKE集群配置列表
CLUSTER_CONFIGS = [
{
    'name': 'test-dev-k8s',
    'description': '',
    'kubernetes_version': '1.28',
    'vpc_id': VPC_ID,
    'delete_protection_enabled': True,
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
    'pods_config': {
        'pod_network_mode': 'VpcCniShared',
        'vpc_cni_config': {
            'subnet_ids': SUBNET_IDS,
            'trunk_eni_enabled': False
        }
    },
    'services_config': {
        'service_cidrsv4': ['172.27.0.0/17']
    },
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
    'node_pools': [
        # 通用计算节点池
        {
            'name': 'general-compute-pool',
            'auto_scaling': {
                'enabled': True,
                'max_replicas': 10,
                'min_replicas': 2,
                'desired_replicas': 2,
                'priority': 10,
                'subnet_policy': 'ZoneBalance'
            },
            'node_config': {
                'instance_type_ids': INSTANCE_TYPES['compute'],
                'subnet_ids': SUBNET_IDS,
                'security': {
                    'security_group_ids': SECURITY_GROUP_IDS,
                    'security_strategies': ['Hids']
                },
                'system_volume': {
                    'size': 100,
                    'type': 'ESSD_PL0'
                },
                'data_volumes': [{
                    'size': 200,
                    'type': 'ESSD_PL0',
                    # 'file_system': 'Xfs',
                    # 'mount_point': '/var/lib/containerd,/var/lib/kubelet'
                }],
                'initialize_script': 'SGVsbG8gZnJvbSBub2RlIGluaXRpYWxpemF0aW9u',
                'additional_container_storage_enabled': True,
                'name_prefix': 'compute',
                'tags': [{
                    'key': 'pool-type',
                    'value': 'compute'
                }]
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
            'tags': [{
                'key': 'purpose',
                'value': 'general-compute'
            }]
        },
        # 内存优化节点池
        {
            'name': 'memory-optimized-pool',
            'auto_scaling': {
                'enabled': True,
                'max_replicas': 5,
                'min_replicas': 1,
                'desired_replicas': 2,
                'priority': 20,
                'subnet_policy': 'ZoneBalance'
            },
            'node_config': {
                'instance_type_ids': INSTANCE_TYPES['memory'],
                'subnet_ids': SUBNET_IDS,
                'security': {
                    'security_group_ids': SECURITY_GROUP_IDS,
                    'security_strategies': ['Hids']
                },
                'system_volume': {
                    'size': 100,
                    'type': 'ESSD_PL0'
                },
                'data_volumes': [{
                    'size': 300,
                    'type': 'ESSD_PL0',
                    # 'file_system': 'Xfs',
                    # 'mount_point': '/var/lib/containerd,/var/lib/kubelet'
                }],
                'initialize_script': 'SGVsbG8gZnJvbSBub2RlIGluaXRpYWxpemF0aW9u',
                'additional_container_storage_enabled': True,
                'name_prefix': 'memory',
                'tags': [{
                    'key': 'pool-type',
                    'value': 'memory-optimized'
                }]
            },
            'kubernetes_config': {
                'labels': [
                    {
                        'key': 'node-role',
                        'value': 'worker'
                    },
                    {
                        'key': 'workload-type',
                        'value': 'memory-intensive'
                    }
                ],
                'taints': [{
                    'key': 'memory-optimized',
                    'value': 'true',
                    'effect': 'PreferNoSchedule'
                }],
                'cordon': False
            },
            'tags': [{
                'key': 'purpose',
                'value': 'memory-optimized'
            }]
        }
        ]
},
# 第二个集群配置
{
    'name': 'test2-dev-k8s',
    'description': 'Production Kubernetes Cluster',
    'kubernetes_version': '1.28',
    'vpc_id': VPC_ID,
    'delete_protection_enabled': True,
    'cluster_config': {
        'subnet_ids': SUBNET_IDS,
        'api_server_public_access_enabled': True,
        'api_server_public_access_config': {
            'public_access_network_config': {
                'billing_type': 3,
                'bandwidth': 20,
                'isp': 'BGP'
            }
        },
        'resource_public_access_default_enabled': True
    },
    'pods_config': {
        'pod_network_mode': 'VpcCniShared',
        'vpc_cni_config': {
            'subnet_ids': SUBNET_IDS,
            'trunk_eni_enabled': False
        }
    },
    'services_config': {
        'service_cidrsv4': ['172.28.0.0/17']
    },
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
    'node_pools': [
        # 生产环境通用计算节点池
        {
            'name': 'prod-compute-pool',
            'auto_scaling': {
                'enabled': True,
                'max_replicas': 20,
                'min_replicas': 3,
                'desired_replicas': 5,
                'priority': 10,
                'subnet_policy': 'ZoneBalance'
            },
            'node_config': {
                'instance_type_ids': INSTANCE_TYPES['production'],
                'subnet_ids': SUBNET_IDS,
                'security': {
                    'security_group_ids': SECURITY_GROUP_IDS,
                    'security_strategies': ['Hids']
                },
                'system_volume': {
                    'size': 200,
                    'type': 'ESSD_PL1'
                },
                'data_volumes': [{
                    'size': 500,
                    'type': 'ESSD_PL1'
                }],
                'initialize_script': 'SGVsbG8gZnJvbSBub2RlIGluaXRpYWxpemF0aW9u',
                'additional_container_storage_enabled': True,
                'name_prefix': 'prod',
                'tags': [{
                    'key': 'env',
                    'value': 'production'
                }]
            },
            'kubernetes_config': {
                'labels': [
                    {
                        'key': 'node-role',
                        'value': 'worker'
                    },
                    {
                        'key': 'env',
                        'value': 'production'
                    }
                ],
                'taints': [],
                'cordon': False
            },
            'tags': [{
                'key': 'purpose',
                'value': 'production-workload'
            }]
        }
    ]
}
]