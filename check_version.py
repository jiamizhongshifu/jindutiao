# -*- coding: utf-8 -*-
"""
检查当前运行的客户端版本
"""
import sys
import os

# 检查是否有_show_qrcode_dialog方法
print("=" * 60)
print("客户端版本检查")
print("=" * 60)
print()

try:
    # 尝试导入membership_ui
    from gaiya.ui.membership_ui import MembershipDialog

    # 检查是否有二维码对话框方法
    has_qrcode_dialog = hasattr(MembershipDialog, '_show_qrcode_dialog')
    has_download_qrcode = hasattr(MembershipDialog, '_download_qrcode')
    has_cancel_payment = hasattr(MembershipDialog, '_cancel_payment')

    print(f"✓ 成功导入 MembershipDialog")
    print()
    print(f"_show_qrcode_dialog 方法: {'✅ 存在' if has_qrcode_dialog else '❌ 不存在'}")
    print(f"_download_qrcode 方法: {'✅ 存在' if has_download_qrcode else '❌ 不存在'}")
    print(f"_cancel_payment 方法: {'✅ 存在' if has_cancel_payment else '❌ 不存在'}")
    print()

    if has_qrcode_dialog and has_download_qrcode and has_cancel_payment:
        print("✅ 当前运行的是新版本 (支持二维码支付)")
    else:
        print("❌ 当前运行的是旧版本 (不支持二维码支付)")
        print()
        print("解决方案:")
        print("1. 关闭所有GaiYa进程: taskkill /F /IM GaiYa-v1.6.exe")
        print("2. 运行新版本: dist\\GaiYa-v1.6.exe")

    # 检查导入的模块路径
    import gaiya.ui.membership_ui
    module_file = gaiya.ui.membership_ui.__file__
    print()
    print(f"模块路径: {module_file}")

    # 如果是pyc文件,说明是打包版本
    if module_file.endswith('.pyc'):
        print("✓ 使用的是打包版本")
    else:
        print("✓ 使用的是源代码版本")

except Exception as e:
    print(f"❌ 导入失败: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 60)
