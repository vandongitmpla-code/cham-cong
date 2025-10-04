from flask import redirect, url_for, flash, render_template, current_app
import os
from app.utils.cleaning import clean_attendance_data
import re
import calendar
from datetime import datetime, timedelta
from app.models import Employee, Payroll, db
from . import bp
from app.models import Employee, Payroll, Holiday, db
from flask import request


def _parse_holidays_for_month(holidays_config, ref_date):
    """
    holidays_config: list có thể chứa int (day-of-month) hoặc 'YYYY-MM-DD' strings hoặc digit-strings.
    ref_date: datetime.date (dùng để lọc holidays trong cùng tháng/năm).
    Trả về set các ngày (int) trong tháng ref_date là ngày lễ.
    """
    holiday_days = set()
    if not holidays_config or not ref_date:
        return holiday_days

    for h in holidays_config:
        try:
            if isinstance(h, int):
                holiday_days.add(h)
            elif isinstance(h, str):
                s = h.strip()
                # full date 'YYYY-MM-DD'
                if re.match(r'^\d{4}-\d{2}-\d{2}$', s):
                    dt = datetime.strptime(s, "%Y-%m-%d").date()
                    if dt.year == ref_date.year and dt.month == ref_date.month:
                        holiday_days.add(dt.day)
                # numeric day as string '2' or '02'
                elif s.isdigit():
                    holiday_days.add(int(s))
                # ignore other formats for now
        except Exception:
            continue
    return holiday_days

def _render_status(cell_val):
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
                    last_day = calendar.monthrange(year, month)[1]
                    day_numbers = list(range(1, last_day + 1))
                    for d in day_numbers:
                        dt = datetime(year, month, d)
                        weekdays[d] = weekday_names[dt.weekday()]
                else:
                    # Kỳ công qua nhiều tháng -> fallback lấy cột số có trong file
                    file_day_cols = sorted([int(c) for c in df.columns if str(c).strip().isdigit()])
                    day_numbers = file_day_cols
                    for d in day_numbers:
                        # weekdays may be ambiguous across months; leave mapping if possible
                        try:
                            # try to map using start_date's month as base if available
                            if start_date:
                                dt = datetime(start_date.year, start_date.month, d)
                                weekdays[d] = weekday_names[dt.weekday()]
                        except Exception:
                            weekdays[d] = ""
        except Exception as e:
            print("Lỗi tạo danh sách ngày/weekday:", e, flush=True)

        # fallback chung
        if not day_numbers:
            day_numbers = sorted([int(c) for c in df.columns if str(c).isdigit()])

        if not day_numbers:
            flash("Không tìm thấy cột ngày (1..N) trong file", "danger")
            return redirect(url_for("main.index"))

        # --- Lấy danh sách ngày lễ từ cấu hình (nếu có) ---
        holidays_config = current_app.config.get("PAYROLL_HOLIDAYS", [])
      # --- Lấy holidays từ DB theo tháng kỳ công ---
        holidays = []
        holiday_days = set()
        if start_date:
            holidays = Holiday.query.filter(
                db.extract("year", Holiday.date) == start_date.year,
                db.extract("month", Holiday.date) == start_date.month
            ).all()
            holiday_days = {h.date.day for h in holidays}

        # --- Tạo dữ liệu bảng payroll ---
        cols = ["Mã", "Tên", "Phòng ban", "Ngày công", "Ngày vắng", "Chủ nhật", "Lễ, tết"] + [str(d) for d in day_numbers]
        records = []
        for _, row in df.iterrows():
            emp_id = row.get("Mã", "") or ""
            emp_name = row.get("Tên", "") or ""
            emp_dept = row.get("Phòng ban", "") or ""

            tong_x = 0
            x_chu_nhat = 0
            x_le = 0
            ngay_vang = 0
            day_statuses = []

            for d in day_numbers:
                key = str(d)
                val = row.get(key, "") if key in df.columns else ""
                status = _render_status(val)
                day_statuses.append(status)

                if status == "x":
                    tong_x += 1
                    if d in holiday_days:
                        x_le += 1
                    else:
                        wd = (weekdays.get(d, "") or "").lower()
                        if "chủ" in wd or "cn" in wd or "sun" in wd:
                            x_chu_nhat += 1
                elif status == "v":
                    ngay_vang += 1

            # công thức tính ngày công
            ngay_cong = tong_x - x_chu_nhat - (x_le * 2)
            if ngay_cong < 0:
                ngay_cong = 0

            row_list = [emp_id, emp_name, emp_dept, ngay_cong, ngay_vang, x_chu_nhat, x_le] + day_statuses
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
            day_count=len(day_numbers),
            holidays=holidays,         # ✅ truyền holidays để hiển thị
            holiday_days=holiday_days  # ✅ truyền list ngày lễ cho highlight
        )
    except Exception as e:
        print("Error in payroll route:", e, flush=True)
        flash(f"Lỗi khi tạo Bảng công tính lương: {e}", "danger")
        return redirect(url_for("main.index"))


# Import dữ liệu Payroll (dùng cùng logic)
@bp.route("/import_payroll/<filename>", methods=["POST"])
def import_payroll(filename):
    import re
    import calendar
    from datetime import datetime
    from app.models import Employee, PayrollRecord, Holiday
    from flask import current_app, request

    upload_folder = os.path.abspath(os.path.join(os.getcwd(), "uploads"))
    file_path = os.path.join(upload_folder, filename)

    try:
        data = clean_attendance_data(file_path)
        df = data["att_log"]

        # --- Lấy kỳ công ---
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

        if not period_str or "~" not in period_str:
            flash("Không xác định được kỳ công trong file!", "danger")
            return redirect(url_for("main.payroll", filename=filename))

        start_s, end_s = period_str.split("~")
        start_date = datetime.strptime(start_s.strip(), "%Y-%m-%d")
        end_date = datetime.strptime(end_s.strip(), "%Y-%m-%d")
        period = start_date.strftime("%Y-%m")

        # --- Tạo danh sách ngày trong tháng ---
        weekday_names = ["Thứ 2","Thứ 3","Thứ 4","Thứ 5","Thứ 6","Thứ 7","Chủ Nhật"]
        year, month = start_date.year, start_date.month
        last_day = calendar.monthrange(year, month)[1]
        day_numbers = list(range(1, last_day + 1))
        weekdays = {d: weekday_names[datetime(year, month, d).weekday()] for d in day_numbers}

        # --- Lấy ngày lễ trong DB ---
        holidays = Holiday.query.filter(
            db.extract("year", Holiday.date) == year,
            db.extract("month", Holiday.date) == month
        ).all()
        holiday_days = {h.date.day for h in holidays}

        # --- Xoá dữ liệu PayrollRecord cũ của kỳ này ---
        PayrollRecord.query.filter_by(period=period).delete()

        # --- Hàm tính status theo cell ---
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

        # --- Tạo danh sách PayrollRecord ---
        records = []
        for _, row in df.iterrows():
            emp_code = str(row.get("Mã", "")).strip()
            emp = Employee.query.filter(
                (Employee.code == emp_code) | (Employee.att_code == emp_code)
            ).first()
            if not emp:
                continue

            ngay_cong = 0
            ngay_vang = 0
            chu_nhat = 0
            le_tet = 0
            tang_ca_nghi = 0
            tang_ca_tuan = 0
            ghi_chu = ""
            daily_status = {}

            for d in day_numbers:
                key = str(d)
                status = render_status(row.get(key, ""))
                daily_status[d] = status

                wd = (weekdays.get(d, "") or "").lower()
                is_sunday = ("chủ" in wd) or ("cn" in wd) or ("sun" in wd)
                is_holiday = d in holiday_days

                if status == "x":
                    if is_sunday:
                        chu_nhat += 1
                        tang_ca_nghi += 8
                    elif is_holiday:
                        le_tet += 1
                    else:
                        ngay_cong += 1
                elif status == "0.5":
                    if not is_sunday:
                        ngay_cong += 0.5
                elif status == "v":
                    ngay_vang += 1

           # --- Ghi chú chi tiết theo định dạng ---
            cn_days = []
            le_days = []
            nghi_days = []

            for d in day_numbers:
                wd = (weekdays.get(d, "") or "").lower()
                is_sunday = ("chủ" in wd) or ("cn" in wd) or ("sun" in wd)
                is_holiday = d in holiday_days
                status = daily_status.get(d, "")

                # Chủ nhật có làm
                if is_sunday and status == "x":
                    cn_days.append(d)

                # Làm ngày lễ
                if is_holiday and status == "x":
                    le_days.append(d)

                # Nghỉ (v)
                if status == "v":
                    nghi_days.append(d)

            # Tạo ghi chú chi tiết
            parts = []
            if cn_days:
                parts.append(f"Tăng ca {len(cn_days)} ngày CN: {','.join(str(d) for d in cn_days)}")
            if le_days:
                parts.append(f"Làm {len(le_days)} ngày Lễ: {','.join(f'{d:02d}/{month:02d}' for d in le_days)}")
            if nghi_days:
                parts.append(f"Nghỉ ngày: {','.join(f'{d:02d}/{month:02d}/{year}' for d in nghi_days)}")

            ghi_chu = " / ".join(parts)

            # 🔹 GÁN GHI CHÚ VÀO RECORD
            record.note = ghi_chu

            db.session.bulk_save_objects(records)
            db.session.commit()


        flash(f"Đã import {len(records)} bản ghi payroll vào Database!", "success")

    except Exception as e:
        db.session.rollback()
        flash(f"Lỗi khi import payroll: {e}", "danger")

    return redirect(url_for("main.payroll", filename=filename))



# Thêm ngày lễ
@bp.route("/add_holiday", methods=["POST"])
def add_holiday():
    try:
        holiday_date = request.form.get("holiday_date")
        holiday_name = request.form.get("holiday_name")

        if not holiday_date:
            flash("Ngày lễ không được để trống", "danger")
            return redirect(url_for("main.payroll", filename=request.args.get("filename")))

        # lưu vào DB
        h = Holiday(
            date=datetime.strptime(holiday_date, "%Y-%m-%d").date(),
            name=holiday_name
        )
        db.session.add(h)
        db.session.commit()
        flash("Thêm ngày lễ thành công!", "success")

    except Exception as e:
        db.session.rollback()
        flash(f"Lỗi khi thêm ngày lễ: {e}", "danger")

    return redirect(url_for("main.payroll", filename=request.args.get("filename")))


# Xóa ngày lễ
@bp.route("/delete_holiday/<int:holiday_id>", methods=["POST"])
def delete_holiday(holiday_id):
    filename = request.args.get("filename")  # lấy lại filename để redirect
    try:
        h = Holiday.query.get_or_404(holiday_id)
        db.session.delete(h)
        db.session.commit()
        flash("Xóa ngày lễ thành công!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Lỗi khi xóa ngày lễ: {e}", "danger")

    return redirect(url_for("main.payroll", filename=filename))
