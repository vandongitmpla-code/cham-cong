# app/views/attendance_print.py
from flask import render_template, redirect, url_for, flash, request
import os
from datetime import datetime, timedelta
from . import bp
from app.models import PayrollRecord
from app.utils.cleaning import clean_attendance_data

# Import các helper functions 
from .attendance_helpers import (
    get_attendance_period, 
    create_attendance_rows, 
    get_attendance_columns, 
    get_company_info
)
from .adjustment_handlers import apply_adjustment_handler, reset_adjustment_handler

@bp.route("/attendance_print/<filename>")
def attendance_print(filename):
    upload_folder = os.path.abspath(os.path.join(os.getcwd(), "uploads"))
    file_path = os.path.join(upload_folder, filename)

    if not os.path.exists(file_path):
        flash(f"File không tồn tại: {filename}", "danger")
        return redirect(url_for("main.index"))

    try:
        # ---- Lấy kỳ công từ file ----
        data = clean_attendance_data(file_path)
        period_str = get_attendance_period(data.get("att_meta", []))

        if not period_str:
            flash("Không xác định được kỳ công từ file!", "danger")
            return redirect(url_for("main.index"))

        period = period_str.strip()

        # ---- Lấy danh sách PayrollRecord ----
        records = (
            PayrollRecord.query
            .filter(PayrollRecord.period == period)
            .order_by(PayrollRecord.employee_code)
            .all()
        )

        if not records:
            flash("Không tìm thấy dữ liệu Payroll cho kỳ công này!", "warning")
            return redirect(url_for("main.index"))

        # ---- Tạo danh sách weekdays và ngày ----
        start_date = datetime.strptime(period + "-01", "%Y-%m-%d")
        last_day = (start_date.replace(day=28) + timedelta(days=4)).replace(day=1).day
        weekday_names = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ Nhật"]

        day_numbers = list(range(1, last_day + 1))
        weekdays = {d: weekday_names[datetime(start_date.year, start_date.month, d).weekday()] for d in day_numbers}

        # ---- Tạo dữ liệu cho template ----
        rows = create_attendance_rows(records, period)
        cols = get_attendance_columns()
        company_info = get_company_info(period)

        return render_template(
            "attendance_print.html",
            company=company_info,
            cols=cols,
            rows=rows,
            period=period,
            weekdays=weekdays,
            day_count=len(day_numbers),
            day_numbers=day_numbers,
            filename=filename
        )

    except Exception as e:
        print("Error in attendance_print route:", e, flush=True)
        flash(f"Lỗi khi tạo bảng chấm công in ký: {e}", "danger")
        return redirect(url_for("main.index"))
