"""
GaiYa每日进度条 - 样式管理器
管理进度条样式和时间标记的下载、购买、收藏等功能
"""
import os
from datetime import datetime
from typing import Dict, Optional, List
from supabase import create_client, Client
import sys

# Supabase配置
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY", "")


class StyleManager:
    """样式管理器"""

    def __init__(self):
        """初始化Supabase客户端"""
        if not SUPABASE_URL or not SUPABASE_KEY:
            print("WARNING: Supabase credentials not configured", file=sys.stderr)
            self.client = None
        else:
            try:
                self.client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
                print("StyleManager initialized successfully", file=sys.stderr)
            except Exception as e:
                print(f"Failed to initialize Supabase client: {e}", file=sys.stderr)
                self.client = None

    def get_available_styles(
        self,
        user_id: str,
        user_tier: str,
        category: Optional[str] = None,
        featured_only: bool = False
    ) -> List[Dict]:
        """
        获取用户可用的样式列表

        Args:
            user_id: 用户ID
            user_tier: 用户等级 (free, pro, lifetime)
            category: 样式分类筛选（可选）
            featured_only: 仅显示精选样式

        Returns:
            样式列表
        """
        if not self.client:
            return []

        try:
            # 1. 构建查询
            query = self.client.table("progress_bar_styles").select("*")

            # 根据用户等级筛选
            if user_tier == "free":
                # 免费用户：基础样式 + 已购买的样式
                query = query.eq("tier", "free")
            # Pro/Lifetime用户可以看到所有样式（free + pro）

            # 分类筛选
            if category:
                query = query.eq("category", category)

            # 仅精选
            if featured_only:
                query = query.eq("featured", True)

            # 仅显示已发布的样式
            query = query.eq("status", "published")

            response = query.order("created_at", desc=True).execute()

            styles = response.data if response.data else []

            # 2. 如果是免费用户，添加已购买的样式
            if user_tier == "free":
                purchased_styles = self._get_purchased_styles(user_id, "style")
                styles.extend(purchased_styles)

            # 3. 添加是否已收藏的标记
            favorite_ids = self._get_user_favorite_ids(user_id, "style")
            for style in styles:
                style["is_favorited"] = style["id"] in favorite_ids

            print(f"Retrieved {len(styles)} styles for user {user_id}", file=sys.stderr)

            return styles

        except Exception as e:
            print(f"Error getting available styles: {e}", file=sys.stderr)
            return []

    def _get_purchased_styles(self, user_id: str, item_type: str) -> List[Dict]:
        """获取用户已购买的样式"""
        if not self.client:
            return []

        try:
            # 1. 获取购买记录
            purchases = self.client.table("user_purchased_styles").select("item_id").eq(
                "user_id", user_id
            ).eq("item_type", item_type).execute()

            if not purchases.data:
                return []

            item_ids = [p["item_id"] for p in purchases.data]

            # 2. 获取样式详情
            if item_type == "style":
                styles = self.client.table("progress_bar_styles").select("*").in_(
                    "id", item_ids
                ).eq("status", "published").execute()
                return styles.data if styles.data else []
            elif item_type == "marker":
                markers = self.client.table("time_markers").select("*").in_(
                    "id", item_ids
                ).eq("status", "published").execute()
                return markers.data if markers.data else []

            return []

        except Exception as e:
            print(f"Error getting purchased styles: {e}", file=sys.stderr)
            return []

    def _get_user_favorite_ids(self, user_id: str, item_type: str) -> set:
        """获取用户收藏的样式ID集合"""
        if not self.client:
            return set()

        try:
            favorites = self.client.table("user_favorites").select("item_id").eq(
                "user_id", user_id
            ).eq("item_type", item_type).execute()

            return {f["item_id"] for f in favorites.data} if favorites.data else set()

        except Exception as e:
            print(f"Error getting user favorites: {e}", file=sys.stderr)
            return set()

    def get_style_details(self, style_id: str) -> Optional[Dict]:
        """
        获取样式详细信息

        Args:
            style_id: 样式ID（UUID或style_id）

        Returns:
            样式详情
        """
        if not self.client:
            return None

        try:
            # 尝试通过UUID查询
            response = self.client.table("progress_bar_styles").select("*").eq("id", style_id).execute()

            if not response.data:
                # 尝试通过style_id查询
                response = self.client.table("progress_bar_styles").select("*").eq("style_id", style_id).execute()

            if response.data:
                return response.data[0]

            return None

        except Exception as e:
            print(f"Error getting style details: {e}", file=sys.stderr)
            return None

    def purchase_style(self, user_id: str, style_id: str, payment_id: str) -> Dict:
        """
        购买样式

        Args:
            user_id: 用户ID
            style_id: 样式ID
            payment_id: 支付记录ID

        Returns:
            购买结果
        """
        if not self.client:
            return {"success": False, "error": "Supabase not configured"}

        try:
            # 1. 获取样式信息
            style = self.get_style_details(style_id)

            if not style:
                return {"success": False, "error": "Style not found"}

            # 2. 检查是否已购买
            existing = self.client.table("user_purchased_styles").select("*").eq(
                "user_id", user_id
            ).eq("item_type", "style").eq("item_id", style["id"]).execute()

            if existing.data:
                return {"success": False, "error": "Already purchased"}

            # 3. 创建购买记录
            purchase_data = {
                "user_id": user_id,
                "item_type": "style",
                "item_id": style["id"],
                "price": style["price"],
                "currency": style["currency"],
                "payment_id": payment_id
            }

            purchase_response = self.client.table("user_purchased_styles").insert(purchase_data).execute()

            # 4. 更新下载统计
            self.client.table("progress_bar_styles").update({
                "downloads": style.get("downloads", 0) + 1
            }).eq("id", style["id"]).execute()

            # 5. 如果是用户创作的样式，记录创作者收益
            if style.get("author_type") == "user" and style.get("author_id"):
                self._record_creator_earnings(
                    style["author_id"],
                    "style",
                    style["id"],
                    purchase_response.data[0]["id"],
                    style["price"]
                )

            print(f"Style {style_id} purchased by user {user_id}", file=sys.stderr)

            return {
                "success": True,
                "purchase": purchase_response.data[0] if purchase_response.data else None
            }

        except Exception as e:
            print(f"Error purchasing style: {e}", file=sys.stderr)
            return {"success": False, "error": str(e)}

    def _record_creator_earnings(
        self,
        creator_id: str,
        item_type: str,
        item_id: str,
        purchase_id: str,
        original_price: float
    ):
        """记录创作者收益（70%分成）"""
        if not self.client:
            return

        try:
            platform_fee_rate = 0.30
            creator_earning_rate = 0.70

            earnings_data = {
                "user_id": creator_id,
                "item_type": item_type,
                "item_id": item_id,
                "purchase_id": purchase_id,
                "original_price": original_price,
                "amount": original_price * creator_earning_rate,
                "platform_fee": original_price * platform_fee_rate,
                "currency": "CNY",
                "status": "available"
            }

            self.client.table("creator_earnings").insert(earnings_data).execute()

            print(f"Creator earnings recorded for user {creator_id}: ¥{earnings_data['amount']:.2f}", file=sys.stderr)

        except Exception as e:
            print(f"Error recording creator earnings: {e}", file=sys.stderr)

    def toggle_favorite(self, user_id: str, item_type: str, item_id: str) -> Dict:
        """
        收藏/取消收藏样式

        Args:
            user_id: 用户ID
            item_type: 类型 (style/marker)
            item_id: 样式ID

        Returns:
            操作结果
        """
        if not self.client:
            return {"success": False, "error": "Supabase not configured"}

        try:
            # 检查是否已收藏
            existing = self.client.table("user_favorites").select("*").eq(
                "user_id", user_id
            ).eq("item_type", item_type).eq("item_id", item_id).execute()

            if existing.data:
                # 取消收藏
                self.client.table("user_favorites").delete().eq("id", existing.data[0]["id"]).execute()

                # 更新统计
                table_name = "progress_bar_styles" if item_type == "style" else "time_markers"
                item = self.client.table(table_name).select("favorites").eq("id", item_id).execute()

                if item.data:
                    new_count = max(0, item.data[0].get("favorites", 0) - 1)
                    self.client.table(table_name).update({"favorites": new_count}).eq("id", item_id).execute()

                return {"success": True, "favorited": False}
            else:
                # 添加收藏
                favorite_data = {
                    "user_id": user_id,
                    "item_type": item_type,
                    "item_id": item_id
                }

                self.client.table("user_favorites").insert(favorite_data).execute()

                # 更新统计
                table_name = "progress_bar_styles" if item_type == "style" else "time_markers"
                item = self.client.table(table_name).select("favorites").eq("id", item_id).execute()

                if item.data:
                    new_count = item.data[0].get("favorites", 0) + 1
                    self.client.table(table_name).update({"favorites": new_count}).eq("id", item_id).execute()

                return {"success": True, "favorited": True}

        except Exception as e:
            print(f"Error toggling favorite: {e}", file=sys.stderr)
            return {"success": False, "error": str(e)}

    def get_user_favorites(self, user_id: str, item_type: Optional[str] = None) -> List[Dict]:
        """
        获取用户收藏列表

        Args:
            user_id: 用户ID
            item_type: 类型筛选（可选）

        Returns:
            收藏列表
        """
        if not self.client:
            return []

        try:
            query = self.client.table("user_favorites").select("*").eq("user_id", user_id)

            if item_type:
                query = query.eq("item_type", item_type)

            favorites = query.order("created_at", desc=True).execute()

            if not favorites.data:
                return []

            # 获取样式详情
            result = []
            for fav in favorites.data:
                table_name = "progress_bar_styles" if fav["item_type"] == "style" else "time_markers"
                item = self.client.table(table_name).select("*").eq("id", fav["item_id"]).execute()

                if item.data:
                    item_data = item.data[0]
                    item_data["favorited_at"] = fav["created_at"]
                    result.append(item_data)

            return result

        except Exception as e:
            print(f"Error getting user favorites: {e}", file=sys.stderr)
            return []

    def upload_style(self, creator_id: str, style_data: Dict) -> Dict:
        """
        上传用户创作的样式（需要审核）

        Args:
            creator_id: 创作者ID
            style_data: 样式数据

        Returns:
            上传结果
        """
        if not self.client:
            return {"success": False, "error": "Supabase not configured"}

        try:
            # 构建样式记录
            upload_data = {
                "style_id": style_data.get("style_id"),
                "name": style_data.get("name"),
                "name_en": style_data.get("name_en"),
                "description": style_data.get("description"),
                "category": style_data.get("category", "custom"),
                "tier": "shop",  # 用户上传的都是商店样式
                "author_id": creator_id,
                "author_type": "user",
                "preview_thumbnail": style_data.get("preview_thumbnail"),
                "preview_video": style_data.get("preview_video"),
                "files": style_data.get("files"),
                "version": style_data.get("version", "1.0.0"),
                "price": style_data.get("price", 0.0),
                "currency": "CNY",
                "status": "draft",  # 初始状态为草稿，需要审核
                "featured": False
            }

            response = self.client.table("progress_bar_styles").insert(upload_data).execute()

            print(f"Style uploaded by user {creator_id}, pending review", file=sys.stderr)

            return {
                "success": True,
                "style": response.data[0] if response.data else None,
                "message": "样式已提交，等待审核"
            }

        except Exception as e:
            print(f"Error uploading style: {e}", file=sys.stderr)
            return {"success": False, "error": str(e)}

    def get_creator_earnings(self, creator_id: str) -> Dict:
        """
        获取创作者收益概览

        Args:
            creator_id: 创作者ID

        Returns:
            收益信息
        """
        if not self.client:
            return {"total_available": 0.0, "total_withdrawn": 0.0, "pending": 0.0}

        try:
            # 1. 可提现金额
            available = self.client.table("creator_earnings").select("amount").eq(
                "user_id", creator_id
            ).eq("status", "available").execute()

            total_available = sum(e["amount"] for e in available.data) if available.data else 0.0

            # 2. 已提现金额
            withdrawn = self.client.table("creator_earnings").select("amount").eq(
                "user_id", creator_id
            ).eq("status", "withdrawn").execute()

            total_withdrawn = sum(e["amount"] for e in withdrawn.data) if withdrawn.data else 0.0

            # 3. 处理中金额
            processing = self.client.table("creator_earnings").select("amount").eq(
                "user_id", creator_id
            ).eq("status", "processing").execute()

            total_processing = sum(e["amount"] for e in processing.data) if processing.data else 0.0

            return {
                "total_available": total_available,
                "total_withdrawn": total_withdrawn,
                "pending": total_processing,
                "currency": "CNY"
            }

        except Exception as e:
            print(f"Error getting creator earnings: {e}", file=sys.stderr)
            return {"total_available": 0.0, "total_withdrawn": 0.0, "pending": 0.0}
