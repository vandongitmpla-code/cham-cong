from flask import Blueprint, render_template, request, redirect, url_for, flash
import os
from . import bp
from werkzeug.utils import secure_filename
from app.utils.cleaning import clean_attendance_data
import datetime
import pandas as pd
from flask import send_file
import io
from app.models import Employee, AttendanceLog, Payroll, db
import re

@bp.route("/import_employees", methods=["POST"])
def import_employees():
    from app.models import Employee, db
    import pandas as pd

    file = request.files.get("file")
    if not file:
        flash("Vui lòng chọn file Excel", "danger")
        return redirect(url_for("main.index"))

    try:
        df = pd.read_excel(file)

        for _, row in df.iterrows():
            emp = Employee(
                code=str(row.get("Mã số", "")).strip(),
                name=row.get("Họ và tên", "").strip(),
                team=row.get("Tổ", ""),
                department=row.get("Phòng ban", ""),
                contract_type=row.get("Loại HĐ", ""),
                salary_base=0  # có thể cập nhật từ file khác
            )
            db.session.add(emp)

        db.session.commit()
        flash("Import nhân viên thành công!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Lỗi khi import nhân viên: {e}", "danger")

    return redirect(url_for("main.index"))

# Danh sách nhân viên
@bp.route("/employees")
def employees():
    employees = Employee.query.all()
    return render_template("employees.html", employees=employees)

# Thêm nhân viên
@bp.route("/employees/add", methods=["GET", "POST"])
def add_employee():
    if request.method == "POST":
        code = request.form.get("code")
        name = request.form.get("name")
        team = request.form.get("team")
        department = request.form.get("department")
        contract_type = request.form.get("contract_type")

        try:
            emp = Employee(
                code=code,
                name=name,
                team=team,
                department=department,
                contract_type=contract_type,
                salary_base=0
            )
            db.session.add(emp)
            db.session.commit()
            flash("Thêm nhân viên thành công!", "success")
            return redirect(url_for("main.employees"))
        except Exception as e:
            db.session.rollback()
            flash(f"Lỗi khi thêm nhân viên: {e}", "danger")

    return render_template("add_employee.html")

# Sửa nhân viên
@bp.route("/employees/edit/<int:emp_id>", methods=["GET", "POST"])
def edit_employee(emp_id):
    emp = Employee.query.get_or_404(emp_id)

    if request.method == "POST":
        emp.code = request.form.get("code")
        emp.name = request.form.get("name")
        emp.team = request.form.get("team")
        emp.department = request.form.get("department")
        emp.contract_type = request.form.get("contract_type")
        emp.att_code = request.form.get("att_code")  # ✅ thêm dòng này
        try:
            db.session.commit()
            flash("Cập nhật nhân viên thành công!", "success")
            return redirect(url_for("main.employees"))
        except Exception as e:
            db.session.rollback()
            flash(f"Lỗi khi cập nhật nhân viên: {e}", "danger")

    return render_template("edit_employee.html", emp=emp)

# Xóa nhân viên
@bp.route("/employees/delete/<int:emp_id>", methods=["POST"])
def delete_employee(emp_id):
    emp = Employee.query.get_or_404(emp_id)
    try:
        db.session.delete(emp)
        db.session.commit()
        flash("Xóa nhân viên thành công!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Lỗi khi xóa nhân viên: {e}", "danger")
    return redirect(url_for("main.employees"))

@bp.route("/employees/<int:emp_id>/update_att_code", methods=["POST"])
def update_att_code(emp_id):
    from app.models import Employee
    from app.extensions import db

    emp = Employee.query.get_or_404(emp_id)
    new_att_code = request.form.get("att_code")

    if not new_att_code:
        flash("Mã chấm công không được để trống!", "warning")
        return redirect(url_for("main.employees"))

    new_att_code = new_att_code.strip()

    # Kiểm tra trùng
    exists = Employee.query.filter(
        Employee.att_code == new_att_code,
        Employee.id != emp_id
    ).first()
    if exists:
        flash("Mã chấm công đã tồn tại cho nhân viên khác!", "danger")
        return redirect(url_for("main.employees"))

    emp.att_code = new_att_code
    try:
        db.session.commit()
        flash("Cập nhật mã chấm công thành công!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Lỗi khi cập nhật mã chấm công: {e}", "danger")

    return redirect(url_for("main.employees"))