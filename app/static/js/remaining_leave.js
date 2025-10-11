// static/js/remaining_leave.js

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

// ✅ XỬ LÝ CLICK ICON THÊM PHÉP NĂM CÒN TỒN (+)
window.handleRemainingLeaveAdd = function(e) {
    const employeeId = e.target.getAttribute('data-employee-id');
    const employeeName = e.target.getAttribute('data-employee-name');
    const period = e.target.getAttribute('data-period');
    const currentRemaining = parseFloat(e.target.getAttribute('data-current-remaining'));
    const filename = e.target.getAttribute('data-filename');
    
    const newValue = prompt(`Nhập số ngày phép còn tồn mới cho ${employeeName}:`, currentRemaining);
    
    if (newValue !== null && !isNaN(parseFloat(newValue))) {
        const formData = new FormData();
        formData.append('employee_id', employeeId);
        formData.append('period', period);
        formData.append('remaining_leave_days', parseFloat(newValue));
        formData.append('filename', filename);
        
        fetch('/update_remaining_leave', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (response.redirected) {
                window.location.href = response.url;
            } else {
                location.reload();
            }
        })
        .catch(error => {
            console.error('Error updating remaining leave:', error);
            alert('Có lỗi xảy ra khi cập nhật phép năm còn tồn.');
        });
    }
}

// ✅ XỬ LÝ CLICK ICON RESET PHÉP NĂM CÒN TỒN (-)
window.handleRemainingLeaveReset = function(e) {
    const employeeId = e.target.getAttribute('data-employee-id');
    const employeeName = e.target.getAttribute('data-employee-name');
    const period = e.target.getAttribute('data-period');
    const filename = e.target.getAttribute('data-filename');
    
    if (confirm(`Bạn có muốn reset phép năm còn tồn về giá trị mặc định cho ${employeeName}?`)) {
        const formData = new FormData();
        formData.append('employee_id', employeeId);
        formData.append('period', period);
        formData.append('filename', filename);
        
        fetch('/reset_remaining_leave', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (response.redirected) {
                window.location.href = response.url;
            } else {
                location.reload();
            }
        })
        .catch(error => {
            console.error('Error resetting remaining leave:', error);
            alert('Có lỗi xảy ra khi reset phép năm còn tồn.');
        });
    }
}

// ✅ EVENT LISTENERS - KHÔNG DÙNG DOMContentLoaded
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

console.log('✅ remaining_leave.js loaded successfully');