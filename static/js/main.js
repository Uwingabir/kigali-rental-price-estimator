// ─── Shared State ─────────────────────────────────────────────────────────────
// Stores the last estimate result so the contact form can pre-fill it
let lastEstimate = null;
let currentUser = null;

// ─── Tab Controller Navigation (For index page) ────────────────────────────────
const TAB_HEADINGS = {
    estimator: {
        title: "Rental Price Estimator",
        subtitle: "Enter property features to predict fair market monthly rent in Kigali, Rwanda"
    },
    insights: {
        title: "Kigali Rental Market Insights",
        subtitle: "Explore real-time spatial analysis and property distributions across Kigali"
    },
    contact: {
        title: "Contact a Commissioner",
        subtitle: "Submit your inquiry and a property commissioner will be notified via WhatsApp"
    }
};

document.querySelectorAll('.nav-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        // Toggle Active Button
        document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        // Swap View Panel
        const tabName = btn.getAttribute('data-tab');
        const targetPanel = document.getElementById(`${tabName}-tab`);
        if (!targetPanel) return; // If tab is on another page, ignore click navigation side-effects

        document.querySelectorAll('.tab-panel').forEach(panel => panel.classList.remove('active'));
        targetPanel.classList.add('active');

        // Update page heading
        const heading = TAB_HEADINGS[tabName] || {};
        const titleEl = document.getElementById('page-title');
        const subtitleEl = document.getElementById('page-subtitle');
        if (titleEl) titleEl.innerText = heading.title || '';
        if (subtitleEl) subtitleEl.innerText = heading.subtitle || '';

        // Tab-specific side effects
        if (tabName === 'insights') {
            initCharts();
        } else if (tabName === 'contact') {
            populateContactContext();
            updateWhatsAppPreview();
        }
    });
});

// Helper: Switch to a tab programmatically
function switchTab(tabName) {
    const btn = document.querySelector(`.nav-btn[data-tab="${tabName}"]`);
    if (btn) btn.click();
}

// Helper: Increment/Decrement Input Counts
function adjustValue(inputId, delta) {
    const input = document.getElementById(inputId);
    if (!input) return;
    const minVal = parseInt(input.getAttribute('min')) || 0;
    const maxVal = parseInt(input.getAttribute('max')) || 100;
    let currentVal = parseInt(input.value) || 0;
    let newVal = currentVal + delta;
    if (newVal >= minVal && newVal <= maxVal) {
        input.value = newVal;
        const displayEl = document.getElementById(`display-${inputId}`);
        if (displayEl) {
            displayEl.innerText = newVal;
        }
    }
}

// Helper: Format number with thousand separators
function formatCurrency(num) {
    return Number(num).toLocaleString('en-US');
}

// Helper: Format a UTC ISO timestamp for display
function formatTimestamp(iso) {
    if (!iso) return '—';
    try {
        const d = new Date(iso);
        return d.toLocaleDateString('en-GB', { day:'2-digit', month:'short', year:'numeric' })
            + ' ' + d.toLocaleTimeString('en-GB', { hour:'2-digit', minute:'2-digit' });
    } catch {
        return iso;
    }
}

// Simple HTML escape helper
function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

// ═══════════════════════════════════════════════════════════════════════════
// RENT ESTIMATOR FORM
// ═══════════════════════════════════════════════════════════════════════════
const estimatorForm = document.getElementById('estimator-form');

if (estimatorForm) {
    estimatorForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const resultsPanel    = document.getElementById('results-panel');
        const placeholder     = document.getElementById('results-placeholder');
        const content         = document.getElementById('results-content');
        const contactCta      = document.getElementById('contact-cta');

        // Clear previous state and show spinner
        placeholder.classList.add('hidden');
        content.classList.add('hidden');
        if (contactCta) contactCta.classList.add('hidden');

        let loader = resultsPanel.querySelector('.spinner');
        if (!loader) {
            loader = document.createElement('div');
            loader.className = 'spinner';
            resultsPanel.appendChild(loader);
        }
        loader.classList.remove('hidden');

        // Build payload
        const formData = new FormData(estimatorForm);
        const payload = {
            property_type:    formData.get('property_type'),
            location:         formData.get('location'),
            bedrooms:         parseInt(formData.get('bedrooms')),
            bathrooms:        parseInt(formData.get('bathrooms')),
            amenities_count:  parseInt(formData.get('amenities_count')),
            furnished_status: formData.get('furnished_status'),
            road_access:      formData.get('road_access'),
            parking:          formData.get('parking'),
            security:         formData.get('security')
        };

        const listedRentVal = formData.get('listed_rent');
        if (listedRentVal && listedRentVal.trim() !== '') {
            payload.listed_rent = parseFloat(listedRentVal);
        }

        try {
            const response = await fetch('/api/predict', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const resData = await response.json();

            if (!response.ok) {
                throw new Error(resData.message || "Failed to estimate rent.");
            }

            // Hide spinner
            loader.classList.add('hidden');

            // Store estimate for contact form pre-fill
            lastEstimate = {
                ...payload,
                predicted_rent: resData.predicted_rent,
                rent_min: resData.rent_min,
                rent_max: resData.rent_max
            };

            // Render main price output
            document.getElementById('val-predicted-rent').innerText = formatCurrency(resData.predicted_rent);
            document.getElementById('val-rent-min').innerText = formatCurrency(resData.rent_min) + " RWF";
            document.getElementById('val-rent-max').innerText = formatCurrency(resData.rent_max) + " RWF";

            // Listed rent evaluation
            const evalBox = document.getElementById('listed-evaluation-box');

            if (resData.listed_rent !== null) {
                evalBox.classList.remove('hidden');
                document.getElementById('val-listed-rent').innerText = formatCurrency(resData.listed_rent) + " RWF";
                document.getElementById('val-model-mae').innerText = resData.model_mae
                    ? `${formatCurrency(resData.model_mae)} RWF`
                    : 'Not available';

                const statusTag = document.getElementById('val-price-status');
                statusTag.innerText = resData.price_status + " Rent";
                const statusClass = resData.price_status.toLowerCase().replace(' ', '-');
                statusTag.className = `status-tag ${statusClass}`;

                const diffText = resData.price_diff_percent > 0
                    ? `${Math.abs(resData.price_diff_percent)}% higher`
                    : `${Math.abs(resData.price_diff_percent)}% lower`;
                document.getElementById('val-price-diff').innerText =
                    resData.price_diff_percent === 0 ? "exactly identical" : diffText;

                const modelNote = document.getElementById('model-note');
                if (modelNote) {
                    const maeText = resData.model_mae
                        ? `The model's typical error is about ${formatCurrency(resData.model_mae)} RWF, so a larger gap can indicate a price that is unusually high or low for this market.`
                        : "Price assessment uses the model's estimated range and typical error level.";
                    modelNote.querySelector('span').innerText = maeText;
                }

                // Gauge pointer
                const pointer = document.getElementById('meter-pointer');
                let offset = 50 + (resData.price_diff_percent * 1.35);
                offset = Math.max(5, Math.min(95, offset));
                pointer.style.left = `${offset}%`;
            } else {
                evalBox.classList.remove('hidden');
                document.getElementById('val-listed-rent').innerText = 'Not provided';
                document.getElementById('val-model-mae').innerText = resData.model_mae
                    ? `${formatCurrency(resData.model_mae)} RWF`
                    : 'Not available';

                const statusTag = document.getElementById('val-price-status');
                statusTag.innerText = 'Fair Market Estimate';
                statusTag.className = 'status-tag fair';

                document.getElementById('val-price-diff').innerText =
                    'This is the estimated fair market rent for the specified property.';

                const modelNote = document.getElementById('model-note');
                if (modelNote) {
                    const maeText = resData.model_mae
                        ? `The model's typical error is about ${formatCurrency(resData.model_mae)} RWF. Enter a listing price to compare.`
                        : 'Enter a listing price to compare against this estimate.';
                    modelNote.querySelector('span').innerText = maeText;
                }

                document.getElementById('meter-pointer').style.left = '50%';
            }

            // Show result block
            content.classList.remove('hidden');

            // Show Contact Commissioner CTA (if user is customer or guest)
            if (contactCta && (!currentUser || currentUser.role === 'customer')) {
                contactCta.classList.remove('hidden');
            }

        } catch (err) {
            loader.classList.add('hidden');
            placeholder.classList.remove('hidden');
            alert("Error executing ML model: " + err.message);
        }
    });
}

// CTA button: go to contact tab (pre-filled)
const goToContactBtn = document.getElementById('go-to-contact-btn');
if (goToContactBtn) {
    goToContactBtn.addEventListener('click', () => {
        switchTab('contact');
    });
}

// ═══════════════════════════════════════════════════════════════════════════
// MARKET INSIGHTS CHARTS
// ═══════════════════════════════════════════════════════════════════════════
let locationChartInstance = null;
let propertyChartInstance = null;
let statsDataCache = null;

async function fetchStats() {
    if (statsDataCache) return statsDataCache;
    try {
        const res = await fetch('/api/stats');
        statsDataCache = await res.json();
        return statsDataCache;
    } catch (e) {
        console.error("Error fetching market stats: ", e);
        return null;
    }
}

async function initCharts() {
    const data = await fetchStats();
    if (!data) return;

    const totalEl = document.getElementById('stat-total-listings');
    const avgEl   = document.getElementById('stat-avg-rent');
    if (totalEl) totalEl.innerText = formatCurrency(data.total_listings);
    if (avgEl)   avgEl.innerText   = formatCurrency(Math.round(data.overall_avg_rent)) + " RWF";

    // 1. Render custom sector bar chart
    const locContainer = document.getElementById('locationChartContainer');
    if (locContainer) {
        locContainer.innerHTML = '';
        const maxVal = Math.max(...data.location_stats.map(item => item.avg_rent));
        data.location_stats.slice(0, 8).forEach(item => {
            const pct = ((item.avg_rent / maxVal) * 100).toFixed(1) + '%';
            const kVal = Math.round(item.avg_rent / 1000);
            
            const row = document.createElement('div');
            row.className = 'sector-bar-row';
            row.innerHTML = `
                <div class="sector-bar-name">${escapeHtml(item.location)}</div>
                <div class="sector-bar-track">
                    <div class="sector-bar-fill" style="width: ${pct};"></div>
                </div>
                <div class="sector-bar-val">${kVal}K</div>
            `;
            locContainer.appendChild(row);
        });
    }

    // 2. Render custom property type donut ring chart
    const propContainer = document.getElementById('propertyTypeChartContainer');
    if (propContainer) {
        propContainer.innerHTML = '';
        const total = data.property_stats.reduce((acc, item) => acc + item.listing_count, 0);
        const colors = ['#7C74F0', '#2DD4BF', '#4ADE80', '#E0A82E', '#EF6B6B', '#9c95f5'];
        
        let svgCircles = '';
        let legendHtml = '<div class="donut-legend">';
        
        const circ = 2 * Math.PI * 54;
        let cum = 0;
        
        data.property_stats.forEach((item, index) => {
            const pctVal = ((item.listing_count / total) * 100);
            const pct = pctVal.toFixed(1);
            const color = colors[index % colors.length];
            const len = (pctVal / 100) * circ;
            const offset = -(cum / 100) * circ;
            
            svgCircles += `<circle cx="79" cy="79" r="54" fill="none" stroke="${color}" stroke-width="20" stroke-dasharray="${len.toFixed(2)} ${(circ - len).toFixed(2)}" stroke-dashoffset="${offset.toFixed(2)}" />`;
            cum += pctVal;
            
            legendHtml += `
                <div class="donut-legend-item">
                    <span class="donut-legend-dot" style="background:${color};"></span>
                    <span class="donut-legend-lbl">${escapeHtml(item.property_type)}</span>
                    <span class="donut-legend-val">${pct}%</span>
                </div>
            `;
        });
        
        legendHtml += '</div>';
        
        const totalK = (total / 1000).toFixed(1) + 'k';
        
        propContainer.innerHTML = `
            <div class="donut-graphic">
                <svg width="158" height="158" viewBox="0 0 158 158">
                    ${svgCircles}
                </svg>
                <div class="donut-center-label">
                    <div class="val" style="color: white;">${totalK}</div>
                    <div class="lbl">listings</div>
                </div>
            </div>
            ${legendHtml}
        `;
    }
}

// ═══════════════════════════════════════════════════════════════════════════
// CONTACT COMMISSIONER FORM
// ═══════════════════════════════════════════════════════════════════════════

// Populate the property context box from last estimate
function populateContactContext() {
    const box = document.getElementById('property-context-box');
    if (!box) return;

    const ctxType = document.getElementById('ctx-type');
    const ctxLoc  = document.getElementById('ctx-location');
    const ctxBeds = document.getElementById('ctx-beds');
    const ctxRent = document.getElementById('ctx-rent');

    if (lastEstimate) {
        if (ctxType) ctxType.innerText = lastEstimate.property_type || '—';
        if (ctxLoc)  ctxLoc.innerText  = lastEstimate.location || '—';
        if (ctxBeds) ctxBeds.innerText  = `${lastEstimate.bedrooms} bed / ${lastEstimate.bathrooms} bath`;
        if (ctxRent) ctxRent.innerText  = lastEstimate.predicted_rent
            ? `~${formatCurrency(lastEstimate.predicted_rent)} RWF/mo`
            : '—';

        // Pre-fill budget with estimate
        const budgetField = document.getElementById('c-budget');
        if (budgetField && lastEstimate.predicted_rent && !budgetField.value) {
            budgetField.value = lastEstimate.predicted_rent;
        }
    } else {
        if (ctxType) ctxType.innerText = 'No estimate yet';
        if (ctxLoc)  ctxLoc.innerText  = '—';
        if (ctxBeds) ctxBeds.innerText  = '—';
        if (ctxRent) ctxRent.innerText  = '—';
    }
}

// Live update the WhatsApp preview card as user types
function updateWhatsAppPreview() {
    const fields = {
        'preview-name':     document.getElementById('c-name'),
        'preview-phone':    document.getElementById('c-phone'),
        'preview-email':    document.getElementById('c-email'),
        'preview-movein':   document.getElementById('c-movein'),
        'preview-budget':   document.getElementById('c-budget'),
    };

    for (const [previewId, inputEl] of Object.entries(fields)) {
        const el = document.getElementById(previewId);
        if (el && inputEl) {
            el.innerText = inputEl.value || (previewId === 'preview-name' ? 'Your Name' : '—');
        }
    }

    // Property from estimate
    if (lastEstimate) {
        const typeEl = document.getElementById('preview-type');
        const locEl  = document.getElementById('preview-location');
        const rentEl = document.getElementById('preview-rent');
        if (typeEl) typeEl.innerText = lastEstimate.property_type || '—';
        if (locEl)  locEl.innerText  = lastEstimate.location || '—';
        if (rentEl && lastEstimate.rent_min && lastEstimate.rent_max) {
            rentEl.innerText = `${formatCurrency(lastEstimate.rent_min)} – ${formatCurrency(lastEstimate.rent_max)} RWF/mo`;
        }
    }
}

// Wire up live preview updates
['c-name', 'c-phone', 'c-email', 'c-movein', 'c-budget'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.addEventListener('input', updateWhatsAppPreview);
});

// Contact form submission
const contactForm = document.getElementById('contact-form');
if (contactForm) {
    contactForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const submitBtn = document.getElementById('contact-submit-btn');
        const btnText   = submitBtn.querySelector('.btn-text');
        btnText.innerText = 'Submitting…';
        submitBtn.disabled = true;

        const payload = {
            name:         document.getElementById('c-name').value.trim(),
            phone:        document.getElementById('c-phone').value.trim(),
            email:        document.getElementById('c-email').value.trim(),
            move_in_date: document.getElementById('c-movein').value.trim(),
            budget:       document.getElementById('c-budget').value.trim(),
            notes:        document.getElementById('c-notes').value.trim(),
        };

        // Attach property context from last estimate
        if (lastEstimate) {
            payload.property_type    = lastEstimate.property_type;
            payload.location         = lastEstimate.location;
            payload.bedrooms         = lastEstimate.bedrooms;
            payload.bathrooms        = lastEstimate.bathrooms;
            payload.amenities_count  = lastEstimate.amenities_count;
            payload.furnished_status = lastEstimate.furnished_status;
            payload.predicted_rent   = lastEstimate.predicted_rent;
            payload.rent_min         = lastEstimate.rent_min;
            payload.rent_max         = lastEstimate.rent_max;
        }

        try {
            const res = await fetch('/api/contact', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const data = await res.json();

            if (!res.ok) {
                throw new Error(data.error || 'Submission failed');
            }

            // Show success card
            contactForm.classList.add('hidden');
            const successCard = document.getElementById('contact-success');
            if (successCard) successCard.classList.remove('hidden');

            // WhatsApp status badge
            const waText = document.getElementById('wa-status-text');
            const waBadge = document.getElementById('wa-status-badge');
            if (data.whatsapp_sent) {
                if (waText) waText.innerHTML = 'WhatsApp notification sent to commissioner <i class="fa-solid fa-check" style="margin-left: 0.25rem;"></i>';
                if (waBadge) waBadge.style.display = 'inline-flex';
            } else {
                if (waBadge) waBadge.style.display = 'none';
            }

        } catch (err) {
            alert('Could not submit inquiry: ' + err.message);
        } finally {
            btnText.innerText = 'Submit Inquiry';
            submitBtn.disabled = false;
        }
    });
}

// "Submit Another Inquiry" button resets the form
const newInquiryBtn = document.getElementById('new-inquiry-btn');
if (newInquiryBtn) {
    newInquiryBtn.addEventListener('click', () => {
        const successCard = document.getElementById('contact-success');
        if (successCard) successCard.classList.add('hidden');
        if (contactForm) {
            contactForm.classList.remove('hidden');
            contactForm.reset();
        }
        const budgetField = document.getElementById('c-budget');
        if (lastEstimate && budgetField) {
            budgetField.value = lastEstimate.predicted_rent || '';
        }
        updateWhatsAppPreview();
    });
}

// ═══════════════════════════════════════════════════════════════════════════
// AUTHENTICATION & PORTAL LOG STATE
// ═══════════════════════════════════════════════════════════════════════════

// Query session details on load
async function checkAuthStateAndLoadDashboard() {
    try {
        const res = await fetch('/api/auth-state');
        const data = await res.json();

        // ── Session Card Injector ──
        const sessionUsername = document.getElementById('session-username');
        const sessionRole     = document.getElementById('session-role');
        const sessionAvatar   = document.getElementById('session-avatar');
        const logoutBtn       = document.getElementById('sidebar-logout-btn');
        const loginBtn        = document.getElementById('sidebar-login-btn');

        if (data.logged_in) {
            currentUser = data.user;
            if (sessionUsername) sessionUsername.innerText = currentUser.username;
            if (sessionRole) sessionRole.innerText = currentUser.role.charAt(0).toUpperCase() + currentUser.role.slice(1);
            if (sessionAvatar) {
                sessionAvatar.innerText = currentUser.username.split(' ').map(n => n[0]).slice(0, 2).join('').toUpperCase();
                sessionAvatar.style.background = 'linear-gradient(135deg, #2FD36F, #12894A)';
            }
            if (logoutBtn) logoutBtn.style.display = 'flex';
            if (loginBtn)  loginBtn.style.display = 'none';

            // Mark switcher active role button
            document.querySelectorAll('.view-as-btn').forEach(btn => btn.classList.remove('active'));
            const activeDemoBtn = document.getElementById(`demo-role-${currentUser.role}`);
            if (activeDemoBtn) activeDemoBtn.classList.add('active');

            // Handle Contact form guard on Index page
            if (!window.location.pathname.includes('/dashboard')) {
                const contactFields = document.getElementById('contact-form');
                const contactGuard  = document.getElementById('contact-auth-guard');
                if (currentUser.role === 'customer') {
                    if (contactFields) contactFields.classList.remove('hidden');
                    if (contactGuard)  contactGuard.remove();
                } else {
                    injectContactAuthGuard(`You are currently logged in as a <strong>${currentUser.role}</strong>. Only House Seekers can submit inquiry requests.`);
                }
            }
        } else {
            currentUser = null;
            if (sessionUsername) sessionUsername.innerText = "Guest Seeker";
            if (sessionRole) sessionRole.innerText = "Anonymous";
            if (sessionAvatar) {
                sessionAvatar.innerText = "?";
                sessionAvatar.style.background = 'rgba(148, 163, 158, 0.2)';
            }
            if (logoutBtn) logoutBtn.style.display = 'none';
            if (loginBtn)  loginBtn.style.display = 'flex';

            // Mark seeker active in demo switcher for guest
            document.querySelectorAll('.view-as-btn').forEach(btn => btn.classList.remove('active'));
            const activeDemoBtn = document.getElementById('demo-role-customer');
            if (activeDemoBtn) activeDemoBtn.classList.add('active');

            // Guard contact form for guests
            if (!window.location.pathname.includes('/dashboard')) {
                injectContactAuthGuard(`Please <a href="/login" style="color:var(--accent-cyan); font-weight:600; text-decoration:none;">Log In or Register</a> as a Customer to contact a property commissioner.`);
            }
        }

        // ── Dashboard Page Layout Config ──
        if (window.location.pathname.includes('/dashboard')) {
            if (!data.logged_in) {
                window.location.href = '/login';
                return;
            }

            currentUser = data.user;
            
            // Set Page Title subhead
            const subtitleEl = document.getElementById('page-subtitle');
            if (subtitleEl) subtitleEl.innerText = `Logged in as ${currentUser.username} (${currentUser.role})`;

            // Toggle specific view panels
            const viewCustEl = document.getElementById('view-customer');
            const viewCommEl = document.getElementById('view-commissioner');
            const viewAdminEl = document.getElementById('view-admin');

            if (currentUser.role === 'customer' && viewCustEl) viewCustEl.classList.remove('hidden');
            if (currentUser.role === 'commissioner' && viewCommEl) viewCommEl.classList.remove('hidden');
            if (currentUser.role === 'admin' && viewAdminEl) viewAdminEl.classList.remove('hidden');

            fetchDashboardData();
        }

    } catch (err) {
        console.error("Auth state query failed: ", err);
    }
}

// Helper: Guard contact form with a clean notice card
function injectContactAuthGuard(htmlText) {
    const contactTab = document.getElementById('contact-tab');
    if (!contactTab) return;

    let guard = document.getElementById('contact-auth-guard');
    if (!guard) {
        guard = document.createElement('div');
        guard.id = 'contact-auth-guard';
        guard.className = 'glass-card';
        guard.style.textAlign = 'center';
        guard.style.padding = '3rem 2rem';
        guard.style.gridColumn = 'span 2';
        guard.style.display = 'flex';
        guard.style.flexDirection = 'column';
        guard.style.alignItems = 'center';
        guard.style.gap = '1rem';

        const formCard = contactTab.querySelector('.contact-form-card');
        if (formCard) {
            const formFields = document.getElementById('contact-form');
            if (formFields) formFields.classList.add('hidden');
            formCard.appendChild(guard);
        }
    }

    guard.innerHTML = `
        <i class="fa-solid fa-lock" style="font-size:3rem; color:var(--text-muted); margin-bottom:0.5rem;"></i>
        <h3>Secure Inquiry Access</h3>
        <p style="color:var(--text-secondary); max-width:320px; font-size:0.9rem; line-height:1.5;">${htmlText}</p>
        <a href="/login" class="submit-btn" style="text-decoration:none; margin-top:1rem; padding: 0.8rem 1.5rem; width:auto; font-size:0.85rem;">
            Go to Login
        </a>
    `;
}

// ═══════════════════════════════════════════════════════════════════════════
// DYNAMIC DASHBOARD DATA FETCH
// ═══════════════════════════════════════════════════════════════════════════
async function fetchDashboardData() {
    if (!currentUser) return;

    try {
        const res = await fetch('/api/dashboard/data');
        const data = await res.json();

        if (!res.ok) {
            throw new Error(data.error || "Failed to load dashboard data");
        }

        if (data.role === 'customer') {
            renderCustomerDashboard(data);
        } else if (data.role === 'commissioner') {
            renderCommissionerDashboard(data);
        } else if (data.role === 'admin') {
            renderAdminDashboard(data);
        }

    } catch (err) {
        console.error("Dashboard load failed: ", err);
    }
}

// ── CUSTOMER VIEW RENDERING ──
function renderCustomerDashboard(data) {
    const list = data.inquiries || [];
    const placeholder = document.getElementById('cust-table-placeholder');
    const table       = document.getElementById('cust-inquiry-table');
    const tbody       = document.getElementById('cust-inquiry-tbody');

    if (!tbody) return;

    if (list.length === 0) {
        if (placeholder) placeholder.classList.remove('hidden');
        if (table) table.classList.add('hidden');
        return;
    }

    if (placeholder) placeholder.classList.add('hidden');
    if (table) table.classList.remove('hidden');
    tbody.innerHTML = '';

    list.forEach(inq => {
        const prop = inq.property || {};
        const rangeText = (prop.rent_min && prop.rent_max)
            ? `${formatCurrency(prop.rent_min)} – ${formatCurrency(prop.rent_max)} RWF`
            : '—';

        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${formatTimestamp(inq.timestamp)}</td>
            <td style="font-weight:600; color:white;">${escapeHtml(prop.property_type || '—')}</td>
            <td>${escapeHtml(prop.location || '—')}</td>
            <td>${rangeText}</td>
            <td>${escapeHtml(inq.move_in_date || '—')}</td>
            <td>${inq.budget ? formatCurrency(inq.budget) + ' RWF' : '—'}</td>
            <td class="td-notes" title="${escapeHtml(inq.notes || '')}">${escapeHtml(inq.notes || '—')}</td>
        `;
        tbody.appendChild(tr);
    });
}

// ── COMMISSIONER VIEW RENDERING ──
function renderCommissionerDashboard(data) {
    const list = data.inquiries || [];
    const totalEl = document.getElementById('comm-total');
    const waSentEl = document.getElementById('comm-wa-sent');
    const latestEl = document.getElementById('comm-latest');
    
    if (totalEl) totalEl.innerText = list.length;
    if (waSentEl) waSentEl.innerText = list.filter(i => i.whatsapp_sent).length;
    if (latestEl) latestEl.innerText = list.length > 0 ? formatTimestamp(list[0].timestamp) : '—';

    const placeholder = document.getElementById('comm-table-placeholder');
    const inboxList = document.getElementById('comm-inbox-list');
    const detailsPane = document.getElementById('comm-details-pane');

    if (!inboxList) return;

    if (list.length === 0) {
        if (placeholder) placeholder.classList.remove('hidden');
        inboxList.innerHTML = '';
        if (detailsPane) {
            detailsPane.style.opacity = '0.5';
            detailsPane.style.pointerEvents = 'none';
        }
        return;
    }

    if (placeholder) placeholder.classList.add('hidden');
    inboxList.innerHTML = '';

    list.forEach((inq, idx) => {
        const prop = inq.property || {};
        const rangeText = (prop.rent_min && prop.rent_max)
            ? `${formatCurrency(prop.rent_min)} – ${formatCurrency(prop.rent_max)} RWF`
            : '—';

        // Avatar initials
        const initials = inq.name ? inq.name.split(' ').map(n => n[0]).slice(0, 2).join('').toUpperCase() : 'U';

        // Create list row item button
        const btn = document.createElement('button');
        btn.className = 'inbox-item-row';
        if (idx === 0) {
            btn.classList.add('active');
            selectInquiryDetails(inq);
        }
        
        btn.innerHTML = `
            <div class="inbox-item-avatar">${initials}</div>
            <div style="flex:1; min-width:0;">
                <div style="font:700 14px Sora; color:white; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${escapeHtml(inq.name)}</div>
                <div style="font:500 12px Manrope; color:#8B978F; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">
                    ${escapeHtml(prop.property_type || '—')} · ${escapeHtml(prop.location || '—')}
                </div>
            </div>
            <div style="text-align:right; flex-shrink:0;">
                <span class="toggle-status-badge active" style="font-size:10px; background:rgba(45,212,191,0.08); color:#2DD4BF;">New</span>
                <div style="font:500 10.5px Manrope; color:#5C6862; margin-top:5px;">${formatTimestamp(inq.timestamp).split(' ')[0]}</div>
            </div>
        `;

        btn.addEventListener('click', () => {
            document.querySelectorAll('.inbox-item-row').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            selectInquiryDetails(inq);
        });

        inboxList.appendChild(btn);
    });
}

// Helper to populate right-hand inbox details panel
function selectInquiryDetails(inq) {
    const detailsPane = document.getElementById('comm-details-pane');
    if (!detailsPane) return;

    detailsPane.style.opacity = '1';
    detailsPane.style.pointerEvents = 'auto';

    const prop = inq.property || {};
    const initials = inq.name ? inq.name.split(' ').map(n => n[0]).slice(0, 2).join('').toUpperCase() : 'U';

    document.getElementById('details-avatar').innerText = initials;
    document.getElementById('details-name').innerText = inq.name || 'Anonymous Seeker';
    document.getElementById('details-meta').innerText = `${inq.phone || 'No Phone'} · ${inq.email || 'No Email'} · ${formatTimestamp(inq.timestamp)}`;
    
    document.getElementById('details-prop-title').innerText = `${prop.property_type || 'Property'} in ${prop.location || 'Kigali'}`;
    document.getElementById('details-prop-spec').innerText = `${prop.bedrooms || 0} bed / ${prop.bathrooms || 0} bath`;
    
    const rangeText = (prop.rent_min && prop.rent_max)
        ? `${formatCurrency(prop.rent_min)} – ${formatCurrency(prop.rent_max)}`
        : '—';
    document.getElementById('details-prop-rent').innerText = rangeText;

    document.getElementById('details-msg').innerText = inq.notes || 'No message details provided.';

    // Setup WhatsApp action link
    const waCleanNumber = inq.phone ? inq.phone.replace(/[^0-9+]/g, '') : '';
    const waMsgText = encodeURIComponent(
        `Hello ${inq.name},\n\nI received your KigaliRent inquiry for the ${prop.property_type} in ${prop.location}. I would be happy to assist you. Let's chat!`
    );
    const waBtn = document.getElementById('details-whatsapp-btn');
    if (waBtn) {
        waBtn.href = `https://wa.me/${waCleanNumber}?text=${waMsgText}`;
    }
}

// ── ADMIN VIEW RENDERING ──
function renderAdminDashboard(data) {
    const stats = data.stats || {};
    const users = data.users || [];
    const inqs  = data.inquiries || [];

    // Overall stats headers
    const statUsers = document.getElementById('admin-stat-users');
    const statAgents = document.getElementById('admin-stat-agents');
    const statInqs  = document.getElementById('admin-stat-inqs');

    if (statUsers)  statUsers.innerText  = stats.total_users || 0;
    if (statAgents) statAgents.innerText = stats.total_commissioners || 0;
    if (statInqs)  statInqs.innerText  = stats.total_inquiries || 0;

    // 1. Render Users list
    const usersTbody = document.getElementById('admin-users-tbody');
    if (usersTbody) {
        usersTbody.innerHTML = '';
        users.forEach(u => {
            let actionsHtml = '';
            if (u.role !== 'admin') {
                if (u.status === 'pending_approval') {
                    actionsHtml = `
                        <button class="action-btn-sm btn-approve" onclick="toggleUserStatus('${u.id}', 'active')">
                            <i class="fa-solid fa-circle-check"></i> Approve
                        </button>
                        <button class="action-btn-sm btn-suspend" onclick="toggleUserStatus('${u.id}', 'suspended')">
                            <i class="fa-solid fa-ban"></i> Suspend
                        </button>
                    `;
                } else if (u.status === 'active') {
                    actionsHtml = `
                        <button class="action-btn-sm btn-suspend" onclick="toggleUserStatus('${u.id}', 'suspended')">
                            <i class="fa-solid fa-ban"></i> Suspend
                        </button>
                    `;
                } else if (u.status === 'suspended') {
                    actionsHtml = `
                        <button class="action-btn-sm btn-activate" onclick="toggleUserStatus('${u.id}', 'active')">
                            <i class="fa-solid fa-arrows-spin"></i> Activate
                        </button>
                    `;
                }
            } else {
                actionsHtml = `<span style="color:var(--text-muted);">Platform Owner</span>`;
            }

            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${formatTimestamp(u.created_at)}</td>
                <td style="font-weight:600; color:white;">${escapeHtml(u.username)}</td>
                <td>${escapeHtml(u.email)}</td>
                <td><span class="role-badge ${u.role}">${u.role}</span></td>
                <td><span class="status-pill ${u.status}">${u.status.replace('_', ' ')}</span></td>
                <td>${actionsHtml}</td>
            `;
            usersTbody.appendChild(tr);
        });
    }

    // 2. Render Inquiries list
    const inqPlaceholder = document.getElementById('admin-table-placeholder');
    const inqTable       = document.getElementById('admin-inquiry-table');
    const inqTbody       = document.getElementById('admin-inquiry-tbody');

    if (inqTbody) {
        if (inqs.length === 0) {
            if (inqPlaceholder) inqPlaceholder.classList.remove('hidden');
            if (inqTable)       inqTable.classList.add('hidden');
            return;
        }

        if (inqPlaceholder) inqPlaceholder.classList.add('hidden');
        if (inqTable)       inqTable.classList.remove('hidden');
        inqTbody.innerHTML = '';

        inqs.forEach(i => {
            const prop = i.property || {};
            const rangeText = (prop.rent_min && prop.rent_max)
                ? `${formatCurrency(prop.rent_min)} – ${formatCurrency(prop.rent_max)} RWF`
                : '—';

            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${formatTimestamp(i.timestamp)}</td>
                <td>
                    <strong>${escapeHtml(i.name)}</strong><br>
                    <span style="font-size:0.75rem; color:var(--text-muted);">${escapeHtml(i.phone)} | ${escapeHtml(i.email)}</span>
                </td>
                <td class="td-notes" title="${escapeHtml(i.notes || '')}">${escapeHtml(i.notes || '—')}</td>
                <td>
                    <strong>${escapeHtml(prop.property_type)}</strong> in <strong>${escapeHtml(prop.location)}</strong><br>
                    <span style="font-size:0.75rem; color:var(--text-muted);">${prop.bedrooms} bed / ${prop.bathrooms} bath</span>
                </td>
                <td>
                    <strong>Budget:</strong> ${i.budget ? formatCurrency(i.budget) + ' RWF' : '—'}<br>
                    <strong>Move-in:</strong> ${escapeHtml(i.move_in_date || '—')}
                </td>
                <td>
                    ${i.whatsapp_sent
                        ? '<span class="status-pill active" style="font-size:0.65rem;"><i class="fa-solid fa-circle-check"></i> Sent</span>'
                        : '<span class="status-pill suspended" style="font-size:0.65rem;">Failed</span>'}
                </td>
            `;
            inqTbody.appendChild(tr);
        });
    }
}

// ── ADMIN CONTROL ACTION ──
async function toggleUserStatus(userId, status) {
    if (!confirm(`Are you sure you want to change this user status to ${status}?`)) return;

    try {
        const res = await fetch('/api/admin/toggle-user', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: userId, status: status })
        });
        const data = await res.json();

        if (!res.ok) {
            throw new Error(data.error || "Failed to update user status.");
        }

        // Reload data
        fetchDashboardData();

    } catch (err) {
        alert(err.message);
    }
}

// ── LOGOUT ACTION ──
async function handleLogout() {
    try {
        await fetch('/api/logout', { method: 'POST' });
        window.location.href = '/';
    } catch (err) {
        console.error("Logout failed: ", err);
    }
}

// Load auth state globally on script load
if (!window.location.pathname.includes('/login')) {
    checkAuthStateAndLoadDashboard();
}

// ── CUSTOM TOGGLES HELPER ──
function toggleSwitch(field) {
    const input = document.getElementById(field);
    const badge = document.getElementById(`badge-${field}`);
    const btn = document.getElementById(`toggle-${field}`);
    if (!input || !badge || !btn) return;

    if (input.value === 'Yes') {
        input.value = 'No';
        badge.innerText = 'No';
        badge.className = 'toggle-status-badge inactive';
        btn.classList.remove('active');
    } else {
        input.value = 'Yes';
        badge.innerText = 'Yes';
        badge.className = 'toggle-status-badge active';
        btn.classList.add('active');
    }
}

// ── QUICK SWITCH DEMO ROLE SWITCHER ──
async function demoSwitchRole(role) {
    let username = '';
    let password = '';
    if (role === 'customer') {
        username = 'seeker_demo';
        password = 'seeker123';
    } else if (role === 'commissioner') {
        username = 'agent_demo';
        password = 'agent123';
    } else if (role === 'admin') {
        username = 'admin';
        password = 'admin123';
    }

    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        const data = await response.json();
        
        if (response.ok) {
            if (role === 'customer') {
                window.location.href = '/';
            } else {
                window.location.href = '/dashboard';
            }
        } else {
            // If the user does not exist (e.g. users.json deleted), register them first
            if (data.error && data.error.includes("Invalid username or password")) {
                const registerUrl = '/api/register';
                const regPayload = {
                    username,
                    password,
                    email: `${username}@kigalirent.com`,
                    role: role === 'customer' ? 'customer' : 'commissioner'
                };
                
                const regResponse = await fetch(registerUrl, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(regPayload)
                });
                
                if (regResponse.ok) {
                    // Try login again
                    const retryResponse = await fetch('/api/login', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ username, password })
                    });
                    if (retryResponse.ok) {
                        window.location.href = (role === 'customer') ? '/' : '/dashboard';
                        return;
                    }
                }
            }
            alert("Demo authentication failed: " + (data.error || "Unknown error"));
        }
    } catch (err) {
        console.error("Demo login error:", err);
    }
}
