#!/usr/bin/env python
# -*- coding: utf-8 -*-

# 标准组件配置列表，用于集群创建后安装基础组件
# 从listaddon.log提取的组件配置
# ingress-nginx 的 subnet 手动修改
STANDARD_ADDONS = [
    # 核心DNS服务
    {
        "name": "core-dns",
        "version": "1.10.1-vke.400",
        "deploy_mode": "Unmanaged",
        "deploy_node_type": "Node",
        "config": '{"Resources":{"Requests":{"Cpu":"2","Memory":"4Gi"}}}'
    },
    
    # 存储相关组件
    {
        "name": "csi-ebs",
        "version": "v1.2.5",
        "deploy_mode": "Unmanaged",
        "deploy_node_type": "Node"
    },
    {
        "name": "csi-nas",
        "version": "v1.2.6",
        "deploy_mode": "Unmanaged",
        "deploy_node_type": "Node"
    },
    {
        "name": "csi-tos",
        "version": "v0.2.9",
        "deploy_mode": "Unmanaged",
        "deploy_node_type": "Node"
    },
    {
        "name": "snapshot-controller",
        "version": "v6.2.1-vke.1",
        "deploy_mode": "Unmanaged",
        "deploy_node_type": "Node"
    },
    
    # 网络相关组件
    {
        "name": "vpc-cni",
        "version": "v1.7.9",
        "deploy_mode": "Unmanaged",
        "deploy_node_type": "Node"
    },
    {
        "name": "ingress-nginx",
        "version": "v1.9.5-vke.2",
        "deploy_mode": "Unmanaged",
        "deploy_node_type": "VirtualNode",
        "config": '{"Replicas":2,"Resources":{"Requests":{"Cpu":"0.1","Memory":"250Mi"},"Limits":{"Cpu":"0.5","Memory":"1024Mi"}},"LoadBalancer":{"BillingType":2,"Spec":"medium_2","ModificationProtectionDisabled":false,"MasterZoneId":"cn-shanghai-a","SlaveZoneId":"cn-shanghai-b"},"PublicNetwork":{"Isp":"BGP","BandWidth":100,"IpFamily":"Ipv4","BillingType":3,"SubnetId":"subnet-5gfoskjvbhts73inqkkgo6ow"}}'
    },
    
    # 监控和日志组件
    {
        "name": "metrics-server",
        "version": "v0.7.1-vke.2",
        "deploy_mode": "Unmanaged",
        "deploy_node_type": "Node"
    },
    {
        "name": "metrics-collector",
        "version": "v1.24.0-vke.2",
        "deploy_mode": "Unmanaged",
        "deploy_node_type": "Node",
        "config": '{"KubeStateMetrics":{"Resources":{"Limits":{"Cpu":"0.8","Memory":"2Gi"},"Requests":{"Cpu":"0.2","Memory":"512Mi"}}},"MetricsCollector":{"Resources":{"Limits":{"Cpu":"2","Memory":"4Gi"},"Requests":{"Cpu":"0.2","Memory":"512Mi"}}}}'
    },
    {
        "name": "log-collector",
        "version": "v2.0.8",
        "deploy_mode": "Unmanaged",
        "deploy_node_type": "Node",
        "config": '{"Controller":{"Resources":{"Requests":{"Cpu":"0.1","Memory":"256Mi"},"Limits":{"Cpu":"4","Memory":"2Gi"}}},"Filebeat":{"Resources":{"Requests":{"Cpu":"0.1","Memory":"256Mi"},"Limits":{"Cpu":"4","Memory":"2Gi"}}}}'
    },
    {
        "name": "node-problem-detector",
        "version": "v0.8.19-vke.2",
        "deploy_mode": "Unmanaged",
        "deploy_node_type": "Node"
    },
    
    # 集群自动伸缩组件
    {
        "name": "cluster-autoscaler",
        "version": "v1.28.0-vke.6",
        "deploy_mode": "Managed",
        "config": '{"ScanInterval":"10s","ScaleDown":{"Enabled":true,"UtilizationThreshold":0.67,"GpuUtilizationThreshold":0.5,"UnneededTime":10,"DelayAfterAdded":10,"DelayAfterFailure":3,"SkipNodesWithLocalStorageDisabled":false,"SkipNodesWithSystemPodsDisabled":false,"MaxEmptyBulkDeleteNumber":5,"MinReplicas":0,"MaxGracefulTermination":600,"DaemonSetEvictionForNodesDisabled":true},"ScaleUp":{"Expander":"random"}}'
    },
    
    # 调度器插件
    {
        "name": "scheduler-plugin",
        "version": "v1.0.10",
        "deploy_mode": "Managed",
        "config": '{"NodePolicy":"spread","ResourceWeights":[{"Name":"Cpu","Weight":1},{"Name":"Memory","Weight":1}],"PodTopologySpreadWeight":2,"GPUShareCardPolicy":"binpack","GangSchedulingEnabled":false,"ResourcePolicySchedulingEnabled":false,"NodeAffinityWeight":2}'
    },
    
    # 虚拟节点组件
    {
        "name": "vci-virtual-kubelet",
        "version": "v1.37.0",
        "deploy_mode": "Managed"
    },
    
    # 可选组件 - 根据需要启用
    {
        "name": "prometheus-agent",
        "version": "v2.6.0-vke.1.24",
        "deploy_mode": "Unmanaged",
        "deploy_node_type": "Node",
        "config": '{"NodeExporterDisabled":false,"AutoScalingEnabled":false,"VmAgent":{"InitShards":1,"Requests":{"Cpu":"2","Memory":"2Gi"},"Limits":{"Cpu":"4","Memory":"4Gi"}},"KubeStateMetrics":{"InitShards":1,"Requests":{"Cpu":"0.2","Memory":"512Mi"},"Limits":{"Cpu":"0.8","Memory":"2Gi"}}}'
    },
    ## 需要手动在日志服务里 手动创建 日志服务和主题
    # {
    #     "name": "event-collector",
    #     "version": "v1.0.8",
    #     "deploy_mode": "Unmanaged",
    #     "deploy_node_type": "Node",
    #     "config": '{"TopicId":"53c3715c-d5cc-4ea8-ae7a-24c6039c1104","ProjectId":"7d1c61be-d155-4766-9e88-4b3f80f69b03"}'
    # }
]