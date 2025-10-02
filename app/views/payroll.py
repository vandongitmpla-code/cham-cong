from flask import Blueprint, render_template, request, redirect, url_for, flash
import os
from werkzeug.utils import secure_filename
from app.utils.cleaning import clean_attendance_data
import datetime
import pandas as pd
from flask import send_file
import io
from app.models import Employee, AttendanceLog, Payroll, db
import re

# Import dữ liệu Payroll
@bp.route("/import_payroll/<filename>", methods=["POST"])
def import_payroll(filename):
    upload_folder = os.path.abspath(os.path.join(os.getcwd(), "uploads"))
    file_path = os.path.join(upload_folder, filename)


    try:
        data = clean_attendance_data(file_path)
        df = data["att_log"]

        # lấy kỳ công
        period_str = ""
        att_meta = data.get("att_meta")
        if att_meta and len(att_meta) > 0:
            header_row = att_meta[0]
            for cell in header_row:
                if isinstance(cell, str):
                    m = re.search(r'\d{4}-\d{2}-\d{2}', cell)
                    if m:
                        period_str = cell
                        break

        # lấy tháng (YYYY-MM)
        month_str = ""
        if period_str and "~" in period_str:
            start_s, _ = period_str.split("~")
            start_date = datetime.strptime(start_s.strip(), "%Y-%m-%d")
            month_str = start_date.strftime("%Y-%m")

        # xoá dữ liệu cũ payroll cùng tháng
        db.session.query(Payroll).filter_by(month=month_str).delete()

        objs = []
        # giả sử payroll logic đã tính ở /payroll
        # ở đây ví dụ đơn giản chỉ lấy số ngày công = số ngày có status "x"
        for _, row in df.iterrows():
            emp_code = str(row.get("Mã", "")).strip()
            emp = Employee.query.filter_by(code=emp_code).first()
            if not emp:
                continue

            working_days = 0
            for d in [c for c in df.columns if str(c).isdigit()]:
                val = str(row.get(d, "")).strip()
                if val:
                    times = re.findall(r'\d{1,2}:\d{2}', val)
                    if len(times) >= 2:
                        working_days += 1

            payroll = Payroll(
                employee_id=emp.id,
                month=month_str,
                working_days=working_days,
                salary=emp.salary_base * working_days / 26.0
            )
            objs.append(payroll)

        db.session.bulk_save_objects(objs)
        db.session.commit()
        flash("Import Payroll thành công!", "success")

    except Exception as e:
        db.session.rollback()
        flash(f"Lỗi khi import payroll: {e}", "danger")

    return redirect(url_for("main.payroll", filename=filename))