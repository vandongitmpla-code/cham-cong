// attendance_print.js - JavaScript cho trang attendance_print - THEO LOGIC MỚI
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

    // Khởi tạo tooltip Bootstrap
    const tooltips = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltips.forEach(t => new bootstrap.Tooltip(t, {container: 'body'}));

    // Xử lý click icon điều chỉnh (+)
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('adjustment-icon')) {
            const employeeCode = e.target.getAttribute('data-employee-code');
            const employeeName = e.target.getAttribute('data-employee-name');
            const period = e.target.getAttribute('data-period');
            const originalDays = parseFloat(e.target.getAttribute('data-original-days'));
            const actualDays = parseFloat(e.target.getAttribute('data-actual-days'));
            const overtimeHours = parseFloat(e.target.getAttribute('data-overtime-hours'));
            
            console.log('Adjustment clicked:', {employeeCode, employeeName, period, originalDays, actualDays, overtimeHours});
            
            // ✅ TÍNH TOÁN THEO LOGIC MỚI - ĐƠN GIẢN
            const adjustedDays = originalDays + Math.floor(overtimeHours / 8);
            const remainingHours = overtimeHours % 8;
            const usedHours = overtimeHours - remainingHours;
            
            // Hiển thị modal
            document.getElementById('modalEmployeeName').textContent = employeeName;
            document.getElementById('modalCurrentDays').textContent = actualDays + ' ngày';
            document.getElementById('modalOvertimeHours').textContent = overtimeHours + ' giờ';
            document.getElementById('modalAdjustedDays').textContent = adjustedDays + ' ngày'; // ✅ CẢ HAI CỘT SẼ HIỂN THỊ GIÁ TRỊ NÀY
            document.getElementById('modalRemainingHours').textContent = remainingHours + ' giờ';
            
            // Điền form
            document.getElementById('formEmployeeCode').value = employeeCode;
            document.getElementById('formPeriod').value = period;
            document.getElementById('formOriginalDays').value = originalDays;
            document.getElementById('formOvertimeHours').value = overtimeHours;
            
            // Hiển thị modal
            const modal = new bootstrap.Modal(document.getElementById('adjustmentModal'));
            modal.show();
        }
    });

    // Xử lý click icon reset (-)
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('reset-icon')) {
            const employeeCode = e.target.getAttribute('data-employee-code');
            const employeeName = e.target.getAttribute('data-employee-name');
            const period = e.target.getAttribute('data-period');
            
            console.log('Reset clicked:', {employeeCode, employeeName, period});
            
            // Hiển thị modal xác nhận reset
            document.getElementById('resetEmployeeName').textContent = employeeName;
            document.getElementById('resetEmployeeCode').value = employeeCode;
            document.getElementById('resetPeriod').value = period;
            
            const resetModal = new bootstrap.Modal(document.getElementById('resetModal'));
            resetModal.show();
        }
    });

    // Xác nhận áp dụng điều chỉnh
    document.getElementById('confirmAdjustment').addEventListener('click', function() {
        console.log('Confirming adjustment...');
        document.getElementById('adjustmentForm').submit();
    });

    // Xác nhận reset
    document.getElementById('confirmReset').addEventListener('click', function() {
        console.log('Confirming reset...');
        document.getElementById('resetForm').submit();
    });

    // Xử lý ghi chú động
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

    // Xử lý xem chi tiết (nếu có)
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('btn-detail')) {
            const empData = JSON.parse(e.target.getAttribute('data-emp'));
            showDetailModal(empData);
        }
    });

    function showDetailModal(empData) {
        // Logic hiển thị modal chi tiết
        console.log('Showing detail modal:', empData);
        // ... phần code chi tiết modal của bạn
    }

    // Xử lý đóng modal chi tiết (nếu có)
    const modalClose = document.querySelector('.modal-close');
    if (modalClose) {
        modalClose.addEventListener('click', function() {
            document.getElementById('detailModal').style.display = 'none';
        });
    }
});

// Hàm tiện ích debug
function debugLog(message, data = null) {
    if (console && console.log) {
        if (data) {
            console.log(`[Attendance Print] ${message}:`, data);
        } else {
            console.log(`[Attendance Print] ${message}`);
        }
    }
}