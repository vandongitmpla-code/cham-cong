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
        
        this.applyFullscreenOptimizations();
        this.updateActiveButton();
        this.saveSettings();
        
        // Force table redraw for better rendering
        this.forceTableRedraw();
    }

    applyFullscreenOptimizations() {
        if (this.currentSize === 'full') {
            this.optimizeForFullscreen();
        } else {
            this.disableCompactMode();
        }
    }

    optimizeForFullscreen() {
        // Apply fullscreen-specific optimizations
        document.body.style.overflow = 'hidden';
        document.documentElement.style.overflow = 'hidden';
        
        // Auto compact mode based on screen height
        if (window.innerHeight < 800) {
            this.enableCompactMode();
        } else {
            this.disableCompactMode();
        }
        
        // Ensure table uses full width
        this.optimizeTableForFullscreen();
    }

    optimizeTableForFullscreen() {
        const tableContainer = this.container.querySelector('.payroll-table-container');
        const table = this.container.querySelector('.payroll-table');
        
        if (tableContainer && table) {
            tableContainer.style.width = '100%';
            table.style.minWidth = '100%';
            
            // Force browser to recalculate layout
            setTimeout(() => {
                tableContainer.style.overflow = 'auto';
            }, 100);
        }
    }

    enableCompactMode() {
        this.compactMode = true;
        this.container.classList.add('compact');
        
        // Hide non-essential elements
        const subtitle = this.container.querySelector('.payroll-subtitle');
        const holidaysSection = this.container.querySelector('.holidays-section');
        const containerControls = this.container.querySelector('.container-controls');
        
        if (subtitle) subtitle.style.display = 'none';
        if (holidaysSection) holidaysSection.style.display = 'none';
        if (containerControls) containerControls.style.display = 'none';
        
        console.log('Compact mode enabled');
    }

    disableCompactMode() {
        this.compactMode = false;
        this.container.classList.remove('compact');
        
        // Show hidden elements
        const subtitle = this.container.querySelector('.payroll-subtitle');
        const holidaysSection = this.container.querySelector('.holidays-section');
        const containerControls = this.container.querySelector('.container-controls');
        
        if (subtitle) subtitle.style.display = 'block';
        if (holidaysSection) holidaysSection.style.display = 'block';
        if (containerControls) containerControls.style.display = 'flex';
    }

    toggleCompactMode() {
        if (this.compactMode) {
            this.disableCompactMode();
        } else {
            this.enableCompactMode();
        }
        this.saveSettings();
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
        
        // Update compact button
        const compactBtn = document.getElementById('toggleCompact');
        if (compactBtn) {
            if (this.compactMode) {
                compactBtn.classList.add('active');
                compactBtn.textContent = 'Bật thường';
            } else {
                compactBtn.classList.remove('active');
                compactBtn.textContent = 'Chế độ compact';
            }
        }
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

        // Compact mode button
        const compactBtn = document.getElementById('toggleCompact');
        if (compactBtn) {
            compactBtn.addEventListener('click', () => {
                this.toggleCompactMode();
            });
        }

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
                    case 'c': case 'C': this.toggleCompactMode(); break;
                }
            }
            
            // Escape key to exit fullscreen
            if (e.key === 'Escape' && this.currentSize === 'full') {
                this.setContainerSize('lg');
            }
        });

        // Window resize handling
        window.addEventListener('resize', () => {
            this.handleResize();
        });

        // Handle page visibility changes
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden && this.currentSize === 'full') {
                this.forceTableRedraw();
            }
        });
    }

    handleResize() {
        // Auto-adjust for mobile screens
        if (window.innerWidth < 768) {
            if (this.currentSize !== 'full') {
                this.setContainerSize('full');
            }
        }
        
        // Re-optimize fullscreen on resize
        if (this.currentSize === 'full') {
            this.optimizeForFullscreen();
        }
    }

    forceTableRedraw() {
        // Force browser to redraw the table for better rendering
        const table = this.container.querySelector('.payroll-table');
        if (table) {
            table.style.display = 'none';
            setTimeout(() => {
                table.style.display = 'table';
            }, 50);
        }
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
                scrollHeight: tableContainer.scrollHeight
            } : null,
            table: table ? {
                width: table.clientWidth,
                scrollWidth: table.scrollWidth
            } : null,
            size: this.currentSize,
            compact: this.compactMode
        };
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Wait a bit for all elements to be fully rendered
    setTimeout(() => {
        window.payrollContainerManager = new PayrollContainerManager();
        
        // Debug info
        console.log('Payroll Container Manager initialized');
        console.log('Container info:', window.payrollContainerManager.getContainerInfo());
        
        // Auto-fullscreen on very wide screens
        if (window.innerWidth > 1920) {
            window.payrollContainerManager.setContainerSize('full');
        }
    }, 100);
});

// Handle page load issues
window.addEventListener('load', () => {
    if (window.payrollContainerManager) {
        window.payrollContainerManager.forceTableRedraw();
    }
});

// Thêm method này vào class PayrollContainerManager
forceScrollableTable() {
    const tableContainer = this.container.querySelector('.payroll-table-container');
    const table = this.container.querySelector('.payroll-table');
    
    if (tableContainer && table) {
        // Đảm bảo container có overflow
        tableContainer.style.overflow = 'auto';
        tableContainer.style.overflowX = 'auto';
        tableContainer.style.overflowY = 'auto';
        
        // Đảm bảo bảng đủ rộng
        table.style.width = 'max-content';
        table.style.minWidth = '100%';
        
        console.log('Scroll forced for table container');
    }
}

// Trong method setContainerSize, thêm dòng này:
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
    
    // QUAN TRỌNG: Đảm bảo scroll hoạt động
    setTimeout(() => {
        this.forceScrollableTable();
    }, 100);
}
