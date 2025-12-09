"""
App Recommender 单元测试
测试智能应用分类推荐引擎
"""
import pytest
from unittest.mock import Mock
from gaiya.core.app_recommender import AppRecommender


@pytest.fixture
def mock_logger():
    """创建Mock Logger"""
    return Mock()


@pytest.fixture
def app_recommender(mock_logger):
    """创建AppRecommender实例"""
    return AppRecommender(logger=mock_logger)


class TestAppRecommenderInit:
    """测试AppRecommender初始化"""

    def test_initialization(self, app_recommender):
        """测试初始化加载规则"""
        assert len(app_recommender.KNOWN_APPS) == 26
        assert len(app_recommender.KEYWORD_RULES) == 6

    def test_known_apps_structure(self, app_recommender):
        """测试已知应用结构"""
        # 检查VSCode
        assert "code.exe" in app_recommender.KNOWN_APPS
        vscode = app_recommender.KNOWN_APPS["code.exe"]
        assert vscode["category"] == "PRODUCTIVE"
        assert vscode["confidence"] == 0.95
        assert vscode["emoji"] == "💻"
        assert "VS Code" in vscode["description"]

    def test_keyword_rules_structure(self, app_recommender):
        """测试关键词规则结构"""
        # 检查第一条规则
        rule = app_recommender.KEYWORD_RULES[0]
        assert "keywords" in rule
        assert "category" in rule
        assert "confidence" in rule
        assert "emoji" in rule


class TestExactMatching:
    """测试精确匹配"""

    def test_exact_match_productive_app(self, app_recommender):
        """测试精确匹配-生产力应用"""
        result = app_recommender.recommend_category("code.exe")

        assert result["category"] == "PRODUCTIVE"
        assert result["confidence"] == 0.95
        assert result["emoji"] == "💻"
        assert "VS Code" in result["description"]
        assert "已知应用" in result["reason"]

    def test_exact_match_leisure_app(self, app_recommender):
        """测试精确匹配-娱乐应用"""
        result = app_recommender.recommend_category("wechat.exe")

        assert result["category"] == "LEISURE"
        assert result["confidence"] == 0.90
        assert result["emoji"] == "💬"
        assert "微信" in result["description"]

    def test_exact_match_neutral_app(self, app_recommender):
        """测试精确匹配-中性应用"""
        result = app_recommender.recommend_category("chrome.exe")

        assert result["category"] == "NEUTRAL"
        assert result["confidence"] == 0.85
        assert result["emoji"] == "🌐"

    def test_exact_match_case_insensitive(self, app_recommender):
        """测试精确匹配大小写不敏感"""
        result1 = app_recommender.recommend_category("Code.exe")
        result2 = app_recommender.recommend_category("CODE.EXE")
        result3 = app_recommender.recommend_category("code.exe")

        assert result1["category"] == result2["category"] == result3["category"]
        assert result1["confidence"] == result2["confidence"] == result3["confidence"]


class TestKeywordMatching:
    """测试关键词匹配"""

    def test_keyword_match_development(self, app_recommender):
        """测试关键词匹配-开发工具"""
        result = app_recommender.recommend_category("vscode-insider.exe")

        assert result["category"] == "PRODUCTIVE"
        assert result["confidence"] == 0.75
        assert "开发工具" in result["description"]
        assert "关键词匹配" in result["reason"]

    def test_keyword_match_game(self, app_recommender):
        """测试关键词匹配-游戏"""
        result = app_recommender.recommend_category("my-game-launcher.exe")

        assert result["category"] == "LEISURE"
        assert result["confidence"] == 0.80
        assert "游戏平台" in result["description"]

    def test_keyword_match_music(self, app_recommender):
        """测试关键词匹配-音乐"""
        # 使用 spotify 关键词进行匹配
        result = app_recommender.recommend_category("spotify.exe")

        assert result["category"] == "LEISURE"
        assert result["confidence"] == 0.75

    def test_keyword_match_video(self, app_recommender):
        """测试关键词匹配-视频"""
        # 使用bilibili关键词进行匹配
        result = app_recommender.recommend_category("bilibiliapp.exe")

        assert result["category"] == "LEISURE"

    def test_keyword_match_office(self, app_recommender):
        """测试关键词匹配-办公软件"""
        result = app_recommender.recommend_category("word-alternative.exe")

        assert result["category"] == "PRODUCTIVE"
        assert "办公软件" in result["description"]

    def test_keyword_match_browser(self, app_recommender):
        """测试关键词匹配-浏览器"""
        result = app_recommender.recommend_category("new-browser.exe")

        assert result["category"] == "NEUTRAL"
        assert "浏览器" in result["description"]


class TestDefaultRecommendation:
    """测试默认推荐"""

    def test_unknown_app(self, app_recommender):
        """测试未知应用"""
        result = app_recommender.recommend_category("unknown-app-12345.exe")

        assert result["category"] == "NEUTRAL"
        assert result["confidence"] == 0.3
        assert result["emoji"] == "❓"
        assert "未分类应用" in result["description"]
        assert "建议手动分类" in result["reason"]

    def test_empty_app_name(self, app_recommender):
        """测试空应用名称"""
        result = app_recommender.recommend_category("")

        assert result["category"] == "NEUTRAL"
        assert result["confidence"] == 0.3
        assert "空应用名称" in result["reason"]

    def test_none_app_name(self, app_recommender):
        """测试None应用名称"""
        result = app_recommender.recommend_category(None)

        assert result["category"] == "NEUTRAL"


class TestBatchRecommend:
    """测试批量推荐"""

    def test_batch_recommend_empty_list(self, app_recommender):
        """测试批量推荐空列表"""
        result = app_recommender.batch_recommend([])

        assert len(result) == 0

    def test_batch_recommend_single_app(self, app_recommender):
        """测试批量推荐单个应用"""
        result = app_recommender.batch_recommend(["code.exe"])

        assert len(result) == 1
        assert "code.exe" in result
        assert result["code.exe"]["category"] == "PRODUCTIVE"

    def test_batch_recommend_multiple_apps(self, app_recommender):
        """测试批量推荐多个应用"""
        apps = ["code.exe", "wechat.exe", "chrome.exe", "unknown.exe"]
        result = app_recommender.batch_recommend(apps)

        assert len(result) == 4
        assert result["code.exe"]["category"] == "PRODUCTIVE"
        assert result["wechat.exe"]["category"] == "LEISURE"
        assert result["chrome.exe"]["category"] == "NEUTRAL"
        assert result["unknown.exe"]["category"] == "NEUTRAL"

    def test_batch_recommend_preserves_app_names(self, app_recommender):
        """测试批量推荐保留应用名称"""
        apps = ["App1.exe", "App2.exe", "App3.exe"]
        result = app_recommender.batch_recommend(apps)

        for app_name in apps:
            assert app_name in result


class TestRecommendationStats:
    """测试推荐统计"""

    def test_get_recommendation_stats(self, app_recommender):
        """测试获取推荐统计"""
        stats = app_recommender.get_recommendation_stats()

        assert "total_known_apps" in stats
        assert "total_rules" in stats
        assert "productive_apps" in stats
        assert "leisure_apps" in stats
        assert "neutral_apps" in stats

        assert stats["total_known_apps"] == 26
        assert stats["total_rules"] == 6

    def test_stats_category_counts(self, app_recommender):
        """测试统计分类计数"""
        stats = app_recommender.get_recommendation_stats()

        # 验证分类数量合理
        total_categorized = (
            stats["productive_apps"] +
            stats["leisure_apps"] +
            stats["neutral_apps"]
        )

        assert total_categorized == stats["total_known_apps"]


class TestConfidenceLevels:
    """测试置信度级别"""

    def test_high_confidence_exact_match(self, app_recommender):
        """测试精确匹配高置信度"""
        result = app_recommender.recommend_category("code.exe")
        assert result["confidence"] >= 0.85

    def test_medium_confidence_keyword_match(self, app_recommender):
        """测试关键词匹配中等置信度"""
        result = app_recommender.recommend_category("my-dev-tool.exe")
        assert 0.65 <= result["confidence"] < 0.85

    def test_low_confidence_unknown(self, app_recommender):
        """测试未知应用低置信度"""
        result = app_recommender.recommend_category("totally-unknown.exe")
        assert result["confidence"] < 0.5


class TestEdgeCases:
    """测试边界情况"""

    def test_app_name_with_spaces(self, app_recommender):
        """测试带空格的应用名称"""
        result = app_recommender.recommend_category("my game player.exe")
        # 应该匹配 "game" 关键词
        assert result["category"] == "LEISURE"

    def test_app_name_with_special_characters(self, app_recommender):
        """测试带特殊字符的应用名称"""
        result = app_recommender.recommend_category("app-with_special@chars.exe")
        assert "category" in result

    def test_app_name_very_long(self, app_recommender):
        """测试超长应用名称"""
        long_name = "a" * 1000 + ".exe"
        result = app_recommender.recommend_category(long_name)
        assert result["category"] == "NEUTRAL"

    def test_app_name_unicode(self, app_recommender):
        """测试Unicode字符"""
        result = app_recommender.recommend_category("cloudmusic.exe")
        # 网易云音乐的实际进程名是 cloudmusic.exe
        assert result["category"] == "LEISURE"


class TestCategoryPriority:
    """测试分类优先级"""

    def test_exact_match_over_keyword(self, app_recommender):
        """测试精确匹配优先于关键词"""
        # chrome.exe 精确匹配为 NEUTRAL (0.85)
        # 但包含 "chrome" 关键词也会匹配到 browser 规则 (0.65)
        result = app_recommender.recommend_category("chrome.exe")

        # 应该使用精确匹配结果
        assert result["category"] == "NEUTRAL"
        assert result["confidence"] == 0.85
        assert "已知应用" in result["reason"]

    def test_first_keyword_match_wins(self, app_recommender):
        """测试第一个匹配的关键词规则生效"""
        # 同时匹配多个关键词时,应该使用第一个匹配的规则
        result = app_recommender.recommend_category("code-game-studio.exe")

        # 应该匹配第一条规则(开发工具)
        assert result["category"] == "PRODUCTIVE"


class TestSpecificApps:
    """测试特定应用"""

    def test_cursor_ide(self, app_recommender):
        """测试Cursor IDE"""
        result = app_recommender.recommend_category("cursor.exe")

        assert result["category"] == "PRODUCTIVE"
        assert "AI代码编辑器" in result["description"]

    def test_bilibili(self, app_recommender):
        """测试B站"""
        result = app_recommender.recommend_category("bilibili.exe")

        assert result["category"] == "LEISURE"
        assert "B站" in result["description"]

    def test_dingtalk(self, app_recommender):
        """测试钉钉"""
        result = app_recommender.recommend_category("dingtalk.exe")

        assert result["category"] == "PRODUCTIVE"
        assert "企业" in result["description"]

    def test_discord(self, app_recommender):
        """测试Discord"""
        result = app_recommender.recommend_category("discord.exe")

        assert result["category"] == "LEISURE"

    def test_notion(self, app_recommender):
        """测试Notion"""
        result = app_recommender.recommend_category("notion.exe")

        assert result["category"] == "PRODUCTIVE"


# Pytest配置
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
