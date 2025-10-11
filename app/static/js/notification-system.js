// notifications.js - Hệ thống quản lý thông báo

class NotificationSystem {
    constructor() {
        this.container = null;
        this.init();
    }

    init() {
        // Tạo container nếu chưa có
        if (!document.querySelector('.notification-container')) {
            this.createContainer();
        }
        this.container = document.querySelector('.notification-container');
    }

    createContainer() {
        const container = document.createElement('div');
        container.className = 'notification-container';
        document.body.appendChild(container);
    }

    show(message, type = 'success', options = {}) {
        const {
            autoDismiss = true,
            dismissTime = 5000,
            icon = true,
            position = 'top-right'
        } = options;

        const alertId = 'alert-' + Date.now();
        const iconClass = this.getIconClass(type);
        const iconHtml = icon ? `<i class="bi ${iconClass} custom-alert-icon"></i>` : '';

        const alertHtml = `
            <div id="${alertId}" class="custom-alert custom-alert-${type} alert-dismissible fade show ${autoDismiss ? 'auto-dismiss' : ''}" role="alert">
                <div class="custom-alert-content">
                    ${iconHtml}
                    <div class="custom-alert-message">${message}</div>
                </div>
                <button type="button" class="btn-close" data-bs-dismiss="alert" onclick="notificationSystem.remove('${alertId}')"></button>
            </div>
        `;

        this.container.insertAdjacentHTML('afterbegin', alertHtml);

        // Tự động ẩn
        if (autoDismiss) {
            setTimeout(() => {
                this.remove(alertId);
            }, dismissTime);
        }

        return alertId;
    }

    remove(alertId) {
        const alert = document.getElementById(alertId);
        if (alert) {
            alert.classList.add('fade-out');
            setTimeout(() => {
                if (alert.parentNode) {
                    alert.parentNode.removeChild(alert);
                }
            }, 300);
        }
    }

    clearAll() {
        const alerts = this.container.querySelectorAll('.custom-alert');
        alerts.forEach(alert => {
            alert.classList.add('fade-out');
            setTimeout(() => {
                if (alert.parentNode) {
                    alert.parentNode.removeChild(alert);
                }
            }, 300);
        });
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

    // Phương thức tiện ích nhanh
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
}

// Khởi tạo global instance
window.notificationSystem = new NotificationSystem();

// Helper functions để sử dụng trực tiếp
window.showSuccess = (message, options) => notificationSystem.success(message, options);
window.showError = (message, options) => notificationSystem.error(message, options);
window.showWarning = (message, options) => notificationSystem.warning(message, options);
window.showInfo = (message, options) => notificationSystem.info(message, options);