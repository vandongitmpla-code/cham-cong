
// payroll-container-manager.js
class PayrollContainerManager {
    constructor() {
        this.currentSize = 'lg';
        this.compactMode = false;
        this.container = document.querySelector('.payroll-container');
        this.init();
    }

    init() {
        this.loadSavedSettings();
        this.updateContainerSize();
        this.addEventListeners();
        this.applyFullscreenOptimizations();
    }

    setContainerSize(size) {
        this.currentSize = size;
        
        // Remove all size classes
        this.container.classList.remove(
            'payroll-container-sm',
            'payroll-container-md', 
            'payroll-container-lg',
            'payroll-container-xl',
            'payroll-container-full'
        );
        
        // Add new size class
        this.container.classList.add(`payroll-container-${size}`);
        
        this.applyFullscreenOptimizations();
        this.updateActiveButton();
        this.saveSettings();
    }

    applyFullscreenOptimizations() {
        if (this.currentSize === 'full') {
            // Tự động áp dụng các tối ưu cho fullscreen
            this.optimizeForFullscreen();
        } else {
            // Khôi phục về bình thường
            this.container.classList.remove('compact');
        }
    }

    optimizeForFullscreen() {
        // Tự động bật compact mode nếu màn hình không đủ cao
        if (window.innerHeight < 800) {
            this.enableCompactMode();
        } else {
            this.disableCompactMode();
        }
    }

    enableCompactMode() {
        this.compactMode = true;
        this.container.classList.add('compact');
        
        // Ẩn các phần không cần thiết
        const subtitle = this.container.querySelector('.payroll-subtitle');
        if (subtitle) subtitle.style.display = 'none';
        
        console.log('Compact mode enabled for better fullscreen experience');
    }

    disableCompactMode() {
        this.compactMode = false;
        this.container.classList.remove('compact');
        
        // Hiện lại các phần đã ẩn
        const subtitle = this.container.querySelector('.payroll-subtitle');
        if (subtitle) subtitle.style.display = 'block';
    }

    toggleCompactMode() {
        if (this.compactMode) {
            this.disableCompactMode();
        } else {
            this.enableCompactMode();
        }
        this.saveSettings();
    }

    saveSettings() {
        localStorage.setItem('payrollContainerSize', this.currentSize);
        localStorage.setItem('payrollCompactMode', this.compactMode);
    }

    loadSavedSettings() {
        const savedSize = localStorage.getItem('payrollContainerSize');
        const savedCompact = localStorage.getItem('payrollCompactMode');
        
        if (savedSize) this.currentSize = savedSize;
        if (savedCompact === 'true') this.compactMode = true;
    }

    addEventListeners() {
        // Size button clicks
        document.querySelectorAll('.btn-size').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const size = e.target.getAttribute('data-size');
                this.setContainerSize(size);
            });
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.altKey) {
                switch(e.key) {
                    case '1': this.setContainerSize('sm'); break;
                    case '2': this.setContainerSize('md'); break;
                    case '3': this.setContainerSize('lg'); break;
                    case '4': this.setContainerSize('xl'); break;
                    case '5': this.setContainerSize('full'); break;
                }
            }
        });

        // Window resize handling
        window.addEventListener('resize', () => {
            this.handleResize();
        });
    }

    handleResize() {
        // Auto-adjust size on very small screens
        if (window.innerWidth < 768) {
            this.container.classList.add('payroll-container-full');
        }
    }

    // Method to get current container dimensions
    getContainerInfo() {
        const rect = this.container.getBoundingClientRect();
        return {
            width: rect.width,
            height: rect.height,
            size: this.currentSize
        };
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.payrollContainerManager = new PayrollContainerManager();
    
    // Debug info (có thể xóa sau)
    console.log('Payroll Container Manager initialized');
    console.log('Container info:', window.payrollContainerManager.getContainerInfo());
});
