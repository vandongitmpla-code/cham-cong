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


@bp.route("/attendance_print/<filename>")
def attendance_print(filename):
    import os
    from datetime import datetime, timedelta
    import re
    from app.models import Employee
    from app.extensions import db

    upload_folder = os.path.abspath(os.path.join(os.getcwd(), "uploads"))
    file_path = os.path.join(upload_folder, filename)

    if not os.path.exists(file_path):
        flash("File không tồn tại: " + filename, "danger")
        return redirect(url_for("main.index"))

    try:
        data = clean_attendance_data(file_path)
        df = data["att_log"]

        # ---- lấy kỳ công ----
        period_str = ""
        att_meta = data.get("att_meta")
        if att_meta and len(att_meta) > 0:
            header_row = att_meta[0]
            for cell in header_row:
                if isinstance(cell, str):
                    m = re.search(r'\d{4}-\d{2}-\d{2}\s*~\s*\d{4}-\d{2}-\d{2}', cell)
                    if m:
                        period_str = m.group(0)
                        break

        # ---- tạo danh sách ngày thuộc kỳ công (day_numbers) và mapping weekdays ----
        weekdays = {}
        day_numbers = []
        start_date = end_date = None
        if period_str and "~" in period_str:
            try:
                start_s, end_s = period_str.split("~")
                start_date = datetime.strptime(start_s.strip(), "%Y-%m-%d")
                end_date = datetime.strptime(end_s.strip(), "%Y-%m-%d")
                current = start_date
                weekday_names = ["Thứ 2","Thứ 3","Thứ 4","Thứ 5","Thứ 6","Thứ 7","Chủ Nhật"]
                while current <= end_date:
                    day_numbers.append(current.day)
                    weekdays[current.day] = weekday_names[current.weekday()]
                    current += timedelta(days=1)
            except Exception as e:
                print("Lỗi tạo days từ period:", e, flush=True)

        # ---- xác định cột ngày thực tế có trong file ----
        file_day_cols = sorted([int(c) for c in df.columns if str(c).strip().isdigit()], key=lambda x: x)

        # nếu đã có day_numbers từ period, lấy giao với file_day_cols (nếu file thiếu cột ngày)
        if day_numbers:
            # intersection but keep order by day_numbers
            day_numbers = [d for d in day_numbers if d in file_day_cols] or day_numbers
        else:
            # fallback: dùng các cột số có trong file
            day_numbers = file_day_cols

        if not day_numbers:
            flash("Không tìm thấy cột ngày hợp lệ trong file.", "danger")
            return redirect(url_for("main.index"))

        day_count = len(day_numbers)

        # ---- hàm render_status ----
        def render_status(cell_val):
            s = "" if cell_val is None else str(cell_val)
            times = re.findall(r'\d{1,2}:\d{2}', s)
            if not times:
                return "v"
            if len(times) == 1:
                return "warn"
            def to_minutes(t):
                hh, mm = t.split(":")
                return int(hh) * 60 + int(mm)
            mins = [to_minutes(t) for t in times]
            first = min(mins)
            last = max(mins)
            if last < first:
                last += 24 * 60
            diff = last - first
            if diff >= 7 * 60:
                return "x"
            if diff >= 3 * 60:
                return "0.5"
            return ""

        # ---- tính toán ----
        rows = []
        for idx, row in df.iterrows():
            emp_att_code = str(row.get("Mã", "")).strip()
            emp_name = row.get("Tên", "")
            emp_dept = row.get("Phòng ban", "")

            # tìm Employee theo att_code (trim)
            emp_db = Employee.query.filter(db.func.trim(Employee.att_code) == emp_att_code).first()

            loai_hd = emp_db.contract_type if emp_db else ""
            to = emp_db.team if emp_db else ""
            emp_code = emp_db.code if emp_db else emp_att_code

            thuc_te = 0.0
            nghi_khong_luong = 0
            nghi_cn_days = []
            tang_ca_nghi = 0.0
            cn_x_days = []
            nghi_days = []

            # lấy month_str (dùng cho ghi chú)
            month_str = ""
            if start_date:
                month_str = start_date.strftime("%m/%Y")

            # lưu toàn bộ dữ liệu gốc (theo day_numbers order) cho modal
            days_raw = [row.get(str(d), "") for d in day_numbers]

            for d in day_numbers:
                key = str(d)
                status = render_status(row.get(key, ""))
                wd = (weekdays.get(d, "") or "").lower()

                if status == "x":
                    # nếu là chủ nhật (hoặc chứa cn/chủ/sun) tính vào tang ca CN
                    if ("chủ" in wd) or ("cn" in wd) or ("sun" in wd):
                        tang_ca_nghi += 8.0
                        cn_x_days.append(d)
                    else:
                        thuc_te += 1.0
                elif status == "0.5":
                    # nửa ngày (chỉ nếu không phải chủ nhật)
                    if not (("chủ" in wd) or ("cn" in wd) or ("sun" in wd)):
                        thuc_te += 0.5
                elif status == "v":
                    nghi_khong_luong += 1
                    nghi_days.append(d)
                    if ("chủ" in wd) or ("cn" in wd) or ("sun" in wd):
                        nghi_cn_days.append(d)
                # warn / "" không cộng vào

            # ---- bù ngày công từ tăng ca CN ----
            ngay_quy_dinh = 26
            if thuc_te < ngay_quy_dinh and tang_ca_nghi > 0:
                missing_days = ngay_quy_dinh - thuc_te
                available_days = int(tang_ca_nghi // 8)
                used_days = min(missing_days, available_days)
                thuc_te += used_days
                tang_ca_nghi -= used_days * 8

            # ---- ghi chú ----
            ghi_chu = ""
            if cn_x_days:
                ghi_chu = f"Tăng ca {len(cn_x_days)} ngày CN: {','.join(map(str, cn_x_days))}"
            if nghi_days and month_str:
                if len(nghi_days) < 15:
                    days_fmt = ",".join([f"{d:02d}" for d in nghi_days])
                    if ghi_chu:
                        ghi_chu += f" / Nghỉ ngày: {days_fmt}/{month_str}"
                    else:
                        ghi_chu = f"Nghỉ ngày: {days_fmt}/{month_str}"
                else:
                    if ghi_chu:
                        ghi_chu += "|||ICON"
                    else:
                        ghi_chu = "ICON_ONLY"

            rows.append([
                idx + 1,
                emp_code,
                emp_name,
                emp_dept,
                loai_hd,
                ngay_quy_dinh,
                "",  # nghỉ phép năm
                {"count": nghi_khong_luong, "sundays": nghi_cn_days},
                thuc_te,
                tang_ca_nghi,
                "",  # tăng ca trong tuần
                ghi_chu,
                "",  # bắt đầu tính phép
                "",  # phép tồn
                to,
                {   # object chi tiết cho modal (days theo đúng ngày trong period)
                    "Mã": emp_code,
                    "Tên": emp_name,
                    "Phòng ban": emp_dept,
                    "days": days_raw
                }
            ])

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

        company_info = {
            "name": "CÔNG TY CP CÔNG NGHỆ OTANICS",
            "tax": "2001337320",
            "address": "KCN phường 8, phường Lý Văn Lâm, Tỉnh Cà Mau, Việt Nam",
            "title": f"BẢNG CHẤM CÔNG VÀ HIỆU SUẤT {start_date.strftime('%m/%Y') if start_date else ''}"
        }

        return render_template(
            "attendance_print.html",
            company=company_info,
            cols=cols,
            rows=rows,
            period=period_str,
            weekdays=weekdays,
            day_count=day_count,
            day_numbers=day_numbers  # nếu muốn dùng explicit list bên client
        )

    except Exception as e:
        print("Error in attendance_print route:", e, flush=True)
        flash(f"Lỗi khi tạo bảng chấm công in ký: {e}", "danger")
        return redirect(url_for("main.index"))
