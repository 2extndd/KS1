/* KF Searcher - Custom JavaScript */

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize sidebar toggle for mobile
    initializeSidebar();
    
    // Initialize search functionality
    initializeSearch();
    
    // Initialize form validation
    initializeFormValidation();
}

function initializeSidebar() {
    // Mobile sidebar toggle
    const sidebarToggle = document.querySelector('[data-bs-target="#sidebar"]');
    const sidebar = document.getElementById('sidebar');
    
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('show');
        });
        
        // Close sidebar when clicking outside on mobile
        document.addEventListener('click', function(event) {
            if (window.innerWidth <= 768) {
                if (!sidebar.contains(event.target) && !sidebarToggle.contains(event.target)) {
                    sidebar.classList.remove('show');
                }
            }
        });
    }
}

function initializeSearch() {
    // Test search URL functionality
    const testSearchBtn = document.getElementById('test-search-btn');
    if (testSearchBtn) {
        testSearchBtn.addEventListener('click', testSearchUrl);
    }
    
    // Run search functionality
    const runSearchBtn = document.getElementById('run-search-btn');
    if (runSearchBtn) {
        runSearchBtn.addEventListener('click', runSearch);
    }
}

function initializeFormValidation() {
    // Bootstrap form validation
    const forms = document.querySelectorAll('.needs-validation');
    Array.from(forms).forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });
}

// API Functions
function testSearchUrl() {
    const urlInput = document.getElementById('search-url');
    const testBtn = document.getElementById('test-search-btn');
    
    if (!urlInput || !urlInput.value) {
        showAlert('Please enter a search URL', 'warning');
        return;
    }
    
    // Show loading state
    const originalText = testBtn.innerHTML;
    testBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Testing...';
    testBtn.disabled = true;
    
    fetch('/api/search/test', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url: urlInput.value })
    })
    .then(response => response.json())
    .then(data => {
        if (data.valid) {
            showAlert('URL is valid! ' + (data.test_results ? 
                `Found ${data.test_results.items_found} items.` : ''), 'success');
            
            if (data.test_results && data.test_results.sample_titles) {
                const titles = data.test_results.sample_titles.join(', ');
                showAlert(`Sample items: ${titles}`, 'info');
            }
        } else {
            showAlert('URL validation failed: ' + (data.error || 'Unknown error'), 'danger');
        }
        
        if (data.test_error) {
            showAlert('Test search failed: ' + data.test_error, 'warning');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('Error testing URL: ' + error.message, 'danger');
    })
    .finally(() => {
        // Restore button state
        testBtn.innerHTML = originalText;
        testBtn.disabled = false;
    });
}

function runSearch() {
    const btn = document.querySelector('.btn[onclick="runSearch()"]');
    if (btn) {
        const originalText = btn.innerHTML;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Running...';
        btn.disabled = true;
        
        fetch('/api/search/run', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showAlert('Search completed successfully!', 'success');
                // Refresh page after 2 seconds
                setTimeout(() => {
                    window.location.reload();
                }, 2000);
            } else {
                showAlert('Search failed: ' + (data.error || 'Unknown error'), 'danger');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showAlert('Error running search: ' + error.message, 'danger');
        })
        .finally(() => {
            btn.innerHTML = originalText;
            btn.disabled = false;
        });
    }
}

function sendTestNotification() {
    fetch('/api/notifications/test', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('Test notification sent successfully!', 'success');
        } else {
            showAlert('Failed to send test notification: ' + (data.error || 'Unknown error'), 'danger');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('Error sending test notification: ' + error.message, 'danger');
    });
}

function deleteSearch(searchId) {
    if (confirm('Are you sure you want to delete this search?')) {
        fetch(`/api/search/${searchId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showAlert('Search deleted successfully!', 'success');
                // Remove the row from table
                const row = document.querySelector(`tr[data-search-id="${searchId}"]`);
                if (row) {
                    row.remove();
                }
            } else {
                showAlert('Failed to delete search: ' + (data.error || 'Unknown error'), 'danger');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showAlert('Error deleting search: ' + error.message, 'danger');
        });
    }
}

function toggleSearch(searchId, isActive) {
    fetch(`/api/search/${searchId}/toggle`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ active: !isActive })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert(`Search ${!isActive ? 'activated' : 'deactivated'} successfully!`, 'success');
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        } else {
            showAlert('Failed to toggle search: ' + (data.error || 'Unknown error'), 'danger');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('Error toggling search: ' + error.message, 'danger');
    });
}

// Utility Functions
function showAlert(message, type = 'info') {
    // Remove existing alerts
    const existingAlerts = document.querySelectorAll('.alert.auto-dismiss');
    existingAlerts.forEach(alert => alert.remove());
    
    // Create new alert
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show auto-dismiss`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Insert at the top of main content
    const mainContent = document.querySelector('.main-content');
    if (mainContent) {
        mainContent.insertBefore(alertDiv, mainContent.firstChild);
    } else {
        document.body.insertBefore(alertDiv, document.body.firstChild);
    }
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

function formatPrice(price, currency = 'BYN') {
    if (!price || price === 0) return 'Цена не указана';
    return new Intl.NumberFormat('ru-RU').format(price) + ' ' + currency;
}

function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('ru-RU') + ' ' + date.toLocaleTimeString('ru-RU', {
        hour: '2-digit',
        minute: '2-digit'
    });
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(function() {
        showAlert('Copied to clipboard!', 'success');
    }).catch(function(err) {
        console.error('Could not copy text: ', err);
        showAlert('Failed to copy to clipboard', 'danger');
    });
}

// Export functions for global use
window.testSearchUrl = testSearchUrl;
window.runSearch = runSearch;
window.sendTestNotification = sendTestNotification;
window.deleteSearch = deleteSearch;
window.toggleSearch = toggleSearch;
window.showAlert = showAlert;
window.copyToClipboard = copyToClipboard;