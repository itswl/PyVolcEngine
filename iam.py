"""火山引擎 IAM 用户和用户组管理模块

本模块用于管理火山引擎云平台的 IAM 用户和用户组：
- 为产品团队、开发团队和运维团队创建用户组
- 创建用户并将其分配到相应的用户组
- 设置安全的登录配置和密码策略
- 为不同用户组分配适当的访问权限策略
- 为每个用户创建访问密钥

作者: IAM Team
日期: 2024
"""

import os
import logging
from typing import Dict, List
import volcenginesdkcore
import volcenginesdkiam
from volcenginesdkcore.rest import ApiException
from configs.api_config import api_config
from configs.iam_config import USER_CONFIG, TEAM_GROUPS, DEFAULT_PASSWORD, SECRET_DIR
import time

# 配置日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class IAMManager:
    """IAM管理器类
    
    用于管理火山引擎IAM用户和用户组的核心类，包含所有IAM相关操作。
    """
    
    def __init__(self):
        self._init_client()
        self.api = volcenginesdkiam
        self.client_api = self.api.IAMApi()

    def _init_client(self):
        configuration = volcenginesdkcore.Configuration()
        configuration.ak = api_config['ak']
        configuration.sk = api_config['sk']
        configuration.region = api_config['region']
        configuration.client_side_validation = True
        volcenginesdkcore.Configuration.set_default(configuration)
    
    def create_user_groups(self) -> Dict:
        """创建用户组，如果用户组已存在则跳过创建
        
        Returns:
            Dict: 创建的用户组信息
        """
        user_groups = {}
        for team_name, group_config in TEAM_GROUPS.items():
            try:
                # 先检查用户组是否已存在
                try:
                    list_groups_request = self.api.ListGroupsRequest()
                    list_groups_response = self.client_api.list_groups(list_groups_request)
                    group_exists = any(group.user_group_name == group_config["user_group_name"] 
                                     for group in list_groups_response.user_groups)
                    
                    if group_exists:
                        logger.info(f"用户组已存在，跳过创建: {group_config['display_name']}")
                        continue
                except Exception as e:
                    logger.warning(f"检查用户组存在性失败: {group_config['display_name']}, 错误: {str(e)}")
                
                # 创建用户组
                create_group_request = self.api.CreateGroupRequest(
                    user_group_name=group_config["user_group_name"],
                    display_name=group_config["display_name"],
                    description=group_config["description"]
                )
                
                response = self.client_api.create_group(create_group_request)
                user_groups[team_name] = response.user_group
                logger.info(f"成功创建用户组: {group_config['display_name']}")
            except Exception as e:
                if "UserGroupAlreadyExists" in str(e):
                    logger.info(f"用户组已存在: {group_config['display_name']}")
                    continue
                logger.error(f"创建用户组失败: {group_config['display_name']}, 错误: {str(e)}")
                raise
        
        return user_groups
    
    def create_users(self) -> List:
        """仅创建用户账号，不设置认证信息
        
        Returns:
            List: 创建的用户信息列表
        """
        users = []
        for user_info in USER_CONFIG:
            try:
                # 先检查用户是否已存在
                try:
                    list_users_request = self.api.ListUsersRequest(limit=1000)
                    list_users_response = self.client_api.list_users(list_users_request)

                    user_exists = any(user.user_name == user_info["user_name"]
                                    for user in list_users_response.user_metadata)
                    
                    if user_exists:
                        logger.info(f"用户已存在，跳过创建: {user_info['display_name']}")
                        continue
                except Exception as e:
                    logger.warning(f"检查用户存在性失败: {user_info['display_name']}, 错误: {str(e)}")
                
                # 创建用户
                create_user_request = self.api.CreateUserRequest(
                    user_name=user_info["user_name"],
                    display_name=user_info["display_name"]
                )
                
                response = self.client_api.create_user(create_user_request)
                users.append(response.user)
                logger.info(f"成功创建用户: {user_info['display_name']}")
                    
            except Exception as e:
                if "UserAlreadyExists" in str(e):
                    logger.info(f"用户已存在: {user_info['display_name']}")
                    continue
                logger.error(f"创建用户失败: {user_info['display_name']}, 错误: {str(e)}")
                raise
        
        return users
    
    def _create_login_profile(self, user_info: Dict) -> None:
        """创建用户登录配置
        
        Args:
            user_info: 用户信息
        """
        try:
            if user_info["auth_type"] not in ["password", "both"]:
                logger.info(f"用户 {user_info['display_name']} 不需要配置登录信息，跳过密码设置")
                return

            # 先检查用户是否已有登录配置
            try:
                get_login_profile_request = self.api.GetLoginProfileRequest(
                    user_name=user_info["user_name"]
                )
                login_profile = self.client_api.get_login_profile(get_login_profile_request)

                if login_profile.login_profile.login_allowed:
                    logger.info(f"用户 {user_info['display_name']} 已有登录配置且允许登录，跳过密码设置")
                    return
            except ApiException as e:
                if "NoSuchEntity" not in str(e):
                    raise
                # 用户没有登录配置，继续创建
                logger.info(f"用户 {user_info['display_name']} 没有登录配置，将创建新的登录配置")
                
            password = user_info.get("password", DEFAULT_PASSWORD)
            create_login_profile_request = self.api.CreateLoginProfileRequest(
                user_name=user_info["user_name"],
                password=password,
                login_allowed=True,
                password_reset_required=False
            )
            
            self.client_api.create_login_profile(create_login_profile_request)
            logger.info(f"成功配置用户登录信息: {user_info['display_name']}")
        except Exception as e:
            logger.error(f"配置用户登录信息失败: {user_info['display_name']}, 错误: {str(e)}")
            raise
    
    def _create_access_key(self, user_info: Dict) -> None:
        """创建用户访问密钥
        
        Args:
            user_info: 用户信息
        """
        os.makedirs(SECRET_DIR, exist_ok=True)
        try:
            # 先检查用户是否已有访问密钥
            try:
                list_access_keys_request = self.api.ListAccessKeysRequest(
                    user_name=user_info["user_name"]
                )
                list_access_keys_response = self.client_api.list_access_keys(list_access_keys_request)
                
                if list_access_keys_response.access_key_metadata and len(list_access_keys_response.access_key_metadata) > 0:
                    logger.info(f"用户 {user_info['display_name']} 已有访问密钥，跳过创建")
                    return
            except Exception as e:
                logger.warning(f"检查用户访问密钥失败: {user_info['display_name']}, 错误: {str(e)}")
            
            create_access_key_request = self.api.CreateAccessKeyRequest()
            create_access_key_request.user_name = user_info["user_name"]
            
            response = self.client_api.create_access_key(create_access_key_request)
            
            # 保存访问密钥到文件
            secret_file = os.path.join(SECRET_DIR, f"{user_info['user_name']}.sk")
            with open(secret_file, "w") as f:
                f.write(f"AccessKeyId: {response.access_key.access_key_id}\n")
                f.write(f"SecretAccessKey: {response.access_key.secret_access_key}\n")
            
            logger.info(f"成功创建访问密钥: {user_info['display_name']}")
        except Exception as e:
            logger.error(f"创建访问密钥失败: {user_info['display_name']}, 错误: {str(e)}")
            raise
    
    def attach_users_to_groups(self) -> None:
        """将用户关联到用户组"""
        for user_info in USER_CONFIG:
            for team_name in user_info["teams"]:
                try:
                    add_user_to_group_request = self.api.AddUserToGroupRequest(
                        user_name=user_info["user_name"],
                        user_group_name=TEAM_GROUPS[team_name]["user_group_name"]
                    )
                    
                    self.client_api.add_user_to_group(add_user_to_group_request)
                    logger.info(f"成功将用户 {user_info['display_name']} 添加到用户组 {TEAM_GROUPS[team_name]['display_name']}")
                except Exception as e:
                    logger.error(f"添加用户到用户组失败: {user_info['display_name']} -> {TEAM_GROUPS[team_name]['display_name']}, 错误: {str(e)}")
                    raise

    def attach_policies_to_user(self) -> None:
        """为指定用户附加权限策略

        Args:
            user_name: 用户名
            policy_names: 策略名称列表
            policy_type: 策略类型，默认为System（系统策略）
            功能未实现，暂时不需要
        """
        try:
            # 获取用户当前的策略列表
            list_policies_request = self.api.ListAttachedUserPoliciesRequest(
                user_name=user_name
            )
            current_policies = self.client_api.list_attached_user_policies(list_policies_request)
            
            for policy_name in policy_names:
                # 检查策略是否已经附加
                policy_exists = any(policy.policy_name == policy_name for policy in current_policies.attached_policy_metadata)
                if policy_exists:
                    logger.info(f"策略已附加到用户，跳过附加: {user_name} -> {policy_name}")
                    continue
                    
                attach_policy_request = self.api.AttachUserPolicyRequest(
                    user_name=user_name,
                    policy_name=policy_name,
                    policy_type=policy_type
                )
                
                self.client_api.attach_user_policy(attach_policy_request)
                logger.info(f"成功为用户 {user_name} 附加策略: {policy_name}")
        except Exception as e:
            logger.error(f"附加策略失败: {user_name} -> {policy_name}, 错误: {str(e)}")
            raise
            
    def list_users(self, limit: int = 1000, offset: int = 0) -> List:
        """获取所有IAM用户列表
        
        Args:
            limit: 每页返回的最大数量，默认1000
            offset: 分页偏移量，默认0
            
        Returns:
            List: 用户列表
        """
        try:
            list_users_request = self.api.ListUsersRequest(
                limit=limit,
                offset=offset
            )
            list_users_response = self.client_api.list_users(list_users_request)
            
            logger.info(f"成功获取用户列表，共 {len(list_users_response.user_metadata)} 个用户")
            return list_users_response.user_metadata
        except Exception as e:
            logger.error(f"获取用户列表失败，错误: {str(e)}")
            raise
    
    def delete_user(self, user_name: str) -> bool:
        """删除指定IAM用户
        
        删除用户前会检查用户是否存在，如果用户不存在则返回False
        
        Args:
            user_name: 要删除的用户名
            
        Returns:
            bool: 删除成功返回True，用户不存在返回False
        """
        try:
            # 先检查用户是否存在
            try:
                list_users_request = self.api.ListUsersRequest(limit=1000)
                list_users_response = self.client_api.list_users(list_users_request)
                
                user_exists = any(user.user_name == user_name 
                                for user in list_users_response.user_metadata)
                
                if not user_exists:
                    logger.warning(f"用户不存在，无法删除: {user_name}")
                    return False
            except Exception as e:
                logger.warning(f"检查用户存在性失败: {user_name}, 错误: {str(e)}")
            
            # 删除用户
            delete_user_request = self.api.DeleteUserRequest(
                user_name=user_name
            )
            
            self.client_api.delete_user(delete_user_request)
            logger.info(f"成功删除用户: {user_name}")
            return True
        except Exception as e:
            if "NoSuchEntity" in str(e):
                logger.warning(f"用户不存在，无法删除: {user_name}")
                return False
            logger.error(f"删除用户失败: {user_name}, 错误: {str(e)}")
            raise

    def attach_policies_to_groups(self) -> None:
        """为用户组附加权限策略"""
        for team_name, group_config in TEAM_GROUPS.items():
            try:
                # 获取用户组当前的策略列表
                list_policies_request = self.api.ListAttachedUserGroupPoliciesRequest(
                    user_group_name=group_config["user_group_name"]
                )
                current_policies = self.client_api.list_attached_user_group_policies(list_policies_request)
                
                for policy_name in group_config["policies"]:
                    # 检查策略是否已经附加
                    policy_exists = any(policy.policy_name == policy_name for policy in current_policies.attached_policy_metadata)
                    if policy_exists:
                        logger.info(f"策略已附加到用户组，跳过附加: {group_config['display_name']} -> {policy_name}")
                        continue
                        
                    attach_policy_request = self.api.AttachUserGroupPolicyRequest(
                        user_group_name=group_config["user_group_name"],
                        policy_name=policy_name,
                        policy_type="System"
                    )
                    
                    self.client_api.attach_user_group_policy(attach_policy_request)
                    logger.info(f"成功为用户组 {group_config['display_name']} 附加策略: {policy_name}")
            except Exception as e:
                logger.error(f"附加策略失败: {group_config['display_name']} -> {policy_name}, 错误: {str(e)}")
                raise

    def set_user_login_profile(self) -> None:
        """为需要密码登录的用户设置登录配置"""
        for user_info in USER_CONFIG:
            if user_info["auth_type"] in ["password", "both"]:
                self._create_login_profile(user_info)
            
    def set_user_access_key(self) -> None:
        """为需要访问密钥的用户创建访问密钥"""
        for user_info in USER_CONFIG:
            if user_info["auth_type"] in ["access_key", "both"]:
                self._create_access_key(user_info)

def main():
    """主函数
    
    支持三种调用方式：
    1. 完整流程：创建用户组、用户，设置权限等
    2. 列出用户：显示所有IAM用户信息
    3. 删除用户：删除指定的用户
    """
    import argparse
    
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description='火山引擎IAM用户管理工具')
    parser.add_argument('mode', choices=['full', 'list', 'delete'],
                        help='运行模式：full-完整流程，list-列出用户，delete-删除用户')
    parser.add_argument('--users', nargs='+', help='要删除的用户名列表（仅在delete模式下需要）')
    
    args = parser.parse_args()
    
    try:
        # 创建IAM管理器实例
        iam_manager = IAMManager()
        
        if args.mode == 'full':
            # 完整流程模式
            # 创建用户组
            iam_manager.create_user_groups()
            logger.info("用户组创建完成")
            
            # 创建用户
            iam_manager.create_users()
            logger.info("用户创建完成")
            
            # 设置用户登录配置
            iam_manager.set_user_login_profile()
            logger.info("用户登录配置完成")
            
            # 设置用户访问密钥
            iam_manager.set_user_access_key()
            logger.info("用户访问密钥配置完成")
            
            # 关联用户到用户组
            iam_manager.attach_users_to_groups()
            logger.info("用户组关联完成")
            
            # 配置权限策略
            iam_manager.attach_policies_to_groups()
            logger.info("用户组权限策略配置完成")
            
            # 列出所有用户
            users = iam_manager.list_users()
            logger.info("当前IAM用户列表:")
            for user in users:
                logger.info(f"- 用户名: {user.user_name}, 显示名称: {user.display_name}")
                
        elif args.mode == 'list':
            # 列出用户模式
            users = iam_manager.list_users()
            if users:
                logger.info("当前IAM用户列表:")
                for user in users:
                    logger.info(f"- 用户名: {user.user_name}, 显示名称: {user.display_name}")
            else:
                logger.info("当前没有IAM用户")
                
        elif args.mode == 'delete':
            # 删除用户模式
            if not args.users:
                logger.error("删除模式下必须指定要删除的用户名列表 (--users)")
                return
            
            # 显示要删除的用户列表并请求确认
            logger.info("将要删除以下用户:")
            for user_name in args.users:
                logger.info(f"- {user_name}")
            
            confirm = input("\n确认要删除这些用户吗？(y/n): ")
            if confirm.lower() != 'y':
                logger.info("操作已取消")
                return
            
            # 执行批量删除
            success_count = 0
            fail_count = 0
            for user_name in args.users:
                if iam_manager.delete_user(user_name):
                    success_count += 1
                    logger.info(f"成功删除用户: {user_name}")
                else:
                    fail_count += 1
                    logger.warning(f"删除用户失败或用户不存在: {user_name}")
            
            # 显示删除结果统计
            logger.info(f"\n删除操作完成：成功 {success_count} 个，失败 {fail_count} 个")

    except Exception as e:
        logger.error(f"程序执行失败: {str(e)}")
        raise

if __name__ == "__main__":
    main()


