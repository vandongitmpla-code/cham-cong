// notifications_system.js - Hệ thống quản lý thông báo chuyên nghiệp

class NotificationSystem {
    constructor() {
        this.container = null;
        this.defaultOptions = {
            autoDismiss: true,
            dismissTime: 5000,
            icon: true,
            position: 'top-right',
            animation: 'slideInDown'
        };
        this.init();
    }

    init() {
        this.createContainer();
        this.setupGlobalStyles();
        console.log('🎯 Notification System initialized');
    }

    createContainer() {
        // Kiểm tra nếu container đã tồn tại
        if (document.querySelector('.notification-container')) {
            this.container = document.querySelector('.notification-container');
            return;
        }

        const container = document.createElement('div');
        container.className = 'notification-container';
        container.setAttribute('aria-live', 'polite');
        container.setAttribute('aria-atomic', 'true');
        document.body.appendChild(container);
        this.container = container;
    }

    setupGlobalStyles() {
        // Đảm bảo CSS đã được load
        if (!document.querySelector('link[href*="notifications_system.css"]')) {
            console.warn('⚠️ notifications_system.css chưa được load');
        }
    }

    show(message, type = 'success', options = {}) {
        const config = { ...this.defaultOptions, ...options };
        const alertId = 'notification-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
        
        const iconClass = this.getIconClass(type);
        const iconHtml = config.icon ? `<i class="bi ${iconClass} custom-alert-icon"></i>` : '';

        const alertHtml = `
            <div id="${alertId}" 
                 class="custom-alert custom-alert-${type} alert-dismissible fade show ${config.autoDismiss ? 'auto-dismiss' : ''} floating-notification" 
                 role="alert" 
                 aria-live="assertive"
                 aria-atomic="true">
                <div class="custom-alert-content">
                    ${iconHtml}
                    <div class="custom-alert-message">${message}</div>
                </div>
                <button type="button" 
                        class="btn-close" 
                        data-bs-dismiss="alert" 
                        aria-label="Đóng"
                        onclick="notificationSystem.remove('${alertId}')">
                </button>
            </div>
        `;

        this.container.insertAdjacentHTML('afterbegin', alertHtml);

        // Tự động ẩn
        if (config.autoDismiss) {
            this.autoDismiss(alertId, config.dismissTime);
        }

        // Log for debugging
        console.log(`🔔 Notification [${type}]: ${message}`);

        return alertId;
    }

    autoDismiss(alertId, dismissTime) {
        setTimeout(() => {
            this.remove(alertId);
        }, dismissTime);
    }

    remove(alertId) {
        const alert = document.getElementById(alertId);
        if (alert) {
            alert.classList.add('fade-out');
            setTimeout(() => {
                if (alert.parentNode) {
                    alert.parentNode.removeChild(alert);
                    console.log(`🗑️ Notification removed: ${alertId}`);
                }
            }, 300);
        }
    }

    clearAll() {
        const alerts = this.container.querySelectorAll('.custom-alert');
        if (alerts.length === 0) {
            console.log('📭 No notifications to clear');
            return;
        }

        alerts.forEach(alert => {
            alert.classList.add('fade-out');
            setTimeout(() => {
                if (alert.parentNode) {
                    alert.parentNode.removeChild(alert);
                }
            }, 300);
        });
        
        console.log(`🧹 Cleared ${alerts.length} notifications`);
    }

    getIconClass(type) {
        const icons = {
            'success': 'bi-check-circle-fill',
            'error': 'bi-exclamation-triangle-fill',
            'warning': 'bi-exclamation-triangle-fill',
            'info': 'bi-info-circle-fill',
            'primary': 'bi-bell-fill'
        };
        return icons[type] || 'bi-info-circle-fill';
    }

    // ====== PHƯƠNG THỨC TIỆN ÍCH NHANH ======
    success(message, options = {}) {
        return this.show(message, 'success', options);
    }

    error(message, options = {}) {
        return this.show(message, 'error', options);
    }

    warning(message, options = {}) {
        return this.show(message, 'warning', options);
    }

    info(message, options = {}) {
        return this.show(message, 'info', options);
    }

    primary(message, options = {}) {
        return this.show(message, 'primary', options);
    }

    // ====== PHƯƠNG THỨC ĐẶC BIỆT ======
    loading(message = 'Đang xử lý...', options = {}) {
        return this.show(`<div class="spinner-border spinner-border-sm me-2" role="status"></div> ${message}`, 'info', {
            autoDismiss: false,
            icon: false,
            ...options
        });
    }

    removeLoading(alertId) {
        this.remove(alertId);
    }

    // ====== FLASH MESSAGE SUPPORT ======
showFlashMessages() {
    // CHỈ hiển thị flash messages thực sự từ Flask, không hiển thị phần giải thích công thức
    const flashMessages = document.querySelectorAll('.alert:not(.alert-info):not(.alert-light)');
    
    flashMessages.forEach(alert => {
        // Kiểm tra không phải là phần giải thích công thức
        const isFormulaExplanation = alert.closest('.print-container') || 
                                   alert.textContent.includes('công thức') ||
                                   alert.textContent.includes('Ngày công thực tế') ||
                                   alert.textContent.includes('Ngày nghỉ cuối') ||
                                   alert.textContent.includes('Giới hạn');
        
        if (!isFormulaExplanation) {
            const type = this.detectFlashType(alert);
            const message = alert.textContent.trim();
            this.show(message, type);
            alert.remove(); // Xóa flash message gốc
        }
    });
}

// ====== GLOBAL INSTANCE & HELPERS ======
window.notificationSystem = new NotificationSystem();

// Global helper functions
window.showSuccess = (message, options) => notificationSystem.success(message, options);
window.showError = (message, options) => notificationSystem.error(message, options);
window.showWarning = (message, options) => notificationSystem.warning(message, options);
window.showInfo = (message, options) => notificationSystem.info(message, options);
window.showLoading = (message, options) => notificationSystem.loading(message, options);
window.hideLoading = (alertId) => notificationSystem.removeLoading(alertId);
window.clearNotifications = () => notificationSystem.clearAll();

// Auto-initialize khi DOM ready
document.addEventListener('DOMContentLoaded', function() {
    // Hiển thị flash messages nếu có
    notificationSystem.showFlashMessages();
    
    // Global error handler
    window.addEventListener('error', function(e) {
        notificationSystem.error('Có lỗi xảy ra trong ứng dụng!');
    });
});

// Export cho module system (nếu cần)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = NotificationSystem;
}