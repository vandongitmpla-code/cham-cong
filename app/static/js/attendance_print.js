// attendance_print.js - JavaScript cho trang attendance_print
document.addEventListener("DOMContentLoaded", function(){
    // Khởi tạo timesheet data
    (function(){
        try {
            const el = document.getElementById('timesheet-data');
            const raw = el ? el.textContent.trim() : null;
            if (!raw) {
                window.__TIMESHEET__ = { weekdays: {}, day_count: 31 };
                return;
            }
            const cfg = JSON.parse(raw);
            cfg.weekdays = cfg.weekdays || {};
            cfg.day_count = Number(cfg.day_count) || 31;
            window.__TIMESHEET__ = cfg;
        } catch (err) {
            console.error("Error parsing timesheet config:", err);
            window.__TIMESHEET__ = { weekdays: {}, day_count: 31 };
        }
    })();

    // Tooltip
    const tooltips = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltips.forEach(t => new bootstrap.Tooltip(t, {container: 'body'}));

    // Xử lý click icon điều chỉnh
    document.querySelectorAll('.adjustment-icon').forEach(icon => {
        icon.addEventListener('click', function() {
            const employeeCode = this.getAttribute('data-employee-code');
            const employeeName = this.getAttribute('data-employee-name');
            const period = this.getAttribute('data-period');
            const originalDays = parseFloat(this.getAttribute('data-original-days'));
            const actualDays = parseFloat(this.getAttribute('data-actual-days'));
            const overtimeHours = parseFloat(this.getAttribute('data-overtime-hours'));
            
            console.log('Adjustment clicked:', {employeeCode, employeeName, period, originalDays, actualDays, overtimeHours});
            
            // Tính toán dự kiến
            const daysNeeded = originalDays - actualDays;
            const hoursNeeded = daysNeeded > 0 ? daysNeeded * 8 : 0;
            const adjustedDays = daysNeeded > 0 ? 
                (overtimeHours >= hoursNeeded ? originalDays : actualDays + Math.floor(overtimeHours / 8)) : 
                actualDays;
            const remainingHours = daysNeeded > 0 ? 
                (overtimeHours >= hoursNeeded ? overtimeHours - hoursNeeded : overtimeHours % 8) : 
                overtimeHours;
            
            // Hiển thị modal
            document.getElementById('modalEmployeeName').textContent = employeeName;
            document.getElementById('modalCurrentDays').textContent = actualDays + ' ngày';
            document.getElementById('modalOvertimeHours').textContent = overtimeHours + ' giờ';
            document.getElementById('modalAdjustedDays').textContent = adjustedDays + ' ngày';
            document.getElementById('modalRemainingHours').textContent = remainingHours + ' giờ';
            
            // Điền form
            document.getElementById('formEmployeeCode').value = employeeCode;
            document.getElementById('formPeriod').value = period;
            document.getElementById('formOriginalDays').value = originalDays;
            document.getElementById('formOvertimeHours').value = overtimeHours;
            
            // Hiển thị modal
            const modal = new bootstrap.Modal(document.getElementById('adjustmentModal'));
            modal.show();
        });
    });

    // Xác nhận áp dụng điều chỉnh
    document.getElementById('confirmAdjustment').addEventListener('click', function() {
        document.getElementById('adjustmentForm').submit();
    });

    // Ghi chú động
    document.querySelectorAll(".note-cell").forEach(cell => {
        const icon = cell.querySelector(".note-icon");
        const input = cell.querySelector(".note-input");

        if(icon){
            icon.addEventListener("click", () => {
                const span = cell.querySelector("span.note-text");
                if(span){
                    input.value = span.textContent.trim();
                    span.remove();
                }
                icon.classList.add("d-none");
                input.classList.remove("d-none");
                input.focus();
            });

            input.addEventListener("blur", () => {
                let value = input.value.trim();
                if(value !== ""){
                    input.classList.add("d-none");
                    icon.classList.remove("d-none");
                    let span = document.createElement("span");
                    span.classList.add("note-text");
                    span.textContent = value;
                    cell.insertBefore(span, icon);
                }else{
                    input.classList.add("d-none");
                    icon.classList.remove("d-none");
                }
            });

            input.addEventListener("keypress", e => {
                if(e.key === "Enter"){ input.blur(); }
            });

            cell.addEventListener("mouseenter", () => { icon.classList.remove("d-none"); });
            cell.addEventListener("mouseleave", () => {
                if(input.value.trim() !== ""){ icon.classList.add("d-none"); }
            });
        }
    });
});

// Xử lý nút reset (-)
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('reset-icon')) {
        const employeeCode = e.target.getAttribute('data-employee-code');
        const employeeName = e.target.getAttribute('data-employee-name');
        const period = e.target.getAttribute('data-period');
        
        // Hiển thị modal xác nhận reset
        document.getElementById('resetEmployeeName').textContent = employeeName;
        document.getElementById('resetEmployeeCode').value = employeeCode;
        document.getElementById('resetPeriod').value = period;
        
        const resetModal = new bootstrap.Modal(document.getElementById('resetModal'));
        resetModal.show();
    }
});

// Xác nhận reset
document.getElementById('confirmReset').addEventListener('click', function() {
    document.getElementById('resetForm').submit();
});

// Logic tính toán điều chỉnh (giữ nguyên)
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('adjustment-icon')) {
        const employeeCode = e.target.getAttribute('data-employee-code');
        const employeeName = e.target.getAttribute('data-employee-name');
        const period = e.target.getAttribute('data-period');
        const originalDays = parseFloat(e.target.getAttribute('data-original-days'));
        const overtimeHours = parseFloat(e.target.getAttribute('data-overtime-hours'));
        
        // Tính toán điều chỉnh
        const standardDays = 22; // Có thể lấy từ server nếu cần
        const ngayThieu = standardDays - originalDays;
        
        let adjustedDays, remainingHours;
        
        if (ngayThieu <= 0) {
            adjustedDays = originalDays;
            remainingHours = overtimeHours;
        } else {
            const gioCanBu = ngayThieu * 8;
            if (overtimeHours >= gioCanBu) {
                adjustedDays = standardDays;
                remainingHours = overtimeHours - gioCanBu;
            } else {
                const ngayDuocBu = Math.floor(overtimeHours / 8);
                adjustedDays = originalDays + ngayDuocBu;
                remainingHours = 0;
            }
        }
        
        // Hiển thị modal
        document.getElementById('modalEmployeeName').textContent = employeeName;
        document.getElementById('modalCurrentDays').textContent = originalDays + ' ngày';
        document.getElementById('modalOvertimeHours').textContent = overtimeHours + ' giờ';
        document.getElementById('modalAdjustedDays').textContent = adjustedDays + ' ngày';
        document.getElementById('modalRemainingHours').textContent = remainingHours + ' giờ';
        
        // Điền form
        document.getElementById('formEmployeeCode').value = employeeCode;
        document.getElementById('formPeriod').value = period;
        document.getElementById('formOriginalDays').value = originalDays;
        document.getElementById('formOvertimeHours').value = overtimeHours;
        
        const adjustmentModal = new bootstrap.Modal(document.getElementById('adjustmentModal'));
        adjustmentModal.show();
    }
});

// Xác nhận điều chỉnh
document.getElementById('confirmAdjustment').addEventListener('click', function() {
    document.getElementById('adjustmentForm').submit();
});

// ... phần code còn lại giữ nguyên