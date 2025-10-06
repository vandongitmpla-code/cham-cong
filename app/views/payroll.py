from flask import redirect, url_for, flash, render_template, current_app, request
import os
from app.utils.cleaning import clean_attendance_data
import re
import calendar
from datetime import datetime
from app.models import db
from . import bp
from app.models import Holiday
from app.models import Employee, PayrollRecord, WorkAdjustment


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


# Import dữ liệu Payroll
@bp.route("/import_payroll/<filename>", methods=["POST"])
def import_payroll(filename):
    upload_folder = os.path.abspath(os.path.join(os.getcwd(), "uploads"))
    file_path = os.path.join(upload_folder, filename)

    try:
        # --- Đọc và làm sạch dữ liệu chấm công ---
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

        # --- Parse ngày bắt đầu & kết thúc ---
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

        # --- Lấy danh sách ngày lễ trong tháng ---
        holidays = Holiday.query.filter(
            db.extract("year", Holiday.date) == year,
            db.extract("month", Holiday.date) == month
        ).all()
        holiday_days = {h.date.day for h in holidays}

        # --- Xoá dữ liệu cũ ---
        PayrollRecord.query.filter_by(period=period).delete()
        WorkAdjustment.query.filter_by(period=period).delete()  # ✅ XÓA CẢ ADJUSTMENT CŨ

        # --- Hàm tính ngày công chuẩn ---
        def calculate_standard_work_days(year, month, holiday_count):
            total_days = calendar.monthrange(year, month)[1]
            sunday_count = 0
            for day in range(1, total_days + 1):
                weekday = datetime(year, month, day).weekday()
                if weekday == 6:  # Chủ nhật
                    sunday_count += 1
            standard_days = total_days - sunday_count - (holiday_count * 2)
            return standard_days, sunday_count

        # --- Hàm điều chỉnh ngày công ---
        def calculate_adjusted_work_days(ngay_cong_thuc_te, ngay_cong_chuan, tang_ca_nghi_gio):
            ngay_thieu = ngay_cong_chuan - ngay_cong_thuc_te
            if ngay_thieu <= 0:
                return ngay_cong_thuc_te, tang_ca_nghi_gio
            gio_can_bu = ngay_thieu * 8
            if tang_ca_nghi_gio >= gio_can_bu:
                ngay_cong_dieu_chinh = ngay_cong_chuan
                tang_ca_nghi_con_lai = tang_ca_nghi_gio - gio_can_bu
            else:
                ngay_duoc_bu = tang_ca_nghi_gio // 8
                ngay_cong_dieu_chinh = ngay_cong_thuc_te + ngay_duoc_bu
                tang_ca_nghi_con_lai = tang_ca_nghi_gio % 8
            return ngay_cong_dieu_chinh, tang_ca_nghi_con_lai

        # --- Hàm xác định trạng thái ---
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

        # --- Tính ngày công chuẩn ---
        ngay_cong_chuan, so_chu_nhat = calculate_standard_work_days(year, month, len(holiday_days))

        # --- Xử lý từng nhân viên ---
        for _, row in df.iterrows():
            emp_code = str(row.get("Mã", "")).strip()
            emp = Employee.query.filter(
                (Employee.code == emp_code) | (Employee.att_code == emp_code)
            ).first()
            if not emp:
                continue

            tong_x = 0
            x_chu_nhat = 0
            x_le = 0
            ngay_vang = 0
            daily_status = {}

            # --- Duyệt từng ngày ---
            for d in day_numbers:
                key = str(d)
                status = render_status(row.get(key, ""))
                daily_status[d] = status

                wd = (weekdays.get(d, "") or "").lower()
                is_sunday = ("chủ" in wd) or ("cn" in wd) or ("sun" in wd)
                is_holiday = d in holiday_days

                if status == "x":
                    tong_x += 1
                    if is_sunday:
                        x_chu_nhat += 1
                    if is_holiday:
                        x_le += 1
                elif status == "v":
                    ngay_vang += 1

            # --- CÔNG THỨC CŨ ---
            ngay_cong_thuc_te = tong_x - x_chu_nhat - (x_le * 2)  # ✅ ĐỊNH NGHĨA BIẾN
            if ngay_cong_thuc_te < 0:
                ngay_cong_thuc_te = 0

            tang_ca_nghi_gio = x_chu_nhat * 8  # ✅ ĐỊNH NGHĨA BIẾN
            tang_ca_tuan = 0
            le_tet_gio = x_le * 16

            # --- ĐIỀU CHỈNH NGÀY CÔNG ---
            ngay_cong_dieu_chinh, tang_ca_nghi_con_lai = calculate_adjusted_work_days(
                ngay_cong_thuc_te, ngay_cong_chuan, tang_ca_nghi_gio
            )  # ✅ ĐỊNH NGHĨA BIẾN

            # --- Ghi chú chi tiết ---
            cn_days, le_days, nghi_days = [], [], []
            for d in day_numbers:
                wd = (weekdays.get(d, "") or "").lower()
                is_sunday = ("chủ" in wd) or ("cn" in wd) or ("sun" in wd)
                is_holiday = d in holiday_days
                status = daily_status.get(d, "")
                if is_sunday and status == "x":
                    cn_days.append(d)
                if is_holiday and status == "x":
                    le_days.append(d)
                if status == "v":
                    nghi_days.append(d)

            # Format ghi_chú
            parts = []
            if cn_days:
                cn_days_formatted = ",".join([str(d) for d in cn_days])
                parts.append(f"Tăng ca {len(cn_days)} CN: {cn_days_formatted}/{month:02d}/{year}")
            if le_days:
                le_days_formatted = ",".join([str(d) for d in le_days])
                parts.append(f"Làm {len(le_days)} ngày lễ: {le_days_formatted}/{month:02d}/{year}")
            if nghi_days:
                nghi_days_formatted = ",".join([str(d) for d in nghi_days])
                parts.append(f"Nghỉ phép từ ngày: {nghi_days_formatted}/{month:02d}/{year}")

            ghi_chu = " - ".join(parts) if parts else "Làm việc đủ ngày"

            # --- Tạo PayrollRecord ---
            record = PayrollRecord(
                employee_id=emp.id,
                employee_code=emp.code,
                employee_name=emp.name,
                period=period,
                ngay_cong=ngay_cong_dieu_chinh,  # ✅ DÙNG NGÀY CÔNG ĐÃ ĐIỀU CHỈNH
                ngay_vang=ngay_vang,
                chu_nhat=x_chu_nhat,
                le_tet=x_le,
                le_tet_gio=le_tet_gio,
                tang_ca_nghi=tang_ca_nghi_con_lai,  # ✅ DÙNG GIỜ TĂNG CA CÒN LẠI
                tang_ca_tuan=tang_ca_tuan,
                ghi_chu=ghi_chu,
                raw_data={
                    'daily_status': daily_status,
                    'summary': {
                        'total_work_days': tong_x,
                        'sunday_work_days': cn_days,
                        'holiday_work_days': le_days,
                        'absence_days': nghi_days,
                        'standard_work_days': ngay_cong_chuan,
                        'original_work_days': ngay_cong_thuc_te
                    }
                },
                to=getattr(emp, "team", ""),
                phong_ban=getattr(emp, "department", ""),
                loai_hd=getattr(emp, "contract_type", "")
            )
            
            # LƯU RECORD TRƯỚC ĐỂ CÓ ID
            db.session.add(record)
            db.session.flush()  # ✅ QUAN TRỌNG: Lấy ID ngay lập tức

            # --- Tạo WorkAdjustment với payroll_record_id đã có ---
            adjustment = WorkAdjustment(
                payroll_record_id=record.id,  # ✅ ĐÃ CÓ ID
                employee_id=emp.id,
                period=period,
                employee_code=emp.code,
                employee_name=emp.name,
                original_work_days=ngay_cong_thuc_te,
                standard_work_days=ngay_cong_chuan,
                original_overtime_hours=tang_ca_nghi_gio,
                adjusted_work_days=ngay_cong_dieu_chinh,
                remaining_overtime_hours=tang_ca_nghi_con_lai,
                used_overtime_hours=tang_ca_nghi_gio - tang_ca_nghi_con_lai,
                adjustment_type="overtime_compensation",
                adjustment_reason=f"Bù {tang_ca_nghi_gio - tang_ca_nghi_con_lai} giờ tăng ca chủ nhật vào ngày công"
            )
            db.session.add(adjustment)

        # COMMIT CUỐI CÙNG
        db.session.commit()
        flash("Đã import payroll thành công!", "success")

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

@bp.route("/apply_adjustment", methods=["POST"])
def apply_adjustment(): 
    try:
        employee_code = request.form.get("employee_code")
        period = request.form.get("period")
        original_days = float(request.form.get("original_days"))
        overtime_hours = float(request.form.get("overtime_hours"))
        current_absence = float(request.form.get("current_absence", 0))
        filename = request.form.get("filename") or request.args.get("filename")
        
        # Tìm employee và payroll record
        emp = Employee.query.filter_by(code=employee_code).first()
        if not emp:
            flash("Không tìm thấy nhân viên!", "danger")
            return redirect(url_for("main.attendance_print", filename=filename)) if filename else redirect(url_for("main.index"))
        
        payroll_record = PayrollRecord.query.filter_by(
            employee_code=employee_code, 
            period=period
        ).first()
        
        if not payroll_record:
            flash("Không tìm thấy bản ghi payroll!", "danger")
            return redirect(url_for("main.attendance_print", filename=filename)) if filename else redirect(url_for("main.index"))
        
        # Tính toán điều chỉnh
        year, month = map(int, period.split('-'))
        
        # Lấy số ngày lễ để tính ngày công chuẩn
        holidays = Holiday.query.filter(
            db.extract("year", Holiday.date) == year,
            db.extract("month", Holiday.date) == month
        ).all()
        
        # Tính ngày công chuẩn
        total_days = calendar.monthrange(year, month)[1]
        sunday_count = 0
        for day in range(1, total_days + 1):
            if datetime(year, month, day).weekday() == 6:
                sunday_count += 1
                
        ngay_cong_chuan = total_days - sunday_count - (len(holidays) * 2)
        
        # ✅ LOGIC MỚI: TÁCH BIỆT DỮ LIỆU GỐC VÀ ĐIỀU CHỈNH
       overtime_days = overtime_hours / 8
        
        # Gộp toàn bộ tăng ca vào ngày công, nhưng không vượt chuẩn
    adjusted_days = original_days + overtime_days
    if adjusted_days > ngay_cong_chuan:
        adjusted_days = ngay_cong_chuan  # Giới hạn ở ngày công chuẩn
        
        # Tính số ngày thực tế được gộp
        actual_used_days = adjusted_days - original_days
        
        # Ngày nghỉ giữ nguyên (vì không dùng để bù)
        adjusted_absence = current_absence
        
        # Tính giờ tăng ca thực tế đã dùng
        used_hours = actual_used_days * 8
        remaining_hours = overtime_hours - used_hours

        # Tạo hoặc cập nhật WorkAdjustment
        adjustment = WorkAdjustment.query.filter_by(
            employee_code=employee_code,
            period=period
        ).first()
        
        if adjustment:
            # Cập nhật adjustment hiện có
            adjustment.adjusted_work_days = adjusted_days
            adjustment.adjusted_absence_days = adjusted_absence  # ✅ LƯU NGÀY VẮNG SAU GỘP
            adjustment.remaining_overtime_hours = remaining_hours
            adjustment.used_overtime_hours = used_hours
            adjustment.adjustment_reason = f"Gộp {used_hours} giờ tăng ca vào ngày công"
        else:
            # Tạo adjustment mới với đầy đủ thông tin
            adjustment = WorkAdjustment(
                payroll_record_id=payroll_record.id,  
                employee_id=emp.id,
                period=period,
                employee_code=employee_code,
                employee_name=emp.name,
                original_work_days=original_days,
                original_absence_days=current_absence,  # ✅ LƯU NGÀY VẮNG GỐC
                original_overtime_hours=overtime_hours,
                adjusted_work_days=adjusted_days,
                adjusted_absence_days=adjusted_absence,  # ✅ LƯU NGÀY VẮNG SAU GỘP
                remaining_overtime_hours=remaining_hours,
                used_overtime_hours=used_hours,
                standard_work_days=ngay_cong_chuan,
                adjustment_type="overtime_compensation",
                adjustment_reason=f"Gộp {used_hours} giờ tăng ca vào ngày công"
            )
            db.session.add(adjustment)
        
       
        
        db.session.commit()
        
        flash(f"Đã áp dụng điều chỉnh cho {emp.name}! Gộp {used_hours} giờ tăng ca.", "success")
        
    except Exception as e:
        db.session.rollback()
        flash(f"Lỗi khi áp dụng điều chỉnh: {e}", "danger")
    
    if filename:
        return redirect(url_for("main.attendance_print", filename=filename))
    else:
        return redirect(url_for("main.index"))


@bp.route("/reset_adjustment_payroll", methods=["POST"])
def reset_adjustment_payroll():
    try:
        employee_code = request.form.get("employee_code")
        period = request.form.get("period")
        filename = request.form.get("filename") or request.args.get("filename")
        
        # Tìm và xóa adjustment
        adjustment = WorkAdjustment.query.filter_by(
            employee_code=employee_code,
            period=period
        ).first()
        
        if adjustment:
            # ✅ KHÔNG CẦN KHÔI PHỤC PAYROLL_RECORD VÌ DỮ LIỆU GỐC VẪN GIỮ NGUYÊN
            db.session.delete(adjustment)
            db.session.commit()
            
            flash(f"✅ Đã khôi phục dữ liệu gốc cho {adjustment.employee_name}", "success")
        else:
            flash("⚠️ Không tìm thấy điều chỉnh để khôi phục", "warning")
            
    except Exception as e:
        db.session.rollback()
        flash(f"❌ Lỗi khi khôi phục: {e}", "danger")
    
    if filename:
        return redirect(url_for("main.attendance_print", filename=filename))
    else:
        return redirect(url_for("main.index"))