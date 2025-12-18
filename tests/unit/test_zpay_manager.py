"""
zpay_manager.py 单元测试
测试支付订单创建、回调处理、签名验证等核心功能

⚠️ 重要提示：
1. 支付测试必须使用Mock，禁止调用真实支付接口
2. 所有敏感信息（商户号、密钥）使用Mock值
3. 重点测试签名验证和金额校验，防止支付篡改
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timedelta
from api.zpay_manager import ZPayManager


@pytest.fixture
def mock_zpay_credentials():
    """Mock ZPAY凭证"""
    return {
        "ZPAY_PID": "test-merchant-123",
        "ZPAY_PKEY": "test-secret-key-abc123"
    }


@pytest.fixture
def zpay_manager(mock_zpay_credentials):
    """创建ZPayManager实例（使用Mock凭证）"""
    with patch.dict('os.environ', mock_zpay_credentials):
        # Patch模块级全局变量
        with patch('api.zpay_manager.ZPAY_PID', mock_zpay_credentials['ZPAY_PID']):
            with patch('api.zpay_manager.ZPAY_PKEY', mock_zpay_credentials['ZPAY_PKEY']):
                manager = ZPayManager()
                return manager


class TestZPayManagerInit:
    """测试ZPayManager初始化"""

    def test_init_with_credentials(self, mock_zpay_credentials):
        """测试使用正确凭证初始化"""
        with patch.dict('os.environ', mock_zpay_credentials):
            with patch('api.zpay_manager.ZPAY_PID', mock_zpay_credentials['ZPAY_PID']):
                with patch('api.zpay_manager.ZPAY_PKEY', mock_zpay_credentials['ZPAY_PKEY']):
                    manager = ZPayManager()
                    assert manager.pid == "test-merchant-123"
                    assert manager.pkey == "test-secret-key-abc123"

    def test_init_without_credentials(self):
        """测试缺少凭证时抛出异常"""
        with patch('api.zpay_manager.ZPAY_PID', None):
            with patch('api.zpay_manager.ZPAY_PKEY', None):
                with pytest.raises(ValueError, match="ZPAY credentials.*required"):
                    ZPayManager()


class TestCreatePaymentOrder:
    """测试支付订单创建"""

    def test_create_order_monthly_subscription(self, zpay_manager):
        """测试创建月度订阅支付订单"""
        # Arrange
        order_no = "ORDER_202501170001"
        money = 29.0
        pay_type = "alipay"

        # Act
        result = zpay_manager.create_order(
            out_trade_no=order_no,
            name="GaiYa月度会员",
            money=money,
            pay_type=pay_type,
            notify_url="https://api.gaiyatime.com/payment-notify",
            return_url="https://gaiyatime.com/payment-success"
        )

        # Assert
        assert result["success"] is True
        assert result["out_trade_no"] == order_no
        assert "payment_url" in result
        assert result["params"]["money"] == "29.00"  # 金额格式化为2位小数
        assert result["params"]["type"] == pay_type
        assert "sign" in result["params"]  # 必须包含签名

    def test_create_order_yearly_subscription(self, zpay_manager):
        """测试创建年度订阅支付订单"""
        result = zpay_manager.create_order(
            out_trade_no="ORDER_YEARLY_001",
            name="GaiYa年度会员",
            money=199.0,
            pay_type="wxpay",
            notify_url="https://api.gaiyatime.com/payment-notify",
            return_url="https://gaiyatime.com/payment-success"
        )

        assert result["success"] is True
        assert result["params"]["money"] == "199.00"
        assert result["params"]["type"] == "wxpay"

    def test_create_order_with_optional_param(self, zpay_manager):
        """测试创建订单时携带可选参数"""
        result = zpay_manager.create_order(
            out_trade_no="ORDER_WITH_PARAM",
            name="测试商品",
            money=29.0,
            pay_type="alipay",
            notify_url="https://api.gaiyatime.com/payment-notify",
            return_url="https://gaiyatime.com/payment-success",
            param="user_123"
        )

        assert result["success"] is True
        assert result["params"]["param"] == "user_123"


class TestCreateAPIOrder:
    """测试API方式创建订单"""

    @patch('api.zpay_manager.requests.post')
    def test_create_api_order_success(self, mock_post, zpay_manager):
        """测试API方式创建订单成功"""
        # Arrange: Mock成功响应
        json_data = {
            "code": 1,
            "msg": "success",
            "trade_no": "ZPAY123456789",
            "O_id": "12345",
            "payurl": "https://pay.example.com/qrcode",
            "qrcode": "https://pay.example.com/qr.png",
            "img": "data:image/png;base64,..."
        }
        mock_response = Mock()
        mock_response.json.return_value = json_data
        mock_response.text = str(json_data)  # 添加 text 属性
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        # Act
        result = zpay_manager.create_api_order(
            out_trade_no="ORDER_API_001",
            name="测试商品",
            money=29.0,
            pay_type="alipay",
            notify_url="https://api.gaiyatime.com/payment-notify",
            clientip="127.0.0.1"
        )

        # Assert
        assert result["success"] is True
        assert result["trade_no"] == "ZPAY123456789"
        assert "payurl" in result
        assert "qrcode" in result

    @patch('api.zpay_manager.requests.post')
    def test_create_api_order_failure(self, mock_post, zpay_manager):
        """测试API方式创建订单失败"""
        # Arrange: Mock失败响应
        json_data = {
            "code": -1,
            "msg": "商户不存在"
        }
        mock_response = Mock()
        mock_response.json.return_value = json_data
        mock_response.text = str(json_data)  # 添加 text 属性
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        # Act
        result = zpay_manager.create_api_order(
            out_trade_no="ORDER_API_002",
            name="测试商品",
            money=29.0,
            pay_type="alipay",
            notify_url="https://api.gaiyatime.com/payment-notify",
            clientip="127.0.0.1"
        )

        # Assert
        assert result["success"] is False
        assert "商户不存在" in result["error"]


class TestQueryOrder:
    """测试订单查询"""

    @patch('api.zpay_manager.requests.get')
    def test_query_order_by_out_trade_no(self, mock_get, zpay_manager):
        """测试通过商户订单号查询"""
        # Arrange: Mock查询成功响应
        json_data = {
            "code": 1,
            "msg": "success",
            "trade_no": "ZPAY123456789",
            "out_trade_no": "ORDER_202501170001",
            "money": "29.00",
            "status": "1"  # 1=已支付
        }
        mock_response = Mock()
        mock_response.json.return_value = json_data
        mock_response.text = str(json_data)  # 添加 text 属性
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        # Act
        result = zpay_manager.query_order(out_trade_no="ORDER_202501170001")

        # Assert
        assert result["success"] is True
        assert result["order"]["out_trade_no"] == "ORDER_202501170001"
        assert result["order"]["status"] == "1"

    @patch('api.zpay_manager.requests.get')
    def test_query_order_by_trade_no(self, mock_get, zpay_manager):
        """测试通过ZPAY订单号查询"""
        # Arrange
        json_data = {
            "code": 1,
            "msg": "success",
            "trade_no": "ZPAY123456789",
            "status": "1"
        }
        mock_response = Mock()
        mock_response.json.return_value = json_data
        mock_response.text = str(json_data)  # 添加 text 属性
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        # Act
        result = zpay_manager.query_order(trade_no="ZPAY123456789")

        # Assert
        assert result["success"] is True

    def test_query_order_without_params(self, zpay_manager):
        """测试查询时未提供订单号"""
        result = zpay_manager.query_order()

        assert result["success"] is False
        assert "required" in result["error"]

    @patch('api.zpay_manager.requests.get')
    def test_query_order_not_found(self, mock_get, zpay_manager):
        """测试查询订单不存在"""
        # Arrange: Mock订单不存在响应
        json_data = {
            "code": -1,
            "msg": "订单不存在"
        }
        mock_response = Mock()
        mock_response.json.return_value = json_data
        mock_response.text = str(json_data)  # 添加 text 属性
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        # Act
        result = zpay_manager.query_order(out_trade_no="NONEXISTENT_ORDER")

        # Assert
        assert result["success"] is False
        assert "不存在" in result["error"]


class TestPaymentNotifyVerification:
    """测试支付回调验证"""

    def test_verify_notify_success(self, zpay_manager):
        """测试成功验证支付回调签名"""
        # Arrange: 构造合法的回调数据
        callback_data = {
            "pid": "test-merchant-123",
            "out_trade_no": "ORDER_202501170001",
            "trade_no": "ZPAY123456789",
            "type": "alipay",
            "money": "29.00",
            "trade_status": "TRADE_SUCCESS"
        }

        # 生成正确的签名
        correct_sign = zpay_manager._generate_sign(callback_data)
        callback_data["sign"] = correct_sign

        # Act
        is_valid = zpay_manager.verify_notify(callback_data)

        # Assert
        assert is_valid is True

    def test_verify_notify_signature_fail(self, zpay_manager):
        """测试签名验证失败（篡改金额）"""
        # Arrange: 构造篡改的回调数据
        callback_data = {
            "pid": "test-merchant-123",
            "out_trade_no": "ORDER_202501170001",
            "trade_no": "ZPAY123456789",
            "type": "alipay",
            "money": "29.00",
            "trade_status": "TRADE_SUCCESS"
        }

        # 生成正确签名
        correct_sign = zpay_manager._generate_sign(callback_data)

        # 篡改金额后使用旧签名
        callback_data["money"] = "1.00"
        callback_data["sign"] = correct_sign

        # Act
        is_valid = zpay_manager.verify_notify(callback_data)

        # Assert: 签名验证应失败
        assert is_valid is False

    def test_verify_notify_missing_signature(self, zpay_manager):
        """测试缺少签名的回调"""
        # Arrange: 回调数据缺少sign字段
        callback_data = {
            "pid": "test-merchant-123",
            "out_trade_no": "ORDER_202501170001",
            "trade_no": "ZPAY123456789",
            "money": "29.00",
            "trade_status": "TRADE_SUCCESS"
        }

        # Act
        is_valid = zpay_manager.verify_notify(callback_data)

        # Assert
        assert is_valid is False

    def test_verify_notify_missing_required_fields(self, zpay_manager):
        """测试缺少必要字段的回调"""
        # Arrange: 缺少money字段
        callback_data = {
            "pid": "test-merchant-123",
            "out_trade_no": "ORDER_202501170001",
            "trade_no": "ZPAY123456789",
            "trade_status": "TRADE_SUCCESS",
            "sign": "fake_signature"
        }

        # Act
        is_valid = zpay_manager.verify_notify(callback_data)

        # Assert: 缺少必要字段应验证失败
        assert is_valid is False


class TestRefundProcessing:
    """测试退款处理"""

    @patch('api.zpay_manager.requests.post')
    def test_request_refund_success(self, mock_post, zpay_manager):
        """测试成功发起退款"""
        # Arrange: Mock成功响应
        mock_response = Mock()
        mock_response.json.return_value = {
            "code": 1,
            "msg": "退款成功"
        }
        mock_post.return_value = mock_response

        # Act
        result = zpay_manager.request_refund(
            out_trade_no="ORDER_TO_REFUND",
            money=29.0
        )

        # Assert
        assert result["success"] is True
        assert "message" in result

    @patch('api.zpay_manager.requests.post')
    def test_request_refund_failure(self, mock_post, zpay_manager):
        """测试退款失败"""
        # Arrange: Mock失败响应
        mock_response = Mock()
        mock_response.json.return_value = {
            "code": -1,
            "msg": "订单不存在或已退款"
        }
        mock_post.return_value = mock_response

        # Act
        result = zpay_manager.request_refund(
            out_trade_no="NONEXISTENT_ORDER",
            money=29.0
        )

        # Assert
        assert result["success"] is False
        assert "不存在" in result["error"] or "已退款" in result["error"]

    @patch('api.zpay_manager.requests.post')
    def test_request_refund_with_trade_no(self, mock_post, zpay_manager):
        """测试使用ZPAY订单号退款"""
        # Arrange
        mock_response = Mock()
        mock_response.json.return_value = {
            "code": 1,
            "msg": "退款成功"
        }
        mock_post.return_value = mock_response

        # Act
        result = zpay_manager.request_refund(
            out_trade_no="ORDER_123",
            money=29.0,
            trade_no="ZPAY987654321"
        )

        # Assert
        assert result["success"] is True


class TestPaymentSecurity:
    """测试支付安全性"""

    def test_signature_generation_consistency(self, zpay_manager):
        """测试签名生成的一致性"""
        # Arrange: 相同的参数
        params = {
            "pid": "test-merchant-123",
            "type": "alipay",
            "out_trade_no": "ORDER001",
            "money": "29.00",
            "name": "测试商品"
        }

        # Act: 多次生成签名
        sign1 = zpay_manager._generate_sign(params)
        sign2 = zpay_manager._generate_sign(params)

        # Assert: 签名应一致
        assert sign1 == sign2
        assert len(sign1) == 32  # MD5签名长度

    def test_signature_tampering_detection(self, zpay_manager):
        """测试签名篡改检测"""
        # Arrange: 原始参数和签名
        params = {
            "pid": "test-merchant-123",
            "out_trade_no": "ORDER001",
            "money": "29.00"
        }
        valid_sign = zpay_manager._generate_sign(params)

        # Act: 篡改金额
        tampered_params = params.copy()
        tampered_params["money"] = "1.00"
        tampered_sign = zpay_manager._generate_sign(tampered_params)

        # Assert: 签名应不同
        assert valid_sign != tampered_sign

    def test_signature_ignores_empty_values(self, zpay_manager):
        """测试签名生成忽略空值"""
        # Arrange: 包含空值的参数
        params_with_empty = {
            "pid": "test-merchant-123",
            "out_trade_no": "ORDER001",
            "money": "29.00",
            "param": ""  # 空值
        }

        params_without_empty = {
            "pid": "test-merchant-123",
            "out_trade_no": "ORDER001",
            "money": "29.00"
        }

        # Act
        sign1 = zpay_manager._generate_sign(params_with_empty)
        sign2 = zpay_manager._generate_sign(params_without_empty)

        # Assert: 签名应相同（空值被忽略）
        assert sign1 == sign2


class TestGetPlanInfo:
    """测试获取订阅计划信息"""

    def test_get_monthly_plan_info(self, zpay_manager):
        """测试获取月度订阅计划"""
        plan = zpay_manager.get_plan_info("pro_monthly")

        # 名称来自 SubscriptionManager.PLANS
        assert plan["name"] == "Pro月度订阅"
        assert plan["price"] == 29.0

    def test_get_yearly_plan_info(self, zpay_manager):
        """测试获取年度订阅计划"""
        plan = zpay_manager.get_plan_info("pro_yearly")

        # 名称来自 SubscriptionManager.PLANS
        assert plan["name"] == "Pro年度订阅"
        assert plan["price"] == 199.0

    def test_get_lifetime_plan_info(self, zpay_manager):
        """测试获取终身订阅计划"""
        plan = zpay_manager.get_plan_info("lifetime")

        # 名称来自 SubscriptionManager.PLANS
        assert plan["name"] == "终身会员"
        assert plan["price"] == 599.0

    def test_get_unknown_plan_info(self, zpay_manager):
        """测试获取不存在的计划"""
        plan = zpay_manager.get_plan_info("unknown_plan")

        assert plan["name"] == "未知套餐"
        assert plan["price"] == 0.0


# Pytest配置
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
