// static/js/notification-system.js

class NotificationSystem {
    constructor() {
        this.container = null;
        this.init();
    }

    init() {
        this.createContainer();
        this.injectStyles();
    }

    createContainer() {
        // Tạo container nếu chưa có
        if (!document.getElementById('notification-container')) {
            const container = document.createElement('div');
            container.id = 'notification-container';
            document.body.appendChild(container);
        }
        this.container = document.getElementById('notification-container');
    }

    injectStyles() {
        // Đảm bảo CSS đã được load, nếu chưa thì inject inline styles cơ bản
        if (!document.querySelector('link[href*="notification-system.css"]')) {
            const basicStyles = `
                #notification-container {
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    z-index: 9999;
                    max-width: 400px;
                }
                .notification {
                    background: white;
                    border-radius: 8px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                    padding: 16px;
                    margin-bottom: 10px;
                    transform: translateX(400px);
                    opacity: 0;
                    transition: all 0.3s ease;
                }
                .notification.show {
                    transform: translateX(0);
                    opacity: 1;
                }
            `;
            const style = document.createElement('style');
            style.textContent = basicStyles;
            document.head.appendChild(style);
        }
    }

    show(options = {}) {
        const {
            type = 'info', // success, error, warning, info
            title = '',
            message = '',
            duration = 5000, // milliseconds (0 = không tự đóng)
            position = 'top-right' // top-right, top-left, bottom-right, bottom-left
        } = options;

        const notification = this.createNotification(type, title, message, duration);
        this.setContainerPosition(position);
        this.container.appendChild(notification);

        // Hiệu ứng xuất hiện
        setTimeout(() => {
            notification.classList.add('show');
        }, 10);

        // Tự động đóng nếu có duration
        if (duration > 0) {
            this.autoClose(notification, duration);
        }

        return notification;
    }

    createNotification(type, title, message, duration) {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        
        const icons = {
            success: 'bi-check-circle-fill',
            error: 'bi-x-circle-fill',
            warning: 'bi-exclamation-triangle-fill',
            info: 'bi-info-circle-fill'
        };

        const closeButton = duration === 0 ? `
            <button class="notification-close" onclick="notificationSystem.close(this.parentElement)">
                <i class="bi bi-x"></i>
            </button>
        ` : '';

        notification.innerHTML = `
            <div class="notification-content">
                <div class="notification-icon">
                    <i class="bi ${icons[type]}"></i>
                </div>
                <div class="notification-text">
                    ${title ? `<div class="notification-title">${title}</div>` : ''}
                    <div class="notification-message">${message}</div>
                </div>
                ${closeButton}
            </div>
            ${duration > 0 ? `<div class="notification-progress"><div class="notification-progress-bar"></div></div>` : ''}
        `;

        return notification;
    }

    setContainerPosition(position) {
        const positions = {
            'top-right': 'top: 20px; right: 20px; left: auto; bottom: auto;',
            'top-left': 'top: 20px; left: 20px; right: auto; bottom: auto;',
            'bottom-right': 'bottom: 20px; right: 20px; top: auto; left: auto;',
            'bottom-left': 'bottom: 20px; left: 20px; top: auto; right: auto;'
        };
        
        this.container.style.cssText = `
            position: fixed;
            z-index: 9999;
            max-width: 400px;
            ${positions[position] || positions['top-right']}
        `;
    }

    autoClose(notification, duration) {
        const progressBar = notification.querySelector('.notification-progress-bar');
        if (progressBar) {
            progressBar.style.transition = `transform ${duration}ms linear`;
            setTimeout(() => {
                progressBar.style.transform = 'scaleX(0)';
            }, 10);
        }

        setTimeout(() => {
            this.close(notification);
        }, duration);
    }

    close(notification) {
        notification.classList.remove('show');
        notification.classList.add('hide');
        
        setTimeout(() => {
            if (notification.parentElement) {
                notification.parentElement.removeChild(notification);
            }
        }, 300);
    }

    closeAll() {
        const notifications = this.container.querySelectorAll('.notification');
        notifications.forEach(notification => {
            this.close(notification);
        });
    }

    // Phương thức tiện ích
    success(message, title = 'Thành công', duration = 5000) {
        return this.show({ type: 'success', title, message, duration });
    }

    error(message, title = 'Lỗi', duration = 5000) {
        return this.show({ type: 'error', title, message, duration });
    }

    warning(message, title = 'Cảnh báo', duration = 5000) {
        return this.show({ type: 'warning', title, message, duration });
    }

    info(message, title = 'Thông tin', duration = 5000) {
        return this.show({ type: 'info', title, message, duration });
    }
}

// Khởi tạo instance toàn cục
const notificationSystem = new NotificationSystem();

// Export cho module system
if (typeof module !== 'undefined' && module.exports) {
    module.exports = notificationSystem;
}