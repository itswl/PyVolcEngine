#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# 获取域名和cname

import os
import json
from typing import Dict, List, Any, Optional, Tuple
from sign import APIConfig, APIClient, APIError
from configs.api_config import api_config
import argparse


class DNSConfig(APIConfig):
    """DNS API配置类，继承自APIConfig"""
    
    def __init__(self):
        # 设置DNS服务的默认参数
        os.environ.setdefault('Service', 'DNS')
        os.environ.setdefault('Version', '2018-08-01')
        os.environ.setdefault('Region', 'cn-beijing')
        os.environ.setdefault('method', 'POST')
        super().__init__()


def list_zones(ak=None, sk=None, region="cn-beijing") -> Dict[str, Any]:
    """获取域名ID列表
    
    Args:
        ak: 访问密钥ID，如果不提供则从环境变量获取
        sk: 访问密钥，如果不提供则从环境变量获取
        region: 区域，默认为cn-beijing
        
    Returns:
        Dict: API响应结果
    """
    # 设置区域信息
    if region:
        os.environ['Region'] = region
    
    os.environ['Action'] = 'ListZones'
    os.environ['API_PARAMS'] = json.dumps({})
    
    try:
        # 创建DNS配置和API客户端
        config = DNSConfig()
        client = APIClient(config)
        
        # 发送请求
        response = client.send_request()
        # print("成功获取域名ID列表")
        # print(json.dumps(response, indent=2, ensure_ascii=False))
        return response
    except (ValueError, APIError) as e:
        error_msg = f"获取域名ID列表失败: {str(e)}"
        print(error_msg)
        return {"error": error_msg}

def ListRecords(ak=None, sk=None, region="cn-beijing", zid=None, PageNumber=1, PageSize=500) -> Dict[str, Any]:
    """获取域名ID列表
    
    Args:
        ak: 访问密钥ID，如果不提供则从环境变量获取
        sk: 访问密钥，如果不提供则从环境变量获取
        region: 区域，默认为cn-beijing
        
    Returns:
        Dict: API响应结果
    """
    # 设置区域信息
    if region:
        os.environ['Region'] = region

    api_params = {
        "ZID": zid,
        "PageNumber": PageNumber,
        "PageSize": PageSize,
    }

    os.environ['Action'] = 'ListRecords'
    os.environ['API_PARAMS'] = json.dumps(api_params)
    
    try:
        # 创建DNS配置和API客户端
        config = DNSConfig()
        client = APIClient(config)
        
        # 发送请求
        response = client.send_request()
        return response
    except (ValueError, APIError) as e:
        error_msg = f"获取域名ID列表失败: {str(e)}"
        print(error_msg)
        return {"error": error_msg}

def create_record(host: str, record_type: str, value: str, zid: int, ak=None, sk=None, region="cn-beijing") -> Dict[str, Any]:
    """添加DNS解析记录
    
    Args:
        host: 主机记录，例如 example.com
        record_type: 记录类型，例如 CNAME, A, AAAA等
        value: 记录值
        zid: 域名ID
        ak: 访问密钥ID，如果不提供则从环境变量获取
        sk: 访问密钥，如果不提供则从环境变量获取
        region: 区域，默认为cn-beijing
        
    Returns:
        Dict: API响应结果
    """
    # 设置区域信息
    if region:
        os.environ['Region'] = region
    
    # 设置API参数
    api_params = {
        "ZID": zid,
        "Host": host,
        "Type": record_type,
        "Value": value
    }
    
    os.environ['Action'] = 'CreateRecord'
    os.environ['API_PARAMS'] = json.dumps(api_params)
    
    try:
        # 创建DNS配置和API客户端
        config = DNSConfig()
        client = APIClient(config)
        
        # 发送请求
        response = client.send_request()
        print(f"成功添加DNS解析记录: {host}")
        print(json.dumps(response, indent=2, ensure_ascii=False))
        return response
    except (ValueError, APIError) as e:
        error_msg = f"添加DNS解析记录失败: {str(e)}"
        print(error_msg)
        return {"error": error_msg}


def export_records_to_file(response: Dict[str, Any], output_file: str = "dns_records.txt") -> bool:
    """将DNS记录导出到文件
    
    Args:
        response: ListRecords函数的返回结果
        output_file: 输出文件路径，默认为dns_records.txt
        
    Returns:
        bool: 是否成功导出
    """
    try:
        # 检查响应是否包含记录
        if "error" in response:
            print(f"错误: {response['error']}")
            return False
            
        if "Result" not in response or "Records" not in response["Result"]:
            print("错误: 响应中没有找到DNS记录")
            return False
            
        records = []
        for item in response["Result"]["Records"]:
            record = {
                'FQDN': item.get('FQDN', ''),
                'Host': item.get('Host', ''),
                'Type': item.get('Type', ''),
                'Value': item.get('Value', ''),
                'Enable': 'Yes' if item.get('Enable', False) else 'No'
            }
            records.append(record)
            
        # 格式化记录为表格
        if not records:
            formatted_table = "没有找到有效的DNS记录"
        else:
            # 确定每列的最大宽度
            max_widths = {}
            headers = ['FQDN', 'Host', 'Type', 'Value', 'Enable']
            
            for header in headers:
                max_widths[header] = len(header)
                for record in records:
                    max_widths[header] = max(max_widths[header], len(str(record.get(header, ''))))
            
            # 创建表头
            header_line = ' | '.join(f"{header:{max_widths[header]}}" for header in headers)
            separator_line = '-+-'.join('-' * max_widths[header] for header in headers)
            
            # 创建表格内容
            table_rows = [header_line, separator_line]
            for record in records:
                row = ' | '.join(f"{str(record.get(header, '')):{max_widths[header]}}" for header in headers)
                table_rows.append(row)
            
            formatted_table = '\n'.join(table_rows)
        
        # 写入文件
        with open(output_file, 'w') as f:
            f.write(formatted_table)
            
        print(f"DNS记录已成功写入文件: {output_file}")
        return True
    except Exception as e:
        print(f"错误: 导出DNS记录时出现异常 - {str(e)}")
        return False


def create_records_from_file(file_path: str, zid: int, ak=None, sk=None, region="cn-beijing") -> List[Dict[str, Any]]:
    """从导出的文件中读取DNS记录并创建这些记录
    
    Args:
        file_path: 导出的DNS记录文件路径
        zid: 域名ID
        ak: 访问密钥ID，如果不提供则从环境变量获取
        sk: 访问密钥，如果不提供则从环境变量获取
        region: 区域，默认为cn-beijing
        
    Returns:
        List[Dict[str, Any]]: 创建记录的结果列表
    """
    try:
        # 读取文件内容
        with open(file_path, 'r') as f:
            content = f.read()
        
        if not content or content.strip() == "没有找到有效的DNS记录":
            print(f"错误: 文件 {file_path} 中没有找到有效的DNS记录")
            return []
        
        # 解析表格内容
        lines = content.strip().split('\n')
        if len(lines) < 3:  # 至少需要表头、分隔线和一条记录
            print(f"错误: 文件 {file_path} 格式不正确，无法解析")
            return []
        
        # 提取表头和记录
        header_line = lines[0]
        headers = [h.strip() for h in header_line.split('|')]
        
        # 创建记录列表
        results = []
        for i in range(2, len(lines)):  # 跳过表头和分隔线
            line = lines[i]
            if not line.strip():
                continue
                
            # 解析记录行
            values = [v.strip() for v in line.split('|')]
            if len(values) < len(headers):
                print(f"警告: 第 {i+1} 行格式不正确，跳过")
                continue
                
            # 创建记录字典
            record = {}
            for j, header in enumerate(headers):
                header = header.strip()
                if j < len(values):
                    record[header] = values[j].strip()
            
            # 检查必要字段
            if not all(k in record and record[k] for k in ['Host', 'Type', 'Value']):
                print(f"警告: 第 {i+1} 行缺少必要字段 (Host, Type, Value)，跳过")
                continue
                
            # 创建DNS记录
            print(f"正在创建记录: Host={record['Host']}, Type={record['Type']}, Value={record['Value']}")
            response = create_record(
                host=record['Host'],
                record_type=record['Type'],
                value=record['Value'],
                zid=zid,
                ak=ak,
                sk=sk,
                region=region
            )
            
            results.append(response)
        
        if not results:
            print("没有创建任何记录")
        else:
            print(f"成功从文件 {file_path} 创建了 {len(results)} 条DNS记录")
            
        return results
    except FileNotFoundError:
        print(f"错误: 文件 {file_path} 不存在")
        return []
    except Exception as e:
        print(f"错误: 从文件创建DNS记录时出现异常 - {str(e)}")
        return []


if __name__ == "__main__":
    # 示例1：获取域名ID列表
    print("\n获取域名ID列表示例:")
    response = list_zones()
    # print(response)
    if "Result" in response and "Zones" in response["Result"]:
        for zone in response["Result"]["Zones"]:
            print(f"ZID: {zone.get('ZID', 'N/A')}, ZoneName: {zone.get('ZoneName', 'N/A')}")
    # 设置命令行参数解析器
    print('\n')
    print('示例命令：')
    print('python dns_operations.py --zid ZID --action export --output dns_records.txt # 导出到文件')
    print('python dns_operations.py --zid ZID --action create --host test.com --type CNAME --value CNAME.test.com # 创建单条CNAME记录')
    print('python dns_operations.py --zid ZID --action import --input dns_records.txt # 从文件导入')
    print('\n')
    parser = argparse.ArgumentParser(description='DNS操作工具')
    parser.add_argument('--action', required=True, 
                        choices=['list', 'create', 'export', 'import'], 
                        help='操作类型: list (列出记录), create (创建记录), export (导出记录到文件) 或 import (从文件导入记录)')
    parser.add_argument('--zid', type=int, required=True, help='域名ID')
    parser.add_argument('--host', help='主机记录，例如: example.com (仅创建记录时需要)')
    parser.add_argument('--type', help='记录类型，例如: CNAME, A, AAAA等 (仅创建记录时需要)')
    parser.add_argument('--value', help='记录值 (仅创建记录时需要)')
    parser.add_argument('--output', default='dns_records.txt', help='输出文件路径 (仅导出记录时需要)')
    parser.add_argument('--input', help='输入文件路径 (仅从文件导入记录时需要)')
    
    args = parser.parse_args()

    # 根据action参数执行不同的操作
    if args.action == 'list':
        # 列出指定域名ID的所有记录
        response = ListRecords(zid=args.zid)
        print("\n域名记录列表:")
        print(json.dumps(response, indent=2, ensure_ascii=False))
    
    elif args.action == 'create':
        # 验证创建记录所需的参数
        if not all([args.host, args.type, args.value]):
            print("错误: 创建记录需要提供 --host, --type 和 --value 参数")
            print('--host test.com --type CNAME --value CNAME.test.com --zid 12345')
            parser.print_help()
            exit(1)
            
        # 创建新记录
        print("\n创建DNS解析记录:")
        create_record(
            host=args.host,
            record_type=args.type,
            value=args.value,
            zid=args.zid
        )
    
    elif args.action == 'export':
        # 导出记录到文件
        print("\n导出DNS记录到文件:")
        response = ListRecords(zid=args.zid)
        export_records_to_file(response, args.output)
    
    elif args.action == 'import':
        # 验证导入记录所需的参数
        if not args.input:
            print("错误: 从文件导入记录需要提供 --input 参数")
            parser.print_help()
            exit(1)
            
        # 从文件导入记录
        print("\n从文件导入DNS记录:")
        create_records_from_file(
            file_path=args.input,
            zid=args.zid
        )
    
    elif args.action == 'export':
        # 获取记录并导出到文件
        print("\n导出DNS记录到文件:")
        response = ListRecords(zid=args.zid)
        export_records_to_file(response, args.output)
