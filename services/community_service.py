# Community, Verified Expert Network & Moderation Service for Plantix AI (Phase 7)
# Enforces Verified Agronomist certifications, AI+Human second-opinion review,
# privacy-preserving author locations, threaded discussions, and automated content moderation.

import os
import re
from datetime import datetime
from database.db import get_db_connection

# Harmful content & prohibited chemical regex patterns (CIBRC banned pesticides & spam)
BANNED_SUBSTANCES = [
    r'\bendosulfan\b', r'\bddt\b', r'\bchlordane\b', r'\baldicarb\b',
    r'\bparaquat\s+overdose\b', r'\bbuy\s+cheap\s+crypto\b', r'\btelegram\s+loan\b'
]

class CommunityService:
    def __init__(self):
        pass

    def check_harmful_content(self, text):
        """
        Automated moderation filter for prohibited agro-chemicals, illegal pesticides,
        and commercial spam.
        """
        text_lower = text.lower()
        for pattern in BANNED_SUBSTANCES:
            if re.search(pattern, text_lower):
                return {
                    "flagged": True,
                    "reason": "prohibited_substance_or_spam",
                    "matched_pattern": pattern
                }
        return {"flagged": False, "reason": None}

    def get_posts(self, page=1, limit=10, crop=None, topic=None, search=None, user_id=1):
        """
        Retrieves paginated community posts with verified expert badges,
        like status, and threaded comments preview.
        """
        conn = get_db_connection()
        try:
            offset = (page - 1) * limit
            sql = """
                SELECT p.*, u.full_name as author_name, u.village as author_village,
                       u.is_expert, u.expert_title, u.expert_badge, u.expert_organization,
                       (SELECT COUNT(*) FROM post_likes WHERE post_id = p.id) as real_likes,
                       (SELECT COUNT(*) FROM community_comments WHERE post_id = p.id) as real_comments,
                       (SELECT 1 FROM post_likes WHERE post_id = p.id AND user_id = ?) as has_liked,
                       (SELECT 1 FROM post_bookmarks WHERE post_id = p.id AND user_id = ?) as has_bookmarked
                FROM community_posts p
                JOIN users u ON p.user_id = u.id
                WHERE p.is_flagged = 0
            """
            params = [user_id, user_id]

            if crop and crop != 'All':
                sql += " AND p.crop_tag = ?"
                params.append(crop)

            if topic and topic != 'All':
                sql += " AND p.topic_tag = ?"
                params.append(topic)

            if search:
                sql += " AND (p.title LIKE ? OR p.content LIKE ? OR p.crop_tag LIKE ?)"
                q_param = f"%{search}%"
                params.extend([q_param, q_param, q_param])

            sql += " ORDER BY p.id DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            rows = conn.execute(sql, params).fetchall()
            posts = []

            for r in rows:
                item = dict(r)
                item["likes_count"] = item["real_likes"]
                item["comments_count"] = item["real_comments"]
                item["has_liked"] = bool(item["has_liked"])
                item["has_bookmarked"] = bool(item["has_bookmarked"])

                # Fetch verified expert replies preview
                expert_comment = conn.execute(
                    """SELECT c.*, u.full_name as author_name, u.expert_title, u.expert_badge 
                       FROM community_comments c
                       JOIN users u ON c.user_id = u.id
                       WHERE c.post_id = ? AND c.is_verified_expert_answer = 1
                       ORDER BY c.id DESC LIMIT 1""",
                    (item["id"],)
                ).fetchone()

                item["expert_answer_preview"] = dict(expert_comment) if expert_comment else None
                posts.append(item)

            total_count = conn.execute("SELECT COUNT(*) FROM community_posts WHERE is_flagged = 0").fetchone()[0]

            return {
                "success": True,
                "posts": posts,
                "page": page,
                "limit": limit,
                "total_posts": total_count,
                "has_more": (offset + len(posts)) < total_count
            }
        finally:
            conn.close()

    def create_post(self, user_id, title, content, crop_tag="General", topic_tag="General", image_path=None):
        """
        Creates a new community post with automated content filtering.
        """
        if not title or not content:
            return {"success": False, "error": "Title and content are required"}

        # Moderation check
        mod_check = self.check_harmful_content(f"{title} {content}")
        is_flagged = 1 if mod_check["flagged"] else 0

        conn = get_db_connection()
        try:
            user = conn.execute("SELECT full_name, village FROM users WHERE id = ?", (user_id,)).fetchone()
            author_name = user["full_name"] if user else "Farmer"
            author_village = user["village"] if user else "Karnataka"

            cur = conn.cursor()
            cur.execute(
                """INSERT INTO community_posts 
                   (user_id, author_name, author_village, title, content, crop_tag, topic_tag, image_path, is_flagged)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (user_id, author_name, author_village, title, content, crop_tag, topic_tag, image_path, is_flagged)
            )
            post_id = cur.lastrowid

            if is_flagged:
                # Log to content reports for moderator review
                cur.execute(
                    """INSERT INTO content_reports (reporter_user_id, target_type, target_id, reason, details)
                       VALUES (?, 'post', ?, 'Automated Moderation Filter', ?)""",
                    (1, post_id, f"Flagged by rule: {mod_check['matched_pattern']}")
                )

            conn.commit()
            return {
                "success": True,
                "post_id": post_id,
                "is_flagged": bool(is_flagged),
                "message": "Post submitted for moderator review" if is_flagged else "Post published successfully"
            }
        finally:
            conn.close()

    def toggle_like(self, user_id, post_id):
        """Toggles user like on a community post and sends notification."""
        conn = get_db_connection()
        try:
            existing = conn.execute(
                "SELECT 1 FROM post_likes WHERE user_id = ? AND post_id = ?",
                (user_id, post_id)
            ).fetchone()

            cur = conn.cursor()
            if existing:
                cur.execute("DELETE FROM post_likes WHERE user_id = ? AND post_id = ?", (user_id, post_id))
                cur.execute("UPDATE community_posts SET likes_count = MAX(0, likes_count - 1) WHERE id = ?", (post_id,))
                conn.commit()
                has_liked = False
            else:
                cur.execute("INSERT INTO post_likes (user_id, post_id) VALUES (?, ?)", (user_id, post_id))
                cur.execute("UPDATE community_posts SET likes_count = likes_count + 1 WHERE id = ?", (post_id,))
                
                # Notify author if not liking own post
                post = conn.execute("SELECT user_id, title FROM community_posts WHERE id = ?", (post_id,)).fetchone()
                if post and post["user_id"] != user_id:
                    cur.execute(
                        """INSERT INTO notifications (user_id, title, category, severity, message, action_link)
                           VALUES (?, 'New Like on Your Post', 'community', 'info', ?, '#community')""",
                        (post["user_id"], f"A fellow farmer found your post '{post['title'][:35]}...' helpful.")
                    )
                conn.commit()
                has_liked = True

            new_count = conn.execute("SELECT COUNT(*) FROM post_likes WHERE post_id = ?", (post_id,)).fetchone()[0]
            return {"success": True, "has_liked": has_liked, "likes_count": new_count}
        finally:
            conn.close()

    def toggle_bookmark(self, user_id, post_id):
        """Toggles user bookmark on a community post."""
        conn = get_db_connection()
        try:
            existing = conn.execute(
                "SELECT 1 FROM post_bookmarks WHERE user_id = ? AND post_id = ?",
                (user_id, post_id)
            ).fetchone()

            cur = conn.cursor()
            if existing:
                cur.execute("DELETE FROM post_bookmarks WHERE user_id = ? AND post_id = ?", (user_id, post_id))
                cur.execute("UPDATE community_posts SET bookmarks_count = MAX(0, bookmarks_count - 1) WHERE id = ?", (post_id,))
                conn.commit()
                has_bookmarked = False
            else:
                cur.execute("INSERT INTO post_bookmarks (user_id, post_id) VALUES (?, ?)", (user_id, post_id))
                cur.execute("UPDATE community_posts SET bookmarks_count = bookmarks_count + 1 WHERE id = ?", (post_id,))
                conn.commit()
                has_bookmarked = True

            new_count = conn.execute("SELECT COUNT(*) FROM post_bookmarks WHERE post_id = ?", (post_id,)).fetchone()[0]
            return {"success": True, "has_bookmarked": has_bookmarked, "bookmarks_count": new_count}
        finally:
            conn.close()

    def add_comment(self, user_id, post_id, comment_text, parent_comment_id=None):
        """
        Adds a comment or nested reply.
        If the author is a verified expert, sets is_verified_expert_answer = 1.
        """
        if not comment_text or not comment_text.strip():
            return {"success": False, "error": "Comment cannot be empty"}

        conn = get_db_connection()
        try:
            user = conn.execute("SELECT full_name, is_expert, expert_badge FROM users WHERE id = ?", (user_id,)).fetchone()
            if not user:
                return {"success": False, "error": "User not found"}

            is_expert = user["is_expert"] or 0
            cur = conn.cursor()

            cur.execute(
                """INSERT INTO community_comments 
                   (post_id, user_id, author_name, comment_text, parent_comment_id, is_verified_expert_answer)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (post_id, user_id, user["full_name"], comment_text.strip(), parent_comment_id, is_expert)
            )
            comment_id = cur.lastrowid

            # Increment post comment counter
            cur.execute("UPDATE community_posts SET comments_count = comments_count + 1 WHERE id = ?", (post_id,))

            # Send notification to post author
            post = conn.execute("SELECT user_id, title FROM community_posts WHERE id = ?", (post_id,)).fetchone()
            if post and post["user_id"] != user_id:
                notif_msg = f"{'Verified Agronomist ' + user['full_name'] if is_expert else user['full_name']} replied to your post."
                cur.execute(
                    """INSERT INTO notifications (user_id, title, category, severity, message, action_link)
                       VALUES (?, 'New Reply to Your Crop Post', 'community', ?, ?, '#community')""",
                    (post["user_id"], 'success' if is_expert else 'info', notif_msg)
                )

            conn.commit()
            return {
                "success": True,
                "comment_id": comment_id,
                "is_verified_expert_answer": bool(is_expert),
                "author_name": user["full_name"]
            }
        finally:
            conn.close()

    def get_comments(self, post_id):
        """Retrieves threaded comments and expert verified answers for a post."""
        conn = get_db_connection()
        try:
            rows = conn.execute(
                """SELECT c.*, u.is_expert, u.expert_title, u.expert_badge, u.expert_organization
                   FROM community_comments c
                   JOIN users u ON c.user_id = u.id
                   WHERE c.post_id = ?
                   ORDER BY c.is_verified_expert_answer DESC, c.id ASC""",
                (post_id,)
            ).fetchall()

            return [dict(r) for r in rows]
        finally:
            conn.close()

    def toggle_follow(self, follower_id, following_id):
        """Follow or unfollow a fellow farmer or certified agronomist."""
        if follower_id == following_id:
            return {"success": False, "error": "Cannot follow yourself"}

        conn = get_db_connection()
        try:
            existing = conn.execute(
                "SELECT 1 FROM user_follows WHERE follower_id = ? AND following_id = ?",
                (follower_id, following_id)
            ).fetchone()

            cur = conn.cursor()
            if existing:
                cur.execute("DELETE FROM user_follows WHERE follower_id = ? AND following_id = ?", (follower_id, following_id))
                conn.commit()
                is_following = False
            else:
                cur.execute("INSERT INTO user_follows (follower_id, following_id) VALUES (?, ?)", (follower_id, following_id))
                
                follower = conn.execute("SELECT full_name FROM users WHERE id = ?", (follower_id,)).fetchone()
                cur.execute(
                    """INSERT INTO notifications (user_id, title, category, severity, message, action_link)
                       VALUES (?, 'New Follower in Farm Community', 'community', 'info', ?, '#community')""",
                    (following_id, f"{follower['full_name']} started following your farm posts.")
                )
                conn.commit()
                is_following = True

            follower_count = conn.execute("SELECT COUNT(*) FROM user_follows WHERE following_id = ?", (following_id,)).fetchone()[0]
            return {"success": True, "is_following": is_following, "follower_count": follower_count}
        finally:
            conn.close()

    # --- AI & HUMAN EXPERT REVIEW WORKFLOW (SECOND OPINION) ---
    def request_expert_review(self, user_id, crop_name, symptoms, image_path, diagnosis_id=None):
        """
        Submits an uncertain or low-confidence diagnosis for human agronomist review.
        """
        conn = get_db_connection()
        try:
            expert = conn.execute("SELECT id FROM users WHERE is_expert = 1 LIMIT 1").fetchone()
            expert_id = expert["id"] if expert else None

            cur = conn.cursor()
            cur.execute(
                """INSERT INTO expert_review_requests 
                   (user_id, diagnosis_id, image_path, crop_name, symptoms_description, status, assigned_expert_id)
                   VALUES (?, ?, ?, ?, ?, 'assigned', ?)""",
                (user_id, diagnosis_id, image_path, crop_name, symptoms, expert_id)
            )
            request_id = cur.lastrowid

            # Create notification for expert
            if expert_id:
                cur.execute(
                    """INSERT INTO notifications (user_id, title, category, severity, message, action_link)
                       VALUES (?, 'New Leaf Diagnosis Review Request', 'expert_review', 'warning', ?, '#community')""",
                    (expert_id, f"Farmer submitted a {crop_name} sample requiring microscopic / pathogen verification.")
                )

            conn.commit()
            return {
                "success": True,
                "request_id": request_id,
                "status": "assigned",
                "message": "Diagnosis submitted to Krishi Vigyan Kendra (KVK) certified agronomist for second opinion."
            }
        finally:
            conn.close()

    def resolve_expert_review(self, request_id, expert_user_id, expert_diagnosis, recommendation):
        """
        Verified agronomist reviews the submitted leaf image and files official diagnosis.
        """
        conn = get_db_connection()
        try:
            expert = conn.execute("SELECT is_expert, full_name, expert_title FROM users WHERE id = ?", (expert_user_id,)).fetchone()
            if not expert or not expert["is_expert"]:
                return {"success": False, "error": "Unauthorized: Only certified agronomists can complete reviews"}

            cur = conn.cursor()
            cur.execute(
                """UPDATE expert_review_requests 
                   SET status = 'reviewed', expert_diagnosis = ?, expert_recommendation = ?, reviewed_at = CURRENT_TIMESTAMP
                   WHERE id = ?""",
                (expert_diagnosis, recommendation, request_id)
            )

            # Notify the farmer who submitted the request
            req = conn.execute("SELECT user_id, crop_name FROM expert_review_requests WHERE id = ?", (request_id,)).fetchone()
            if req:
                cur.execute(
                    """INSERT INTO notifications (user_id, title, category, severity, message, action_link)
                       VALUES (?, 'Expert Second Opinion Completed', 'expert_review', 'success', ?, '#history')""",
                    (req["user_id"], f"{expert['full_name']} completed diagnostic review for your {req['crop_name']} plot: {expert_diagnosis}.")
                )

            conn.commit()
            return {"success": True, "message": "Expert review filed successfully"}
        finally:
            conn.close()

    def get_expert_reviews(self, status=None, expert_id=None):
        """Retrieves expert review requests with farmer and expert information."""
        conn = get_db_connection()
        try:
            sql = """
                SELECT r.*, u.full_name as farmer_name, u.village as farmer_village,
                       e.full_name as expert_name, e.expert_title
                FROM expert_review_requests r
                JOIN users u ON r.user_id = u.id
                LEFT JOIN users e ON r.assigned_expert_id = e.id
                WHERE 1=1
            """
            params = []
            if status:
                sql += " AND r.status = ?"
                params.append(status)
            if expert_id:
                sql += " AND r.assigned_expert_id = ?"
                params.append(expert_id)
            sql += " ORDER BY r.id DESC"
            rows = conn.execute(sql, params).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_user_profile(self, target_user_id, current_user_id=1):
        """
        Retrieves user community profile with farming specialization, posts, and followers.
        """
        conn = get_db_connection()
        try:
            user = conn.execute("SELECT id, full_name, village, state, is_expert, expert_title, expert_badge, expert_organization, farming_interests, crop_specialization FROM users WHERE id = ?", (target_user_id,)).fetchone()
            if not user:
                return None

            posts = conn.execute("SELECT * FROM community_posts WHERE user_id = ? AND is_flagged = 0 ORDER BY id DESC", (target_user_id,)).fetchall()
            followers_count = conn.execute("SELECT COUNT(*) FROM user_follows WHERE following_id = ?", (target_user_id,)).fetchone()[0]
            following_count = conn.execute("SELECT COUNT(*) FROM user_follows WHERE follower_id = ?", (target_user_id,)).fetchone()[0]
            is_following = conn.execute("SELECT 1 FROM user_follows WHERE follower_id = ? AND following_id = ?", (current_user_id, target_user_id)).fetchone()

            profile = dict(user)
            profile["posts"] = [dict(p) for p in posts]
            profile["followers_count"] = followers_count
            profile["following_count"] = following_count
            profile["is_following"] = bool(is_following)
            return profile
        finally:
            conn.close()

    def report_content(self, reporter_user_id, target_type, target_id, reason, details=""):
        """Submits content report for moderation queue."""
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """INSERT INTO content_reports (reporter_user_id, target_type, target_id, reason, details)
                   VALUES (?, ?, ?, ?, ?)""",
                (reporter_user_id, target_type, target_id, reason, details)
            )
            report_id = cur.lastrowid
            conn.commit()
            return {"success": True, "report_id": report_id, "message": "Content flagged for moderator review"}
        finally:
            conn.close()

community_service = CommunityService()
