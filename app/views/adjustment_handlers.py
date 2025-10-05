# app/views/adjustment_handlers.py
from flask import flash, request
from app.models import PayrollRecord, WorkAdjustment, db
from .attendance_helpers import calculate_standard_work_days, calculate_adjustment_details
from datetime import datetime

def apply_adjustment_handler():
    """
    Xử lý áp dụng điều chỉnh ngày công
    """
    try:
        employee_code = request.form.get("employee_code")
        period = request.form.get("period")
        original_days = float(request.form.get("original_days"))
        overtime_hours = float(request.form.get("overtime_hours"))
        filename = request.form.get("filename") or request.args.get("filename")
        
        print(f"Applying adjustment for: {employee_code}, period: {period}")
        
        # Tìm payroll record
        payroll_record = PayrollRecord.query.filter_by(
            employee_code=employee_code, 
            period=period
        ).first()
        
        if not payroll_record:
            flash("Không tìm thấy bản ghi payroll!", "danger")
            return False, filename
        
        # Tính toán điều chỉnh
        year, month = map(int, period.split('-'))
        standard_days = calculate_standard_work_days(year, month)
        
        adjusted_days, remaining_hours, used_hours = calculate_adjustment_details(
            original_days, standard_days, overtime_hours
        )
        
        # Tạo hoặc cập nhật WorkAdjustment
        adjustment = WorkAdjustment.query.filter_by(
            employee_code=employee_code,
            period=period
        ).first()
        
        if adjustment:
            # Cập nhật adjustment hiện có
            adjustment.adjusted_work_days = adjusted_days
            adjustment.remaining_overtime_hours = remaining_hours
            adjustment.used_overtime_hours = used_hours
            adjustment.adjustment_reason = f"Áp dụng thủ công - gộp {used_hours} giờ tăng ca"
        else:
            # Tạo adjustment mới
            adjustment = WorkAdjustment(
                payroll_record_id=payroll_record.id,
                employee_id=payroll_record.employee_id,
                period=period,
                employee_code=employee_code,
                employee_name=payroll_record.employee_name,
                original_work_days=original_days,
                standard_work_days=standard_days,
                original_overtime_hours=overtime_hours,
                adjusted_work_days=adjusted_days,
                remaining_overtime_hours=remaining_hours,
                used_overtime_hours=used_hours,
                adjustment_type="overtime_compensation",
                adjustment_reason=f"Áp dụng thủ công - gộp {used_hours} giờ tăng ca"
            )
            db.session.add(adjustment)
        
        # Cập nhật PayrollRecord
        payroll_record.ngay_cong = adjusted_days
        payroll_record.tang_ca_nghi = remaining_hours
        
        db.session.commit()
        
        flash(f"✅ Đã áp dụng điều chỉnh cho {payroll_record.employee_name}! Gộp {used_hours} giờ tăng ca.", "success")
        return True, filename
        
    except Exception as e:
        db.session.rollback()
        print(f"Error applying adjustment: {e}")
        flash(f"❌ Lỗi khi áp dụng điều chỉnh: {e}", "danger")
        return False, filename

def reset_adjustment_handler(employee_code, period):
    """
    Xử lý reset điều chỉnh
    """
    filename = request.args.get("filename")
    try:
        # Xóa adjustment
        adjustment = WorkAdjustment.query.filter_by(
            employee_code=employee_code,
            period=period
        ).first()
        
        if adjustment:
            # Khôi phục dữ liệu gốc
            payroll_record = PayrollRecord.query.filter_by(
                employee_code=employee_code,
                period=period
            ).first()
            
            if payroll_record:
                payroll_record.ngay_cong = adjustment.original_work_days
                payroll_record.tang_ca_nghi = adjustment.original_overtime_hours
            
            db.session.delete(adjustment)
            db.session.commit()
            flash(f"✅ Đã khôi phục dữ liệu gốc cho {employee_code}", "success")
        else:
            flash("⚠️ Không tìm thấy điều chỉnh để khôi phục", "warning")
            
    except Exception as e:
        db.session.rollback()
        flash(f"❌ Lỗi khi khôi phục: {e}", "danger")
    
    return filename