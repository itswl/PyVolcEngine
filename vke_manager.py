#!/usr/bin/env python
# -*- coding: utf-8 -*-

# 火山引擎VKE管理工具：集群、节点池和组件管理

from __future__ import print_function
import os
import json
import time
import volcenginesdkcore
import volcenginesdkvke
from volcenginesdkcore.rest import ApiException
from volcenginesdkvke.models.create_cluster_request import CreateClusterRequest
from volcenginesdkvke.models.create_node_pool_request import CreateNodePoolRequest
from volcenginesdkvke.models.create_kubeconfig_request import CreateKubeconfigRequest
from volcenginesdkvke.models.list_clusters_request import ListClustersRequest
from volcenginesdkvke.models.list_node_pools_request import ListNodePoolsRequest
from volcenginesdkvke.models.create_addon_request import CreateAddonRequest
from volcenginesdkvke.models.list_addons_request import ListAddonsRequest
from configs.vke_configs import CLUSTER_CONFIGS
from configs.api_config import api_config

class VKEManager:
    """VKE管理类，包含集群、节点池和组件管理功能"""
    
    def __init__(self, ak=None, sk=None, region='cn-shanghai'):
        """初始化VKE管理器
        
        Args:
            ak (str): 访问密钥ID
            sk (str): 访问密钥密码
            region (str): 区域，默认为上海
        """
        self.configuration = volcenginesdkcore.Configuration()
        self.configuration.ak = ak or api_config['ak']
        self.configuration.sk = sk or api_config['sk']
        self.configuration.region = region or api_config['region']
        self.configuration.client_side_validation = True
        volcenginesdkcore.Configuration.set_default(self.configuration)
        # 使用全局默认配置初始化API客户端
        self.vke_api = volcenginesdkvke.VKEApi()
    
    def wait_for_cluster_ready(self, cluster_id, timeout=600, interval=30):
        """等待集群就绪
        
        Args:
            cluster_id (str): 集群ID
            timeout (int): 超时时间（秒）
            interval (int): 检查间隔（秒）
            
        Returns:
            bool: 集群是否就绪
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                list_clusters_request = ListClustersRequest()
                clusters_response = self.vke_api.list_clusters(list_clusters_request)
                # print(clusters_response)
                if clusters_response and clusters_response.items:
                    for cluster in clusters_response.items:
                        # print('=======')
                        print(cluster.status.phase)
                        if cluster.id == cluster_id and cluster.status.phase == 'Running':
                            print('集群已就绪')
                            return True
                print(f'等待集群就绪中，已等待 {int(time.time() - start_time)} 秒...')
                time.sleep(interval)
            except Exception as e:
                print(f'检查集群状态时发生错误: {str(e)}')
                time.sleep(interval)
        print(f'等待集群就绪超时，已等待 {timeout} 秒')
        return False
    
    def create_clusters(self):
        """创建多个集群
        
        从配置文件中读取集群配置列表，创建多个集群
        
        Returns:
            dict: 创建结果，包含每个集群的ID和状态
        """
        results = {}
        
        # 从配置文件获取集群配置列表
        cluster_configs = CLUSTER_CONFIGS
        
        for cluster_config in cluster_configs:
            try:
                cluster_id = self.create_cluster(cluster_config['name'], cluster_config)
                results[cluster_config['name']] = {
                    'cluster_id': cluster_id,
                    'status': 'created' if cluster_id else 'failed'
                }
            except Exception as e:
                results[cluster_config['name']] = {
                    'cluster_id': None,
                    'status': 'failed',
                    'error': str(e)
                }
            
            # 避免请求过于频繁
            time.sleep(2)
        
        return results

    def create_cluster(self, cluster_name, cluster_config=None):
        """创建或获取已存在的集群
        
        Args:
            cluster_name (str): 集群名称
            cluster_config (dict, optional): 集群配置，如果不提供则使用默认配置
            
        Returns:
            str: 集群ID
        """
        try:
            # 检查集群是否已存在
            list_clusters_request = ListClustersRequest()
            clusters_response = self.vke_api.list_clusters(list_clusters_request)

            # 检查是否有同名集群
            existing_cluster = None
            if clusters_response and clusters_response.items:
                for cluster in clusters_response.items:
                    if cluster.name == cluster_name:
                        existing_cluster = cluster
                        break
            
            if existing_cluster:
                print(f'找到已存在的同名集群，ID: {existing_cluster.id}')
                return existing_cluster.id
            
            # 创建新集群
            # 如果没有提供配置，使用第一个默认配置
            if cluster_config is None:
                from configs.vke_configs import CLUSTER_CONFIGS
                cluster_config = CLUSTER_CONFIGS[0]
                
            api_server_public_access_config = volcenginesdkvke.ApiServerPublicAccessConfigForCreateClusterInput(
                public_access_network_config=volcenginesdkvke.PublicAccessNetworkConfigForCreateClusterInput(
                    billing_type=cluster_config['cluster_config']['api_server_public_access_config']['public_access_network_config']['billing_type'],
                    bandwidth=cluster_config['cluster_config']['api_server_public_access_config']['public_access_network_config']['bandwidth'],
                    isp=cluster_config['cluster_config']['api_server_public_access_config']['public_access_network_config']['isp']
                )
            )
            
            cluster_config_obj = volcenginesdkvke.ClusterConfigForCreateClusterInput(
                subnet_ids=cluster_config['cluster_config']['subnet_ids'],
                api_server_public_access_enabled=cluster_config['cluster_config']['api_server_public_access_enabled'],
                api_server_public_access_config=api_server_public_access_config,
                resource_public_access_default_enabled=cluster_config['cluster_config']['resource_public_access_default_enabled']
            )
            
            # 配置日志设置
            req_log_setups = volcenginesdkvke.LogSetupForCreateClusterInput(
                enabled=True,
                log_ttl=30,
                log_type="Audit"
            )
            req_log_setups1 = volcenginesdkvke.LogSetupForCreateClusterInput(
                enabled=True,
                log_ttl=30,
                log_type="KubeApiServer"
            )
            req_log_setups2 = volcenginesdkvke.LogSetupForCreateClusterInput(
                enabled=True,
                log_ttl=30,
                log_type="KubeScheduler"
            )
            req_log_setups3 = volcenginesdkvke.LogSetupForCreateClusterInput(
                enabled=True,
                log_ttl=30,
                log_type="KubeControllerManager"
            )
            req_log_setups4 = volcenginesdkvke.LogSetupForCreateClusterInput(
                enabled=True,
                log_ttl=30,
                log_type="CloudControllerManager"
            )
            req_log_setups5 = volcenginesdkvke.LogSetupForCreateClusterInput(
                enabled=True,
                log_ttl=30,
                log_type="Etcd"
            )
            req_logging_config = volcenginesdkvke.LoggingConfigForCreateClusterInput(
                log_setups=[req_log_setups, req_log_setups1, req_log_setups2, req_log_setups3, req_log_setups4, req_log_setups5]
            )

            cluster_request = CreateClusterRequest(
                name=cluster_name,
                description=cluster_config['description'],
                kubernetes_version=cluster_config['kubernetes_version'],
                # vpc_id=cluster_config['vpc_id'],
                delete_protection_enabled=cluster_config['delete_protection_enabled'],
                cluster_config=cluster_config_obj,
                pods_config=volcenginesdkvke.PodsConfigForCreateClusterInput(
                    pod_network_mode=cluster_config['pods_config']['pod_network_mode'],
                    vpc_cni_config=volcenginesdkvke.VpcCniConfigForCreateClusterInput(
                        subnet_ids=cluster_config['pods_config']['vpc_cni_config']['subnet_ids']
                    )
                ),
                services_config=volcenginesdkvke.ServicesConfigForCreateClusterInput(
                    service_cidrsv4=cluster_config['services_config']['service_cidrsv4']
                ),
                logging_config=req_logging_config,
                
                # kubernetes_config=CLUSTER_CONFIG['kubernetes_config']
            )
            
            cluster_response = self.vke_api.create_cluster(cluster_request)
            print(cluster_response)
            cluster_id = cluster_response.id
            print(f'集群创建成功，ID: {cluster_id}')
            return cluster_id
        except Exception as e:
            print(f'创建集群时发生错误: {str(e)}')
            return None
    
    def create_node_pool(self, cluster_id, node_pool_config=None):
        """创建单个节点池
        
        Args:
            cluster_id (str): 集群ID
            node_pool_config (dict, optional): 节点池配置，如果不提供则使用默认配置
            
        Returns:
            str: 节点池ID
        """
        try:
            # 如果没有提供配置，使用集群配置中的第一个节点池配置
            if node_pool_config is None:
                # 从集群配置中获取节点池配置
                list_clusters_request = ListClustersRequest()
                clusters_response = self.vke_api.list_clusters(list_clusters_request)
                
                if clusters_response and clusters_response.items:
                    for cluster in clusters_response.items:
                        if cluster.id == cluster_id:
                            # 从CLUSTER_CONFIGS中找到对应的集群配置
                            for config in CLUSTER_CONFIGS:
                                if config['name'] == cluster.name:
                                    node_pool_config = config['node_pools'][0]  # 使用第一个节点池配置
                                    break
                            break
                
                if node_pool_config is None:
                    raise Exception('未找到集群对应的节点池配置')
            
            # 检查是否已有同名节点池
            req_filter = volcenginesdkvke.FilterForListNodePoolsInput(
                cluster_ids=[cluster_id],
            )
            list_node_pools_request = ListNodePoolsRequest(
                filter=req_filter,
            )
            node_pools_response = self.vke_api.list_node_pools(list_node_pools_request)
            
            # 检查是否有同名节点池
            if node_pools_response and node_pools_response.items:
                for node_pool in node_pools_response.items:
                    if node_pool.name == node_pool_config['name']:
                        print(f'找到已存在的同名节点池，ID: {node_pool.id}')
                        return node_pool.id
            
            # 创建登录配置
            req_login = volcenginesdkvke.LoginForCreateNodePoolInput(
                password = 'TnNAU2hlbnpoZW4yMDI0'
            )
            
            # 创建安全配置
            req_security = volcenginesdkvke.SecurityForCreateNodePoolInput(
                login=req_login,
                security_group_ids=node_pool_config['node_config']['security']['security_group_ids'],
                security_strategies=node_pool_config['node_config']['security']['security_strategies']
            )
            
            # 创建节点配置
            req_node_config = volcenginesdkvke.NodeConfigForCreateNodePoolInput(
                security=req_security,
                instance_type_ids=node_pool_config['node_config']['instance_type_ids'],
                subnet_ids=node_pool_config['node_config']['subnet_ids'],
                system_volume=volcenginesdkvke.SystemVolumeForCreateNodePoolInput(
                    size=node_pool_config['node_config']['system_volume']['size'],
                    type=node_pool_config['node_config']['system_volume']['type']
                ),
                data_volumes=[volcenginesdkvke.DataVolumeForCreateNodePoolInput(
                    size=volume['size'],
                    type=volume['type'],
                    # file_system=volume['file_system'],
                    # mount_point=volume['mount_point'],
                ) for volume in node_pool_config['node_config']['data_volumes']],
                initialize_script=node_pool_config['node_config']['initialize_script'],
                additional_container_storage_enabled=node_pool_config['node_config']['additional_container_storage_enabled'],
                name_prefix=node_pool_config['node_config']['name_prefix'],
                tags=[volcenginesdkvke.TagForCreateNodePoolInput(
                    key=tag['key'],
                    value=tag['value']
                ) for tag in node_pool_config['node_config']['tags']]
            )
            
            # 创建节点池请求
            node_pool_request = CreateNodePoolRequest(
                cluster_id=cluster_id,
                name=node_pool_config['name'],
                node_config=req_node_config,
                auto_scaling=volcenginesdkvke.AutoScalingForCreateNodePoolInput(
                    enabled=node_pool_config['auto_scaling']['enabled'],
                    max_replicas=node_pool_config['auto_scaling']['max_replicas'],
                    min_replicas=node_pool_config['auto_scaling']['min_replicas'],
                    desired_replicas=node_pool_config['auto_scaling']['desired_replicas'],
                    priority=node_pool_config['auto_scaling']['priority'],
                    subnet_policy=node_pool_config['auto_scaling']['subnet_policy']
                ),
                kubernetes_config=volcenginesdkvke.KubernetesConfigForCreateNodePoolInput(
                    labels=[volcenginesdkvke.LabelForCreateNodePoolInput(
                        key=label['key'],
                        value=label['value']
                    ) for label in node_pool_config['kubernetes_config']['labels']],
                    taints=[volcenginesdkvke.TaintForCreateNodePoolInput(
                        key=taint['key'],
                        value=taint['value'],
                        effect=taint['effect']
                    ) for taint in node_pool_config['kubernetes_config']['taints']],
                    cordon=node_pool_config['kubernetes_config']['cordon']
                ),
                tags=[volcenginesdkvke.TagForCreateNodePoolInput(
                    key=tag['key'],
                    value=tag['value']
                ) for tag in node_pool_config['tags']]
            )
            # print(node_pool_request)
            node_pool_response = self.vke_api.create_node_pool(node_pool_request)
            # print(node_pool_response)
            if node_pool_response and node_pool_response.id:
                print(f'节点池创建成功，ID: {node_pool_response.id}')
                return node_pool_response.id
            else:
                print('创建节点池失败：API响应不完整')
                return None
        except Exception as e:
            print(f'创建节点池时发生错误: {str(e)}')
            return None
            
    def create_node_pools(self, cluster_id):
        """创建多个节点池
        
        Args:
            cluster_id (str): 集群ID
            
        Returns:
            dict: 创建结果，包含每个节点池的ID和状态
        """
        results = {}
        
        # 从集群配置中获取节点池配置列表
        list_clusters_request = ListClustersRequest()
        clusters_response = self.vke_api.list_clusters(list_clusters_request)
        
        # 找到对应的集群配置
        cluster_config = None
        if clusters_response and clusters_response.items:
            for cluster in clusters_response.items:
                if cluster.id == cluster_id:
                    for config in CLUSTER_CONFIGS:
                        if config['name'] == cluster.name:
                            cluster_config = config
                            break
                    break
        
        if cluster_config is None or 'node_pools' not in cluster_config:
            print('未找到集群对应的节点池配置')
            return results
        
        for node_pool_config in cluster_config['node_pools']:

            try:
                # 创建节点池
                node_pool_id = self.create_node_pool(cluster_id, node_pool_config)
                results[node_pool_config['name']] = {
                    'node_pool_id': node_pool_id,
                    'status': 'created' if node_pool_id else 'failed'
                }
            except Exception as e:
                results[node_pool_config['name']] = {
                    'node_pool_id': None,
                    'status': 'failed',
                    'error': str(e)
                }
            
            # 避免请求过于频繁
            time.sleep(2)
        
        return results
    
    def get_cluster_kubeconfig(self, cluster_id):
        """获取集群的kubeconfig配置
        
        Args:
            cluster_id (str): 集群ID
            
        Returns:
            bool: 是否成功获取kubeconfig
        """
        try:
            # 先检查是否已存在public类型的kubeconfig
            kubeconfig_req_filter = volcenginesdkvke.FilterForListKubeconfigsInput(
                cluster_ids=[cluster_id],
                types=["Public"]
            )
            kubeconfig_request = volcenginesdkvke.ListKubeconfigsRequest(
                filter=kubeconfig_req_filter,
                page_number=1,
                page_size=100,
            )
            kubeconfig_response = self.vke_api.list_kubeconfigs(kubeconfig_request)
            
            # 如果没有找到现有的public kubeconfig，则创建新的
            if not (kubeconfig_response and kubeconfig_response.items):
                # 创建新的kubeconfig
                create_kubeconfig_request = CreateKubeconfigRequest(
                    cluster_id=cluster_id,
                    type="Public",
                    valid_duration=867240
                )
                create_response = self.vke_api.create_kubeconfig(create_kubeconfig_request)
                print('成功创建新的kubeconfig')
                
                # 重新获取创建的kubeconfig
                kubeconfig_response = self.vke_api.list_kubeconfigs(kubeconfig_request)
            
            if kubeconfig_response and kubeconfig_response.items:
                # print(kubeconfig_response)
                for kubeconfig in kubeconfig_response.items:
                    print(kubeconfig.kubeconfig)  # 使用正确的属性名
                return True
            print('未找到集群的kubeconfig配置')
            return False
        except Exception as e:
            print(f'获取kubeconfig时发生错误: {str(e)}')
            return False
    
    def list_addons(self, cluster_id):
        """列出集群中的所有组件
        
        Args:
            cluster_id (str): 集群ID
            
        Returns:
            dict: 组件列表信息
        """
        try:
            request = ListAddonsRequest()
            request.filter = volcenginesdkvke.FilterForListAddonsInput(
                cluster_ids=[cluster_id]
            )
            response = self.vke_api.list_addons(request)
            return response
        except ApiException as e:
            print(f"获取组件列表失败: {e}")
            return None
    
    def install_addon(self, cluster_id, name, version, deploy_mode, deploy_node_type=None, config=None):
        """安装单个组件
        
        Args:
            cluster_id (str): 集群ID
            name (str): 组件名称
            version (str): 组件版本
            deploy_mode (str): 部署模式，'Managed'或'Unmanaged'
            deploy_node_type (str, optional): 部署节点类型，'Node'或'VirtualNode'
            config (str, optional): 组件配置，JSON格式字符串
            
        Returns:
            bool: 安装是否成功
        """
        try:
            create_addon_request = CreateAddonRequest(
                cluster_id=cluster_id,
                name=name,
                version=version,
                deploy_mode=deploy_mode
            )
            
            if deploy_node_type:
                create_addon_request.deploy_node_type = deploy_node_type
            if config:
                create_addon_request.config = config
                
            response = self.vke_api.create_addon(create_addon_request)
            print(f"组件 {name} 安装请求已提交")
            return True
        except ApiException as e:
            # 检查是否为组件已存在的错误
            if e.status == 409 and 'AlreadyExists.Name' in str(e):
                print(f"组件 {name} 已存在，跳过安装")
                return True
            print(f"安装组件 {name} 失败: {e}")
            return False
    
    def install_standard_addons(self, cluster_id):
        """安装标准组件集
        
        根据预定义的标准组件列表，安装集群所需的基本组件
        
        Args:
            cluster_id (str): 集群ID
            
        Returns:
            dict: 安装结果，包含成功和失败的组件列表
        """
        # 使用导入的标准组件配置
        standard_addons = STANDARD_ADDONS
        
        results = {
            "success": [],
            "failed": []
        }
        
        # 获取已安装的组件列表
        existing_addons = self.list_addons(cluster_id)
        existing_addon_names = []
        if existing_addons and hasattr(existing_addons, 'items'):
            existing_addon_names = [addon.name for addon in existing_addons.items]
        
        # 安装缺失的组件
        for addon in standard_addons:
            if addon["name"] in existing_addon_names:
                print(f"组件 {addon['name']} 已存在，跳过安装")
                continue
                
            success = self.install_addon(
                cluster_id=cluster_id,
                name=addon["name"],
                version=addon["version"],
                deploy_mode=addon["deploy_mode"],
                deploy_node_type=addon.get("deploy_node_type"),
                config=addon.get("config")
            )
            
            if success:
                results["success"].append(addon["name"])
            else:
                results["failed"].append(addon["name"])
            
            # 避免请求过于频繁
            time.sleep(2)
        
        return results

    def install_addons_from_log(self, log_file, cluster_id):
        """从日志文件中读取组件配置并安装
        
        Args:
            log_file (str): 日志文件路径
            cluster_id (str): 目标集群ID
            
        Returns:
            dict: 安装结果
        """
        try:
            # 读取日志文件
            with open(log_file, 'r') as f:
                log_data = json.load(f)
            
            # 提取组件列表
            addons = log_data.get("Result", {}).get("Items", [])
            # print(addons)
            if not addons:
                print("未在日志文件中找到组件列表")
                return {"success": [], "failed": []}
            
            results = {
                "success": [],
                "failed": []
            }
            
            # 获取已安装的组件列表
            existing_addons = self.list_addons(cluster_id)
            existing_addon_names = []
            if existing_addons and hasattr(existing_addons, 'items'):
                existing_addon_names = [addon.name for addon in existing_addons.items]
            
            # 安装组件
            for addon in addons:
                # print(addon)
                name = addon.get("Name")
                if name in existing_addon_names:
                    print(f"组件 {name} 已存在，跳过安装")
                    continue
                    
                # 准备组件配置
                addon_config = {
                    "name": name,
                    "version": addon.get("Version"),
                    "deploy_mode": addon.get("DeployMode"),
                    "deploy_node_type": addon.get("DeployNodeType"),
                    "config": addon.get("Config")
                }
                
                # 安装组件
                success = self.install_addon(
                    cluster_id=cluster_id,
                    name=addon_config["name"],
                    version=addon_config["version"],
                    deploy_mode=addon_config["deploy_mode"],
                    deploy_node_type=addon_config.get("deploy_node_type"),
                    config=addon_config.get("config")
                )
                
                if success:
                    results["success"].append(name)
                else:
                    results["failed"].append(name)
                
                # 避免请求过于频繁
                time.sleep(2)
            
            return results
        except Exception as e:
            print(f"从日志文件安装组件时发生错误: {e}")
            return {"success": [], "failed": [], "error": str(e)}


def main():
    """主函数示例"""
    # 配置信息
    ak = ""  # 替换为您的AK
    sk = ""  # 替换为您的SK
    region = "cn-shanghai"
    
    # 初始化VKE管理器
    vke_manager = VKEManager(ak=ak, sk=sk, region=region)
    
    # 步骤1: 创建或获取多个集群
    clusters_result = vke_manager.create_clusters()
    if not clusters_result:
        print("创建集群失败")
        return
        
    # 打印集群创建结果
    for cluster_name, result in clusters_result.items():
        if result['status'] == 'created':
            print(f'成功创建集群 {cluster_name}，ID: {result["cluster_id"]}')
        else:
            print(f'创建集群 {cluster_name} 失败: {result.get("error", "未知错误")}')
    
    # 步骤2: 对每个成功创建的集群执行后续操作
    for cluster_name, cluster_result in clusters_result.items():
        print(cluster_result)
        if cluster_result['status'] != 'created':
            continue
            
        cluster_id = cluster_result['cluster_id']
        print(f"\n开始处理集群: {cluster_name} (ID: {cluster_id})")
        
        # 等待集群就绪
        if not vke_manager.wait_for_cluster_ready(cluster_id):
            print(f"集群 {cluster_name} 未能在预期时间内就绪，跳过后续操作")
            continue
        
        # 创建多个节点池
        node_pools_result = vke_manager.create_node_pools(cluster_id)
        if not node_pools_result:
            print(f"为集群 {cluster_name} 创建节点池失败")
            continue
            
        for name, result in node_pools_result.items():
            if result['status'] == 'created':
                print(f'成功创建节点池 {name}，ID: {result["node_pool_id"]}')
            else:
                print(f'创建节点池 {name} 失败: {result.get("error", "未知错误")}')
    
        # 获取集群kubeconfig
        if not vke_manager.get_cluster_kubeconfig(cluster_id):
            print(f"获取集群 {cluster_name} 的kubeconfig失败")
            continue
            
        # # 安装标准组件
        # results = vke_manager.install_standard_addons(cluster_id)
        # print(f"集群 {cluster_name} 标准组件安装结果: {results}")
        
        # 从日志文件安装额外组件（可选）
        log_file = "listaddon.log"  # 替换为实际的日志文件路径
        if os.path.exists(log_file):
            results = vke_manager.install_addons_from_log(log_file, cluster_id)
            print(f"集群 {cluster_name} 从日志文件安装组件结果: {results}")
            
        print(f"集群 {cluster_name} 处理完成\n")


if __name__ == "__main__":
    main()