import logging
from devops_mcp_servers.settings import LOGLEVEL

loglevel = getattr(logging, LOGLEVEL)
# 配置日志
logging.basicConfig(
    level=loglevel,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
