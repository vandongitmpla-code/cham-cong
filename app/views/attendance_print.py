from flask import  render_template, redirect, url_for, flash
import os
from app.utils.cleaning import clean_attendance_data
from . import bp
from app.models import db
import os
from datetime import datetime, timedelta
import re
from app.models import Employee
from app.extensions import db   
from app.models import db, PayrollRecord, Employee

@bp.route("/attendance_print/<filename>")
def attendance_print(filename):
    """
    In bảng chấm công (đọc dữ liệu Payroll từ database).
    filename vẫn được giữ lại để tương thích UI, 
    nhưng không dùng để đọc file thực tế nữa.
    """
    try:
        # --- Xác định tháng từ filename hoặc lấy tháng hiện tại ---
        # VD: filename = "payroll_2025-09.xlsx" -> lấy "2025-09"
        import re
        m = re.search(r"(\d{4})-(\d{2})", filename)
        if m:
            month = m.group(0)
        else:
            now = datetime.now()
            month = f"{now.year}-{now.month:02d}"

        # --- Truy vấn payroll records từ DB ---
        records = (
            db.session.query(PayrollRecord)
            .join(Employee, PayrollRecord.employee_id == Employee.id)
            .filter(PayrollRecord.month == month)
            .order_by(Employee.code)
            .all()
        )

        if not records:
            flash(f"Không tìm thấy dữ liệu Payroll cho kỳ {month}.", "warning")
            return redirect(url_for("main.index"))

        # --- Tạo dữ liệu để hiển thị ---
        rows = []
        for idx, pr in enumerate(records, start=1):
            emp = pr.employee
            rows.append([
                idx,
                emp.code,
                emp.name,
                emp.department or "",
                emp.contract_type or "",
                pr.ngay_cong,          # ✅ Số ngày làm việc quy định
                "",                    # Nghỉ phép năm (để trống)
                pr.ngay_vang,          # ✅ Số ngày nghỉ không lương
                pr.ngay_cong,          # ✅ Số ngày làm việc thực tế
                pr.tang_ca_nghi,       # ✅ Số giờ làm việc tăng ca CN
                "",                    # Tăng ca trong tuần (để trống)
                pr.ghi_chu or "",      # ✅ Ghi chú
                "", "",                # Bắt đầu tính phép, phép tồn
                emp.team or "",        # Tổ
                {}                     # Chi tiết (nếu cần cho modal)
            ])

        # --- Cấu trúc cột như trong template ---
        cols = [
            "STT","Mã số","Họ và tên","Phòng ban","Loại HĐ",
            "Số ngày/giờ làm việc quy định trong tháng",
            "Số ngày nghỉ phép năm","Số ngày nghỉ không lương",
            "Số ngày/giờ làm việc thực tế trong tháng",
            "Số giờ làm việc tăng ca (ngày nghỉ hàng tuần)",
            "Số giờ làm việc tăng ca (ngày làm trong tuần)",
            "Ghi chú","Bắt đầu tính phép từ tháng",
            "Số ngày phép còn tồn","Tổ","Chi tiết"
        ]

        # --- Thông tin công ty ---
        company_info = {
            "name": "CÔNG TY CP CÔNG NGHỆ OTANICS",
            "tax": "2001337320",
            "address": "KCN phường 8, phường Lý Văn Lâm, Tỉnh Cà Mau, Việt Nam",
            "title": f"BẢNG CHẤM CÔNG VÀ HIỆU SUẤT THÁNG {month[5:]}/{month[:4]}"
        }

        # --- Trả về giao diện ---
        return render_template(
            "attendance_print.html",
            company=company_info,
            cols=cols,
            rows=rows,
            period=month,
            weekdays={}, day_count=30, day_numbers=[]
        )

    except Exception as e:
        print("Error in attendance_print route:", e, flush=True)
        flash(f"Lỗi khi tạo bảng chấm công in ký: {e}", "danger")
        return redirect(url_for("main.index"))