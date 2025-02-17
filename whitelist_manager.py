import time
import volcenginesdkcore
from volcenginesdkcore.rest import ApiException
import volcenginesdkrdspostgresql
from configs.whitelist_config import whitelist_config
from configs.api_config import api_config
import logging
import os

# 确保logs目录存在
log_dir = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(log_dir, exist_ok=True)

# 配置日志记录
# 添加文件处理器
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
file_handler = logging.FileHandler(os.path.join(log_dir, 'whitelist_manager.log'))
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)



class WhitelistManager:
    def __init__(self):
        self._init_client()
        self.pg_api = volcenginesdkrdspostgresql.RDSPOSTGRESQLApi()

    def _init_client(self):
        configuration = volcenginesdkcore.Configuration()
        configuration.ak = api_config['ak']
        configuration.sk = api_config['sk']
        configuration.region = api_config['region']
        configuration.client_side_validation = True
        volcenginesdkcore.Configuration.set_default(configuration)

    def create_whitelist(self, whitelist_config):
        """
        创建白名单
        :param whitelist_config: 白名单配置信息
        :return: (bool, str) 元组，包含创建结果和白名单ID（如果创建成功）
        """
        try:
            # 先检查是否已存在同名白名单
            list_request = volcenginesdkrdspostgresql.DescribeAllowListsRequest(
                region_id=api_config['region']
            )
            list_response = self.pg_api.describe_allow_lists(list_request)
            
            if hasattr(list_response, 'allow_lists'):
                for allow_list in list_response.allow_lists:
                    if allow_list.allow_list_name == whitelist_config['name']:
                        logger.info(f"白名单 {whitelist_config['name']} 已存在，白名单ID: {allow_list.allow_list_id}")
                        return True, allow_list.allow_list_id

            # 如果不存在，则创建新的白名单
            create_request = volcenginesdkrdspostgresql.CreateAllowListRequest(
                allow_list_desc=whitelist_config['description'],
                allow_list_name=whitelist_config['name'],
                allow_list=','.join(whitelist_config['ip_list'])
            )
            create_response = self.pg_api.create_allow_list(create_request)
            logger.info(f"白名单 {whitelist_config['name']} 创建成功")
            logger.info(f"白名单详细信息：")
            logger.info(f"  - ID: {create_response.allow_list_id}")
            logger.info(f"  - 名称: {whitelist_config['name']}")
            logger.info(f"  - 描述: {whitelist_config['description']}")
            logger.info(f"  - IP列表: {', '.join(whitelist_config['ip_list'])}")
            return True, create_response.allow_list_id
            
        except ApiException as e:
            logger.error(f"创建白名单时发生异常: {e}")
            return False, None

    def create_all_whitelists(self):
        """
        创建配置文件中定义的所有白名单
        :return: dict 包含所有创建的白名单ID
        """
        whitelist_ids = {}
        for whitelist_item in whitelist_config['whitelists']:
            success, whitelist_id = self.create_whitelist(whitelist_item)
            if success and whitelist_id:
                whitelist_ids[whitelist_item['name']] = whitelist_id
                # 获取并记录已存在白名单的详细信息
                if whitelist_id:
                    try:
                        detail_request = volcenginesdkrdspostgresql.DescribeAllowListDetailRequest(
                            allow_list_id=whitelist_id
                        )
                        detail_response = self.pg_api.describe_allow_list_detail(detail_request)
                        logger.info(f"已存在的白名单详细信息：")
                        logger.info(f"  - ID: {whitelist_id}")
                        logger.info(f"  - 名称: {whitelist_item['name']}")
                        logger.info(f"  - 描述: {whitelist_item['description']}")
                        logger.info(f"  - IP列表: {', '.join(whitelist_item['ip_list'])}")
                    except ApiException as e:
                        logger.warning(f"获取白名单 {whitelist_id} 详细信息时发生异常: {e}")
        return whitelist_ids

def main():
    try:
        # 创建白名单管理器实例
        whitelist_manager = WhitelistManager()
        
        # 创建所有白名单
        whitelist_ids = whitelist_manager.create_all_whitelists()
        
        # 输出创建结果
        if whitelist_ids:
            logger.info("成功创建以下白名单：")
            for name, whitelist_id in whitelist_ids.items():
                logger.info(f"- {name}: {whitelist_id}")
            logger.info("所有白名单创建完成！")
        else:
            logger.warning("没有成功创建任何白名单")
            
    except Exception as e:
        logger.error(f"执行过程中发生错误: {e}")
        return

if __name__ == "__main__":
    main()
