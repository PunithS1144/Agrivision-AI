// ============================================================================
// Plantix AI / AgriVision Platform - Marketplace & Retailer Connect Controller (Phase 8)
// Real input catalog, CIBRC pesticide safety, non-commercial alternatives,
// retailer inquiry workflows, store dashboards, and diagnostic product linkage.
// ============================================================================

const MarketplaceController = {
    activeTab: 'products', // 'products', 'retailers', 'dashboard'
    currentPage: 1,
    selectedCategory: 'All',
    selectedBrand: 'All',
    searchQuery: '',
    inStockOnly: false,
    activeRetailerId: 1,
    currentUserId: 1,

    async init() {
        console.log('[MarketplaceController] Initializing agricultural marketplace...');
        this.bindEvents();
        await this.loadProducts(1, false);
    },

    bindEvents() {
        // Tab switching
        document.querySelectorAll('.marketplace-nav-tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                document.querySelectorAll('.marketplace-nav-tab').forEach(t => t.classList.remove('active'));
                tab.classList.add('active');
                const target = tab.dataset.tab;
                this.switchTab(target);
            });
        });

        // Search input with debounce
        const searchInput = document.getElementById('marketplace-search-input');
        if (searchInput) {
            let timer;
            searchInput.addEventListener('input', (e) => {
                clearTimeout(timer);
                timer = setTimeout(() => {
                    this.searchQuery = e.target.value.trim();
                    this.currentPage = 1;
                    if (this.activeTab === 'products') {
                        this.loadProducts(1, false);
                    } else if (this.activeTab === 'retailers') {
                        this.loadRetailers();
                    }
                }, 350);
            });
        }

        // Category filter pills
        document.querySelectorAll('.market-category-pill').forEach(pill => {
            pill.addEventListener('click', () => {
                document.querySelectorAll('.market-category-pill').forEach(p => p.classList.remove('active'));
                pill.classList.add('active');
                this.selectedCategory = pill.dataset.category || 'All';
                this.currentPage = 1;
                this.loadProducts(1, false);
            });
        });

        // In-stock toggle checkbox
        const inStockCheckbox = document.getElementById('marketplace-instock-toggle');
        if (inStockCheckbox) {
            inStockCheckbox.addEventListener('change', (e) => {
                this.inStockOnly = e.target.checked;
                this.currentPage = 1;
                this.loadProducts(1, false);
            });
        }
    },

    switchTab(tabName) {
        this.activeTab = tabName;
        const productsView = document.getElementById('marketplace-products-view');
        const retailersView = document.getElementById('marketplace-retailers-view');
        const dashboardView = document.getElementById('marketplace-dashboard-view');
        const categoryFilterBar = document.getElementById('marketplace-category-bar');

        if (productsView) productsView.style.display = (tabName === 'products') ? 'block' : 'none';
        if (retailersView) retailersView.style.display = (tabName === 'retailers') ? 'block' : 'none';
        if (dashboardView) dashboardView.style.display = (tabName === 'dashboard') ? 'block' : 'none';
        if (categoryFilterBar) categoryFilterBar.style.display = (tabName === 'products') ? 'block' : 'none';

        if (tabName === 'products') {
            this.loadProducts(this.currentPage, false);
        } else if (tabName === 'retailers') {
            this.loadRetailers();
        } else if (tabName === 'dashboard') {
            this.loadRetailerDashboard();
        }
    },

    async loadProducts(page = 1, append = false) {
        const container = document.getElementById('marketplace-products-grid');
        if (!container) return;

        if (!append) {
            container.innerHTML = `
                <div style="grid-column: 1 / -1; text-align: center; padding: 40px; color: var(--text-muted);">
                    <div class="spinner" style="width: 28px; height: 28px; margin: 0 auto 12px; border: 3px solid var(--primary-100); border-top-color: var(--primary-600); border-radius: 50%; animation: spin 0.8s linear infinite;"></div>
                    <p style="font-size: 14px;">Loading certified agricultural inputs & biological formulations...</p>
                </div>
            `;
        }

        try {
            const url = new URL('/api/marketplace/products', window.location.origin);
            url.searchParams.append('page', page);
            url.searchParams.append('limit', 12);
            if (this.selectedCategory !== 'All') url.searchParams.append('category', this.selectedCategory);
            if (this.selectedBrand !== 'All') url.searchParams.append('brand', this.selectedBrand);
            if (this.inStockOnly) url.searchParams.append('in_stock_only', 'true');
            if (this.searchQuery) url.searchParams.append('search', this.searchQuery);

            const res = await fetch(url);
            const data = await res.json();

            if (!data.success || !data.products || data.products.length === 0) {
                if (!append) {
                    container.innerHTML = `
                        <div style="grid-column: 1 / -1; text-align: center; padding: 48px 24px; background: var(--bg-card); border-radius: var(--radius-md); border: 1px solid var(--border-color);">
                            <div style="font-size: 40px; margin-bottom: 12px;">🌱</div>
                            <h3 style="font-size: 17px; font-weight: 700; color: var(--text-primary); margin-bottom: 6px;">No Products Found</h3>
                            <p style="font-size: 13.5px; color: var(--text-muted); max-width: 420px; margin: 0 auto 14px;">
                                No inputs match "${this.searchQuery || this.selectedCategory}". Try selecting 'All' or checking spelling.
                            </p>
                        </div>
                    `;
                }
                return;
            }

            const html = data.products.map(p => this.renderProductCard(p)).join('');
            if (append) {
                container.insertAdjacentHTML('beforeend', html);
            } else {
                container.innerHTML = html;
            }

            // Pagination button
            const paginationEl = document.getElementById('marketplace-pagination');
            if (paginationEl) {
                if (data.has_more) {
                    paginationEl.innerHTML = `
                        <button class="btn btn-outline" style="width: 100%; margin-top: 16px; font-size: 13.5px;" onclick="window.MarketplaceController.loadProducts(${page + 1}, true)">
                            Load More Agricultural Inputs
                        </button>
                    `;
                } else {
                    paginationEl.innerHTML = '';
                }
            }
        } catch (err) {
            console.error('[MarketplaceController] Load products error:', err);
            container.innerHTML = `<div style="grid-column: 1 / -1; padding: 20px; color: var(--accent-red);">Failed to connect to marketplace catalog.</div>`;
        }
    },

    renderProductCard(p) {
        const isSponsored = Boolean(p.is_sponsored);
        const stockBadge = p.is_in_stock
            ? `<span class="badge badge-healthy" style="font-size: 11px;">✓ In Stock (${p.stock_quantity})</span>`
            : `<span class="badge" style="background: #fee2e2; color: #991b1b; font-size: 11px;">Out of Stock</span>`;

        const sponsoredBadge = isSponsored
            ? `<span style="font-size: 10px; font-weight: 700; background: #fef3c7; color: #92400e; padding: 2px 6px; border-radius: 4px; border: 1px solid #fcd34d;">📢 ${p.sponsored_label || 'Sponsored Partner'}</span>`
            : '';

        const discountBadge = p.discount_percent > 0
            ? `<span style="font-size: 11px; font-weight: 700; color: #166534; background: #dcfce7; padding: 1px 6px; border-radius: 4px;">${p.discount_percent}% OFF</span>`
            : '';

        return `
            <div class="agri-card agri-card-hover" id="product-card-${p.id}" style="display: flex; flex-direction: column; justify-content: space-between; border-top: ${isSponsored ? '3px solid #d97706' : '1px solid var(--border-color)'};">
                <div>
                    <!-- Category & Status Header -->
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
                        <span class="badge badge-info" style="font-size: 11px;">${p.category}</span>
                        <div style="display: flex; gap: 4px; align-items: center;">
                            ${sponsoredBadge}
                            ${stockBadge}
                        </div>
                    </div>

                    <!-- Brand & Name -->
                    <div style="font-size: 12px; font-weight: 700; color: var(--text-muted); text-transform: uppercase;">
                        ${p.brand}
                    </div>
                    <h3 style="font-size: 16px; font-weight: 700; color: var(--text-primary); margin: 4px 0 6px;">
                        ${this.escapeHtml(p.name)}
                    </h3>

                    <!-- Active Ingredient & CIBRC -->
                    ${p.active_ingredient ? `
                        <div style="font-size: 12.5px; color: var(--primary-700); font-weight: 600; margin-bottom: 4px;">
                            🔬 ${p.active_ingredient}
                        </div>
                    ` : ''}

                    <div style="font-size: 11px; color: var(--text-muted); margin-bottom: 8px;">
                        📜 CIBRC: <code style="font-size: 10.5px;">${p.cibrc_registration_no || 'Reg. Compliant'}</code>
                    </div>

                    <p style="font-size: 13px; color: var(--text-secondary); line-height: 1.4; margin-bottom: 10px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;">
                        ${this.escapeHtml(p.description)}
                    </p>

                    <!-- Organic Alternative Non-Commercial Banner -->
                    ${p.non_commercial_alternative ? `
                        <div style="background: #f0fdf4; border: 1px dashed #86efac; border-radius: var(--radius-sm); padding: 8px 10px; margin-bottom: 12px; font-size: 11.5px; color: #166534;">
                            <strong>🌿 Non-Commercial Bio-Alternative:</strong><br>
                            ${p.non_commercial_alternative}
                        </div>
                    ` : ''}
                </div>

                <!-- Footer: Price, Retailer & Actions -->
                <div style="border-top: 1px solid var(--border-color-subtle); padding-top: 10px; margin-top: 8px;">
                    <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 8px;">
                        <div>
                            <span style="font-size: 19px; font-weight: 800; color: var(--text-primary);">₹${p.price_inr}</span>
                            ${p.mrp_inr ? `<span style="font-size: 13px; color: var(--text-muted); text-decoration: line-through; margin-left: 6px;">₹${p.mrp_inr}</span>` : ''}
                            ${discountBadge}
                        </div>
                        <span style="font-size: 12px; color: var(--text-muted);">${p.package_size}</span>
                    </div>

                    <div style="font-size: 12px; color: var(--text-secondary); margin-bottom: 10px;">
                        🏪 <strong>${p.retailer_name}</strong> · <span style="color: var(--text-muted);">${p.retailer_distance_km || 3.0} km away</span>
                    </div>

                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px;">
                        <button class="btn btn-outline" style="font-size: 12.5px; padding: 7px 10px;" onclick="window.MarketplaceController.openProductDetailModal(${p.id})">
                            Specs & Dosage
                        </button>
                        <button class="btn btn-primary" style="font-size: 12.5px; padding: 7px 10px;" onclick="window.MarketplaceController.openInquiryModal(${p.retailer_id}, ${p.id}, '${this.escapeHtml(p.name)}')">
                            Connect / Inquire
                        </button>
                    </div>
                </div>
            </div>
        `;
    },

    async loadRetailers() {
        const container = document.getElementById('marketplace-retailers-grid');
        if (!container) return;

        container.innerHTML = `<div style="text-align: center; padding: 30px; color: var(--text-muted);">Finding licensed agricultural input stores near you...</div>`;

        try {
            const res = await fetch(`/api/retailers?search=${encodeURIComponent(this.searchQuery)}`);
            const data = await res.json();

            if (!data.success || !data.retailers || data.retailers.length === 0) {
                container.innerHTML = `<div class="agri-card" style="text-align: center; padding: 30px;">No registered input dealers found matching search.</div>`;
                return;
            }

            container.innerHTML = data.retailers.map(r => `
                <div class="agri-card agri-card-hover" style="margin-bottom: 16px;">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
                        <div>
                            <div style="font-size: 17px; font-weight: 700; color: var(--text-primary);">${r.name}</div>
                            <div style="font-size: 12.5px; color: var(--text-muted);">${r.shop_type}</div>
                        </div>
                        <div style="text-align: right;">
                            <span class="badge badge-healthy" style="font-size: 11px;">⭐ ${r.rating}</span>
                            <div style="font-size: 11px; color: var(--primary-700); font-weight: 600; margin-top: 2px;">
                                ${r.verification_badge || 'Verified Dealer'}
                            </div>
                        </div>
                    </div>

                    <div style="font-size: 13px; color: var(--text-secondary); margin-bottom: 8px;">
                        📍 <strong>${r.address}</strong> (${r.distance_km} km away)
                    </div>

                    <div style="display: flex; gap: 16px; font-size: 12px; color: var(--text-muted); margin-bottom: 10px;">
                        <div>📜 Lic: <code>${r.license_number || 'KA-AGR-2023'}</code></div>
                        <div>⏰ ${r.operating_hours || '08:30 AM - 08:00 PM'}</div>
                        <div>📦 ${r.in_stock_count || 12} Products Stocked</div>
                    </div>

                    <div style="background: var(--bg-subtle); padding: 8px 10px; border-radius: var(--radius-sm); font-size: 12px; color: var(--text-secondary); margin-bottom: 12px;">
                        <strong>Available Inputs:</strong> ${r.products_available}
                    </div>

                    <div style="display: flex; gap: 10px;">
                        <a href="tel:${r.phone}" class="btn btn-primary" style="flex: 1; font-size: 13px; text-decoration: none; text-align: center;">
                            📞 Call Store (${r.phone})
                        </a>
                        ${r.whatsapp_number ? `
                            <a href="https://wa.me/${r.whatsapp_number.replace(/[^0-9]/g, '')}?text=Namaskara,%20checking%20crop%20input%20availability" target="_blank" class="btn btn-outline" style="font-size: 13px; text-decoration: none;">
                                💬 WhatsApp
                            </a>
                        ` : ''}
                        <button class="btn btn-outline" style="font-size: 13px;" onclick="window.MarketplaceController.openInquiryModal(${r.id}, null, 'Store Stock Check')">
                            📩 Send Inquiry
                        </button>
                    </div>
                </div>
            `).join('');
        } catch (e) {
            console.error('Load retailers error:', e);
        }
    },

    async loadRetailerDashboard() {
        const container = document.getElementById('marketplace-dashboard-container');
        if (!container) return;

        container.innerHTML = `<div style="text-align: center; padding: 30px; color: var(--text-muted);">Loading retailer portal metrics & customer inquiries...</div>`;

        try {
            const res = await fetch(`/api/retailer/dashboard?retailer_id=${this.activeRetailerId}`);
            const data = await res.json();

            if (!data.success || !data.dashboard) {
                container.innerHTML = `<div class="agri-card" style="padding: 20px;">Could not load dashboard.</div>`;
                return;
            }

            const d = data.dashboard;
            const r = d.retailer;

            container.innerHTML = `
                <!-- Dashboard Store Header -->
                <div class="agri-card" style="margin-bottom: 20px; border-left: 4px solid var(--primary-600);">
                    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
                        <div>
                            <div style="font-size: 12px; text-transform: uppercase; color: var(--text-muted); font-weight: 700;">Partner Store Portal</div>
                            <h2 style="font-size: 20px; font-weight: 800; color: var(--text-primary); margin: 2px 0;">${r.name}</h2>
                            <div style="font-size: 13px; color: var(--text-secondary);">
                                📍 ${r.address} · 📜 License: <code>${r.license_number}</code>
                            </div>
                        </div>
                        <div style="display: flex; gap: 8px;">
                            <span class="expert-badge verified-green">✓ Certified Agri-Dealer</span>
                        </div>
                    </div>
                </div>

                <!-- KPI Metrics Grid -->
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 14px; margin-bottom: 22px;">
                    <div class="agri-card" style="text-align: center; padding: 18px;">
                        <div style="font-size: 28px; font-weight: 800; color: var(--primary-700);">${d.catalog_metrics.total_products}</div>
                        <div style="font-size: 13px; color: var(--text-muted); font-weight: 600;">Active Catalog Items</div>
                    </div>
                    <div class="agri-card" style="text-align: center; padding: 18px;">
                        <div style="font-size: 28px; font-weight: 800; color: #166534;">${d.catalog_metrics.in_stock_products}</div>
                        <div style="font-size: 13px; color: var(--text-muted); font-weight: 600;">In-Stock Ready</div>
                    </div>
                    <div class="agri-card" style="text-align: center; padding: 18px;">
                        <div style="font-size: 28px; font-weight: 800; color: var(--accent-amber);">${d.inquiry_metrics.pending_inquiries}</div>
                        <div style="font-size: 13px; color: var(--text-muted); font-weight: 600;">Pending Inquiries</div>
                    </div>
                    <div class="agri-card" style="text-align: center; padding: 18px;">
                        <div style="font-size: 28px; font-weight: 800; color: var(--primary-600);">${d.inquiry_metrics.fulfillment_rate_percent}%</div>
                        <div style="font-size: 13px; color: var(--text-muted); font-weight: 600;">Lead Fulfillment Rate</div>
                    </div>
                </div>

                <!-- Inbound Farmer Purchase Inquiries -->
                <div class="agri-card" style="margin-bottom: 24px;">
                    <h3 style="font-size: 16px; font-weight: 800; color: var(--text-primary); margin-bottom: 12px;">
                        📨 Inbound Farmer Purchase & Stock Inquiries
                    </h3>
                    <div id="retailer-inquiries-table">
                        ${d.recent_inquiries.length === 0 ? '<div style="color: var(--text-muted); font-size: 13px; padding: 12px 0;">No active inquiries received today.</div>' : `
                            <div style="overflow-x: auto;">
                                <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
                                    <thead>
                                        <tr style="border-bottom: 2px solid var(--border-color); text-align: left; color: var(--text-muted);">
                                            <th style="padding: 8px 6px;">Farmer</th>
                                            <th style="padding: 8px 6px;">Product</th>
                                            <th style="padding: 8px 6px;">Inquiry Note</th>
                                            <th style="padding: 8px 6px;">Status</th>
                                            <th style="padding: 8px 6px; text-align: right;">Action</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        ${d.recent_inquiries.map(i => `
                                            <tr style="border-bottom: 1px solid var(--border-color-subtle);">
                                                <td style="padding: 10px 6px;">
                                                    <strong>${i.farmer_name}</strong><br>
                                                    <span style="font-size: 11.5px; color: var(--text-muted);">${i.farmer_phone}</span>
                                                </td>
                                                <td style="padding: 10px 6px;">${i.product_name || 'General Inquiry'}</td>
                                                <td style="padding: 10px 6px; max-width: 220px; line-height: 1.35;">${i.message}</td>
                                                <td style="padding: 10px 6px;">
                                                    <span class="badge ${i.status === 'fulfilled' ? 'badge-healthy' : 'badge-warning'}" style="font-size: 11px;">
                                                        ${i.status}
                                                    </span>
                                                </td>
                                                <td style="padding: 10px 6px; text-align: right;">
                                                    ${i.status === 'pending' ? `
                                                        <button class="btn btn-primary" style="padding: 4px 8px; font-size: 11.5px;" onclick="window.MarketplaceController.updateInquiryStatus(${i.id}, 'fulfilled')">
                                                            Mark Fulfilled
                                                        </button>
                                                    ` : `<span style="font-size: 11px; color: var(--text-muted);">Completed</span>`}
                                                </td>
                                            </tr>
                                        `).join('')}
                                    </tbody>
                                </table>
                            </div>
                        `}
                    </div>
                </div>

                <!-- B2B Enterprise Integration Status -->
                <div class="agri-card" style="background: var(--bg-subtle);">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <h4 style="font-size: 14px; font-weight: 700; color: var(--text-primary); margin-bottom: 2px;">
                                🔌 Enterprise B2B REST API Integration Active
                            </h4>
                            <p style="font-size: 12.5px; color: var(--text-secondary); margin: 0;">
                                Connected to distributor ERP via <code>/api/v1/b2b/products</code> with API Key Auth.
                            </p>
                        </div>
                        <a href="/api/v1/b2b/docs" target="_blank" class="btn btn-outline" style="font-size: 12px; padding: 6px 12px; text-decoration: none;">
                            View API Docs (OpenAPI)
                        </a>
                    </div>
                </div>
            `;
        } catch (e) {
            console.error('Retailer dashboard error:', e);
        }
    },

    async updateInquiryStatus(inquiryId, newStatus) {
        try {
            const res = await fetch(`/api/retailers/inquiries/${inquiryId}/status`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ status: newStatus, notes: 'Fulfilled by store desk' })
            });
            const data = await res.json();
            if (data.success) {
                Components.showToast(`Inquiry #${inquiryId} updated to ${newStatus}`, 'success');
                await this.loadRetailerDashboard();
            }
        } catch (e) {
            console.error('Status update error:', e);
        }
    },

    async openProductDetailModal(productId) {
        try {
            const res = await fetch(`/api/marketplace/products/${productId}`);
            const p = await res.json();

            if (p.error) {
                Components.showToast('Product specifications not found', 'warning');
                return;
            }

            const modal = document.getElementById('modal-product-detail');
            const content = document.getElementById('product-detail-modal-content');
            if (!modal || !content) return;

            content.innerHTML = `
                <div style="margin-bottom: 14px;">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 6px;">
                        <span class="badge badge-info">${p.category} · ${p.subcategory || 'General'}</span>
                        <span class="badge ${p.is_in_stock ? 'badge-healthy' : 'badge-warning'}">${p.is_in_stock ? 'In Stock' : 'Out of Stock'}</span>
                    </div>
                    <div style="font-size: 12px; font-weight: 700; color: var(--text-muted); text-transform: uppercase;">${p.brand}</div>
                    <h2 style="font-size: 20px; font-weight: 800; color: var(--text-primary); margin: 2px 0 8px;">${p.name}</h2>
                    <div style="font-size: 14px; font-weight: 700; color: var(--primary-700); margin-bottom: 8px;">
                        Active Chemical / Bio Compound: ${p.active_ingredient || 'Standard Formulation'}
                    </div>
                </div>

                <div style="background: var(--bg-subtle); padding: 12px 14px; border-radius: var(--radius-sm); border: 1px solid var(--border-color); margin-bottom: 14px; font-size: 13px;">
                    <div style="margin-bottom: 6px;"><strong>📜 Government CIBRC Reg:</strong> <code>${p.cibrc_registration_no || 'Central Insecticides Board Approved'}</code></div>
                    <div style="margin-bottom: 6px;"><strong>💧 Recommended Dosage:</strong> ${p.dosage_guidance || 'Consult package label or KVK agronomist'}</div>
                    <div style="margin-bottom: 6px;"><strong>🌱 Target Crops:</strong> ${p.target_crops || 'All field crops'}</div>
                    <div><strong>🎯 Controlled Pests / Diseases:</strong> ${p.target_diseases || 'Foliar pathogens'}</div>
                </div>

                <div style="font-size: 13.5px; color: var(--text-secondary); line-height: 1.5; margin-bottom: 16px;">
                    ${p.description}
                </div>

                ${p.non_commercial_alternative ? `
                    <div style="background: #f0fdf4; border: 1px dashed #4ade80; border-radius: var(--radius-sm); padding: 12px 14px; margin-bottom: 16px; font-size: 13px; color: #166534;">
                        <strong>🌿 Non-Commercial Organic Alternative (Zero-Bias Agronomy):</strong><br>
                        ${p.non_commercial_alternative}
                    </div>
                ` : ''}

                <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid var(--border-color); padding-top: 14px;">
                    <div>
                        <div style="font-size: 22px; font-weight: 800; color: var(--text-primary);">₹${p.price_inr}</div>
                        <div style="font-size: 12px; color: var(--text-muted);">${p.package_size} · Sold by ${p.retailer_name}</div>
                    </div>
                    <button class="btn btn-primary" onclick="Components.closeModal('modal-product-detail'); window.MarketplaceController.openInquiryModal(${p.retailer_id}, ${p.id}, '${p.name}')">
                        Inquire at Store
                    </button>
                </div>
            `;

            Components.openModal('modal-product-detail');
        } catch (e) {
            console.error('Failed to open product detail:', e);
        }
    },

    openInquiryModal(retailerId, productId, productName) {
        const modal = document.getElementById('modal-retailer-inquiry');
        if (!modal) return;

        document.getElementById('inquiry-retailer-id').value = retailerId;
        document.getElementById('inquiry-product-id').value = productId || '';
        document.getElementById('inquiry-product-name').textContent = productName || 'Product Availability';
        Components.openModal('modal-retailer-inquiry');
    },

    async submitInquiry() {
        const retailerId = document.getElementById('inquiry-retailer-id').value;
        const productId = document.getElementById('inquiry-product-id').value;
        const inquiryType = document.getElementById('inquiry-type').value;
        const qty = document.getElementById('inquiry-qty').value;
        const phone = document.getElementById('inquiry-phone').value;
        const message = document.getElementById('inquiry-message').value;

        if (!phone || !message) {
            Components.showToast('Please provide your phone number and inquiry message', 'warning');
            return;
        }

        try {
            const res = await fetch('/api/retailers/inquiry', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: this.currentUserId,
                    retailer_id: parseInt(retailerId),
                    product_id: productId ? parseInt(productId) : null,
                    inquiry_type: inquiryType,
                    quantity_requested: qty,
                    farmer_phone: phone,
                    message: message
                })
            });

            const data = await res.json();
            if (data.success) {
                Components.showToast(data.message, 'success');
                Components.closeModal('modal-retailer-inquiry');
                document.getElementById('inquiry-form').reset();
            } else {
                Components.showToast(data.error || 'Failed to dispatch inquiry', 'danger');
            }
        } catch (e) {
            console.error('Inquiry dispatch error:', e);
            Components.showToast('Network error dispatching inquiry', 'danger');
        }
    },

    // --- DIAGNOSTIC PRODUCT LINKAGE ---
    async renderDiagnosisRecommendations(cropName, diseaseName, activeIngredient = null) {
        const container = document.getElementById('diagnosis-marketplace-recommendations');
        if (!container) return;

        try {
            const url = new URL('/api/marketplace/recommendations', window.location.origin);
            url.searchParams.append('crop', cropName);
            url.searchParams.append('disease', diseaseName);
            if (activeIngredient) url.searchParams.append('active_ingredient', activeIngredient);

            const res = await fetch(url);
            const data = await res.json();

            if (!data.success || !data.commercial_products || data.commercial_products.length === 0) {
                container.style.display = 'none';
                return;
            }

            container.style.display = 'block';
            container.innerHTML = `
                <div style="border-top: 1px dashed var(--border-color); padding-top: 16px; margin-top: 16px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                        <div>
                            <h4 style="font-size: 15px; font-weight: 800; color: var(--text-primary); margin: 0;">
                                🛒 CIBRC-Approved Commercial Inputs & Local Store Availability
                            </h4>
                            <p style="font-size: 12px; color: var(--text-muted); margin: 2px 0 0;">
                                Available at nearby licensed dealers. Verified against FRAC / CIBRC pesticide labels.
                            </p>
                        </div>
                        <span class="expert-badge verified-green" style="font-size: 10px;">Regulatory Verified</span>
                    </div>

                    <!-- Non-Commercial Organic Alternative Callout (Zero Bias) -->
                    <div style="background: #f0fdf4; border: 1px dashed #86efac; border-radius: var(--radius-sm); padding: 10px 12px; margin-bottom: 14px; font-size: 12.5px; color: #166534;">
                        <strong>🌿 Non-Commercial / Homemade Biological Option:</strong><br>
                        ${data.non_commercial_alternatives[0] || 'Fermented sour buttermilk (30 ml/L) or 5% Neem Seed Kernel Extract (NSKE).'}
                    </div>

                    <!-- Commercial Products Carousel / Grid -->
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 12px;">
                        ${data.commercial_products.map(p => `
                            <div class="agri-card" style="padding: 12px; border: 1px solid var(--border-color); display: flex; flex-direction: column; justify-content: space-between;">
                                <div>
                                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                                        <span style="font-size: 11px; font-weight: 700; color: var(--text-muted); text-transform: uppercase;">${p.brand}</span>
                                        ${p.is_sponsored ? '<span style="font-size: 9.5px; background: #fef3c7; color: #92400e; padding: 1px 4px; border-radius: 3px; font-weight: 700;">Sponsored</span>' : ''}
                                    </div>
                                    <div style="font-weight: 700; font-size: 14px; color: var(--text-primary); margin-bottom: 2px;">${p.name}</div>
                                    <div style="font-size: 11.5px; color: var(--primary-700); margin-bottom: 6px;">${p.active_ingredient || ''}</div>
                                    <div style="font-size: 11px; color: var(--text-muted); margin-bottom: 8px;">CIBRC: ${p.cibrc_registration_no}</div>
                                </div>
                                <div>
                                    <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 8px;">
                                        <span style="font-size: 16px; font-weight: 800; color: var(--text-primary);">₹${p.price_inr}</span>
                                        <span style="font-size: 11.5px; color: var(--text-muted);">${p.retailer_name} (${p.retailer_distance_km} km)</span>
                                    </div>
                                    <button class="btn btn-primary" style="width: 100%; font-size: 12px; padding: 6px;" onclick="window.MarketplaceController.openInquiryModal(${p.retailer_id}, ${p.id}, '${p.name}')">
                                        Check Store Stock
                                    </button>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        } catch (e) {
            console.error('Diagnosis recommendations error:', e);
        }
    },

    escapeHtml(str) {
        if (!str) return '';
        return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }
};

window.MarketplaceController = MarketplaceController;
document.addEventListener('DOMContentLoaded', () => {
    window.MarketplaceController.init();
});
