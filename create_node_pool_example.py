# Example Code generated by Beijing Volcanoengine Technology.
from __future__ import print_function
import volcenginesdkcore
import volcenginesdkvke
from volcenginesdkcore.rest import ApiException

if __name__ == '__main__':
    # 注意示例代码安全，代码泄漏会导致AK/SK泄漏，有极大的安全风险。
    configuration = volcenginesdkcore.Configuration()
    configuration.ak = "Your AK"
    configuration.sk = "Your SK"
    configuration.region = "cn-shanghai"
    # set default configuration
    volcenginesdkcore.Configuration.set_default(configuration)

    # use global default configuration
    api_instance = volcenginesdkvke.VKEApi()
    
    # 创建节点池配置
    req_login = volcenginesdkvke.LoginForCreateNodePoolInput(
        # 密码必须包含大小写字母、数字和特殊字符，长度8-30位
        password="Volc2024@Test",
    )
    
    req_security = volcenginesdkvke.SecurityForCreateNodePoolInput(
        login=req_login,
        # 安全组ID，根据实际情况修改
        security_group_ids=["sg-xxxxxxxx"],
        # 安全策略
        security_strategies=["Hids"]
    )
    
    req_node_config = volcenginesdkvke.NodeConfigForCreateNodePoolInput(
        security=req_security,
        # 实例类型，根据实际情况修改
        instance_type_ids=["ecs.g1.large"],
        # 子网ID，根据实际情况修改
        subnet_ids=["subnet-xxxxxxxx"],
        # 系统盘配置
        system_volume=volcenginesdkvke.SystemVolumeForCreateNodePoolInput(
            size=100,  # 系统盘大小，单位GB
            type="ESSD_PL0"  # 磁盘类型
        ),
        # 数据盘配置
        data_volumes=[volcenginesdkvke.DataVolumeForCreateNodePoolInput(
            size=200,  # 数据盘大小，单位GB
            type="ESSD_PL0"  # 磁盘类型
        )],
        name_prefix="node",  # 节点名称前缀
        additional_container_storage_enabled=True
    )
    
    create_node_pool_request = volcenginesdkvke.CreateNodePoolRequest(
        # 集群ID，必填
        cluster_id="your_cluster_id",
        # 节点池名称
        name="example-nodepool",
        node_config=req_node_config,
        # 弹性伸缩配置
        auto_scaling=volcenginesdkvke.AutoScalingForCreateNodePoolInput(
            enabled=True,
            max_replicas=10,
            min_replicas=1,
            desired_replicas=2,
            priority=10,
            subnet_policy="ZoneBalance"
        ),
        # Kubernetes配置
        kubernetes_config=volcenginesdkvke.KubernetesConfigForCreateNodePoolInput(
            labels=[volcenginesdkvke.LabelForCreateNodePoolInput(
                key="example-key",
                value="example-value"
            )],
            taints=[volcenginesdkvke.TaintForCreateNodePoolInput(
                key="example-taint",
                value="true",
                effect="NoSchedule"
            )],
            cordon=False
        )
    )
    
    try:
        # 创建节点池
        response = api_instance.create_node_pool(create_node_pool_request)
        print(f"节点池创建成功，ID: {response.node_pool_id}")
    except ApiException as e:
        print(f"创建节点池失败: {e}")