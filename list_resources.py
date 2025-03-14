# coding: utf-8
from __future__ import absolute_import
from list_eip_resources import EIPResourceManager
from list_network_resources import NetworkResourceManager
from list_vke_clusters import VKEClusterManager
from list_database_resources import DatabaseResourceManager
import logging
import os

# 配置日志记录
logger = logging.getLogger(__name__)

def print_menu():
    """打印菜单选项"""
    print("\n资源列表查询系统")
    print("-" * 30)
    print("1. 列出所有EIP资源")
    print("2. 列出所有网络资源")
    print("3. 列出所有VKE集群")
    print("4. 列出所有数据库和消息队列资源")
    print("0. 退出")
    print("-" * 30)

def list_all_resources():
    """列出所有资源"""
    try:
        # 创建资源管理器实例
        eip_manager = EIPResourceManager()
        network_manager = NetworkResourceManager()
        vke_manager = VKEClusterManager()
        database_manager = DatabaseResourceManager()

        # 获取并写入资源信息
        eip_manager.list_and_write_resources()
        network_manager.list_and_write_resources()
        vke_manager.list_and_write_resources()
        database_manager.list_and_write_resources()

        print("成功完成所有资源信息的收集和记录")
    except Exception as e:
        print(f"执行过程中发生错误: {e}")

def main():
    while True:
        try:
            print_menu()
            choice = input("请选择操作 (0-4): ").strip()
            
            if choice == '0':
                print("感谢使用，再见！")
                break
            elif choice == '1':
                eip_manager = EIPResourceManager()
                eip_manager.list_and_write_resources()
                print("成功完成EIP资源信息的收集和记录")
            elif choice == '2':
                network_manager = NetworkResourceManager()
                network_manager.list_and_write_resources()
                print("成功完成网络资源信息的收集和记录")
            elif choice == '3':
                vke_manager = VKEClusterManager()
                vke_manager.list_and_write_resources()
                print("成功完成VKE集群信息的收集和记录")
            elif choice == '4':
                database_manager = DatabaseResourceManager()
                database_manager.list_and_write_resources()
                print("成功完成数据库和消息队列资源信息的收集和记录")
            else:
                print("无效的选择，请重新输入")
                
        except KeyboardInterrupt:
            print("\n程序被用户中断")
            break
        except Exception as e:
            logger.error(f"执行过程中发生错误: {e}")
            print(f"执行过程中发生错误: {e}")

if __name__ == "__main__":
    main()