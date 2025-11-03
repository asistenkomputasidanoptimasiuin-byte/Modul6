// Manufacturing System Global Functions

// Initialize tooltips
document.addEventListener('DOMContentLoaded', function() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});

// Format numbers with thousands separator
function formatNumber(num) {
    return new Intl.NumberFormat('id-ID').format(num);
}

// Calculate OEE components
function calculateOEEComponents(availability, performance, quality) {
    return {
        availability: availability,
        performance: performance,
        quality: quality,
        oee: (availability * performance * quality) / 10000
    };
}

// Show notification
function showNotification(message, type = 'info') {
    const alertClass = {
        'success': 'alert-success',
        'error': 'alert-danger',
        'warning': 'alert-warning',
        'info': 'alert-info'
    }[type] || 'alert-info';

    const notification = document.createElement('div');
    notification.className = `alert ${alertClass} alert-dismissible fade show`;
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    // Add to page
    const container = document.querySelector('.container');
    container.insertBefore(notification, container.firstChild);

    // Auto remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

// Validate form inputs
function validateForm(formId) {
    const form = document.getElementById(formId);
    const inputs = form.querySelectorAll('input[required], select[required]');
    let isValid = true;

    inputs.forEach(input => {
        if (!input.value.trim()) {
            input.classList.add('is-invalid');
            isValid = false;
        } else {
            input.classList.remove('is-invalid');
        }
    });

    return isValid;
}

// Export data to CSV
function exportToCSV(data, filename) {
    const csvContent = "data:text/csv;charset=utf-8," 
        + data.map(row => row.join(",")).join("\n");
    
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", filename);
    document.body.appendChild(link);
    
    link.click();
    document.body.removeChild(link);
}

// Date formatting utilities
function formatDate(date) {
    return new Date(date).toLocaleDateString('id-ID', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit'
    });
}

function getCurrentDate() {
    return new Date().toISOString().split('T')[0];
}

// Inventory management helpers
function checkLowStock(inventory) {
    const alerts = [];
    
    inventory.raw_materials.forEach(material => {
        if (material.stock < material.min_stock) {
            alerts.push(`${material.name} stock rendah: ${material.stock} ${material.unit}`);
        }
    });
    
    inventory.finished_products.forEach(product => {
        if (product.stock < product.min_stock) {
            alerts.push(`${product.name} stock rendah: ${product.stock} ${product.unit}`);
        }
    });
    
    return alerts;
}

// Production analytics
function calculateProductionYield(quantity, defects) {
    if (quantity === 0) return 0;
    return ((quantity - defects) / quantity * 100).toFixed(1);
}

function getYieldBadgeClass(yieldPercent) {
    if (yieldPercent >= 95) return 'bg-success';
    if (yieldPercent >= 90) return 'bg-warning';
    return 'bg-danger';
}

// Machine status management
function getMachineStatusBadge(status) {
    const statusMap = {
        'running': { class: 'bg-success', text: 'Berjalan' },
        'maintenance': { class: 'bg-warning', text: 'Maintenance' },
        'stopped': { class: 'bg-danger', text: 'Berhenti' }
    };
    
    return statusMap[status] || { class: 'bg-secondary', text: 'Tidak Diketahui' };
}

// OEE assessment
function getOEEAssessment(oeePercent) {
    if (oeePercent >= 85) return { class: 'bg-success', level: 'Excellent' };
    if (oeePercent >= 70) return { class: 'bg-warning', level: 'Good' };
    if (oeePercent >= 50) return { class: 'bg-info', level: 'Fair' };
    return { class: 'bg-danger', level: 'Poor' };
}