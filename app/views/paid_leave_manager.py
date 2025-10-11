# app/views/paid_leave_manager.py
from flask import request, flash, redirect, url_for, jsonify
from app.models import PayrollRecord, db
from . import bp

@bp.route("/update_remaining_leave", methods=["POST"])
def update_remaining_leave():
    """
    Cập nhật số ngày phép còn tồn cho tháng sau
    """
    try:
        employee_id = request.form.get("employee_id")
        period = request.form.get("period")
        remaining_leave_days = float(request.form.get("remaining_leave_days", 0))
        filename = request.form.get("filename")
        
        # Tìm payroll_record
        payroll_record = PayrollRecord.query.filter_by(
            employee_id=employee_id,
            period=period
        ).first()
        
        if payroll_record:
            # Cập nhật số ngày phép còn tồn
            payroll_record.ngay_phep_con_lai = remaining_leave_days
            db.session.commit()
            
            flash(f"Đã cập nhật phép năm còn tồn thành {remaining_leave_days} ngày!", "success")
        else:
            flash("Không tìm thấy bản ghi payroll!", "danger")
            
    except Exception as e:
        db.session.rollback()
        flash(f"Lỗi khi cập nhật phép năm còn tồn: {e}", "danger")
    
    return redirect(url_for("main.attendance_print", filename=filename))

@bp.route("/reset_remaining_leave", methods=["POST"])
def reset_remaining_leave():
    """
    Reset số ngày phép còn tồn về giá trị mặc định
    """
    try:
        employee_id = request.form.get("employee_id")
        period = request.form.get("period")
        filename = request.form.get("filename")
        
        from .attendance_helpers import calculate_leave_info
        from app.models import Employee
        
        employee = Employee.query.get(employee_id)
        if not employee:
            flash("Không tìm thấy nhân viên!", "danger")
            return redirect(url_for("main.attendance_print", filename=filename))
        
        # Tính lại số phép năm từ tháng bắt đầu
        thang_bat_dau_tinh_phep, so_thang_duoc_huong, so_ngay_phep_duoc_huong = calculate_leave_info(employee, period)
        
        payroll_record = PayrollRecord.query.filter_by(
            employee_id=employee_id,
            period=period
        ).first()
        
        if payroll_record:
            payroll_record.ngay_phep_con_lai = so_ngay_phep_duoc_huong
            db.session.commit()
            
            flash(f"Đã reset phép năm còn tồn về {so_ngay_phep_duoc_huong} ngày!", "success")
        else:
            flash("Không tìm thấy bản ghi payroll!", "danger")
            
    except Exception as e:
        db.session.rollback()
        flash(f"Lỗi khi reset phép năm còn tồn: {e}", "danger")
    
    return redirect(url_for("main.attendance_print", filename=filename))