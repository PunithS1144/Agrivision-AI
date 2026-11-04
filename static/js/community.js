// ============================================================================
// Plantix AI / AgriVision Platform - Farmer Community & Expert Network Controller (Phase 7)
// Integrates certified agronomist credentials, threaded discussions, likes,
// bookmarks, automated moderation, second-opinion review, and privacy-first regional locations.
// ============================================================================

const CommunityController = {
    currentPage: 1,
    selectedCrop: 'All',
    selectedTopic: 'All',
    searchQuery: '',
    currentUserId: 1, // Default user: Punith Gowda
    currentUserIsExpert: false,
    activePostCommentsMap: {},

    async init() {
        console.log('[CommunityController] Initializing community and expert network...');
        this.bindEvents();
        await this.checkUserStatus();
        await this.loadPosts(1, false);
    },

    async checkUserStatus() {
        try {
            const res = await fetch('/api/state');
            const data = await res.json();
            if (data && data.user) {
                this.currentUserId = data.user.id || 1;
                this.currentUserIsExpert = Boolean(data.user.is_expert);
                if (this.currentUserIsExpert) {
                    const expertTab = document.getElementById('community-expert-queue-tab');
                    if (expertTab) expertTab.style.display = 'inline-flex';
                }
            }
        } catch (e) {
            console.error('[CommunityController] Failed to check user status:', e);
        }
    },

    bindEvents() {
        // Search Input with Debounce
        const searchInput = document.getElementById('community-search-input');
        if (searchInput) {
            let debounceTimer;
            searchInput.addEventListener('input', (e) => {
                clearTimeout(debounceTimer);
                debounceTimer = setTimeout(() => {
                    this.searchQuery = e.target.value.trim();
                    this.currentPage = 1;
                    this.loadPosts(1, false);
                }, 350);
            });
        }

        // Crop Filter Pills
        document.querySelectorAll('.crop-filter-pill').forEach(btn => {
            btn.addEventListener('click', (e) => {
                document.querySelectorAll('.crop-filter-pill').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.selectedCrop = btn.dataset.crop || 'All';
                this.currentPage = 1;
                this.loadPosts(1, false);
            });
        });

        // Topic Filter Pills
        document.querySelectorAll('.topic-filter-pill').forEach(btn => {
            btn.addEventListener('click', (e) => {
                document.querySelectorAll('.topic-filter-pill').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.selectedTopic = btn.dataset.topic || 'All';
                this.currentPage = 1;
                this.loadPosts(1, false);
            });
        });

        // Create Post Form Submission
        const createForm = document.getElementById('create-post-form');
        if (createForm) {
            createForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                await this.submitNewPost();
            });
        }

        // Image Attachment Preview
        const imageInput = document.getElementById('new-post-image');
        const imagePreview = document.getElementById('new-post-image-preview');
        if (imageInput && imagePreview) {
            imageInput.addEventListener('change', (e) => {
                const file = e.target.files[0];
                if (file) {
                    const reader = new FileReader();
                    reader.onload = (re) => {
                        imagePreview.src = re.target.result;
                        imagePreview.style.display = 'block';
                    };
                    reader.readAsDataURL(file);
                } else {
                    imagePreview.src = '';
                    imagePreview.style.display = 'none';
                }
            });
        }
    },

    async loadPosts(page = 1, append = false) {
        const container = document.getElementById('community-posts-list');
        if (!container) return;

        if (!append) {
            container.innerHTML = `
                <div style="text-align: center; padding: 40px; color: var(--text-muted);">
                    <div class="spinner" style="width: 28px; height: 28px; margin: 0 auto 12px; border: 3px solid var(--primary-100); border-top-color: var(--primary-600); border-radius: 50%; animation: spin 0.8s linear infinite;"></div>
                    <p style="font-size: 14px;">Loading farmer discussions & expert advisories...</p>
                </div>
            `;
        }

        try {
            const url = new URL('/api/community/posts', window.location.origin);
            url.searchParams.append('page', page);
            url.searchParams.append('limit', 10);
            url.searchParams.append('user_id', this.currentUserId);
            if (this.selectedCrop !== 'All') url.searchParams.append('crop', this.selectedCrop);
            if (this.selectedTopic !== 'All') url.searchParams.append('topic', this.selectedTopic);
            if (this.searchQuery) url.searchParams.append('search', this.searchQuery);

            const res = await fetch(url);
            const data = await res.json();

            if (!data.success || !data.posts || data.posts.length === 0) {
                if (!append) {
                    container.innerHTML = `
                        <div class="agri-card" style="text-align: center; padding: 48px 24px; color: var(--text-muted);">
                            <div style="font-size: 40px; margin-bottom: 12px;">🌾</div>
                            <h3 style="font-size: 17px; font-weight: 700; color: var(--text-primary); margin-bottom: 6px;">No Discussions Found</h3>
                            <p style="font-size: 13.5px; max-width: 420px; margin: 0 auto 18px;">
                                Be the first grower to ask a question or share a crop management solution with the farmer network.
                            </p>
                            <button class="btn btn-primary" onclick="Components.openModal('modal-create-post')" style="font-size: 13px;">
                                ✍️ Start Discussion
                            </button>
                        </div>
                    `;
                }
                return;
            }

            const html = data.posts.map(p => this.renderPostCard(p)).join('');
            if (append) {
                container.insertAdjacentHTML('beforeend', html);
            } else {
                container.innerHTML = html;
            }

            // Pagination Controls
            const paginationContainer = document.getElementById('community-pagination');
            if (paginationContainer) {
                if (data.has_more) {
                    paginationContainer.innerHTML = `
                        <button class="btn btn-outline" style="width: 100%; margin-top: 16px; font-size: 13.5px;" onclick="window.CommunityController.loadPosts(${page + 1}, true)">
                            Load More Discussions
                        </button>
                    `;
                } else {
                    paginationContainer.innerHTML = '';
                }
            }
        } catch (err) {
            console.error('[CommunityController] Load posts error:', err);
            container.innerHTML = `
                <div class="agri-card" style="border-left: 4px solid var(--accent-red); padding: 20px;">
                    <p style="color: var(--accent-red); font-size: 14px;">Failed to connect to Community Network. Please verify your connection.</p>
                </div>
            `;
        }
    },

    renderPostCard(p) {
        const isAuthorExpert = Boolean(p.is_expert);
        const authorBadge = isAuthorExpert ? `
            <span class="expert-badge verified-green" title="Certified Agricultural Scientist">
                ✓ ${p.expert_badge || 'Verified Agronomist'}
            </span>
        ` : '';

        const expertCallout = p.expert_answer_preview ? `
            <div class="expert-callout">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;">
                    <div style="display: flex; align-items: center; gap: 6px;">
                        <span style="font-size: 14px;">👨‍🔬</span>
                        <strong style="font-size: 13px; color: #166534;">Verified Expert Answer</strong>
                        <span class="expert-badge" style="font-size: 10px;">${p.expert_answer_preview.expert_badge || 'KVK Certified'}</span>
                    </div>
                    <span style="font-size: 11.5px; color: var(--text-muted);">${p.expert_answer_preview.author_name} (${p.expert_answer_preview.expert_title || 'Extension Scientist'})</span>
                </div>
                <p style="font-size: 13px; color: #1e293b; margin: 0; line-height: 1.45;">
                    "${p.expert_answer_preview.comment_text}"
                </p>
            </div>
        ` : '';

        const imageHtml = p.image_path ? `
            <div style="margin: 12px 0; border-radius: var(--radius-md); overflow: hidden; max-height: 320px; background: #000;">
                <img src="${p.image_path}" alt="Crop leaf symptom" style="width: 100%; height: auto; max-height: 320px; object-fit: contain; display: block;">
            </div>
        ` : '';

        return `
            <div class="agri-card" id="post-card-${p.id}" style="margin-bottom: 16px; transition: transform 0.15s ease;">
                <!-- Post Header -->
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 10px;">
                    <div style="display: flex; align-items: center; gap: 10px; cursor: pointer;" onclick="window.CommunityController.openUserProfile(${p.user_id})">
                        <div class="avatar" style="width: 38px; height: 38px; font-size: 14px; background: ${isAuthorExpert ? '#166534' : 'var(--primary-600)'}; color: #fff;">
                            ${p.author_name ? p.author_name[0] : 'F'}
                        </div>
                        <div>
                            <div style="display: flex; align-items: center; gap: 6px;">
                                <span style="font-weight: 700; font-size: 14px; color: var(--text-primary);">${p.author_name}</span>
                                ${authorBadge}
                            </div>
                            <div style="font-size: 12px; color: var(--text-muted);">
                                📍 ${p.author_village || 'Karnataka'} · <span style="opacity: 0.85;">${this.formatDate(p.created_at)}</span>
                            </div>
                        </div>
                    </div>
                    <div style="display: flex; gap: 6px;">
                        <span class="badge badge-info" style="font-size: 11px;">🌱 ${p.crop_tag || 'General'}</span>
                        <span class="badge" style="background: var(--bg-subtle); border: 1px solid var(--border-color); font-size: 11px;">🏷️ ${p.topic_tag || 'Discussion'}</span>
                    </div>
                </div>

                <!-- Post Content -->
                <h3 style="font-size: 16px; font-weight: 700; color: var(--text-primary); margin: 6px 0 8px;">
                    ${this.escapeHtml(p.title)}
                </h3>
                <p style="font-size: 13.5px; color: var(--text-secondary); line-height: 1.5; margin: 0 0 10px; white-space: pre-line;">
                    ${this.escapeHtml(p.content)}
                </p>

                ${imageHtml}
                ${expertCallout}

                <!-- Action Toolbar -->
                <div style="display: flex; justify-content: space-between; align-items: center; padding-top: 12px; border-top: 1px solid var(--border-color-subtle); margin-top: 10px;">
                    <div style="display: flex; gap: 8px;">
                        <button class="action-btn ${p.has_liked ? 'active' : ''}" onclick="window.CommunityController.toggleLike(${p.id}, this)">
                            <span>👍</span>
                            <span class="like-count">${p.likes_count || 0}</span>
                        </button>
                        <button class="action-btn" onclick="window.CommunityController.toggleComments(${p.id})">
                            <span>💬</span>
                            <span>${p.comments_count || 0} Comments</span>
                        </button>
                        <button class="action-btn ${p.has_bookmarked ? 'active' : ''}" onclick="window.CommunityController.toggleBookmark(${p.id}, this)">
                            <span>${p.has_bookmarked ? '🔖' : '📑'}</span>
                            <span>Save</span>
                        </button>
                    </div>
                    <div>
                        <button class="btn btn-outline" style="padding: 4px 8px; font-size: 11.5px; color: var(--text-muted);" onclick="window.CommunityController.openReportModal('post', ${p.id})">
                            🚩 Report
                        </button>
                    </div>
                </div>

                <!-- Comments Container Drawer -->
                <div id="comments-drawer-${p.id}" style="display: none; margin-top: 14px; padding-top: 12px; border-top: 1px dashed var(--border-color);">
                    <div class="comments-list" id="comments-list-${p.id}"></div>
                    <form onsubmit="window.CommunityController.submitComment(event, ${p.id})" style="margin-top: 10px; display: flex; gap: 8px;">
                        <input type="text" id="comment-input-${p.id}" class="form-control" placeholder="${this.currentUserIsExpert ? 'Add verified agronomist guidance...' : 'Write your comment or experience...'}" required style="font-size: 13px;">
                        <button type="submit" class="btn btn-primary" style="padding: 6px 14px; font-size: 13px; white-space: nowrap;">
                            Post
                        </button>
                    </form>
                </div>
            </div>
        `;
    },

    async toggleLike(postId, btn) {
        try {
            const res = await fetch('/api/community/like', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ post_id: postId, user_id: this.currentUserId })
            });
            const data = await res.json();
            if (data.success) {
                const countSpan = btn.querySelector('.like-count');
                if (countSpan) countSpan.textContent = data.likes_count;
                if (data.has_liked) {
                    btn.classList.add('active');
                } else {
                    btn.classList.remove('active');
                }
            }
        } catch (err) {
            console.error('Like toggle error:', err);
        }
    },

    async toggleBookmark(postId, btn) {
        try {
            const res = await fetch('/api/community/bookmark', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ post_id: postId, user_id: this.currentUserId })
            });
            const data = await res.json();
            if (data.success) {
                if (data.has_bookmarked) {
                    btn.classList.add('active');
                    btn.innerHTML = `<span>🔖</span><span>Saved</span>`;
                    Components.showToast('Post bookmarked to saved articles', 'success');
                } else {
                    btn.classList.remove('active');
                    btn.innerHTML = `<span>📑</span><span>Save</span>`;
                }
            }
        } catch (err) {
            console.error('Bookmark error:', err);
        }
    },

    async toggleComments(postId) {
        const drawer = document.getElementById(`comments-drawer-${postId}`);
        if (!drawer) return;

        if (drawer.style.display === 'block') {
            drawer.style.display = 'none';
            return;
        }

        drawer.style.display = 'block';
        await this.loadComments(postId);
    },

    async loadComments(postId) {
        const list = document.getElementById(`comments-list-${postId}`);
        if (!list) return;

        list.innerHTML = `<div style="font-size: 12px; color: var(--text-muted); padding: 8px 0;">Loading comments...</div>`;

        try {
            const res = await fetch(`/api/community/comments?post_id=${postId}`);
            const comments = await res.json();

            if (!comments || comments.length === 0) {
                list.innerHTML = `<div style="font-size: 12.5px; color: var(--text-muted); padding: 6px 0;">No comments yet. Be the first to advise or share insights!</div>`;
                return;
            }

            list.innerHTML = comments.map(c => `
                <div class="comment-thread-item ${c.is_verified_expert_answer ? 'expert-reply' : ''}">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                        <div style="display: flex; align-items: center; gap: 6px;">
                            <strong style="font-size: 13px; color: var(--text-primary);">${c.author_name}</strong>
                            ${c.is_verified_expert_answer ? `
                                <span class="expert-badge verified-green" style="font-size: 10px;">
                                    ✓ ${c.expert_badge || 'Verified Expert'}
                                </span>
                            ` : ''}
                        </div>
                        <span style="font-size: 11px; color: var(--text-muted);">${this.formatDate(c.created_at)}</span>
                    </div>
                    <p style="font-size: 13px; color: var(--text-secondary); margin: 0 0 4px; line-height: 1.4;">
                        ${this.escapeHtml(c.comment_text)}
                    </p>
                </div>
            `).join('');
        } catch (e) {
            console.error('Failed to load comments:', e);
            list.innerHTML = `<div style="font-size: 12px; color: var(--accent-red);">Failed to load comments</div>`;
        }
    },

    async submitComment(event, postId) {
        event.preventDefault();
        const input = document.getElementById(`comment-input-${postId}`);
        if (!input || !input.value.trim()) return;

        const text = input.value.trim();
        try {
            const res = await fetch('/api/community/comment', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    post_id: postId,
                    user_id: this.currentUserId,
                    comment_text: text
                })
            });
            const data = await res.json();
            if (data.success) {
                input.value = '';
                Components.showToast(data.is_verified_expert_answer ? 'Verified Expert Answer published!' : 'Comment posted!', 'success');
                await this.loadComments(postId);
            } else {
                Components.showToast(data.error || 'Failed to post comment', 'danger');
            }
        } catch (e) {
            console.error('Submit comment error:', e);
            Components.showToast('Network error while posting comment', 'danger');
        }
    },

    async submitNewPost() {
        const titleEl = document.getElementById('new-post-title');
        const contentEl = document.getElementById('new-post-content');
        const cropEl = document.getElementById('new-post-tag');
        const topicEl = document.getElementById('new-post-topic');
        const fileInput = document.getElementById('new-post-image');

        if (!titleEl || !contentEl || !titleEl.value.trim() || !contentEl.value.trim()) {
            Components.showToast('Please provide a title and question description', 'warning');
            return;
        }

        const formData = new FormData();
        formData.append('title', titleEl.value.trim());
        formData.append('content', contentEl.value.trim());
        formData.append('crop_tag', cropEl ? cropEl.value : 'General');
        formData.append('topic_tag', topicEl ? topicEl.value : 'General');
        formData.append('user_id', this.currentUserId);

        if (fileInput && fileInput.files[0]) {
            formData.append('image', fileInput.files[0]);
        }

        try {
            const res = await fetch('/api/community/posts', {
                method: 'POST',
                body: formData
            });
            const data = await res.json();

            if (data.success) {
                if (data.is_flagged) {
                    Components.showToast('Post queued for moderator review due to chemical safety checks.', 'warning');
                } else {
                    Components.showToast('Discussion published to farmer community!', 'success');
                }
                Components.closeModal('modal-create-post');
                document.getElementById('create-post-form').reset();
                const preview = document.getElementById('new-post-image-preview');
                if (preview) { preview.src = ''; preview.style.display = 'none'; }
                await this.loadPosts(1, false);
            } else {
                Components.showToast(data.error || 'Failed to submit post', 'danger');
            }
        } catch (err) {
            console.error('Submit post error:', err);
            Components.showToast('Network error while submitting post', 'danger');
        }
    },

    async openUserProfile(userId) {
        try {
            const res = await fetch(`/api/community/users/${userId}?current_user_id=${this.currentUserId}`);
            const profile = await res.json();

            if (profile.error) {
                Components.showToast('User profile not found', 'warning');
                return;
            }

            const modal = document.getElementById('modal-user-profile');
            const content = document.getElementById('user-profile-modal-content');
            if (!modal || !content) return;

            const isExpert = Boolean(profile.is_expert);
            const isSelf = (profile.id === this.currentUserId);

            content.innerHTML = `
                <div style="text-align: center; margin-bottom: 18px;">
                    <div class="avatar" style="width: 64px; height: 64px; font-size: 24px; margin: 0 auto 10px; background: ${isExpert ? '#166534' : 'var(--primary-600)'}; color: #fff;">
                        ${profile.full_name ? profile.full_name[0] : 'U'}
                    </div>
                    <h3 style="font-size: 18px; font-weight: 800; color: var(--text-primary); margin-bottom: 4px;">
                        ${profile.full_name}
                    </h3>
                    ${isExpert ? `
                        <div class="expert-badge verified-green" style="margin-bottom: 6px;">
                            ✓ ${profile.expert_badge || 'Verified Agronomist'}
                        </div>
                        <div style="font-size: 12px; color: var(--text-secondary); margin-bottom: 4px;">
                            ${profile.expert_title} · ${profile.expert_organization}
                        </div>
                    ` : `
                        <div style="font-size: 12.5px; color: var(--text-secondary); margin-bottom: 4px;">
                            📍 ${profile.village}, ${profile.state}
                        </div>
                    `}
                    <div style="display: flex; justify-content: center; gap: 20px; margin: 12px 0; font-size: 13px;">
                        <div><strong>${profile.followers_count || 0}</strong> <span style="color: var(--text-muted);">Followers</span></div>
                        <div><strong>${profile.following_count || 0}</strong> <span style="color: var(--text-muted);">Following</span></div>
                        <div><strong>${profile.posts ? profile.posts.length : 0}</strong> <span style="color: var(--text-muted);">Posts</span></div>
                    </div>
                    ${!isSelf ? `
                        <button class="btn ${profile.is_following ? 'btn-outline' : 'btn-primary'}" style="font-size: 13px; padding: 6px 20px;" onclick="window.CommunityController.toggleFollow(${profile.id}, this)">
                            ${profile.is_following ? 'Unfollow' : '+ Follow'}
                        </button>
                    ` : ''}
                </div>

                <div style="border-top: 1px solid var(--border-color); padding-top: 14px;">
                    <h4 style="font-size: 13px; font-weight: 700; text-transform: uppercase; color: var(--text-muted); margin-bottom: 8px;">Farming Specialization</h4>
                    <p style="font-size: 13.5px; color: var(--text-primary); margin-bottom: 12px;">${profile.crop_specialization || 'Multi-crop grower'}</p>
                    
                    <h4 style="font-size: 13px; font-weight: 700; text-transform: uppercase; color: var(--text-muted); margin-bottom: 8px;">Farming Interests</h4>
                    <p style="font-size: 13.5px; color: var(--text-primary); margin-bottom: 16px;">${profile.farming_interests || 'Integrated Pest Management (IPM)'}</p>
                </div>
            `;

            Components.openModal('modal-user-profile');
        } catch (e) {
            console.error('Failed to open user profile:', e);
        }
    },

    async toggleFollow(targetUserId, btn) {
        try {
            const res = await fetch('/api/community/follow', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ follower_id: this.currentUserId, following_id: targetUserId })
            });
            const data = await res.json();
            if (data.success) {
                if (data.is_following) {
                    btn.className = 'btn btn-outline';
                    btn.textContent = 'Unfollow';
                    Components.showToast('Followed grower for field updates', 'success');
                } else {
                    btn.className = 'btn btn-primary';
                    btn.textContent = '+ Follow';
                }
            }
        } catch (e) {
            console.error('Follow error:', e);
        }
    },

    // --- AI + HUMAN SECOND OPINION REVIEW MODAL ---
    openExpertReviewModal(diagnosisData = null) {
        const modal = document.getElementById('modal-expert-review-request');
        if (!modal) return;

        // Try getting active diagnosis from DiagnosisController if not provided
        const activeDiag = diagnosisData || (window.DiagnosisController ? window.DiagnosisController.currentDiagnosisResult : null);

        const cropInput = document.getElementById('expert-review-crop');
        const symptomsInput = document.getElementById('expert-review-symptoms');
        const previewImg = document.getElementById('expert-review-img-preview');
        const diagIdInput = document.getElementById('expert-review-diagnosis-id');

        if (activeDiag) {
            if (cropInput) cropInput.value = activeDiag.crop_detected || 'Crop';
            if (symptomsInput) symptomsInput.value = `AI Prediction: ${activeDiag.disease_detected || 'Uncertain'}. Observed Symptoms: ${activeDiag.symptoms_description || 'Leaf lesions / discoloration requiring expert verification.'}`;
            if (diagIdInput) diagIdInput.value = activeDiag.id || '';
            if (previewImg && activeDiag.image_path) {
                previewImg.src = activeDiag.image_path;
                previewImg.style.display = 'block';
            }
        }

        Components.openModal('modal-expert-review-request');
    },

    async submitExpertReviewRequest() {
        const cropName = document.getElementById('expert-review-crop').value;
        const symptoms = document.getElementById('expert-review-symptoms').value;
        const previewImg = document.getElementById('expert-review-img-preview');
        const diagId = document.getElementById('expert-review-diagnosis-id').value;

        if (!cropName || !symptoms) {
            Components.showToast('Please provide crop name and symptoms description', 'warning');
            return;
        }

        try {
            const res = await fetch('/api/expert/reviews/request', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: this.currentUserId,
                    crop_name: cropName,
                    symptoms: symptoms,
                    image_path: previewImg ? previewImg.src : '',
                    diagnosis_id: diagId ? parseInt(diagId) : null
                })
            });
            const data = await res.json();
            if (data.success) {
                Components.showToast('Submitted to KVK Certified Agronomist for microscopic verification!', 'success');
                Components.closeModal('modal-expert-review-request');
            } else {
                Components.showToast(data.error || 'Failed to submit review request', 'danger');
            }
        } catch (e) {
            console.error('Expert review submit error:', e);
            Components.showToast('Network error submitting request', 'danger');
        }
    },

    // --- CONTENT MODERATION REPORTING ---
    openReportModal(targetType, targetId) {
        const modal = document.getElementById('modal-report-content');
        if (!modal) return;
        document.getElementById('report-target-type').value = targetType;
        document.getElementById('report-target-id').value = targetId;
        Components.openModal('modal-report-content');
    },

    async submitReport() {
        const targetType = document.getElementById('report-target-type').value;
        const targetId = document.getElementById('report-target-id').value;
        const reason = document.getElementById('report-reason').value;
        const details = document.getElementById('report-details').value;

        try {
            const res = await fetch('/api/community/report', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: this.currentUserId,
                    target_type: targetType,
                    target_id: targetId,
                    reason: reason,
                    details: details
                })
            });
            const data = await res.json();
            if (data.success) {
                Components.showToast('Content flagged for moderator review. Thank you for keeping the community safe.', 'success');
                Components.closeModal('modal-report-content');
            }
        } catch (e) {
            console.error('Report error:', e);
        }
    },

    formatDate(dateStr) {
        if (!dateStr) return 'Recently';
        try {
            const d = new Date(dateStr);
            return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
        } catch (e) {
            return dateStr;
        }
    },

    escapeHtml(str) {
        if (!str) return '';
        return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }
};

window.CommunityController = CommunityController;
document.addEventListener('DOMContentLoaded', () => {
    window.CommunityController.init();
});
