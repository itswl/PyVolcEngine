# -*- coding: utf-8 -*-

import os
import json
from typing import Dict, List, Optional, Union
from volcenginesdkcore.rest import ApiException
from volcenginesdkcore import Configuration
import volcenginesdkclb
from volcenginesdkclb import CLBApi, DescribeLoadBalancersRequest
from configs.api_config import api_config
from configs.clb_configs import clb_configs
import time

class CLBManager:
    """负载均衡资源管理器"""

    def __init__(self):
        """初始化CLB管理器"""
        self.config = Configuration()
        self.config.ak = os.getenv('volcAK')  or api_config['ak']
        self.config.sk = os.getenv('volcSK')  or api_config['sk']
        self.config.region = os.getenv('Region', 'cn-shanghai')  or api_config['region']
        Configuration.set_default(self.config)
        self.client = CLBApi()

    def create_load_balancer(self, name: str, subnet_id: str, type: str = 'public',
                           load_balancer_spec: str = 'small_1', eip: Optional[Dict] = None,
                           address_ip_version: str = 'ipv4',
                           load_balancer_billing_type: int = 2) -> Dict:
        """创建负载均衡实例

        Args:
            name: 负载均衡实例名称
            subnet_id: 子网ID
            type: 负载均衡类型，可选值：public（公网）、private（私网）
            load_balancer_spec: 规格，可选值：small_1, medium_1, large_1
            eip: EIP配置信息，可选，包含bandwidth和eip_billing_type
            address_ip_version: IP版本，可选值：ipv4、ipv6，默认ipv4
            load_balancer_billing_type: 计费类型，默认2

        Returns:
            Dict: 创建的负载均衡实例信息
        """
        try:
            request = volcenginesdkclb.CreateLoadBalancerRequest(
                load_balancer_name=name,
                subnet_id=subnet_id,
                type=type,
                load_balancer_spec=load_balancer_spec,
                address_ip_version=address_ip_version,
                load_balancer_billing_type=load_balancer_billing_type,
                region_id=self.config.region
            )
            
            if eip:
                eip_config = volcenginesdkclb.EipBillingConfigForCreateLoadBalancerInput(
                    bandwidth=eip.get('bandwidth', 10),
                    eip_billing_type=eip.get('eip_billing_type', 2)
                )
                request.eip_billing_config = eip_config
            # print(request)
            response = self.client.create_load_balancer(request)
            print(f'成功创建负载均衡实例：{name}')
            return response.to_dict()
        except ApiException as e:
            print(f'创建负载均衡实例失败：{str(e)}')
            raise

    def describe_load_balancers(self, load_balancer_ids: Optional[List[str]] = None) -> Dict:
        """查询负载均衡实例列表

        Args:
            load_balancer_ids: 负载均衡实例ID列表，可选

        Returns:
            Dict: 负载均衡实例列表信息
        """
        try:
            request = volcenginesdkclb.DescribeLoadBalancersRequest()
            if load_balancer_ids:
                request.load_balancer_ids = load_balancer_ids
            response = self.client.describe_load_balancers(request)
            return response.to_dict()
        except ApiException as e:
            print(f'查询负载均衡实例列表失败：{str(e)}')
            raise

    def modify_load_balancer_attributes(self, load_balancer_id: str,
                                      name: Optional[str] = None,
                                      description: Optional[str] = None) -> Dict:
        """修改负载均衡实例属性

        Args:
            load_balancer_id: 负载均衡实例ID
            name: 新的负载均衡实例名称，可选
            description: 新的描述信息，可选

        Returns:
            Dict: 修改结果
        """
        try:
            request = {'LoadBalancerId': load_balancer_id}
            if name:
                request['LoadBalancerName'] = name
            if description:
                request['Description'] = description
            response = self.client.modify_load_balancer_attributes(request)
            print(f'成功修改负载均衡实例属性：{load_balancer_id}')
            return response.to_dict()
        except ApiException as e:
            print(f'修改负载均衡实例属性失败：{str(e)}')
            raise

    def delete_load_balancer(self, load_balancer_ids: Union[str, List[str]]) -> List[Dict]:
        """删除负载均衡实例

        Args:
            load_balancer_ids: 单个负载均衡实例ID或ID列表

        Returns:
            List[Dict]: 删除结果列表
        """
        if isinstance(load_balancer_ids, str):
            load_balancer_ids = [load_balancer_ids]

        results = []
        for lb_id in load_balancer_ids:
            try:
                delete_load_balancer_request = volcenginesdkclb.DeleteLoadBalancerRequest(
                    force_delete=True,
                    load_balancer_id=lb_id
                )
                response = self.client.delete_load_balancer(delete_load_balancer_request)
                print(f'成功删除负载均衡实例：{lb_id}')
                results.append(response.to_dict())
            except ApiException as e:
                print(f'删除负载均衡实例失败：{lb_id}, 错误：{str(e)}')
                continue
        return results

    def create_load_balancers_from_config(self) -> List[Dict]:
        """从配置文件创建多个负载均衡实例

        Returns:
            List[Dict]: 创建的负载均衡实例信息列表
        """
        results = []
        # 获取现有负载均衡实例列表
        existing_lbs = self.describe_load_balancers()
        existing_names = [lb['load_balancer_name'] for lb in existing_lbs.get('load_balancers', [])]
        # print(existing_names)
        # time.sleep(100)
        for config in clb_configs:
            try:
                # 检查是否存在同名实例
                if config['name'] in existing_names:
                    print(f'跳过创建负载均衡实例 {config["name"]}：已存在同名实例')
                    continue

                result = self.create_load_balancer(
                    name=config['name'],
                    subnet_id=config['subnet_id'],
                    type=config['type'],
                    load_balancer_spec=config['load_balancer_spec'],
                    eip=config['eip']
                )
                result_dict = result.to_dict() if hasattr(result, 'to_dict') else result
                if 'description' in config and 'LoadBalancerId' in result_dict:
                    self.modify_load_balancer_attributes(
                        load_balancer_id=result_dict['LoadBalancerId'],
                        description=config['description']
                    )
                results.append(result_dict)
            except ApiException as e:
                print(f'创建负载均衡实例 {config["name"]} 失败：{str(e)}')
                continue
        return results

    def write_load_balancers_to_file(self):
        """将负载均衡实例信息写入文件"""
        # 查询现有的负载均衡实例
        load_balancers = self.describe_load_balancers()
        # 筛选并格式化输出指定字段
        formatted_lbs = [{
            'load_balancer_id': lb.get('load_balancer_id'),
            'load_balancer_name': lb.get('load_balancer_name'),
            'load_balancer_spec': lb.get('load_balancer_spec'),
            'description': lb.get('description'),
            'status': lb.get('status'),
            'address_ip_version': lb.get('address_ip_version'),
            'eip_address': lb.get('eip_address'),
            'eip_id': lb.get('eip_id'),
            'eni_address': lb.get('eni_address'),
            'master_zone_id': lb.get('master_zone_id'),
            'slave_zone_id': lb.get('slave_zone_id'),
            'vpc_id': lb.get('vpc_id'),
            'subnet_id': lb.get('subnet_id')
        } for lb in load_balancers.get('load_balancers', [])]

        # 确保logs目录存在
        os.makedirs('./logs', exist_ok=True)
        # 将负载均衡实例信息写入文件
        with open('./logs/load_balancers.json', 'w', encoding='utf-8') as f:
            json.dump({'load_balancers': formatted_lbs}, f, indent=2, ensure_ascii=False)
        print('现有负载均衡实例列表已写入./logs/load_balancers.json')

def main():
    """主函数，用于测试CLB管理器的功能"""
    import argparse

    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description='CLB管理器命令行工具')
    parser.add_argument('--create', action='store_true', help='从配置文件创建CLB实例')
    parser.add_argument('--delete', type=str, nargs='+', help='要删除的负载均衡实例ID列表')
    args = parser.parse_args()

    try:
        
        
        if args.delete:
            # 如果指定了删除参数，先验证实例是否存在
            load_balancers = clb_manager.describe_load_balancers()
            existing_ids = [lb['load_balancer_id'] for lb in load_balancers.get('load_balancers', [])]
            not_found_ids = [lb_id for lb_id in args.delete if lb_id not in existing_ids]
            
            if not_found_ids:
                print(f'错误：找不到以下ID的负载均衡实例：{", ".join(not_found_ids)}')
            
            # 执行删除操作
            else:
                print(f'正在删除负载均衡实例：{args.delete}')
                clb_manager.delete_load_balancer(args.delete)

        elif args.create:
            # 如果指定了创建参数，从配置文件创建实例
            print('开始从配置文件创建负载均衡实例...')
            created_load_balancers = clb_manager.create_load_balancers_from_config()
            print(f'成功创建 {len(created_load_balancers)} 个负载均衡实例')


    except Exception as e:
        print(f'操作失败：{str(e)}')

if __name__ == '__main__':
    clb_manager = CLBManager()
    main() 
    time.sleep(5)
    clb_manager.write_load_balancers_to_file()