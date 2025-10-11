// remaining_leave.js - JavaScript cho phép năm còn tồn (PHIÊN BẢN FIX)

// ✅ HÀM HIỂN THỊ/ẨN NÚT PHÉP NĂM CÒN TỒN - GLOBAL
window.showRemainingLeaveButtons = function(cell) {
    const buttons = cell.querySelector('.remaining-leave-buttons');
    if (buttons) {
        buttons.style.display = 'block';
    }
}

window.hideRemainingLeaveButtons = function(cell) {
    const buttons = cell.querySelector('.remaining-leave-buttons');
    if (buttons) {
        buttons.style.display = 'none';
    }
}

// ✅ BIẾN LƯU TRỮ TẠM THỜI
let currentRemainingLeaveData = {};

// ✅ XỬ LÝ CLICK ICON THÊM PHÉP NĂM CÒN TỒN (+)
window.handleRemainingLeaveAdd = function(e) {
    const employeeId = e.target.getAttribute('data-employee-id');
    const employeeName = e.target.getAttribute('data-employee-name');
    const period = e.target.getAttribute('data-period');
    const currentRemaining = parseFloat(e.target.getAttribute('data-current-remaining'));
    const filename = e.target.getAttribute('data-filename');
    
    console.log('Remaining leave add clicked:', {employeeId, employeeName, currentRemaining});
    
    // Lưu dữ liệu tạm thời
    currentRemainingLeaveData = {
        employeeId,
        employeeName,
        period,
        currentRemaining,
        filename
    };
    
    // Hiển thị modal
    document.getElementById('remainingLeaveEmployeeName').textContent = employeeName;
    document.getElementById('remainingLeaveCurrentValue').textContent = currentRemaining + ' ngày';
    document.getElementById('remainingLeaveInput').value = currentRemaining;
    
    // Hiển thị modal Bootstrap
    const modal = new bootstrap.Modal(document.getElementById('remainingLeaveModal'));
    modal.show();
}

// ✅ XỬ LÝ CLICK ICON RESET PHÉP NĂM CÒN TỒN (-)
window.handleRemainingLeaveReset = function(e) {
    const employeeId = e.target.getAttribute('data-employee-id');
    const employeeName = e.target.getAttribute('data-employee-name');
    const period = e.target.getAttribute('data-period');
    const filename = e.target.getAttribute('data-filename');
    
    console.log('Remaining leave reset clicked:', {employeeId, employeeName});
    
    // Lưu dữ liệu tạm thời
    currentRemainingLeaveData = {
        employeeId,
        employeeName,
        period,
        filename
    };
    
    // Hiển thị modal xác nhận reset
    document.getElementById('resetRemainingLeaveEmployeeName').textContent = employeeName;
    
    const modal = new bootstrap.Modal(document.getElementById('resetRemainingLeaveModal'));
    modal.show();
}

// ✅ XÁC NHẬN CẬP NHẬT PHÉP NĂM CÒN TỒN
document.addEventListener('DOMContentLoaded', function() {
    console.log('✅ remaining_leave.js loaded (Fixed Modal Version)');
    
    // Xử lý xác nhận cập nhật
    document.getElementById('confirmRemainingLeave')?.addEventListener('click', function() {
        const newValue = parseFloat(document.getElementById('remainingLeaveInput').value);
        
        if (isNaN(newValue) || newValue < 0) {
            alert('Vui lòng nhập số ngày phép hợp lệ!');
            return;
        }
        
        console.log('Updating remaining leave to:', newValue);
        
        // Điền form và submit
        document.getElementById('formRemainingLeaveEmployeeId').value = currentRemainingLeaveData.employeeId;
        document.getElementById('formRemainingLeavePeriod').value = currentRemainingLeaveData.period;
        document.getElementById('formRemainingLeaveDays').value = newValue;
        
        document.getElementById('remainingLeaveForm').submit();
    });
    
    // Xử lý xác nhận reset
    document.getElementById('confirmResetRemainingLeave')?.addEventListener('click', function() {
        console.log('Resetting remaining leave');
        
        // Điền form và submit
        document.getElementById('resetRemainingLeaveEmployeeId').value = currentRemainingLeaveData.employeeId;
        document.getElementById('resetRemainingLeavePeriod').value = currentRemainingLeaveData.period;
        
        document.getElementById('resetRemainingLeaveForm').submit();
    });
    
    // Xử lý enter trong input
    document.getElementById('remainingLeaveInput')?.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            document.getElementById('confirmRemainingLeave').click();
        }
    });
    
    // Event listeners cho các icon
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('remaining-leave-add-icon')) {
            window.handleRemainingLeaveAdd(e);
        }
    });
    
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('remaining-leave-reset-icon')) {
            window.handleRemainingLeaveReset(e);
        }
    });
});