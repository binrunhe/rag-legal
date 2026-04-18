#!/usr/bin/env python
"""
测试邮件发送功能的脚本
"""
import asyncio
import sys
from pathlib import Path

# 确保导入本地模块
sys.path.insert(0, str(Path(__file__).parent))

from utils import EmailService, generate_6_digit_code, _smtp_settings


async def test_email_sending():
    """测试邮件发送功能"""
    print("=" * 60)
    print("邮件发送功能测试")
    print("=" * 60)
    
    # 显示SMTP配置
    settings = _smtp_settings()
    print("\n📧 SMTP配置信息：")
    print(f"  Host: {settings['smtp_host']}")
    print(f"  Port: {settings['smtp_port']}")
    print(f"  User: {settings['smtp_user']}")
    print(f"  From: {settings['smtp_from']}")
    print(f"  Use SSL: {settings['use_ssl']}")
    print(f"  Use TLS: {settings['use_tls']}")
    
    # 检查必要的配置
    if not settings['smtp_user'] or not settings['smtp_password']:
        print("\n❌ 错误: SMTP_USER 或 SMTP_PASSWORD 未配置")
        return False
    
    # 生成验证码
    code = generate_6_digit_code()
    print(f"\n🔐 生成的验证码: {code}")
    
    # 测试邮件发送
    test_email = input("\n请输入接收测试邮件的邮箱地址 (按Enter跳过测试发送): ").strip()
    
    if not test_email:
        print("已跳过邮件发送测试")
        return True
    
    if "@" not in test_email:
        print("❌ 邮箱地址格式不正确")
        return False
    
    print(f"\n📤 正在发送测试邮件到: {test_email}")
    print("   请稍候...")
    
    try:
        await EmailService.send_verification_email(test_email, code)
        print("✅ 邮件发送成功！")
        print(f"   验证码: {code}")
        print("   请检查您的邮箱")
        return True
    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")
        print(f"   错误类型: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主函数"""
    try:
        success = await test_email_sending()
        print("\n" + "=" * 60)
        if success:
            print("✅ 测试完成，邮件发送功能可用！")
            print("=" * 60)
            sys.exit(0)
        else:
            print("❌ 测试失败，请检查配置")
            print("=" * 60)
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n已取消测试")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试过程出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
