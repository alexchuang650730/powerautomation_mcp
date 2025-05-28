"""
测试Release管理器模块

该脚本用于测试ReleaseManager模块的功能，包括：
1. 检查新的release
2. 下载release到本地
3. 上传更改到GitHub
4. 创建新的release

作者: Manus AI
日期: 2025-05-28
"""

import os
import sys
import time
import json

# 添加父目录到系统路径，以便导入mcp_tool包
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp_tool.thought_action_recorder import ThoughtActionRecorder
from mcp_tool.release_manager import ReleaseManager

def test_release_manager():
    """测试ReleaseManager的基本功能"""
    print("开始测试ReleaseManager...")
    
    # 创建测试目录
    test_repo_dir = os.path.join(os.getcwd(), "test_repo")
    os.makedirs(test_repo_dir, exist_ok=True)
    
    # 初始化记录器
    recorder = ThoughtActionRecorder(log_dir=os.path.join(test_repo_dir, "logs"))
    
    # 初始化Release管理器
    # 注意：这里使用的是测试仓库，实际使用时需要替换为真实的仓库
    release_manager = ReleaseManager(
        local_repo_path=test_repo_dir,
        github_repo="alexchuang650730/powerautomation",
        ssh_key_path="~/.ssh/id_rsa",
        recorder=recorder
    )
    
    print(f"Release管理器初始化完成，本地仓库路径: {test_repo_dir}")
    
    # 测试验证SSH密钥
    print("\n测试验证SSH密钥...")
    ssh_result = release_manager.verify_ssh_key()
    
    if ssh_result["success"]:
        print("SSH密钥验证成功")
    else:
        print(f"SSH密钥验证失败: {ssh_result.get('error')}")
        print("继续测试其他功能...")
    
    # 测试检查新的release
    print("\n测试检查新的release...")
    new_releases = release_manager.check_for_new_releases()
    
    print(f"发现 {len(new_releases)} 个新release:")
    for release in new_releases:
        print(f"- {release}")
    
    # 如果有新的release，测试下载
    if new_releases:
        print(f"\n测试下载最新的release: {new_releases[0]}...")
        download_result = release_manager.download_release(new_releases[0])
        
        if download_result["success"]:
            print(f"成功下载release {new_releases[0]} 到 {test_repo_dir}")
        else:
            print(f"下载release失败: {download_result.get('error')}")
    else:
        print("\n没有新的release可供下载，跳过下载测试")
    
    # 测试上传更改到GitHub（创建测试文件）
    print("\n测试上传更改到GitHub...")
    
    # 创建测试文件
    test_file = os.path.join(test_repo_dir, "test_file.txt")
    with open(test_file, "w") as f:
        f.write(f"测试文件，创建于 {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 上传更改
    upload_result = release_manager.upload_to_github("测试提交 - 由ReleaseManager测试脚本创建")
    
    if upload_result["success"]:
        print("成功上传更改到GitHub")
    else:
        print(f"上传更改失败: {upload_result.get('error')}")
    
    # 测试创建新的release（仅在测试环境中执行）
    # 注意：在实际环境中，应谨慎创建新的release
    if os.environ.get("TEST_CREATE_RELEASE") == "1":
        print("\n测试创建新的release...")
        
        tag_name = f"test-{int(time.time())}"
        release_name = f"测试Release {time.strftime('%Y-%m-%d %H:%M:%S')}"
        release_notes = f"这是一个由ReleaseManager测试脚本创建的测试release。\n\n创建时间: {time.strftime('%Y-%m-%d %H:%M:%S')}"
        
        create_result = release_manager.create_new_release(tag_name, release_name, release_notes)
        
        if create_result["success"]:
            print(f"成功创建新的release: {tag_name}")
        else:
            print(f"创建release失败: {create_result.get('error')}")
    else:
        print("\n跳过创建新release的测试（设置环境变量TEST_CREATE_RELEASE=1以启用）")
    
    print("\n测试完成!")
    return release_manager

if __name__ == "__main__":
    release_manager = test_release_manager()
