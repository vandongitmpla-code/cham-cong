from flask import render_template, redirect, url_for, flash
import os
from datetime import datetime, timedelta
from . import bp
from app.models import db, PayrollRecord, Employee


@bp.route("/attendance_print/<filename>")
def attendance_print(filename):
    upload_folder = os.path.abspath(os.path.join(os.getcwd(), "uploads"))
    file_path = os.path.join(upload_folder, filename)

    if not os.path.exists(file_path):
        flash(f"File không tồn tại: {filename}", "danger")
        return redirect(url_for("main.index"))

    try:
        # ---- Lấy kỳ công từ file để tìm period ----
        from app.utils.cleaning import clean_attendance_data
        import re

        data = clean_attendance_data(file_path)
        att_meta = data.get("att_meta", [])

        period_str = ""
        if att_meta and len(att_meta) > 0:
            header_row = att_meta[0]
            for cell in header_row:
                if isinstance(cell, str):
                    m = re.search(r"\d{4}-\d{2}", cell)
                    if m:
                        period_str = m.group(0)
                        break

        if not period_str:
            flash("Không xác định được kỳ công từ file!", "danger")
            return redirect(url_for("main.index"))

        period = period_str.strip()  # Ví dụ "2025-09"

        # ---- Lấy danh sách PayrollRecord cho kỳ công đó ----
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
        last_day = (start_date.replace(day=28) + timedelta(days=4)).day
        weekday_names = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ Nhật"]

        day_numbers = list(range(1, last_day + 1))
        weekdays = {d: weekday_names[datetime(start_date.year, start_date.month, d).weekday()] for d in day_numbers}

        # ---- Tạo dữ liệu bảng attendance_print ----
        rows = []
        for rec in records:
            rows.append([
                rec.id,                       # STT
                rec.employee_code,            # Mã số
                rec.employee_name,            # Họ và tên
                rec.phong_ban,                # Phòng ban
                rec.loai_hd,                  # Loại HĐ
                26,                            # Số ngày/giờ làm việc quy định trong tháng (mặc định 26)
                "",                            # Nghỉ phép năm
                rec.ngay_vang,                # Số ngày nghỉ không lương
                rec.ngay_cong,                 # Số ngày/giờ làm việc thực tế
                rec.tang_ca_nghi,             # Số giờ làm việc tăng ca (ngày nghỉ hàng tuần)
                rec.tang_ca_tuan,             # Số giờ làm việc tăng ca (ngày làm trong tuần)
                rec.ghi_chu,                  # Ghi chú
                "", "",                       # Bắt đầu tính phép từ tháng / Số ngày phép còn tồn
                rec.to,                       # Tổ
                {}                             # Chi tiết (có thể thêm nếu cần)
            ])

        cols = [
            "STT", "Mã số", "Họ và tên", "Phòng ban", "Loại HĐ",
            "Số ngày/giờ làm việc quy định trong tháng", "Số ngày nghỉ phép năm",
            "Số ngày nghỉ không lương", "Số ngày/giờ làm việc thực tế trong tháng",
            "Số giờ làm việc tăng ca (ngày nghỉ hàng tuần)",
            "Số giờ làm việc tăng ca (ngày làm trong tuần)",
            "Ghi chú", "Bắt đầu tính phép từ tháng",
            "Số ngày phép còn tồn", "Tổ", "Chi tiết"
        ]

        company_info = {
            "name": "CÔNG TY CP CÔNG NGHỆ OTANICS",
            "tax": "2001337320",
            "address": "KCN phường 8, phường Lý Văn Lâm, Tỉnh Cà Mau, Việt Nam",
            "title": f"BẢNG CHẤM CÔNG VÀ HIỆU SUẤT {period}"
        }

        return render_template(
            "attendance_print.html",
            company=company_info,
            cols=cols,
            rows=rows,
            period=period,
            weekdays=weekdays,
            day_count=len(day_numbers),
            day_numbers=day_numbers
        )

    except Exception as e:
        print("Error in attendance_print route:", e, flush=True)
        flash(f"Lỗi khi tạo bảng chấm công in ký: {e}", "danger")
        return redirect(url_for("main.index"))
