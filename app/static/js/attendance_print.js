// ✅ ĐẶT CÁC HÀM GLOBAL Ở ĐẦU FILE - TRƯỚC KHI ĐƯỢC GỌI
window.handleConfirmAdjustment = function() {
    console.log('🎯 === HANDLE CONFIRM ADJUSTMENT CALLED ===');
    
    const employeeCode = document.getElementById('formEmployeeCode');
    const period = document.getElementById('formPeriod');
    const filename = document.getElementById('formFilename');
    
    console.log('🔍 Form elements check:', {
        employeeCode: employeeCode ? 'EXISTS' : 'MISSING',
        period: period ? 'EXISTS' : 'MISSING', 
        filename: filename ? 'EXISTS' : 'MISSING'
    });
    
    if (!employeeCode || !period || !filename) {
        console.error('❌ Form elements missing!');
        alert('Lỗi: Không tìm thấy thông tin form. Vui lòng thử lại.');
        return;
    }
    
    const empCode = employeeCode.value;
    const periodVal = period.value;
    const filenameVal = filename.value;
    
    console.log('📋 Form values:', {
        employeeCode: empCode,
        period: periodVal,
        filename: filenameVal,
        originalDays: document.getElementById('formOriginalDays')?.value,
        overtimeHours: document.getElementById('formOvertimeHours')?.value,
        currentAbsence: document.getElementById('formCurrentAbsence')?.value
    });
    
    if (!empCode || !periodVal) {
        console.error('❌ Missing required form values!');
        alert('Lỗi: Thiếu thông tin cần thiết. Vui lòng thử lại.');
        return;
    }
    
    const modal = bootstrap.Modal.getInstance(document.getElementById('adjustmentModal'));
    if (modal) {
        console.log('🔒 Closing modal...');
        modal.hide();
    } else {
        console.log('⚠️ Modal instance not found');
    }
    
    console.log('🚀 Calling applyAdjustment...');
    window.applyAdjustment(empCode, periodVal, filenameVal);
};

window.applyAdjustment = function(employeeCode, period, filename) {
    console.log('=== STARTING ADJUSTMENT PROCESS ===');
    console.log('Employee:', employeeCode, 'Period:', period, 'Filename:', filename);
    
    const form = document.getElementById('adjustmentForm');
    if (!form) {
        console.error('❌ Adjustment form not found!');
        alert('Lỗi: Không tìm thấy form điều chỉnh.');
        return;
    }
    
    const formData = new FormData(form);
    
    console.log('Form data:');
    for (let [key, value] of formData.entries()) {
        console.log(`${key}: ${value}`);
    }
    
    // ✅ THÊM: Header để xác định đây là AJAX request
    const headers = new Headers();
    headers.append('X-Requested-With', 'XMLHttpRequest');
    
    fetch('/apply_adjustment', {
        method: 'POST',
        body: formData,
        headers: headers
    })
    .then(response => {
        console.log('Response status:', response.status, 'Redirected:', response.redirected);
        
        const contentType = response.headers.get('content-type');
        console.log('Content-Type:', contentType);
        
        if (response.redirected) {
            console.log('Response redirected to:', response.url);
            window.location.href = response.url;
            return null;
        }
        
        if (contentType && contentType.includes('application/json')) {
            return response.json();
        } else {
            console.log('Not JSON response, reloading page');
            location.reload();
            return null;
        }
    })
    .then(data => {
        if (!data) return;
        
        console.log('API JSON Response:', data);
        
        if (data.need_extra_leave_confirmation && data.remaining_absence > 0) {
            console.log('Need extra leave confirmation:', data.remaining_absence, 'days remaining');
            window.showExtraLeaveConfirmation(employeeCode, period, filename, data.remaining_absence, data.available_leave);
        } else {
            console.log('No extra leave needed, reloading page');
            location.reload();
        }
    })
    .catch(error => {
        console.error('Error applying adjustment:', error);
        alert('Có lỗi xảy ra khi áp dụng điều chỉnh. Vui lòng thử lại.');
        location.reload();
    });
};

// ✅ HÀM HIỂN THỊ XÁC NHẬN THÊM PHÉP NĂM
window.showExtraLeaveConfirmation = function(employeeCode, period, filename, remainingAbsence, availableLeave) {
    console.log('Showing extra leave confirmation:', {remainingAbsence, availableLeave});
    
    const message = availableLeave >= remainingAbsence 
        ? `Vẫn còn ${remainingAbsence} ngày nghỉ không lương. Bạn có muốn dùng thêm phép năm để bù luôn không?`
        : `Vẫn còn ${remainingAbsence} ngày nghỉ không lương. Bạn không còn đủ phép năm (chỉ còn ${availableLeave} ngày).`;
    
    const canUseExtraLeave = availableLeave >= remainingAbsence;
    
    if (canUseExtraLeave && confirm(message)) {
        console.log('User confirmed extra leave usage');
        const formData = new FormData();
        formData.append('employee_code', employeeCode);
        formData.append('period', period);
        formData.append('filename', filename);
        formData.append('use_extra_leave', 'true');
        formData.append('original_days', document.getElementById('formOriginalDays').value);
        formData.append('overtime_hours', document.getElementById('formOvertimeHours').value);
        formData.append('current_absence', document.getElementById('formCurrentAbsence').value);
        
        // ✅ THÊM: Header cho request thứ 2
        const headers = new Headers();
        headers.append('X-Requested-With', 'XMLHttpRequest');
        
        console.log('Calling API with extra leave...');
        
        fetch('/apply_adjustment', {
            method: 'POST',
            body: formData,
            headers: headers
        })
        .then(response => {
            console.log('Extra leave response - Redirected:', response.redirected);
            if (response.redirected) {
                window.location.href = response.url;
            } else {
                location.reload();
            }
        })
        .catch(error => {
            console.error('Error in extra leave call:', error);
            location.reload();
        });
    } else {
        console.log('User declined extra leave or not enough leave available');
        location.reload();
    }
}

// ✅ CÁC HÀM HIỂN THỊ/ẨN NÚT
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

// ✅ DEBUG: KIỂM TRA NGAY KHI LOAD
console.log('🎯 attendance_print.js loaded - handleConfirmAdjustment defined:', typeof window.handleConfirmAdjustment);
console.log('🎯 attendance_print.js loaded - applyAdjustment defined:', typeof window.applyAdjustment);

// attendance_print.js - JavaScript cho trang attendance_print - CÔNG THỨC MỚI ĐÃ SỬA
document.addEventListener("DOMContentLoaded", function(){
    // ✅ DEBUG: KIỂM TRA GLOBAL FUNCTIONS
    console.log('🔍 Global functions check:', {
        handleConfirmAdjustment: typeof window.handleConfirmAdjustment,
        applyAdjustment: typeof window.applyAdjustment,
        showExtraLeaveConfirmation: typeof window.showExtraLeaveConfirmation
    });

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

// ✅ THÊM: Event listener cho nút confirm adjustment
document.getElementById('confirmAdjustmentBtn')?.addEventListener('click', function(e) {
        console.log('🎯 CONFIRM BUTTON CLICKED - EVENT LISTENER FIRED!');
        e.preventDefault();
        window.handleConfirmAdjustment();
    });

    // ✅ HÀM TÍNH TOÁN ĐIỀU CHỈNH MỚI (ĐỒNG BỘ VỚI BACKEND)
    function calculateAdjustedWorkDays(originalDays, standardDays, overtimeHours, currentAbsence, ngayNghiPhepNamDaDung = 0) {
        const overtimeDays = overtimeHours / 8;
        
        const ngayVangConLaiSauPhep = Math.max(0, currentAbsence - ngayNghiPhepNamDaDung);
        const soNgayBuTuTangCa = Math.min(overtimeDays, ngayVangConLaiSauPhep);
        
        const ngayCongTam = originalDays + ngayNghiPhepNamDaDung + soNgayBuTuTangCa;
        
        let ngayNghiPhepNamDaDungFinal = ngayNghiPhepNamDaDung;
        let soNgayBuTuTangCaFinal = soNgayBuTuTangCa;
        let ngayCongCuoi = ngayCongTam;
        
        if (ngayCongTam > standardDays) {
            let ngayThua = ngayCongTam - standardDays;
            
            if (soNgayBuTuTangCaFinal >= ngayThua) {
                soNgayBuTuTangCaFinal -= ngayThua;
                ngayThua = 0;
            } else {
                ngayThua -= soNgayBuTuTangCaFinal;
                soNgayBuTuTangCaFinal = 0;
            }
            
            if (ngayThua > 0) {
                ngayNghiPhepNamDaDungFinal -= ngayThua;
            }
            
            ngayCongCuoi = standardDays;
        }
        
        const ngayVangCuoi = Math.max(0, currentAbsence - ngayNghiPhepNamDaDungFinal - soNgayBuTuTangCaFinal);
        const tangCaConLai = overtimeHours - (soNgayBuTuTangCaFinal * 8);
        
        return {
            ngayCongCuoi,
            ngayVangCuoi,
            tangCaConLai,
            soNgayBuTuTangCa: soNgayBuTuTangCaFinal,
            ngayNghiPhepNamDaDung: ngayNghiPhepNamDaDungFinal,
            gioTangCaDaDung: soNgayBuTuTangCaFinal * 8
        };
    }

    // Khởi tạo tooltip Bootstrap
    const tooltips = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltips.forEach(t => new bootstrap.Tooltip(t, {container: 'body'}));

    // ✅ XỬ LÝ CLICK ICON ĐIỀU CHỈNH (+) - CÔNG THỨC MỚI
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('adjustment-icon')) {
            const employeeCode = e.target.getAttribute('data-employee-code');
            const employeeName = e.target.getAttribute('data-employee-name');
            const period = e.target.getAttribute('data-period');
            const originalDays = parseFloat(e.target.getAttribute('data-original-days'));
            const overtimeHours = parseFloat(e.target.getAttribute('data-overtime-hours'));
            const currentAbsence = parseFloat(e.target.getAttribute('data-current-absence') || 0);
            const standardDays = parseFloat(e.target.getAttribute('data-standard-days') || 26);
            const ngayNghiPhepNamDaDung = parseFloat(e.target.getAttribute('data-ngay-nghi-phep-nam') || 0);
            
            console.log('Adjustment clicked:', {
                employeeCode, 
                employeeName, 
                period, 
                originalDays, 
                overtimeHours, 
                currentAbsence, 
                standardDays, 
                ngayNghiPhepNamDaDung
            });
            
            if (originalDays >= standardDays) {
                if (typeof notificationSystem !== 'undefined') {
                    notificationSystem.warning(
                        `Không thể gộp tăng ca cho <strong>${employeeName}</strong>!<br>
                        <strong>Lý do:</strong> Số ngày làm việc thực tế (${originalDays} ngày) đã đạt ngày công quy định (${standardDays} ngày).`,
                        'Không thể gộp tăng ca'
                    );
                } else {
                    alert(`Không thể gộp tăng ca cho ${employeeName}! Số ngày làm việc thực tế (${originalDays} ngày) đã đạt ngày công quy định (${standardDays} ngày).`);
                }
                return;
            }
            
            const result = calculateAdjustedWorkDays(
                originalDays, 
                standardDays, 
                overtimeHours, 
                currentAbsence, 
                ngayNghiPhepNamDaDung
            );
            
            console.log(`DEBUG CÔNG THỨC MỚI:`);
            console.log(`- Ngày công ban đầu: ${originalDays} ngày`);
            console.log(`- Phép năm đã dùng: ${ngayNghiPhepNamDaDung} ngày`);
            console.log(`- Ngày CN đã làm: ${(overtimeHours/8).toFixed(1)} ngày (${overtimeHours} giờ)`);
            console.log(`- Ngày công sau gộp: ${result.ngayCongCuoi.toFixed(1)} ngày`);
            console.log(`- Ngày nghỉ: ${currentAbsence} -> ${result.ngayVangCuoi.toFixed(1)} ngày`);
            console.log(`- Giờ tăng ca: ${overtimeHours} -> ${result.tangCaConLai.toFixed(1)} giờ (đã dùng ${result.gioTangCaDaDung.toFixed(1)} giờ)`);
            console.log(`- Phép năm đã dùng: ${result.ngayNghiPhepNamDaDung} ngày`);

            document.getElementById('modalEmployeeName').textContent = employeeName;
            document.getElementById('modalCurrentDays').textContent = originalDays + ' ngày';
            document.getElementById('modalOvertimeHours').textContent = overtimeHours + ' giờ (' + (overtimeHours/8).toFixed(1) + ' ngày)';
            document.getElementById('modalCurrentAbsence').textContent = currentAbsence + ' ngày';
            document.getElementById('modalAdjustedDays').textContent = result.ngayCongCuoi.toFixed(1) + ' ngày';
            document.getElementById('modalNewAbsence').textContent = result.ngayVangCuoi.toFixed(1) + ' ngày';
            document.getElementById('modalRemainingHours').textContent = result.tangCaConLai.toFixed(1) + ' giờ';
            document.getElementById('modalPhepNamUsed').textContent = result.ngayNghiPhepNamDaDung + ' ngày';
            
            document.getElementById('formEmployeeCode').value = employeeCode;
            document.getElementById('formPeriod').value = period;
            document.getElementById('formOriginalDays').value = originalDays;
            document.getElementById('formOvertimeHours').value = overtimeHours;
            document.getElementById('formCurrentAbsence').value = currentAbsence;
            
            const modal = new bootstrap.Modal(document.getElementById('adjustmentModal'));
            modal.show();
        }
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

            document.getElementById('leaveEmployeeName').textContent = employeeName;
            document.getElementById('leaveDaysInput').value = currentLeave;
            document.getElementById('leaveDaysInput').max = maxLeave;
            document.getElementById('maxLeaveDays').textContent = maxLeave;
            
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
            
            document.getElementById('resetLeaveEmployeeName').textContent = employeeName;
            document.getElementById('resetLeaveEmployeeId').value = employeeId;
            document.getElementById('resetLeavePeriod').value = period;
            
            const resetModal = new bootstrap.Modal(document.getElementById('resetLeaveModal'));
            resetModal.show();
        }
    });

    // ✅ XỬ LÝ CLICK ICON RESET ĐIỀU CHỈNH (-)
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('reset-icon')) {
            const employeeCode = e.target.getAttribute('data-employee-code');
            const employeeName = e.target.getAttribute('data-employee-name');
            const period = e.target.getAttribute('data-period');
            
            console.log('Reset clicked:', {employeeCode, employeeName, period});
            
            document.getElementById('resetEmployeeName').textContent = employeeName;
            document.getElementById('resetEmployeeCode').value = employeeCode;
            document.getElementById('resetPeriod').value = period;
            
            const resetModal = new bootstrap.Modal(document.getElementById('resetModal'));
            resetModal.show();
        }
    });

    // Xác nhận reset điều chỉnh
    document.getElementById('confirmReset')?.addEventListener('click', function() {
        console.log('Confirming reset...');
        document.getElementById('resetForm').submit();
    });

    // ✅ XÁC NHẬN RESET PHÉP NĂM
    document.getElementById('confirmResetLeave')?.addEventListener('click', function() {
        console.log('Confirming leave reset...');
        document.getElementById('resetLeaveForm').submit();
    });

    // Xác nhận thêm phép năm
    document.getElementById('confirmLeave')?.addEventListener('click', function() {
        const leaveDays = parseFloat(document.getElementById('leaveDaysInput').value);
        const maxLeave = parseFloat(document.getElementById('leaveDaysInput').max);
        
        if (leaveDays > maxLeave) {
            if (typeof notificationSystem !== 'undefined') {
                notificationSystem.warning(
                    `Số ngày phép không được vượt quá ${maxLeave} ngày!`,
                    'Số ngày phép không hợp lệ'
                );
            } else {
                alert(`Số ngày phép không được vượt quá ${maxLeave} ngày!`);
            }
            return;
        }
        
        if (leaveDays < 0) {
            if (typeof notificationSystem !== 'undefined') {
                notificationSystem.warning('Số ngày phép không được âm!', 'Số ngày phép không hợp lệ');
            } else {
                alert('Số ngày phép không được âm!');
            }
            return;
        }
        
        document.getElementById('formLeaveDays').value = leaveDays;
        document.getElementById('leaveForm').submit();
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
        console.log('Showing detail modal:', empData);
    }

    // Xử lý đóng modal chi tiết (nếu có)
    const modalClose = document.querySelector('.modal-close');
    if (modalClose) {
        modalClose.addEventListener('click', function() {
            document.getElementById('detailModal').style.display = 'none';
        });
    }
    
    // ✅ DEBUG: KIỂM TRA NÚT CONFIRM SAU KHI DOM LOADED
    console.log('🔍 Checking confirm button after DOM loaded...');
    const confirmBtn = document.getElementById('confirmAdjustmentBtn');
    console.log('Confirm button found:', confirmBtn);

    if (confirmBtn) {
        console.log('✅ Confirm button exists, checking onclick...');
        console.log('onclick attribute:', confirmBtn.getAttribute('onclick'));
    } else {
        console.log('❌ Confirm button NOT FOUND after DOM loaded!');
    }
});

