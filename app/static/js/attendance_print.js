// attendance_print.js - JavaScript cho trang attendance_print - CÔNG THỨC MỚI
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

    // ✅ HÀM HIỂN THỊ/ẨN NÚT ĐIỀU CHỈNH KHI HOVER
    function showAdjustmentButtons(cell) {
        const buttons = cell.querySelector('.adjustment-buttons');
        if (buttons) {
            buttons.style.display = 'block';
        }
    }

    function hideAdjustmentButtons(cell) {
        const buttons = cell.querySelector('.adjustment-buttons');
        if (buttons) {
            buttons.style.display = 'none';
        }
    }

    // ✅ KHỞI TẠO SỰ KIỆN HOVER CHO TẤT CẢ CÁC Ô CÓ THỂ ĐIỀU CHỈNH
    const adjustableCells = document.querySelectorAll('.adjustable-cell');
    adjustableCells.forEach(cell => {
        cell.addEventListener('mouseenter', function() {
            showAdjustmentButtons(this);
        });
        
        cell.addEventListener('mouseleave', function() {
            hideAdjustmentButtons(this);
        });
    });

    // Khởi tạo tooltip Bootstrap
    const tooltips = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltips.forEach(t => new bootstrap.Tooltip(t, {container: 'body'}));

    // Trong phần xử lý click icon điều chỉnh
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('adjustment-icon')) {
            const employeeCode = e.target.getAttribute('data-employee-code');
            const employeeName = e.target.getAttribute('data-employee-name');
            const period = e.target.getAttribute('data-period');
            const originalDays = parseFloat(e.target.getAttribute('data-original-days'));
            const overtimeHours = parseFloat(e.target.getAttribute('data-overtime-hours'));
            const currentAbsence = parseFloat(e.target.getAttribute('data-current-absence') || 0);
            const standardDays = parseFloat(e.target.getAttribute('data-standard-days') || 26);
            const actualDays = parseFloat(e.target.getAttribute('data-actual-days') || originalDays);
            
            console.log('Adjustment clicked:', {employeeCode, employeeName, period, originalDays, overtimeHours, currentAbsence, standardDays, actualDays});
            
            // ✅ KIỂM TRA: NẾU "THỰC TẾ" ĐÃ >= "QUY ĐỊNH" THÌ KHÔNG CHO GỘP
            if (actualDays >= standardDays) {
                notificationSystem.warning(
                    `Không thể gộp tăng ca cho <strong>${employeeName}</strong>!<br>
                    <strong>Lý do:</strong> Số ngày làm việc thực tế (${actualDays} ngày) đã đạt/vượt ngày công quy định (${standardDays} ngày).`,
                    'Không thể gộp tăng ca'
                );
                return;
            }
            
            // ✅ CÔNG THỨC MỚI: CHỈ GỘP VÀO NGÀY CÔNG, KHÔNG BÙ NGÀY NGHỈ
            const overtimeDays = overtimeHours / 8;
            
            // 1. Gộp toàn bộ tăng ca vào ngày công (KHÔNG VƯỢT CHUẨN)
            let adjustedDays = originalDays + overtimeDays;
            if (adjustedDays > standardDays) {
                adjustedDays = standardDays;
            }
            
            // 2. ✅ KHÔNG DÙNG TĂNG CA ĐỂ BÙ NGÀY NGHỈ - GIỮ NGUYÊN NGÀY NGHỈ
            const newAbsenceDays = currentAbsence; // Giữ nguyên
            const remainingHours = overtimeHours - ((adjustedDays - originalDays) * 8);
            const usedHours = overtimeHours - remainingHours;
            
            console.log(`DEBUG CÔNG THỨC MỚI (KHÔNG BÙ NGÀY NGHỈ):`);
            console.log(`- Ngày công ban đầu: ${originalDays} ngày`);
            console.log(`- Ngày CN đã làm: ${overtimeDays.toFixed(1)} ngày (${overtimeHours} giờ)`);
            console.log(`- Ngày công sau gộp: ${adjustedDays.toFixed(1)} ngày`);
            console.log(`- Ngày nghỉ: ${currentAbsence} -> ${newAbsenceDays.toFixed(1)} ngày (GIỮ NGUYÊN)`);
            console.log(`- Giờ tăng ca: ${overtimeHours} -> ${remainingHours.toFixed(1)} giờ (đã dùng ${usedHours.toFixed(1)} giờ)`);

            // Hiển thị modal
            document.getElementById('modalEmployeeName').textContent = employeeName;
            document.getElementById('modalCurrentDays').textContent = originalDays + ' ngày';
            document.getElementById('modalOvertimeHours').textContent = overtimeHours + ' giờ (' + overtimeDays.toFixed(1) + ' ngày)';
            document.getElementById('modalCurrentAbsence').textContent = currentAbsence + ' ngày';
            document.getElementById('modalAdjustedDays').textContent = adjustedDays.toFixed(1) + ' ngày';
            document.getElementById('modalNewAbsence').textContent = newAbsenceDays.toFixed(1) + ' ngày (giữ nguyên)';
            document.getElementById('modalRemainingHours').textContent = remainingHours.toFixed(1) + ' giờ';
            
            // Điền form
            document.getElementById('formEmployeeCode').value = employeeCode;
            document.getElementById('formPeriod').value = period;
            document.getElementById('formOriginalDays').value = originalDays;
            document.getElementById('formOvertimeHours').value = overtimeHours;
            document.getElementById('formCurrentAbsence').value = currentAbsence;
            
            // Hiển thị modal
            const modal = new bootstrap.Modal(document.getElementById('adjustmentModal'));
            modal.show();
        }
    });

    // ✅ SỬA LỖI: Xử lý click icon reset (-) - DÙNG 'reset-icon'
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
    document.getElementById('confirmAdjustment')?.addEventListener('click', function() {
        console.log('Confirming adjustment...');
        document.getElementById('adjustmentForm').submit();
    });

    // Xác nhận reset
    document.getElementById('confirmReset')?.addEventListener('click', function() {
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

// ✅ HÀM HIỂN THỊ/ẨN NÚT PHÉP NĂM KHI HOVER
function showLeaveButtons(cell) {
    const buttons = cell.querySelector('.leave-buttons');
    if (buttons) {
        buttons.style.display = 'block';
    }
}

function hideLeaveButtons(cell) {
    const buttons = cell.querySelector('.leave-buttons');
    if (buttons) {
        buttons.style.display = 'none';
    }
}

// Xử lý click icon phép năm
document.addEventListener("DOMContentLoaded", function(){
    if (e.target.classList.contains('leave-icon')) {
        const employeeId = e.target.getAttribute('data-employee-id');
        const employeeName = e.target.getAttribute('data-employee-name');
        const period = e.target.getAttribute('data-period');
        const maxLeave = parseFloat(e.target.getAttribute('data-max-leave'));
        const currentLeave = parseFloat(e.target.getAttribute('data-current-leave'));
        const currentAbsence = parseFloat(e.target.getAttribute('data-current-absence'));
        const leaveCells = document.querySelectorAll('.leave-cell');
            leaveCells.forEach(cell => {
                cell.addEventListener('mouseenter', function() {
                    showLeaveButtons(this);
                });
                
                cell.addEventListener('mouseleave', function() {
                    hideLeaveButtons(this);
                });
            });
        
        // ✅ XỬ LÝ CLICK ICON THÊM PHÉP NĂM (+)
        document.addEventListener('click', function(e) {
            if (e.target.classList.contains('leave-add-icon')) {
                const employeeId = e.target.getAttribute('data-employee-id');
                const employeeName = e.target.getAttribute('data-employee-name');
                const period = e.target.getAttribute('data-period');
                const maxLeave = parseFloat(e.target.getAttribute('data-max-leave'));
                const currentLeave = parseFloat(e.target.getAttribute('data-current-leave'));
                const currentAbsence = parseFloat(e.target.getAttribute('data-current-absence'));
                
                console.log('Leave add clicked:', {employeeId, employeeName, period, maxLeave, currentLeave, currentAbsence});

                // Hiển thị modal thêm phép năm
                document.getElementById('leaveEmployeeName').textContent = employeeName;
                document.getElementById('leaveDaysInput').value = currentLeave;
                document.getElementById('leaveDaysInput').max = maxLeave;
                document.getElementById('maxLeaveDays').textContent = maxLeave;
                
                // Điền form
                document.getElementById('formEmployeeId').value = employeeId;
                document.getElementById('formLeavePeriod').value = period;
                
                const modal = new bootstrap.Modal(document.getElementById('leaveModal'));
                modal.show();
            }
        });
        // ✅ XỬ LÝ CLICK ICON RESET PHÉP NĂM (-)
        document.addEventListener('click', function(e) {
            if (e.target.classList.contains('leave-reset-icon')) {
                const employeeId = e.target.getAttribute('data-employee-id');
                const employeeName = e.target.getAttribute('data-employee-name');
                const period = e.target.getAttribute('data-period');
                
                console.log('Leave reset clicked:', {employeeId, employeeName, period});
                
                // Hiển thị modal xác nhận reset phép năm
                document.getElementById('resetLeaveEmployeeName').textContent = employeeName;
                document.getElementById('resetLeaveEmployeeId').value = employeeId;
                document.getElementById('resetLeavePeriod').value = period;
                
                const resetModal = new bootstrap.Modal(document.getElementById('resetLeaveModal'));
                resetModal.show();
            }
        



// Xác nhận thêm phép năm
document.getElementById('confirmLeave')?.addEventListener('click', function() {
    const leaveDays = parseFloat(document.getElementById('leaveDaysInput').value);
    const maxLeave = parseFloat(document.getElementById('leaveDaysInput').max);
    
    if (leaveDays > maxLeave) {
        notificationSystem.warning(
            `Số ngày phép không được vượt quá ${maxLeave} ngày!`,
            'Số ngày phép không hợp lệ'
        );
        return;
    }
    
    if (leaveDays < 0) {
        notificationSystem.warning('Số ngày phép không được âm!', 'Số ngày phép không hợp lệ');
        return;
    }
    
    document.getElementById('formLeaveDays').value = leaveDays;
    document.getElementById('leaveForm').submit();
});