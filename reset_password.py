#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
管理员密码重置脚本
当管理员忘记密码时，可以运行此脚本重置密码

使用方法：
python reset_password.py
"""

import sys
import os
import getpass

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.auth import DEFAULT_ADMIN, hash_password


def reset_admin_password():
    """重置管理员密码"""
    print("=" * 50)
    print("管理员密码重置工具")
    print("=" * 50)
    print()
    
    # 显示当前管理员信息
    print(f"当前管理员用户名: {DEFAULT_ADMIN['username']}")
    print(f"当前管理员邮箱: {DEFAULT_ADMIN['email']}")
    print()
    
    # 确认重置操作
    confirm = input("确认要重置管理员密码吗？(输入 'yes' 确认): ").strip().lower()
    if confirm != 'yes':
        print("操作已取消")
        return
    
    print()
    
    # 输入新密码
    while True:
        try:
            new_password = getpass.getpass("请输入新密码（至少6位）: ")
            if len(new_password) < 6:
                print("❌ 密码长度至少6位，请重新输入")
                continue
                
            confirm_password = getpass.getpass("请确认新密码: ")
            if new_password != confirm_password:
                print("❌ 两次输入的密码不一致，请重新输入")
                continue
                
            break
            
        except KeyboardInterrupt:
            print("\n操作已取消")
            return
        except Exception as e:
            print(f"❌ 输入错误: {e}")
            continue
    
    try:
        # 更新密码
        DEFAULT_ADMIN['password_hash'] = hash_password(new_password)
        
        print()
        print("✅ 密码重置成功！")
        print(f"新的登录信息：")
        print(f"  用户名: {DEFAULT_ADMIN['username']}")
        print(f"  密码: {new_password}")
        print()
        print("⚠️  请妥善保管新密码，建议登录后立即通过后台修改密码功能再次更改")
        print("⚠️  重启应用后新密码生效")
        
    except Exception as e:
        print(f"❌ 密码重置失败: {str(e)}")
        return


def show_usage():
    """显示使用说明"""
    print("=" * 60)
    print("管理员密码找回解决方案")
    print("=" * 60)
    print()
    print("1. 使用重置脚本（推荐）:")
    print("   python reset_password.py")
    print()
    print("2. 环境变量临时密码:")
    print("   export ADMIN_TEMP_PASSWORD=新密码")
    print("   python run.py")
    print("   (登录后立即修改密码)")
    print()
    print("3. 重新初始化（会丢失所有数据）:")
    print("   python init_db.py --reset")
    print("   (恢复默认密码: admin123)")
    print()
    print("=" * 60)


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--help':
        show_usage()
    else:
        reset_admin_password() 