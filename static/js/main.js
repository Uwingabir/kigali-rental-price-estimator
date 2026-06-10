// Tab Controller Navigation
document.querySelectorAll('.nav-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        // Toggle Active Button
        document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        
        // Swap View Panel
        const tabName = btn.getAttribute('data-tab');
        document.querySelectorAll('.tab-panel').forEach(panel => panel.classList.remove('active'));
        document.getElementById(`${tabName}-tab`).classList.add('active');
        
        // Modify Page Headings
        const pageTitle = document.getElementById('page-title');
        const pageSubtitle = document.getElementById('page-subtitle');
        
        if (tabName === 'estimator') {
            pageTitle.innerText = "Rental Price Estimator";
            pageSubtitle.innerText = "Enter property features to predict fair market monthly rent in Kigali, Rwanda";
        } else {
            pageTitle.innerText = "Kigali Rental Market Insights";
            pageSubtitle.innerText = "Explore real-time spatial analysis and property distributions across Kigali";
            // Trigger chart initialization when navigating to insights
            initCharts();
        }
    });
});

// Helper Function: Increment/Decrement Input Counts
function adjustValue(inputId, delta) {
    const input = document.getElementById(inputId);
    const minVal = parseInt(input.getAttribute('min')) || 0;
    const maxVal = parseInt(input.getAttribute('max')) || 100;
    
    let currentVal = parseInt(input.value) || 0;
    let newVal = currentVal + delta;
    
    if (newVal >= minVal && newVal <= maxVal) {
        input.value = newVal;
    }
}

// Format number with thousands separators (commas)
function formatCurrency(num) {
    return Number(num).toLocaleString('en-US');
}

// Intercept Rent Estimator Form Submission
const form = document.getElementById('estimator-form');
form.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const resultsPanel = document.getElementById('results-panel');
    const placeholder = document.getElementById('results-placeholder');
    const content = document.getElementById('results-content');
    
    // Clear previous view and show a loading spinner
    placeholder.classList.add('hidden');
    content.classList.add('hidden');
    
    // Inject loader if not present
    let loader = resultsPanel.querySelector('.spinner');
    if (!loader) {
        loader = document.createElement('div');
        loader.className = 'spinner';
        resultsPanel.appendChild(loader);
    }
    loader.classList.remove('hidden');
    
    // Assemble form data to JSON payload
    const formData = new FormData(form);
    const payload = {
        property_type: formData.get('property_type'),
        location: formData.get('location'),
        bedrooms: parseInt(formData.get('bedrooms')),
        bathrooms: parseInt(formData.get('bathrooms')),
        amenities_count: parseInt(formData.get('amenities_count')),
        furnished_status: formData.get('furnished_status'),
        road_access: formData.get('road_access'),
        parking: formData.get('parking'),
        security: formData.get('security')
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
        
        // Render Output Estimates
        document.getElementById('val-predicted-rent').innerText = formatCurrency(resData.predicted_rent);
        document.getElementById('val-rent-min').innerText = formatCurrency(resData.rent_min) + " RWF";
        document.getElementById('val-rent-max').innerText = formatCurrency(resData.rent_max) + " RWF";
        
        // Handle Listed Rent Price Check
        const evalBox = document.getElementById('listed-evaluation-box');
        if (resData.listed_rent !== null) {
            evalBox.classList.remove('hidden');
            document.getElementById('val-listed-rent').innerText = formatCurrency(resData.listed_rent) + " RWF";
            
            const statusTag = document.getElementById('val-price-status');
            statusTag.innerText = resData.price_status + " Rent";
            statusTag.className = `status-tag ${resData.price_status.toLowerCase()}`;
            
            // Text comparison description
            const diffText = resData.price_diff_percent > 0 
                ? `${Math.abs(resData.price_diff_percent)}% higher` 
                : `${Math.abs(resData.price_diff_percent)}% lower`;
            
            document.getElementById('val-price-diff').innerText = resData.price_diff_percent === 0 ? "exactly identical" : diffText;
            
            // Adjust pointer location on gauge (Middle is 50%. Underpriced: 5-50%. Overpriced: 50-95%)
            const pointer = document.getElementById('meter-pointer');
            let offset = 50 + (resData.price_diff_percent * 1.35); // Scale sensitivity
            offset = Math.max(5, Math.min(95, offset)); // Bound limits
            pointer.style.left = `${offset}%`;
        } else {
            evalBox.classList.add('hidden');
        }
        
        // Display result block
        content.classList.remove('hidden');
        
    } catch (err) {
        loader.classList.add('hidden');
        placeholder.classList.remove('hidden');
        alert("Error executing ML model: " + err.message);
    }
});

// Chart.js Chart Instances Caching
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
    
    // Update metric dashboard numbers dynamically
    document.getElementById('stat-total-listings').innerText = formatCurrency(data.total_listings);
    document.getElementById('stat-avg-rent').innerText = formatCurrency(Math.round(data.overall_avg_rent)) + " RWF";
    
    // Initialize/Update Location Price Chart (Horizontal Bar Chart)
    const locCanvas = document.getElementById('locationChart');
    if (locCanvas) {
        const ctx = locCanvas.getContext('2d');
        
        const locLabels = data.location_stats.map(item => item.location);
        const locPrices = data.location_stats.map(item => Math.round(item.avg_rent / 1000)); // In Thousand RWF
        
        if (locationChartInstance) {
            locationChartInstance.destroy();
        }
        
        locationChartInstance = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: locLabels,
                datasets: [{
                    label: 'Avg Monthly Rent (Thousand RWF)',
                    data: locPrices,
                    backgroundColor: 'rgba(6, 182, 212, 0.6)',
                    borderColor: 'rgba(6, 182, 212, 1)',
                    borderWidth: 1.5,
                    borderRadius: 5
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return ` Avg Rent: ${formatCurrency(context.raw * 1000)} RWF`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: { color: 'rgba(255, 255, 255, 0.05)' },
                        ticks: { color: 'rgba(255, 255, 255, 0.6)' }
                    },
                    y: {
                        grid: { display: false },
                        ticks: { color: 'rgba(255, 255, 255, 0.8)' }
                    }
                }
            }
        });
    }
    
    // Initialize/Update Property Distribution Chart (Doughnut Chart)
    const propCanvas = document.getElementById('propertyTypeChart');
    if (propCanvas) {
        const ctx = propCanvas.getContext('2d');
        
        const propLabels = data.property_stats.map(item => item.property_type);
        const propCounts = data.property_stats.map(item => item.listing_count);
        
        if (propertyChartInstance) {
            propertyChartInstance.destroy();
        }
        
        propertyChartInstance = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: propLabels,
                datasets: [{
                    data: propCounts,
                    backgroundColor: [
                        'rgba(99, 102, 241, 0.7)',  // Violet
                        'rgba(6, 182, 212, 0.7)',   // Cyan
                        'rgba(34, 197, 94, 0.7)',   // Green
                        'rgba(234, 179, 8, 0.7)',   // Orange/Yellow
                        'rgba(239, 68, 68, 0.7)'    // Red
                    ],
                    borderColor: 'rgba(15, 23, 42, 1)',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: { color: 'rgba(255, 255, 255, 0.8)', padding: 15 }
                    }
                }
            }
        });
    }
}
