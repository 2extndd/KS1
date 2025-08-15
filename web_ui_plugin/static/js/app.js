/**
 * Main JavaScript file for KF Searcher Web UI
 * Handles common functionality across all pages
 */

// Global variables
let isLoading = false;
let toastContainer = null;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

/**
 * Initialize the application
 */
function initializeApp() {
    // Create toast container
    createToastContainer();
    
    // Initialize tooltips
    initializeTooltips();
    
    // Setup global event listeners
    setupEventListeners();
    
    // Setup auto-refresh for certain pages
    setupAutoRefresh();
    
    console.log('KF Searcher Web UI initialized');
}

/**
 * Create toast container for notifications
 */
function createToastContainer() {
    toastContainer = document.createElement('div');
    toastContainer.className = 'toast-container';
    toastContainer.setAttribute('aria-live', 'polite');
    toastContainer.setAttribute('aria-atomic', 'true');
    document.body.appendChild(toastContainer);
}

/**
 * Initialize Bootstrap tooltips
 */
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Setup global event listeners
 */
function setupEventListeners() {
    // Handle form submissions with loading states
    document.addEventListener('submit', function(e) {
        const form = e.target;
        if (form.tagName === 'FORM') {
            handleFormSubmission(form);
        }
    });
    
    // Handle AJAX errors globally
    window.addEventListener('unhandledrejection', function(e) {
        console.error('Unhandled promise rejection:', e.reason);
        showToast('An unexpected error occurred', 'error');
    });
}

/**
 * Setup auto-refresh for dashboard and logs
 */
function setupAutoRefresh() {
    const currentPath = window.location.pathname;
    
    // Auto-refresh dashboard every 30 seconds
    if (currentPath === '/' || currentPath === '/dashboard') {
        setInterval(refreshDashboardStats, 30000);
    }
    
    // Auto-refresh logs every 60 seconds (only first page)
    if (currentPath === '/logs') {
        const urlParams = new URLSearchParams(window.location.search);
        const page = urlParams.get('page');
        
        if (!page || page === '1') {
            setInterval(refreshLogsTable, 60000);
        }
    }
}

/**
 * Handle form submission with loading state
 */
function handleFormSubmission(form) {
    const submitBtn = form.querySelector('button[type="submit"]');
    if (submitBtn && !submitBtn.disabled) {
        setLoadingState(submitBtn, true);
        
        // Re-enable button after 10 seconds as fallback
        setTimeout(() => {
            setLoadingState(submitBtn, false);
        }, 10000);
    }
}

/**
 * Set loading state for buttons
 */
function setLoadingState(button, loading) {
    if (loading) {
        button.disabled = true;
        const originalText = button.innerHTML;
        button.setAttribute('data-original-text', originalText);
        button.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Loading...';
    } else {
        button.disabled = false;
        const originalText = button.getAttribute('data-original-text');
        if (originalText) {
            button.innerHTML = originalText;
        }
    }
}

/**
 * Show toast notification
 */
function showToast(message, type = 'info', duration = 5000) {
    const toastId = 'toast-' + Date.now();
    const iconClass = getToastIcon(type);
    const bgClass = getToastBgClass(type);
    
    const toastHtml = `
        <div class="toast ${bgClass} text-white" id="${toastId}" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header ${bgClass} text-white border-0">
                <i class="${iconClass} me-2"></i>
                <strong class="me-auto">KF Searcher</strong>
                <small class="opacity-75">${new Date().toLocaleTimeString()}</small>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        </div>
    `;
    
    toastContainer.insertAdjacentHTML('beforeend', toastHtml);
    
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, {
        delay: duration
    });
    
    toast.show();
    
    // Remove toast element after it's hidden
    toastElement.addEventListener('hidden.bs.toast', function() {
        toastElement.remove();
    });
}

/**
 * Get icon class for toast type
 */
function getToastIcon(type) {
    const icons = {
        'success': 'fas fa-check-circle',
        'error': 'fas fa-exclamation-circle',
        'warning': 'fas fa-exclamation-triangle',
        'info': 'fas fa-info-circle'
    };
    return icons[type] || icons['info'];
}

/**
 * Get background class for toast type
 */
function getToastBgClass(type) {
    const classes = {
        'success': 'bg-success',
        'error': 'bg-danger',
        'warning': 'bg-warning',
        'info': 'bg-info'
    };
    return classes[type] || classes['info'];
}

/**
 * Run search manually (called from navbar)
 */
function runSearch() {
    if (isLoading) {
        showToast('A search is already running', 'warning');
        return;
    }
    
    isLoading = true;
    showToast('Starting search...', 'info');
    
    fetch('/api/search/run', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        isLoading = false;
        
        if (data.error) {
            showToast(`Search failed: ${data.error}`, 'error');
        } else {
            const message = `Search completed! Found ${data.new_items} new items. ${data.successful_searches}/${data.total_searches} searches successful.`;
            showToast(message, 'success', 8000);
            
            // Refresh current page if it's dashboard or items
            const currentPath = window.location.pathname;
            if (currentPath === '/' || currentPath === '/items') {
                setTimeout(() => {
                    window.location.reload();
                }, 2000);
            }
        }
    })
    .catch(error => {
        isLoading = false;
        console.error('Search error:', error);
        showToast('Search failed due to network error', 'error');
    });
}

/**
 * Refresh dashboard statistics
 */
function refreshDashboardStats() {
    fetch('/api/stats')
        .then(response => response.json())
        .then(data => {
            if (data.database) {
                updateStatsCards(data.database);
            }
        })
        .catch(error => {
            console.error('Failed to refresh stats:', error);
        });
}

/**
 * Update stats cards on dashboard
 */
function updateStatsCards(stats) {
    const statsMapping = {
        'total_items': stats.total_items || 0,
        'items_today': stats.items_today || 0,
        'unsent_items': stats.unsent_items || 0,
        'active_searches': stats.active_searches || 0
    };
    
    Object.keys(statsMapping).forEach(key => {
        const element = document.querySelector(`[data-stat="${key}"]`);
        if (element) {
            element.textContent = statsMapping[key].toLocaleString();
        }
    });
}

/**
 * Refresh logs table
 */
function refreshLogsTable() {
    const logsTable = document.querySelector('.table-responsive');
    if (!logsTable) return;
    
    fetch(window.location.href)
        .then(response => response.text())
        .then(html => {
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            const newTable = doc.querySelector('.table-responsive');
            
            if (newTable) {
                logsTable.innerHTML = newTable.innerHTML;
            }
        })
        .catch(error => {
            console.error('Failed to refresh logs:', error);
        });
}

/**
 * Copy text to clipboard
 */
function copyToClipboard(text) {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(() => {
            showToast('Copied to clipboard', 'success', 2000);
        }).catch(err => {
            console.error('Failed to copy:', err);
            showToast('Failed to copy to clipboard', 'error');
        });
    } else {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        
        try {
            document.execCommand('copy');
            showToast('Copied to clipboard', 'success', 2000);
        } catch (err) {
            console.error('Failed to copy:', err);
            showToast('Failed to copy to clipboard', 'error');
        }
        
        document.body.removeChild(textArea);
    }
}

/**
 * Format number with thousand separators
 */
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
}

/**
 * Format price with currency
 */
function formatPrice(price, currency = 'BYN') {
    if (price === 0 || price === null || price === undefined) {
        return 'Price not specified';
    }
    return `${formatNumber(price)} ${currency}`;
}

/**
 * Format date for display
 */
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    
    return date.toLocaleDateString('ru-RU');
}

/**
 * Debounce function for search inputs
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Validate URL format
 */
function isValidUrl(string) {
    try {
        new URL(string);
        return true;
    } catch (_) {
        return false;
    }
}

/**
 * Validate KF URL specifically
 */
function isValidKufarUrl(url) {
    if (!isValidUrl(url)) return false;
    
    const parsedUrl = new URL(url);
    return parsedUrl.hostname.includes('kufar.by');
}

/**
 * Show confirmation dialog
 */
function showConfirmDialog(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

/**
 * Export data as JSON
 */
function exportAsJson(data, filename) {
    const dataStr = JSON.stringify(data, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    
    const exportFileDefaultName = filename || 'kf-searcher-export.json';
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
}

/**
 * Handle API errors consistently
 */
function handleApiError(error, defaultMessage = 'An error occurred') {
    console.error('API Error:', error);
    
    let message = defaultMessage;
    if (error.message) {
        message = error.message;
    } else if (typeof error === 'string') {
        message = error;
    }
    
    showToast(message, 'error');
}

/**
 * Make API request with error handling
 */
async function apiRequest(url, options = {}) {
    try {
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        return await response.json();
    } catch (error) {
        handleApiError(error);
        throw error;
    }
}

// Make functions globally available
window.KFSearcher = {
    showToast,
    runSearch,
    copyToClipboard,
    formatNumber,
    formatPrice,
    formatDate,
    debounce,
    isValidUrl,
    isValidKufarUrl,
    showConfirmDialog,
    exportAsJson,
    handleApiError,
    apiRequest
};
