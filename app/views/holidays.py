from flask import render_template, request, redirect, url_for, flash
from . import bp
from app.models import Holiday, db
from datetime import datetime

# Danh sách ngày lễ
@bp.route("/holidays")
def holidays():
    holidays = Holiday.query.order_by(Holiday.date).all()
    return render_template("holidays.html", holidays=holidays)

# Thêm ngày lễ
@bp.route("/add_holiday", methods=["POST"])
def add_holiday():
    try:
        date_str = request.form.get("holiday_date")
        name = request.form.get("holiday_name")
        filename = request.args.get("filename")  # để redirect lại đúng file

        if not date_str:
            flash("Vui lòng chọn ngày lễ!", "warning")
            return redirect(url_for("main.payroll", filename=filename))

        holiday_date = datetime.strptime(date_str, "%Y-%m-%d").date()

        # kiểm tra trùng ngày
        exists = Holiday.query.filter_by(date=holiday_date).first()
        if exists:
            flash("Ngày lễ này đã tồn tại!", "warning")
        else:
            holiday = Holiday(date=holiday_date, name=name or "")
            db.session.add(holiday)
            db.session.commit()
            flash("Thêm ngày lễ thành công!", "success")

    except Exception as e:
        db.session.rollback()
        flash(f"Lỗi khi thêm ngày lễ: {e}", "danger")

    return redirect(url_for("main.payroll", filename=filename))


# Xóa ngày lễ
@bp.route("/delete_holiday/<int:holiday_id>")
def delete_holiday(holiday_id):
    filename = request.args.get("filename")
    try:
        holiday = Holiday.query.get_or_404(holiday_id)
        db.session.delete(holiday)
        db.session.commit()
        flash("Xóa ngày lễ thành công!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Lỗi khi xóa ngày lễ: {e}", "danger")

    return redirect(url_for("main.payroll", filename=filename))
# Xóa ngày lễ
@bp.route("/holidays/delete/<int:holiday_id>", methods=["POST"])
def delete_holiday(holiday_id):
    holiday = Holiday.query.get_or_404(holiday_id)
    try:
        db.session.delete(holiday)
        db.session.commit()
        flash("Xóa ngày lễ thành công!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Lỗi khi xóa ngày lễ: {e}", "danger")
    return redirect(url_for("main.holidays"))
