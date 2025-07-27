#\!/usr/bin/env python3
"""
调试API状态
"""

from ticktick_mcp.config import ConfigManager
import requests

def debug_api():
    config_manager = ConfigManager()
    config = config_manager.load_config()
    headers = {
        'Authorization': f'Bearer {config.access_token}',
        'Content-Type': 'application/json',
        'Accept-Encoding': None,
        'User-Agent': 'TickTick-MCP-Client/1.0',
    }

    print('🔍 检查API状态:')

    # 测试基本项目访问
    response = requests.get(f'{config.base_url}/project', headers=headers, timeout=10)
    print(f'项目列表状态码: {response.status_code}')
    if response.status_code != 200:
        print(f'错误: {response.text[:200]}')
    else:
        projects = response.json()
        print(f'找到 {len(projects)} 个项目')
        for project in projects:
            print(f'  - {project.get("name", "Unknown")} (ID: {project.get("id", "Unknown")})')

if __name__ == "__main__":
    debug_api()