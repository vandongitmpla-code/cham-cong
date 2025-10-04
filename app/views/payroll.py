from flask import  redirect, url_for, flash, render_template
import os
from app.utils.cleaning import clean_attendance_data
import datetime
from app.models import Employee, Payroll, db
import re, import calendar
from datetime import datetime, timedelta
from . import bp


# bảng công tính lương
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

        # --- Lấy period --- 
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

        # --- Tạo danh sách ngày và mapping weekdays ---
        weekdays = {}
        day_numbers = []
        start_date = end_date = None
        weekday_names = ["Thứ 2","Thứ 3","Thứ 4","Thứ 5","Thứ 6","Thứ 7","Chủ Nhật"]

        try:
            if period_str and "~" in period_str:
                start_s, end_s = period_str.split("~")
                start_date = datetime.strptime(start_s.strip(), "%Y-%m-%d")
                end_date = datetime.strptime(end_s.strip(), "%Y-%m-%d")

                # Nếu kỳ công nằm trong cùng 1 tháng -> hiển thị toàn bộ ngày của tháng đó
                if start_date.year == end_date.year and start_date.month == end_date.month:
                    year = start_date.year
                    month = start_date.month
                    last_day = calendar.monthrange(year, month)[1]   # số ngày trong tháng
                    day_numbers = list(range(1, last_day + 1))
                    for d in day_numbers:
                        dt = datetime(year, month, d)
                        weekdays[d] = weekday_names[dt.weekday()]
                else:
                    # Kỳ công qua nhiều tháng: fallback xuống lấy cột số có trong file
                    file_day_cols = sorted([int(c) for c in df.columns if str(c).strip().isdigit()])
                    day_numbers = file_day_cols
                    # optionally we can fill weekdays for these day numbers using start_date's month,
                    # but since they span months it's ambiguous — leaving weekdays for these as empty or partial.
        except Exception as e:
            print("Lỗi tạo danh sách ngày/weekday:", e, flush=True)

        # fallback chung: nếu vẫn chưa có day_numbers thì lấy từ cột trong file
        if not day_numbers:
            day_numbers = sorted([int(c) for c in df.columns if str(c).strip().isdigit()])

        if not day_numbers:
            flash("Không tìm thấy cột ngày (1..N) trong file", "danger")
            return redirect(url_for("main.index"))

        # --- Hàm quyết định trạng thái ---
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

        # --- Tạo dữ liệu bảng payroll ---
        cols = ["Mã", "Tên", "Phòng ban", "Ngày công", "Ngày vắng", "Chủ nhật"] + [str(d) for d in day_numbers]
        records = []
        for _, row in df.iterrows():
            emp_id = row.get("Mã", "") or ""
            emp_name = row.get("Tên", "") or ""
            emp_dept = row.get("Phòng ban", "") or ""

            ngay_cong = 0
            ngay_vang = 0
            chu_nhat = 0
            day_statuses = []

            for d in day_numbers:
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

        # sắp xếp theo tên
        records = sorted(records, key=lambda r: (r[1] or "").lower())

        return render_template(
            "payroll.html",
            filename=filename,
            cols=cols,
            rows=records,
            period=period_str,
            weekdays=weekdays,
            day_count=len(day_numbers)
        )

    except Exception as e:
        print("Error in payroll route:", e, flush=True)
        flash(f"Lỗi khi tạo Bảng công tính lương: {e}", "danger")
        return redirect(url_for("main.index"))


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