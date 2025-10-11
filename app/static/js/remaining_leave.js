// static/js/remaining_leave.js

// ✅ HÀM HIỂN THỊ/ẨN NÚT PHÉP NĂM CÒN TỒN
function showRemainingLeaveButtons(cell) {
    const buttons = cell.querySelector('.remaining-leave-buttons');
    if (buttons) {
        buttons.style.display = 'block';
    }
}

function hideRemainingLeaveButtons(cell) {
    const buttons = cell.querySelector('.remaining-leave-buttons');
    if (buttons) {
        buttons.style.display = 'none';
    }
}

// ✅ XỬ LÝ CLICK ICON THÊM PHÉP NĂM CÒN TỒN (+)
function handleRemainingLeaveAdd(e) {
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
function handleRemainingLeaveReset(e) {
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

// ✅ KHỞI TẠO EVENT LISTENERS
document.addEventListener('DOMContentLoaded', function() {
    // Xử lý click icon thêm phép năm còn tồn
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('remaining-leave-add-icon')) {
            handleRemainingLeaveAdd(e);
        }
    });
    
    // Xử lý click icon reset phép năm còn tồn
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('remaining-leave-reset-icon')) {
            handleRemainingLeaveReset(e);
        }
    });
    
    console.log('✅ remaining_leave.js loaded successfully');
});