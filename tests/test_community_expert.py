# ============================================================================
# Unit and Integration Tests for Phase 7: Farmer Community & Expert Network
# Tests moderation, verified agronomist certification, threaded discussions,
# like/bookmark toggles, user follows, and AI+Human second opinion review.
# ============================================================================

import unittest
from app import app
from database.db import init_db, get_db_connection
from services.community_service import community_service

class TestCommunityAndExpertNetwork(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config['TESTING'] = True
        with app.app_context():
            init_db()

    def setUp(self):
        self.client = app.test_client()

    # 1. Moderation & Banned Substance Filter
    def test_automated_content_moderation(self):
        # Clean text should pass
        clean_res = community_service.check_harmful_content("How do I use neem oil for tomato leaf curl?")
        self.assertFalse(clean_res["flagged"])

        # Prohibited CIBRC banned chemicals must be flagged
        banned_res = community_service.check_harmful_content("Spray 50ml endosulfan directly on chili flowers")
        self.assertTrue(banned_res["flagged"])
        self.assertEqual(banned_res["reason"], "prohibited_substance_or_spam")

        # Spam content must be flagged
        spam_res = community_service.check_harmful_content("Join telegram loan group to buy cheap crypto")
        self.assertTrue(spam_res["flagged"])

    # 2. Post Creation & Moderation Flagging
    def test_post_creation_safe_and_flagged(self):
        # Valid post creation
        res = self.client.post('/api/community/post', json={
            "user_id": 1,
            "title": "Best organic mulching for bell pepper in summer",
            "content": "Using dry paddy straw mulch keeps soil temperature 5C cooler and conserves drip irrigation.",
            "crop_tag": "Chili",
            "topic_tag": "Organic Farming"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertFalse(data["is_flagged"])
        post_id = data["post_id"]

        # Flagged post creation (contains banned chemical)
        flagged_res = self.client.post('/api/community/post', json={
            "user_id": 1,
            "title": "Use DDT for quick insect control",
            "content": "DDT kills all aphids instantly on foliage.",
            "crop_tag": "Tomato",
            "topic_tag": "Disease & Pests"
        })
        self.assertEqual(flagged_res.status_code, 200)
        flagged_data = flagged_res.get_json()
        self.assertTrue(flagged_data["success"])
        self.assertTrue(flagged_data["is_flagged"])

    # 3. Community Feed & Pagination & Filtering
    def test_community_feed_and_filters(self):
        res = self.client.get('/api/community/posts?page=1&limit=5')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertIn("posts", data)
        self.assertGreater(len(data["posts"]), 0)

        # Test crop filter
        crop_res = self.client.get('/api/community/posts?crop=Chili')
        self.assertEqual(crop_res.status_code, 200)
        crop_data = crop_res.get_json()
        for p in crop_data["posts"]:
            self.assertEqual(p["crop_tag"], "Chili")

        # Test search filter (search for seeded Trichoderma post)
        search_res = self.client.get('/api/community/posts?search=Trichoderma')
        self.assertEqual(search_res.status_code, 200)
        search_data = search_res.get_json()
        self.assertTrue(any("trichoderma" in p["title"].lower() or "trichoderma" in p["content"].lower() for p in search_data["posts"]))

    # 4. Likes & Bookmarks Toggle
    def test_likes_and_bookmarks_toggle(self):
        # Fetch an existing post ID
        feed_res = self.client.get('/api/community/posts?limit=1')
        post_id = feed_res.get_json()["posts"][0]["id"]

        # 1st Like (add)
        like1 = self.client.post('/api/community/like', json={"post_id": post_id, "user_id": 1})
        self.assertEqual(like1.status_code, 200)
        d1 = like1.get_json()
        self.assertTrue(d1["success"])
        self.assertTrue(d1["has_liked"])

        # 2nd Like (remove / toggle off)
        like2 = self.client.post('/api/community/like', json={"post_id": post_id, "user_id": 1})
        self.assertEqual(like2.status_code, 200)
        d2 = like2.get_json()
        self.assertTrue(d2["success"])
        self.assertFalse(d2["has_liked"])

        # 1st Bookmark (add)
        bm1 = self.client.post('/api/community/bookmark', json={"post_id": post_id, "user_id": 1})
        self.assertEqual(bm1.status_code, 200)
        bmd1 = bm1.get_json()
        self.assertTrue(bmd1["success"])
        self.assertTrue(bmd1["has_bookmarked"])

        # 2nd Bookmark (remove / toggle off)
        bm2 = self.client.post('/api/community/bookmark', json={"post_id": post_id, "user_id": 1})
        self.assertEqual(bm2.status_code, 200)
        bmd2 = bm2.get_json()
        self.assertTrue(bmd2["success"])
        self.assertFalse(bmd2["has_bookmarked"])

    # 5. Threaded Comments & Certified Agronomist Verified Answer Enforcement
    def test_comments_and_expert_verification(self):
        feed_res = self.client.get('/api/community/posts?limit=1')
        post_id = feed_res.get_json()["posts"][0]["id"]

        # Regular farmer comment (user_id 1 is not expert)
        farmer_cmt = self.client.post('/api/community/comment', json={
            "post_id": post_id,
            "user_id": 1,
            "comment_text": "I tried cow urine spray and it partially worked."
        })
        self.assertEqual(farmer_cmt.status_code, 200)
        fc_data = farmer_cmt.get_json()
        self.assertTrue(fc_data["success"])
        self.assertFalse(fc_data["is_verified_expert_answer"])

        # Certified agronomist comment (user_id 2: Dr. Rajesh K. Gowda, is_expert=1)
        expert_cmt = self.client.post('/api/community/comment', json={
            "post_id": post_id,
            "user_id": 2,
            "comment_text": "Recommended IPM dosage: Spray Azadirachtin 10,000 ppm at 1.5 ml/L during dusk hours."
        })
        self.assertEqual(expert_cmt.status_code, 200)
        ec_data = expert_cmt.get_json()
        self.assertTrue(ec_data["success"])
        self.assertTrue(ec_data["is_verified_expert_answer"])

        # Fetch comments and verify ranking & expert badge
        cmts_res = self.client.get(f'/api/community/comments?post_id={post_id}')
        self.assertEqual(cmts_res.status_code, 200)
        comments = cmts_res.get_json()
        self.assertGreater(len(comments), 0)
        # Verified expert answer should be prioritized first
        self.assertEqual(comments[0]["is_verified_expert_answer"], 1)
        self.assertEqual(comments[0]["expert_badge"], "Verified ICAR Agronomist")

    # 6. Follow / Unfollow System
    def test_follow_and_unfollow(self):
        # Follow user 2 (Dr. Rajesh Gowda)
        res1 = self.client.post('/api/community/follow', json={"follower_id": 1, "following_id": 2})
        self.assertEqual(res1.status_code, 200)
        d1 = res1.get_json()
        self.assertTrue(d1["success"])
        self.assertTrue(d1["is_following"])

        # Unfollow user 2
        res2 = self.client.post('/api/community/follow', json={"follower_id": 1, "following_id": 2})
        self.assertEqual(res2.status_code, 200)
        d2 = res2.get_json()
        self.assertTrue(d2["success"])
        self.assertFalse(d2["is_following"])

        # Cannot follow self
        self_res = self.client.post('/api/community/follow', json={"follower_id": 1, "following_id": 1})
        self.assertEqual(self_res.status_code, 400)

    # 7. Community User Profile
    def test_user_profile(self):
        # Farmer profile
        farmer_res = self.client.get('/api/community/users/1')
        self.assertEqual(farmer_res.status_code, 200)
        f_data = farmer_res.get_json()
        self.assertEqual(f_data["id"], 1)
        self.assertIn("village", f_data)
        self.assertIn("crop_specialization", f_data)

        # Certified Expert profile
        expert_res = self.client.get('/api/community/users/2')
        self.assertEqual(expert_res.status_code, 200)
        e_data = expert_res.get_json()
        self.assertEqual(e_data["id"], 2)
        self.assertEqual(e_data["is_expert"], 1)
        self.assertEqual(e_data["expert_badge"], "Verified ICAR Agronomist")
        self.assertEqual(e_data["expert_organization"], "Krishi Vigyan Kendra (KVK) / UAS Bangalore")

    # 8. AI + Human Second-Opinion Expert Review Workflow
    def test_expert_second_opinion_workflow(self):
        # Submit review request for uncertain tomato blight
        req_res = self.client.post('/api/expert/reviews/request', json={
            "user_id": 1,
            "crop_name": "Tomato",
            "symptoms": "AI flagged uncertain Early Blight vs Septoria Leaf Spot with 54% calibrated confidence.",
            "image_path": "/static/uploads/sample_tomato_uncertain.jpg"
        })
        self.assertEqual(req_res.status_code, 200)
        req_data = req_res.get_json()
        self.assertTrue(req_data["success"])
        review_id = req_data["request_id"]
        self.assertEqual(req_data["status"], "assigned")

        # List review requests
        list_res = self.client.get('/api/expert/reviews?status=assigned')
        self.assertEqual(list_res.status_code, 200)
        reviews = list_res.get_json()["reviews"]
        self.assertTrue(any(r["id"] == review_id for r in reviews))

        # Non-expert attempting to resolve review must fail
        unauth_resolve = self.client.post(f'/api/expert/reviews/{review_id}/resolve', json={
            "expert_user_id": 1, # Not an expert
            "expert_diagnosis": "Confirmed Alternaria solani",
            "recommendation": "Spray Mancozeb"
        })
        self.assertEqual(unauth_resolve.status_code, 400)

        # Certified Agronomist resolves review
        resolve_res = self.client.post(f'/api/expert/reviews/{review_id}/resolve', json={
            "expert_user_id": 2, # Dr. Rajesh Gowda (is_expert=1)
            "expert_diagnosis": "Confirmed Early Blight (Alternaria solani) with secondary concentric target rings",
            "recommendation": "Spray Chlorothalonil 75% WP @ 2g/L water; follow 7-day PHI."
        })
        self.assertEqual(resolve_res.status_code, 200)
        res_data = resolve_res.get_json()
        self.assertTrue(res_data["success"])

        # Check farmer received notification
        state_res = self.client.get('/api/state')
        state_data = state_res.get_json()
        has_review_notif = any(n["category"] == "expert_review" for n in state_data["notifications"])
        self.assertTrue(has_review_notif)

    # 9. Content Moderation Reporting
    def test_content_reporting(self):
        res = self.client.post('/api/community/report', json={
            "user_id": 1,
            "target_type": "post",
            "target_id": 1,
            "reason": "Dangerous Chemical Concentration",
            "details": "User recommended spraying 10x recommended concentration."
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertIn("report_id", data)

if __name__ == '__main__':
    unittest.main()
