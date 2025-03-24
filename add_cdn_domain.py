#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
python add_cdn_domain.py \
    --domain eve-cn-prod-cms-object-cdn.yourdomain.com \
    --primary-origin eve-cn-prod-cms-object.tos-cn-shanghai.volces.com \
    --service-type web \
	--instance_type tos \
    --service-region chinese_mainland \
    --origin-protocol followclient \
    --auto-cert true \
    --https true --ipv6 true --project default
'''
import os
import sys
import json
import argparse
from typing import Dict, List, Any, Optional, Tuple
from configs.api_config import api_config
from sign import APIConfig, APIClient, APIError


class CDNConfig(APIConfig):
    """CDN API配置类，继承自APIConfig"""
    
    def __init__(self):
        # 设置CDN服务的默认参数
        os.environ.setdefault('Service', 'CDN')
        os.environ.setdefault('Version', '2021-03-01')
        os.environ.setdefault('Region', 'cn-shanghai')
        os.environ.setdefault('Action', 'AddCdnDomain')
        os.environ.setdefault('method', 'POST')
        os.environ.setdefault('volcAK', api_config['ak'])
        os.environ.setdefault('volcSK', api_config['sk'])
        super().__init__()


def get_certificate() -> Tuple[Optional[str], Optional[str]]:
    """获取证书ID和证书名称
    
    Returns:
        Tuple[Optional[str], Optional[str]]: 证书ID和证书名称
    """
    try:
        print("开始获取证书...")
        # 设置证书服务的默认参数
        os.environ['Service'] = 'CDN'
        os.environ['Version'] = '2021-03-01'
        os.environ['Region'] = 'cn-beijing'
        os.environ['Action'] = 'ListCertInfo'
        os.environ['method'] = 'POST'
        os.environ.setdefault('volcAK', api_config['ak'])
        os.environ.setdefault('volcSK', api_config['sk'])
        # 使用正确的Source参数
        os.environ['API_PARAMS'] = '{"Source": "volc_cert_center"}'
        # print("API参数:", os.environ['API_PARAMS'])
        
        # 确保api_config中有AK和SK
        if not os.environ.get('volcAK') or not os.environ.get('volcSK'):
            print("错误: AK或SK未设置")
            return None, None
            
        # 创建API客户端
        config = APIConfig()
        client = APIClient(config)
        
        print("发送证书API请求...")
        # 发送请求
        try:
            response = client.send_request()
            # print('证书API响应:', response)
            
            # 检查是否有证书
            if 'Result' in response and 'CertInfo' in response['Result'] and response['Result']['CertInfo']:
                cert = response['Result']['CertInfo'][0]  # 使用第一个证书
                print(f"找到证书: {cert.get('CertName')} (ID: {cert.get('CertId')})")
                return cert.get('CertId'), cert.get('CertName')
            else:
                print("API响应中未找到证书:", json.dumps(response, indent=2, ensure_ascii=False))
        except Exception as e:
            print(f"证书API请求异常: {str(e)}")
            # 尝试打印response变量，如果存在
            if 'response' in locals():
                print("响应内容:", response)
            import traceback
            traceback.print_exc()
            
        print("未找到可用证书")
        return None, None
    except Exception as e:
        print(f"获取证书失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, None


def get_cdn_cname(domain: str) -> Optional[str]:
    """获取CDN域名的CNAME
    
    Args:
        domain: CDN域名
        
    Returns:
        Optional[str]: CNAME记录
    """
    try:
        print(f"获取域名 {domain} 的CNAME...")
        # 设置CDN服务的默认参数
        os.environ['Service'] = 'CDN'
        os.environ['Version'] = '2021-03-01'
        os.environ['Region'] = 'cn-shanghai'
        os.environ['Action'] = 'DescribeCdnConfig'
        os.environ['method'] = 'POST'
        os.environ.setdefault('volcAK', api_config['ak'])
        os.environ.setdefault('volcSK', api_config['sk'])
        
        # 设置API参数
        api_params = {
            "Domain": domain
        }
        os.environ['API_PARAMS'] = json.dumps(api_params)
        
        # 创建API客户端
        config = APIConfig()
        client = APIClient(config)
        
        # 发送请求
        response = client.send_request()
        
        # 检查响应中是否有CNAME信息
        if 'Result' in response and 'DomainConfig' in response['Result']:
            cname = response['Result']['DomainConfig'].get('Cname')
            if cname:
                print(f"获取到CNAME: {cname}")
                return cname
        
        print(f"未找到域名 {domain} 的CNAME")
        return None
    except Exception as e:
        print(f"获取CNAME失败: {str(e)}")
        return None


def add_cdn_domain(
    domain: str,
    primary_origin: List[str],
    service_type: str = 'web',
    service_region: str = 'chinese_mainland',
    origin_protocol: str = 'followclient',
    https: bool = True,
    ipv6: bool = True,
    project: str = 'default',
    cert_id: Optional[str] = None,
    cert_name: Optional[str] = None,
    instance_type: Optional[str] = None,
    auto_cert: bool = False
) -> Dict[str, Any]:
    """添加CDN域名
    
    Args:
        domain: CDN域名，例如 example.com
        primary_origin: 源站列表，例如 ["example-origin.com"]
        service_type: 服务类型，可选值: web, download, video
        service_region: 服务区域，可选值: chinese_mainland, global, overseas
        origin_protocol: 回源协议，可选值: http, https, followclient
        https: 是否开启HTTPS
        ipv6: 是否开启IPv6
        project: 项目名称
        cert_id: 证书ID，启用HTTPS时必填
        cert_name: 证书名称，启用HTTPS时必填
        instance_type: 实例类型，例如: tos
        auto_cert: 是否自动获取证书
        
    Returns:
        Dict: API响应结果
    """
    # 如果启用HTTPS并设置了自动获取证书，且未提供证书信息
    if https and auto_cert and (not cert_id or not cert_name):
        cert_id, cert_name = get_certificate()
        if not cert_id or not cert_name:
            print("警告: 未找到可用证书，将禁用HTTPS")
            https = False

    # 构建源站配置
    origin_lines = []
    for origin in primary_origin:
        origin_line = {
            "Address": origin,
            "OriginType": "primary"
        }
        # 如果提供了实例类型，添加到源站配置中
        if instance_type:
            origin_line["InstanceType"] = instance_type
        origin_lines.append(origin_line)

    # 设置API参数
    api_params = {
        "Domain": domain,
        "ServiceType": service_type,
        "Origin": [
            {
                "OriginAction": {
                    "OriginLines": origin_lines
                }
            }
        ],
        "OriginProtocol": origin_protocol,
        "IPv6": {"Switch": ipv6},
        "ServiceRegion": service_region,
        "Project": project
    }
    
    # 如果启用HTTPS，添加HTTPS配置
    if https:
        https_config = {"Switch": https}
        https_config["HTTP2"] = True
        # 如果提供了证书信息，添加到HTTPS配置中
        if cert_id and cert_name:
            https_config["CertInfo"] = {
                "CertId": cert_id,
                "CertName": cert_name
            }
        api_params["HTTPS"] = https_config
    else:
        api_params["HTTPS"] = {"Switch": False}
    
    # 将API参数设置到环境变量
    os.environ['API_PARAMS'] = json.dumps(api_params)
    os.environ['Action'] = 'AddCdnDomain'
    
    # print(os.environ['API_PARAMS'])
    try:
        # 创建CDN配置和API客户端
        config = CDNConfig()
        client = APIClient(config)
        
        # 发送请求
        response = client.send_request()
        print(f"成功添加CDN域名: {domain}")
        return response
    except (ValueError, APIError) as e:
        print(f"添加CDN域名失败: {str(e)}")
        return {"error": str(e)}


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='添加火山引擎CDN域名')
    parser.add_argument('--domain', required=True, help='CDN域名，例如: example.com')
    parser.add_argument('--primary-origin', required=True, nargs='+', help='源站列表，例如: origin1.com origin2.com')
    parser.add_argument('--service-type', default='web', choices=['web', 'download', 'video'], help='服务类型')
    parser.add_argument('--service-region', default='chinese_mainland', 
                        choices=['chinese_mainland', 'global', 'overseas'], help='服务区域')
    parser.add_argument('--origin-protocol', default='followclient', 
                        choices=['http', 'https', 'followclient'], help='回源协议')
    parser.add_argument('--https', type=lambda x: x.lower() not in ('false', '0', 'no', 'n'), default=True, 
                        help='是否开启HTTPS，可接受的值: true/false, yes/no, 1/0')
    parser.add_argument('--ipv6', type=lambda x: x.lower() not in ('false', '0', 'no', 'n'), default=True, 
                        help='是否开启IPv6，可接受的值: true/false, yes/no, 1/0')
    parser.add_argument('--cert-id', help='证书ID，启用HTTPS时必填')
    parser.add_argument('--cert-name', help='证书名称，启用HTTPS时必填')
    parser.add_argument('--project', default='default', help='项目名称')
    parser.add_argument('--instance_type', help='实例类型，例如: tos')
    parser.add_argument('--auto-cert', action='store_true', help='是否自动获取证书')
    
    return parser.parse_args()


def main():
    """主函数"""
    args = parse_arguments()
    
    # 检查HTTPS参数，如果没有设置自动获取证书
    if args.https and not args.auto_cert and (not args.cert_id or not args.cert_name):
        print("错误: 启用HTTPS时必须提供证书ID(--cert-id)和证书名称(--cert-name)，或者使用--auto-cert自动获取证书")
        sys.exit(1)
    
    # 调用添加CDN域名函数
    result = add_cdn_domain(
        domain=args.domain,
        primary_origin=args.primary_origin,
        service_type=args.service_type,
        service_region=args.service_region,
        origin_protocol=args.origin_protocol,
        https=args.https,
        ipv6=args.ipv6,
        project=args.project,
        cert_id=args.cert_id,
        cert_name=args.cert_name,
        instance_type=args.instance_type,
        auto_cert=args.auto_cert
    )
    
    # 打印完整响应
    print(json.dumps(result, indent=2, ensure_ascii=False))

        
        # 获取CNAME
    cname = get_cdn_cname(args.domain)
    if cname:
        result['Cname'] = cname
        
    # 如果成功添加了域名并获取到了CNAME，单独打印CNAME信息
    if 'Cname' in result:
        print("\n============================================")
        # print(f"域名: {args.domain}")
        # print(f"CNAME: {result['Cname']}")
        # print("============================================")
        print("请在您的DNS服务商处添加此CNAME记录，以便将流量路由到CDN")
        # 提取域名前缀，动态识别并提取
        import re
        # 提取域名的第一部分（主机名）
        domain_name = '.'.join(args.domain.split('.')[-2:])
        host_prefix = args.domain.removesuffix('.' + domain_name)
        print(f"python dns_operations.py --domain {domain_name} --action create --host {host_prefix} --type CNAME --value {result['Cname']}")


if __name__ == '__main__':
    main()