from flask import  render_template, request, redirect, url_for, flash
import os
from werkzeug.utils import secure_filename
from app.utils.cleaning import clean_attendance_data
from flask import send_file
from . import bp
from app.models import db


#bảng công tính lương
@bp.route("/payroll/<filename>")
def payroll(filename):
    upload_folder = os.path.abspath(os.path.join(os.getcwd(), "uploads"))
    file_path = os.path.join(upload_folder, filename)

    if not os.path.exists(file_path):
        flash("File không tồn tại: " + filename, "danger")
        return redirect(url_for("main.index"))

    try:
        data = clean_attendance_data(file_path)
        df = data["att_log"]

        # Lấy period (vd: "2025-08-01 ~ 2025-08-31") từ att_meta nếu có
        import re
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
            if not period_str and isinstance(header_row[0], str) and header_row[0].strip():
                period_str = header_row[0].strip()

        # Tạo map weekdays: day number -> "Thứ X" / "Chủ Nhật"
        from datetime import datetime, timedelta
        weekdays = {}
        try:
            if period_str and "~" in period_str:
                start_s, end_s = period_str.split("~")
                start_date = datetime.strptime(start_s.strip(), "%Y-%m-%d")
                end_date = datetime.strptime(end_s.strip(), "%Y-%m-%d")
                current = start_date
                weekday_names = ["Thứ 2","Thứ 3","Thứ 4","Thứ 5","Thứ 6","Thứ 7","Chủ Nhật"]
                while current <= end_date:
                    weekdays[current.day] = weekday_names[current.weekday()]
                    current += timedelta(days=1)
        except Exception as e:
            print("Lỗi tạo weekdays:", e, flush=True)

        # Xác định cột ngày (1..N)
        day_cols = [c for c in df.columns if str(c).strip().isdigit()]
        day_cols = sorted(day_cols, key=lambda x: int(str(x).strip())) if day_cols else []
        if not day_cols:
            flash("Không tìm thấy cột ngày (1..31) trong file", "danger")
            return redirect(url_for("main.index"))

        day_count = max(int(str(c)) for c in day_cols)

        # Hàm quyết định trạng thái giống modal: 'x', '0.5', 'v', 'warn', '' (empty)
        import re
        def render_status(cell_val):
            s = "" if cell_val is None else str(cell_val)
            times = re.findall(r'\d{1,2}:\d{2}', s)
            if not times:
                return "v"
            if len(times) == 1:
                return "warn"
            # chuyển sang phút và tính diff first->last (handle qua đêm)
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

        # Tạo dữ liệu rows: mỗi hàng là list tương ứng cols order
        cols = ["Mã", "Tên", "Phòng ban", "Ngày công", "Ngày vắng", "Chủ nhật"] + [str(i) for i in range(1, day_count+1)]
        records = []
        for _, row in df.iterrows():
            emp_id = row.get("Mã", "") or ""
            emp_name = row.get("Tên", "") or ""
            emp_dept = row.get("Phòng ban", "") or ""

            ngay_cong = 0
            ngay_vang = 0
            chu_nhat = 0
            day_statuses = []
            for d in range(1, day_count+1):
                key = str(d)
                val = row.get(key, "") if key in df.columns else ""
                status = render_status(val)
                day_statuses.append(status)
                if status == "x":
                    ngay_cong += 1
                    wd = (weekdays.get(d, "") or "").lower()
                    if "chủ" in wd or "cn" in wd or "sun" in wd:
                        chu_nhat += 1
                elif status == "v":
                    ngay_vang += 1

            row_list = [emp_id, emp_name, emp_dept, ngay_cong, ngay_vang, chu_nhat] + day_statuses
            records.append(row_list)

        # sắp xếp theo tên (cột index 1)
        records = sorted(records, key=lambda r: (r[1] or "").lower())

        return render_template(
            "payroll.html",
            filename=filename,
            cols=cols,
            rows=records,
            period=period_str,
            weekdays=weekdays,
            day_count=day_count
        )

    except Exception as e:
        print("Error in payroll route:", e, flush=True)
        flash(f"Lỗi khi tạo Bảng công tính lương: {e}", "danger")
        return redirect(url_for("main.index"))

@bp.route("/attendance_print/<filename>")
def attendance_print(filename):
    upload_folder = os.path.abspath(os.path.join(os.getcwd(), "uploads"))
    file_path = os.path.join(upload_folder, filename)

    if not os.path.exists(file_path):
        flash("File không tồn tại: " + filename, "danger")
        return redirect(url_for("main.index"))

    try:
        from app.models import Employee
        data = clean_attendance_data(file_path)
        df = data["att_log"]

        # ---- lấy kỳ công ----
        period_str = ""
        att_meta = data.get("att_meta")
        if att_meta and len(att_meta) > 0:
            header_row = att_meta[0]
            import re
            for cell in header_row:
                if isinstance(cell, str):
                    m = re.search(r'\d{4}-\d{2}-\d{2}\s*~\s*\d{4}-\d{2}-\d{2}', cell)
                    if m:
                        period_str = m.group(0)
                        break

        # ---- tạo map weekdays ----
        weekdays = {}
        from datetime import datetime, timedelta
        if period_str and "~" in period_str:
            try:
                start_s, end_s = period_str.split("~")
                start_date = datetime.strptime(start_s.strip(), "%Y-%m-%d")
                end_date = datetime.strptime(end_s.strip(), "%Y-%m-%d")
                current = start_date
                weekday_names = ["Thứ 2","Thứ 3","Thứ 4","Thứ 5","Thứ 6","Thứ 7","Chủ Nhật"]
                while current <= end_date:
                    weekdays[current.day] = weekday_names[current.weekday()]
                    current += timedelta(days=1)
            except Exception as e:
                print("Lỗi tạo weekdays:", e, flush=True)

        # ---- xác định cột ngày ----
        day_cols = [c for c in df.columns if str(c).isdigit()]
        day_cols = sorted(day_cols, key=lambda x: int(x)) if day_cols else []
        day_count = max(int(c) for c in day_cols) if day_cols else 0

        # ---- hàm render_status ----
        def render_status(cell_val):
            import re
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

            # lấy nhân viên từ DB bằng att_code
            emp_db = Employee.query.filter(
                db.func.trim(Employee.att_code) == emp_att_code
            ).first()

            loai_hd = emp_db.contract_type if emp_db else ""
            to = emp_db.team if emp_db else ""
            emp_code = emp_db.code if emp_db else emp_att_code

            thuc_te = 0
            nghi_khong_luong = 0
            nghi_cn_days = []
            tang_ca_nghi = 0.0
            cn_x_days = []
            nghi_days = []

            # lấy tháng từ kỳ công
            month_str = ""
            if period_str and "~" in period_str:
                try:
                    start_s, _ = period_str.split("~")
                    start_date = datetime.strptime(start_s.strip(), "%Y-%m-%d")
                    month_str = start_date.strftime("%m/%Y")
                except:
                    month_str = ""

            # lưu toàn bộ dữ liệu gốc cho modal
            days_raw = [row.get(str(d), "") for d in range(1, day_count + 1)]

            for d in range(1, day_count + 1):
                key = str(d)
                status = render_status(row.get(key, ""))
                wd = (weekdays.get(d, "") or "").lower()

                if status == "x":
                    if not ("chủ" in wd or "cn" in wd or "sun" in wd):
                        thuc_te += 1
                    else:
                        tang_ca_nghi += 8.0
                        cn_x_days.append(d)
                elif status == "0.5":
                    if not ("chủ" in wd or "cn" in wd or "sun" in wd):
                        thuc_te += 0.5
                elif status == "v":
                    nghi_khong_luong += 1
                    nghi_days.append(d)
                    if "chủ" in wd or "cn" in wd or "sun" in wd:
                        nghi_cn_days.append(d)

            # ---- bù ngày công từ tăng ca CN ----
            ngay_quy_dinh = 26
            if thuc_te < ngay_quy_dinh and tang_ca_nghi > 0:
                missing_days = ngay_quy_dinh - thuc_te
                available_days = tang_ca_nghi // 8
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
                {   # object chi tiết cho modal
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
            "title": "BẢNG CHẤM CÔNG VÀ HIỆU SUẤT THÁNG 08/2025"
        }

        return render_template(
            "attendance_print.html",
            company=company_info,
            cols=cols,
            rows=rows,
            period=period_str,
            weekdays=weekdays,   # ✅ truyền thêm
            day_count=day_count  # ✅ truyền thêm
        )

    except Exception as e:
        print("Error in attendance_print route:", e, flush=True)
        flash(f"Lỗi khi tạo bảng chấm công in ký: {e}", "danger")
        return redirect(url_for("main.index"))