
// payroll-container-manager.js
class PayrollContainerManager {
    constructor() {
        this.currentSize = 'lg'; // default size
        this.container = document.querySelector('.payroll-container');
        this.init();
    }

    init() {
        this.loadSavedSize();
        this.updateContainerSize();
        this.addEventListeners();
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
        
        this.updateActiveButton();
        this.saveSize();
    }

    updateContainerSize() {
        this.setContainerSize(this.currentSize);
    }

    updateActiveButton() {
        // Remove active class from all buttons
        document.querySelectorAll('.btn-size').forEach(btn => {
            btn.classList.remove('active');
        });
        
        // Add active class to current size button
        const activeBtn = document.querySelector(`.btn-size[data-size="${this.currentSize}"]`);
        if (activeBtn) {
            activeBtn.classList.add('active');
        }
    }

    saveSize() {
        localStorage.setItem('payrollContainerSize', this.currentSize);
    }

    loadSavedSize() {
        const savedSize = localStorage.getItem('payrollContainerSize');
        if (savedSize) {
            this.currentSize = savedSize;
        }
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
