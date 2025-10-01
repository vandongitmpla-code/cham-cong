# app/routes.py
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
bp = Blueprint("main", __name__)

ALLOWED_EXT = {".xls", ".xlsx"}

def parse_salary(val):
    # Trả về float; nếu rỗng hoặc không parse được -> 0.0
    if pd.isna(val) or val is None:
        return 0.0
    s = str(val).strip()
    if s == "":
        return 0.0
    # loại bỏ dấu ngăn nghìn và ký tự lạ
    s = s.replace(" ", "").replace(",", "").replace("₫", "")
    s = re.sub(r"[^\d\.]", "", s)
    try:
        return float(s)
    except:
        return 0.0

def allowed_filename(filename):
    _, ext = os.path.splitext(filename.lower())
    return ext in ALLOWED_EXT
@bp.route("/report/<filename>")
def report(filename):
    return render_template("report.html", filename=filename)


@bp.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files.get("file")
        if not file:
            flash("Vui lòng chọn file", "danger")
            return redirect(url_for("main.index"))

        filename = secure_filename(file.filename)
        upload_folder = os.path.abspath(os.path.join(os.getcwd(), "uploads"))
        os.makedirs(upload_folder, exist_ok=True)
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)

        flash("Upload thành công!", "success")
        return redirect(url_for("main.report", filename=filename))

    return render_template("upload.html")



@bp.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        flash("Không có file gửi lên.", "danger")
        return redirect(url_for("main.index"))

    f = request.files["file"]
    if f.filename == "":
        flash("Bạn chưa chọn file.", "warning")
        return redirect(url_for("main.index"))

    if not allowed_filename(f.filename):
        flash("Chỉ chấp nhận file .xls hoặc .xlsx", "warning")
        return redirect(url_for("main.index"))

    filename = secure_filename(f.filename)
    upload_folder = os.path.abspath(os.path.join(os.getcwd(), "uploads"))
    os.makedirs(upload_folder, exist_ok=True)
    save_path = os.path.join(upload_folder, filename)
    f.save(save_path)

    # Sau khi upload thành công -> render report.html
    return render_template("report.html", filename=filename)



def format_cell(cell):
    """Chuẩn hoá cell cho report.html (không phải timesheet)."""
    if cell is None or cell == "" or str(cell).lower() == "nan":
        return ""
    if isinstance(cell, (datetime.time, datetime.datetime, pd.Timestamp)):
        return cell.strftime("%H:%M")
    if isinstance(cell, (int, float)):
        try:
            return pd.to_datetime(cell, unit="d", origin="1899-12-30").strftime("%H:%M")
        except Exception:
            return str(cell)
    if isinstance(cell, str):
        import re

        times = re.findall(r"\d{1,2}:\d{2}", cell)
        if times:
            return "<br>".join(times)
    return str(cell)

@bp.route("/timesheet/<filename>")
def timesheet(filename):
    upload_folder = os.path.abspath(os.path.join(os.getcwd(), "uploads"))
    file_path = os.path.join(upload_folder, filename)

    if not os.path.exists(file_path):
        flash("File không tồn tại: " + filename, "danger")
        return redirect(url_for("main.index"))

    try:
        data = clean_attendance_data(file_path)
        df = data["att_log"]

        # Lấy period từ att_meta nếu có (tìm chuỗi dạng YYYY-MM-DD ~ YYYY-MM-DD)
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
            # fallback: lấy ô đầu tiên nếu không tìm thấy pattern
            if not period_str and isinstance(header_row[0], str) and header_row[0].strip():
                period_str = header_row[0].strip()

        if not period_str:
            period_str = ""  # nếu không có, để rỗng

        # Tạo mapping weekdays: key = day number (1..31) -> "Thứ 2"/.../"Chủ Nhật"
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

        # Xác định các cột ngày (1..31) có trong df
        day_cols = [c for c in df.columns if str(c).strip().isdigit()]
        day_cols = sorted(day_cols, key=lambda x: int(str(x).strip())) if day_cols else []
        if not day_cols:
            flash("Không tìm thấy cột ngày (1..31) trong file", "danger")
            return redirect(url_for("main.index"))

        # day_count = số ngày hiển thị (dựa vào day_cols)
        day_count = max(int(str(c)) for c in day_cols)

        # Chuẩn hoá ô ngày -> chuỗi (các giờ nối bằng "<br>")
        def normalize_cell(val):
            import re
            if isinstance(val, (list, tuple)):
                return "<br>".join(val)
            if pd.isna(val) or str(val).strip().lower() in ["", "nan"]:
                return ""
            times = re.findall(r"\d{1,2}:\d{2}", str(val))
            if times:
                return "<br>".join(times)
            # nếu chuỗi rỗng hoặc khác
            return str(val)

        # Tạo bản output: một hàng / nhân viên (các cột '1'..'N')
        records = []
        for _, row in df.iterrows():
            rec = {
                "Mã": row.get("Mã", ""),
                "Tên": row.get("Tên", ""),
                "Phòng ban": row.get("Phòng ban", "")
            }
            # điền theo thứ tự day_cols (nếu thiếu ngày nào thì vẫn tạo key)
            for d in range(1, day_count + 1):
                key = str(d)
                rec[key] = normalize_cell(row.get(key, "")) if key in df.columns else ""
            records.append(rec)

        df_out = pd.DataFrame(records)

        # đảm bảo thứ tự cột
        cols = ["Mã", "Tên", "Phòng ban"] + [str(i) for i in range(1, day_count + 1)]
        cols = [c for c in cols if c in df_out.columns]
        df_out = df_out[cols]

        # sắp xếp theo tên
        if "Tên" in df_out.columns:
            df_out = df_out.sort_values(by="Tên").reset_index(drop=True)

        cols_out = df_out.columns.tolist()
        rows_out = df_out.fillna("").values.tolist()

        return render_template(
            "timesheet.html",
            filename=filename,
            cols=cols_out,
            rows=rows_out,
            att_meta={"period": period_str},
            weekdays=weekdays,
            day_count=day_count,
            period=period_str
        )

    except Exception as e:
        print("Error in timesheet route:", e, flush=True)
        flash(f"Lỗi khi tạo Bảng chấm công: {e}", "danger")
        return redirect(url_for("main.index"))
    
# Import dữ liệu AttendanceLog
@bp.route("/import_timesheet/<filename>", methods=["POST"])
def import_timesheet(filename):
    upload_folder = os.path.abspath(os.path.join(os.getcwd(), "uploads"))
    file_path = os.path.join(upload_folder, filename)

    from datetime import datetime
    import re

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

        # xoá dữ liệu cũ
        db.session.query(AttendanceLog).delete()

        objs = []
        day_cols = [c for c in df.columns if str(c).isdigit()]
        for _, row in df.iterrows():
            emp_code = str(row.get("Mã", "")).strip()
            emp = Employee.query.filter_by(code=emp_code).first()
            if not emp:
                continue

            for d in day_cols:
                val = str(row.get(d, "")).strip()
                if val:
                    times = re.findall(r'\d{1,2}:\d{2}', val)
                    checkin = checkout = None
                    if times:
                        checkin = datetime.strptime(times[0], "%H:%M").time()
                        checkout = datetime.strptime(times[-1], "%H:%M").time()
                    log = AttendanceLog(
                        employee_id=emp.id,
                        date=datetime(start_date.year, start_date.month, int(d)).date(),
                        checkin=checkin,
                        checkout=checkout
                    )
                    objs.append(log)

        db.session.bulk_save_objects(objs)
        db.session.commit()
        flash("Import AttendanceLog thành công!", "success")

    except Exception as e:
        db.session.rollback()
        flash(f"Lỗi khi import timesheet: {e}", "danger")

    return redirect(url_for("main.timesheet", filename=filename))


# Import dữ liệu Payroll
@bp.route("/import_payroll/<filename>", methods=["POST"])
def import_payroll(filename):
    upload_folder = os.path.abspath(os.path.join(os.getcwd(), "uploads"))
    file_path = os.path.join(upload_folder, filename)

    from datetime import datetime
    import re

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

    emp.att_code = new_att_code
    try:
        db.session.commit()
        flash("Cập nhật mã chấm công thành công!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Lỗi khi cập nhật mã chấm công: {e}", "danger")

    return redirect(url_for("main.employees"))


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
