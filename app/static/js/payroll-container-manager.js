// payroll-container-manager.js - Simplified for beautiful container
class PayrollContainerManager {
    constructor() {
        this.currentSize = 'lg';
        this.container = document.querySelector('.payroll-container');
        this.init();
    }

    init() {
        this.loadSavedSize();
        this.updateContainerSize();
        this.addEventListeners();
        this.ensureTableScroll(); // Đảm bảo bảng có scroll
    }

    updateContainerSize() {
        this.setContainerSize(this.currentSize);
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
        this.ensureTableScroll(); // Đảm bảo scroll hoạt động sau khi thay đổi kích thước
    }

    ensureTableScroll() {
        const tableContainer = this.container.querySelector('.payroll-table-container');
        const table = this.container.querySelector('.payroll-table');
        
        if (tableContainer && table) {
            // Đảm bảo container có scroll
            tableContainer.style.overflow = 'auto';
            tableContainer.style.overflowX = 'auto';
            tableContainer.style.overflowY = 'auto';
            
            // Đảm bảo bảng đủ rộng
            table.style.width = 'max-content';
            table.style.minWidth = '100%';
            
            console.log('Table scroll ensured for size:', this.currentSize);
        }
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
                e.preventDefault();
                switch(e.key) {
                    case '1': this.setContainerSize('sm'); break;
                    case '2': this.setContainerSize('md'); break;
                    case '3': this.setContainerSize('lg'); break;
                    case '4': this.setContainerSize('xl'); break;
                    case '5': this.setContainerSize('full'); break;
                }
            }
        });

        // Ensure scroll works on window resize
        window.addEventListener('resize', () => {
            setTimeout(() => {
                this.ensureTableScroll();
            }, 100);
        });
    }

    // Method to get current container dimensions
    getContainerInfo() {
        if (!this.container) return null;
        
        const rect = this.container.getBoundingClientRect();
        const tableContainer = this.container.querySelector('.payroll-table-container');
        const table = this.container.querySelector('.payroll-table');
        
        return {
            container: {
                width: rect.width,
                height: rect.height
            },
            tableContainer: tableContainer ? {
                width: tableContainer.clientWidth,
                height: tableContainer.clientHeight,
                scrollWidth: tableContainer.scrollWidth,
                scrollHeight: tableContainer.scrollHeight,
                hasScroll: tableContainer.scrollWidth > tableContainer.clientWidth || 
                          tableContainer.scrollHeight > tableContainer.clientHeight
            } : null,
            table: table ? {
                width: table.clientWidth,
                scrollWidth: table.scrollWidth
            } : null,
            size: this.currentSize
        };
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.payrollContainerManager = new PayrollContainerManager();
    
    // Debug info
    console.log('Payroll Container Manager initialized');
    console.log('Container info:', window.payrollContainerManager.getContainerInfo());
});

// Handle page load to ensure scroll works
window.addEventListener('load', () => {
    if (window.payrollContainerManager) {
        // Force scroll check after everything is loaded
        setTimeout(() => {
            window.payrollContainerManager.ensureTableScroll();
            console.log('Scroll check after page load:', window.payrollContainerManager.getContainerInfo());
        }, 500);
    }
});