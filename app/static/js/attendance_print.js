// ✅ HÀM XỬ LÝ CLICK TRỰC TIẾP - THÊM VÀO ĐẦU FILE
// ✅ THÊM DEBUG ĐỂ KIỂM TRA
// ✅ THÊM DEBUG ĐỂ KIỂM TRA
console.log('🎯 attendance_print.js loaded - handleConfirmAdjustment defined:', typeof handleConfirmAdjustment);

// ✅ HÀM XỬ LÝ CLICK TRỰC TIẾP - THÊM VÀO ĐẦU FILE
function handleConfirmAdjustment() {
    console.log('🎯 === HANDLE CONFIRM ADJUSTMENT CALLED ===');
    
    // Kiểm tra xem các form field có tồn tại không
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
        originalDays: document.getElementById('formOriginalDays').value,
        overtimeHours: document.getElementById('formOvertimeHours').value,
        currentAbsence: document.getElementById('formCurrentAbsence').value
    });
    
    // Kiểm tra xem có giá trị không
    if (!empCode || !periodVal) {
        console.error('❌ Missing required form values!');
        alert('Lỗi: Thiếu thông tin cần thiết. Vui lòng thử lại.');
        return;
    }
    
    // Đóng modal trước
    const modal = bootstrap.Modal.getInstance(document.getElementById('adjustmentModal'));
    if (modal) {
        console.log('🔒 Closing modal...');
        modal.hide();
    } else {
        console.log('⚠️ Modal instance not found');
    }
    
    // Gọi hàm điều chỉnh
    console.log('🚀 Calling applyAdjustment...');
    applyAdjustment(empCode, periodVal, filenameVal);
}

// attendance_print.js - JavaScript cho trang attendance_print - CÔNG THỨC MỚI ĐÃ SỬA
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

    // ✅ HÀM TÍNH TOÁN ĐIỀU CHỈNH MỚI (ĐỒNG BỘ VỚI BACKEND)
    function calculateAdjustedWorkDays(originalDays, standardDays, overtimeHours, currentAbsence, ngayNghiPhepNamDaDung = 0) {
        const overtimeDays = overtimeHours / 8;
        
        // BƯỚC 1: Tính số ngày có thể bù từ tăng ca
        const ngayVangConLaiSauPhep = Math.max(0, currentAbsence - ngayNghiPhepNamDaDung);
        const soNgayBuTuTangCa = Math.min(overtimeDays, ngayVangConLaiSauPhep);
        
        // BƯỚC 2: Tính ngày công tạm thời
        const ngayCongTam = originalDays + ngayNghiPhepNamDaDung + soNgayBuTuTangCa;
        
        // BƯỚC 3: Giới hạn không vượt quá chuẩn
        let ngayNghiPhepNamDaDungFinal = ngayNghiPhepNamDaDung;
        let soNgayBuTuTangCaFinal = soNgayBuTuTangCa;
        let ngayCongCuoi = ngayCongTam;
        
        if (ngayCongTam > standardDays) {
            let ngayThua = ngayCongTam - standardDays;
            
            // Giảm số ngày bù từ tăng ca trước
            if (soNgayBuTuTangCaFinal >= ngayThua) {
                soNgayBuTuTangCaFinal -= ngayThua;
                ngayThua = 0;
            } else {
                ngayThua -= soNgayBuTuTangCaFinal;
                soNgayBuTuTangCaFinal = 0;
            }
            
            // Nếu vẫn thừa, giảm phép năm đã dùng
            if (ngayThua > 0) {
                ngayNghiPhepNamDaDungFinal -= ngayThua;
            }
            
            ngayCongCuoi = standardDays;
        }
        
        // Tính kết quả cuối
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

    // ✅ KHỞI TẠO SỰ KIỆN HOVER CHO CÁC Ô PHÉP NĂM
    const leaveCells = document.querySelectorAll('.leave-cell');
    leaveCells.forEach(cell => {
        cell.addEventListener('mouseenter', function() {
            showLeaveButtons(this);
        });
        
        cell.addEventListener('mouseleave', function() {
            hideLeaveButtons(this);
        });
    });

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
            
            // ✅ KIỂM TRA: NẾU ĐÃ ĐẠT CHUẨN THÌ KHÔNG CHO GỘP
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
            
            // ✅ TÍNH TOÁN THEO CÔNG THỨC MỚI
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

            // Hiển thị modal
            document.getElementById('modalEmployeeName').textContent = employeeName;
            document.getElementById('modalCurrentDays').textContent = originalDays + ' ngày';
            document.getElementById('modalOvertimeHours').textContent = overtimeHours + ' giờ (' + (overtimeHours/8).toFixed(1) + ' ngày)';
            document.getElementById('modalCurrentAbsence').textContent = currentAbsence + ' ngày';
            document.getElementById('modalAdjustedDays').textContent = result.ngayCongCuoi.toFixed(1) + ' ngày';
            document.getElementById('modalNewAbsence').textContent = result.ngayVangCuoi.toFixed(1) + ' ngày';
            document.getElementById('modalRemainingHours').textContent = result.tangCaConLai.toFixed(1) + ' giờ';
            document.getElementById('modalPhepNamUsed').textContent = result.ngayNghiPhepNamDaDung + ' ngày';
            
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
    });

    // ✅ XỬ LÝ CLICK ICON RESET ĐIỀU CHỈNH (-)
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
        document.getElementById('confirmAdjustment')?.addEventListener('click', function() {
        const employeeCode = document.getElementById('formEmployeeCode').value;
        const period = document.getElementById('formPeriod').value;
        const filename = document.getElementById('formFilename').value; // Cần thêm field này vào form
        
        applyAdjustment(employeeCode, period, filename);
    });
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

// ✅ HÀM GỌI API ĐIỀU CHỈNH VỚI XÁC NHẬN PHÉP NĂM
function applyAdjustment(employeeCode, period, filename) {
    console.log('Starting adjustment process for:', employeeCode, period, filename);
    
    // Lấy dữ liệu từ form
    const formData = new FormData(document.getElementById('adjustmentForm'));
    
    // Gọi API lần đầu (không dùng extra leave)
    fetch('/apply_adjustment', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (response.redirected) {
            // Nếu redirect (thành công hoặc lỗi thông thường)
            window.location.href = response.url;
            return;
        }
        return response.json();
    })
    .then(data => {
        console.log('API response:', data);
        if (data && data.need_extra_leave_confirmation && data.remaining_absence > 0) {
            // Hiển thị popup xác nhận thứ hai
            showExtraLeaveConfirmation(employeeCode, period, filename, data.remaining_absence, data.available_leave);
        } else {
            // Không cần xác nhận thêm → reload trang
            location.reload();
        }
    })
    .catch(error => {
        console.error('Error applying adjustment:', error);
        location.reload(); // Fallback: reload trang
    });
}



// ✅ HÀM HIỂN THỊ XÁC NHẬN THÊM PHÉP NĂM
function showExtraLeaveConfirmation(employeeCode, period, filename, remainingAbsence, availableLeave) {
    console.log('Showing extra leave confirmation:', {remainingAbsence, availableLeave});
    
    const message = availableLeave >= remainingAbsence 
        ? `Vẫn còn ${remainingAbsence} ngày nghỉ không lương. Bạn có muốn dùng thêm phép năm để bù luôn không?`
        : `Vẫn còn ${remainingAbsence} ngày nghỉ không lương. Bạn không còn đủ phép năm (chỉ còn ${availableLeave} ngày).`;
    
    const canUseExtraLeave = availableLeave >= remainingAbsence;
    
    if (canUseExtraLeave && confirm(message)) {
        console.log('User confirmed extra leave usage');
        // Gọi API lần thứ hai với use_extra_leave=true
        const formData = new FormData();
        formData.append('employee_code', employeeCode);
        formData.append('period', period);
        formData.append('filename', filename);
        formData.append('use_extra_leave', 'true');
        formData.append('original_days', document.getElementById('formOriginalDays').value);
        formData.append('overtime_hours', document.getElementById('formOvertimeHours').value);
        formData.append('current_absence', document.getElementById('formCurrentAbsence').value);
        
        console.log('Calling API with extra leave...');
        
        fetch('/apply_adjustment', {
            method: 'POST',
            body: formData
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



// ✅ THÊM CÁC HÀM BỊ THIẾU
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