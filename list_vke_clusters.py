#!/usr/bin/env python
# -*- coding: utf-8 -*-

import volcenginesdkcore
import volcenginesdkvke
from volcenginesdkvke.models.list_clusters_request import ListClustersRequest
from configs.api_config import api_config
from base_resource_manager import BaseResourceManager
import os

class VKEClusterManager(BaseResourceManager):
    def __init__(self):
        super().__init__("VKE")
        self.vke_api = volcenginesdkvke.VKEApi()

    def _init_client(self):
        configuration = volcenginesdkcore.Configuration()
        configuration.ak = api_config['ak']
        configuration.sk = api_config['sk']
        configuration.region = api_config['region']
        configuration.client_side_validation = True
        volcenginesdkcore.Configuration.set_default(configuration)

    def list_resources(self):
        """列出所有集群信息"""
        try:
            request = ListClustersRequest()
            response = self.vke_api.list_clusters(request)
            
            if response and response.items:
                return [self._format_cluster_info(cluster) for cluster in response.items]
            return []
            
        except Exception as e:
            self.logger.error(f'获取集群列表时发生错误: {str(e)}')
            return []

    def _format_cluster_info(self, cluster):
        """格式化集群信息"""
        cluster_info = {
            'name': cluster.name,
            'id': cluster.id,
            'kubernetes_version': cluster.kubernetes_version,
            'create_time': cluster.create_time,
            'status': cluster.status.phase,
            'description': cluster.description,
            'network_config': {
                'vpc_id': cluster.cluster_config.vpc_id,
                'subnet_ids': cluster.cluster_config.subnet_ids,
                'service_cidr': cluster.services_config.service_cidrsv4,
                'pod_network_mode': cluster.pods_config.pod_network_mode
            },
            'access_config': {
                'public_access': cluster.cluster_config.api_server_public_access_enabled,
                'default_public_access': cluster.cluster_config.resource_public_access_default_enabled
            }
        }
        
        # 获取kubeconfig
        try:
            kubeconfig_req_filter = volcenginesdkvke.FilterForListKubeconfigsInput(
                cluster_ids=[cluster.id],
                types=["Public"]
            )
            kubeconfig_request = volcenginesdkvke.ListKubeconfigsRequest(
                filter=kubeconfig_req_filter,
                page_number=1,
                page_size=100,
            )
            kubeconfig_response = self.vke_api.list_kubeconfigs(kubeconfig_request)
            
            if not (kubeconfig_response and kubeconfig_response.items):
                create_kubeconfig_request = volcenginesdkvke.CreateKubeconfigRequest(
                    cluster_id=cluster.id,
                    type="Public",
                    valid_duration=867240
                )
                self.vke_api.create_kubeconfig(create_kubeconfig_request)
                kubeconfig_response = self.vke_api.list_kubeconfigs(kubeconfig_request)
            
            if kubeconfig_response and kubeconfig_response.items:
                cluster_info['kubeconfig'] = kubeconfig_response.items[0].kubeconfig
            else:
                cluster_info['kubeconfig'] = '无法获取kubeconfig配置'
        except Exception as e:
            cluster_info['kubeconfig'] = f'获取kubeconfig时发生错误: {str(e)}'
            
        return cluster_info

    def _write_resources_to_file(self, file, clusters):
        """将集群信息写入文件"""
        # 写入集群基本信息表格
        file.write("### VKE集群基本信息\n")
        file.write("| 集群名称 | 集群ID | Kubernetes版本 | 状态 | 创建时间 |\n")
        file.write("|----------|---------|----------------|------|----------|\n")
        for cluster in clusters:
            file.write(f"| {cluster['name']} | {cluster['id']} | {cluster['kubernetes_version']} | {cluster['status']} | {cluster['create_time']} |\n")
        file.write("\n")

        # 写入详细信息
        for cluster in clusters:
            file.write(f"#### 集群: {cluster['name']}\n")
            
            # 基本信息
            file.write("##### 基本信息\n")
            file.write("| 属性 | 值 |\n")
            file.write("|------|-----|\n")
            file.write(f"| 描述 | {cluster['description']} |\n")
            
            # 网络配置
            file.write("\n##### 网络配置\n")
            file.write("| 配置项 | 值 |\n")
            file.write("|--------|-----|\n")
            file.write(f"| VPC ID | {cluster['network_config']['vpc_id']} |\n")
            file.write(f"| 子网IDs | {cluster['network_config']['subnet_ids']} |\n")
            file.write(f"| 服务CIDR | {cluster['network_config']['service_cidr']} |\n")
            file.write(f"| Pod网络模式 | {cluster['network_config']['pod_network_mode']} |\n")
            
            # 访问配置
            file.write("\n##### 访问配置\n")
            file.write("| 配置项 | 状态 |\n")
            file.write("|--------|------|\n")
            file.write(f"| 公网访问 | {'已开启' if cluster['access_config']['public_access'] else '未开启'} |\n")
            file.write(f"| 默认公网访问 | {'已开启' if cluster['access_config']['default_public_access'] else '未开启'} |\n")
            
            # Kubeconfig配置
            file.write("\n##### Kubeconfig配置\n")
            file.write("```\n")
            file.write(cluster['kubeconfig'])
            file.write("\n```\n\n")

    def list_and_write_resources(self):
        """收集并记录网络资源信息
        
        获取所有网络资源信息并写入Markdown文件。
        """
        try:
            manager = VKEClusterManager()
            resources = manager.list_resources()
            
            # 确保logs目录存在
            os.makedirs('./markdown', exist_ok=True)
            
            # 写入Markdown文件
            with open('./markdown/vke_resources.md', 'w', encoding='utf-8') as f:
                manager._write_resources_to_file(f, resources)
                
            manager.logger.info('VKE资源信息已写入 ./markdown/vke_resources.md')
            print("成功完成所有VKE资源信息的收集和记录")
            return True
        except Exception as e:
            print(f"执行过程中发生错误: {e}")
            return False

if __name__ == "__main__":
    manager = VKEClusterManager()
    manager.list_and_write_resources()