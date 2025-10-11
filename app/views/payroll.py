from flask import redirect, url_for, flash, render_template, current_app, request
import os
from app.utils.cleaning import clean_attendance_data
import re
import calendar
from datetime import datetime
from app.models import db
from . import bp
from app.models import Holiday
from app.models import Employee, PayrollRecord, WorkAdjustment, PaidLeave
from .attendance_helpers import calculate_leave_info
from flask import jsonify

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

        # ✅ XÓA DỮ LIỆU CŨ
        WorkAdjustment.query.filter(WorkAdjustment.period == period).delete(synchronize_session=False)
        PayrollRecord.query.filter_by(period=period).delete(synchronize_session=False)

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

            # ✅ TÍNH TOÁN THÔNG TIN PHÉP NĂM
            from .attendance_helpers import calculate_leave_info
            thang_bat_dau_tinh_phep, so_thang_duoc_huong, so_ngay_phep_duoc_huong = calculate_leave_info(emp, period)

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

            # --- CÔNG THỨC TÍNH NGÀY CÔNG THỰC TẾ GỐC ---
            ngay_cong_thuc_te = tong_x - x_chu_nhat - (x_le * 2)
            if ngay_cong_thuc_te < 0:
                ngay_cong_thuc_te = 0

            tang_ca_nghi_gio = x_chu_nhat * 8
            tang_ca_tuan = 0
            le_tet_gio = x_le * 16

            # ✅ QUAN TRỌNG: KHI IMPORT CHỈ LƯU GIÁ TRỊ GỐC, KHÔNG TÍNH ĐIỀU CHỈNH
            ngay_cong_goc = ngay_cong_thuc_te
            ngay_vang_goc = ngay_vang
            tang_ca_nghi_goc = tang_ca_nghi_gio

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

            # --- Tạo PayrollRecord VỚI GIÁ TRỊ GỐC VÀ PHÉP NĂM ---
            record = PayrollRecord(
                employee_id=emp.id,
                employee_code=emp.code,
                employee_name=emp.name,
                period=period,
                ngay_cong=ngay_cong_goc,      # ✅ GIÁ TRỊ GỐC
                ngay_vang=ngay_vang_goc,       # ✅ GIÁ TRỊ GỐC  
                chu_nhat=x_chu_nhat,
                le_tet=x_le,
                le_tet_gio=le_tet_gio,
                tang_ca_nghi=tang_ca_nghi_goc, # ✅ GIÁ TRỊ GỐC
                tang_ca_tuan=tang_ca_tuan,
                standard_work_days=ngay_cong_chuan,
                ghi_chu=ghi_chu,
                raw_data={
                    'daily_status': daily_status,
                    'summary': {
                        'total_work_days': tong_x,
                        'sunday_work_days': cn_days,
                        'holiday_work_days': le_days,
                        'absence_days': nghi_days,
                        'standard_work_days': ngay_cong_chuan,
                        'original_work_days': ngay_cong_thuc_te,
                        'original_absence_days': ngay_vang
                    }
                },
                to=getattr(emp, "team", ""),
                phong_ban=getattr(emp, "department", ""),
                loai_hd=getattr(emp, "contract_type", ""),
                # ✅ THÊM: Lưu thông tin phép năm
                thang_bat_dau_tinh_phep=thang_bat_dau_tinh_phep,
                ngay_phep_con_lai=so_ngay_phep_duoc_huong,  # Số phép năm ban đầu
                ngay_nghi_phep_nam=0  # Chưa dùng phép năm
            )
            
            # ✅ CHỈ LƯU PayrollRecord, KHÔNG TẠO WorkAdjustment KHI IMPORT
            db.session.add(record)

        # COMMIT CUỐI CÙNG
        db.session.commit()
        flash("Đã import payroll thành công! Dữ liệu đang ở trạng thái gốc.", "success")

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
        use_extra_leave = request.form.get("use_extra_leave") == "true"
        
        print(f"DEBUG: apply_adjustment called - employee_code: {employee_code}, use_extra_leave: {use_extra_leave}")
        
        emp = Employee.query.filter_by(code=employee_code).first()
        if not emp:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'error': 'Không tìm thấy nhân viên!'}), 400
            flash("Không tìm thấy nhân viên!", "danger")
            return redirect(url_for("main.attendance_print", filename=filename)) if filename else redirect(url_for("main.index"))
        
        # ✅ LẤY THÔNG TIN PHÉP NĂM TỪ PAYROLL_RECORDS
        payroll_record = PayrollRecord.query.filter_by(
            employee_code=employee_code, 
            period=period
        ).first()
        
        if not payroll_record:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'error': 'Không tìm thấy bản ghi payroll!'}), 400
            flash("Không tìm thấy bản ghi payroll!", "danger")
            return redirect(url_for("main.attendance_print", filename=filename)) if filename else redirect(url_for("main.index"))

        # ✅ CHỈ DÙNG DỮ LIỆU TỪ PAYROLL_RECORDS
        ngay_nghi_phep_nam_da_dung = payroll_record.ngay_nghi_phep_nam or 0
        phep_nam_kha_dung = payroll_record.ngay_phep_con_lai or 0

        print(f"DEBUG PHÉP NĂM từ payroll_records: đã_dùng={ngay_nghi_phep_nam_da_dung}, còn_lại={phep_nam_kha_dung}")

        # ✅ TÍNH NGÀY CÔNG CHUẨN
        year, month = map(int, period.split('-'))
        holidays = Holiday.query.filter(
            db.extract("year", Holiday.date) == year,
            db.extract("month", Holiday.date) == month
        ).count()
        
        total_days = calendar.monthrange(year, month)[1]
        sunday_count = 0
        for day in range(1, total_days + 1):
            if datetime(year, month, day).weekday() == 6:
                sunday_count += 1
                
        ngay_cong_chuan = total_days - sunday_count - (holidays * 2)

        # ✅ TÍNH TOÁN ĐIỀU CHỈNH
        from .attendance_helpers import calculate_adjustment_details
        
        result = calculate_adjustment_details(
            original_days=original_days,
            standard_days=ngay_cong_chuan,
            ngay_vang_ban_dau=current_absence,
            overtime_hours=overtime_hours,
            ngay_nghi_phep_nam_da_dung=ngay_nghi_phep_nam_da_dung,  # ✅ TRUYỀN PHÉP NĂM ĐÃ "+"
            phep_nam_kha_dung=phep_nam_kha_dung,
            use_extra_leave=use_extra_leave
        )

        print(f"DEBUG: Calculation result - ngay_vang_con_lai: {result.get('ngay_vang_con_lai')}, phep_nam_kha_dung: {result.get('phep_nam_kha_dung')}")

        # ✅ KIỂM TRA CÓ CẦN XÁC NHẬN THÊM PHÉP NĂM KHÔNG
        can_xac_nhan_them_phep = (
            result.get('ngay_vang_con_lai', 0) > 0 and 
            result.get('phep_nam_kha_dung', 0) > 0 and
            not use_extra_leave
        )
        
        print(f"DEBUG: Check extra leave - need_confirmation: {can_xac_nhan_them_phep}")
        
        # ✅ NẾU LÀ AJAX VÀ CẦN XÁC NHẬN THÊM PHÉP
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        if can_xac_nhan_them_phep and is_ajax:
            print(f"DEBUG: Returning JSON confirmation - remaining_absence: {result['ngay_vang_con_lai']}, available_leave: {result['phep_nam_kha_dung']}")
            return jsonify({
                'need_extra_leave_confirmation': True,
                'remaining_absence': result['ngay_vang_con_lai'],
                'available_leave': result['phep_nam_kha_dung'],
                'employee_code': employee_code,
                'period': period
            })

        # ✅ Tạo hoặc cập nhật WorkAdjustment
        adjustment = WorkAdjustment.query.filter_by(
            employee_code=employee_code,
            period=period
        ).first()
        
        if adjustment:
            adjustment.adjusted_work_days = result['ngay_cong_cuoi']
            adjustment.adjusted_absence_days = result['ngay_vang_cuoi']
            adjustment.remaining_overtime_hours = result['tang_ca_con_lai']
            adjustment.used_overtime_hours = result['gio_tang_ca_da_dung']
            adjustment.adjustment_reason = f"Gộp {result['so_ngay_bu_tu_tang_ca']} ngày CN, dùng {result['ngay_nghi_phep_nam_da_dung']} ngày phép năm"
        else:
            adjustment = WorkAdjustment(
                payroll_record_id=payroll_record.id,  
                employee_id=emp.id,
                period=period,
                employee_code=employee_code,
                employee_name=emp.name,
                original_work_days=original_days,
                original_absence_days=current_absence,
                original_overtime_hours=overtime_hours,
                adjusted_work_days=result['ngay_cong_cuoi'],
                adjusted_absence_days=result['ngay_vang_cuoi'],
                remaining_overtime_hours=result['tang_ca_con_lai'],
                used_overtime_hours=result['gio_tang_ca_da_dung'],
                standard_work_days=ngay_cong_chuan,
                adjustment_type="overtime_compensation",
                adjustment_reason=f"Gộp {result['so_ngay_bu_tu_tang_ca']} ngày CN, dùng {result['ngay_nghi_phep_nam_da_dung']} ngày phép năm"
            )
            db.session.add(adjustment)
        
        # ✅ CẬP NHẬT LẠI PAYROLL_RECORD VỚI THÔNG TIN PHÉP NĂM MỚI
        payroll_record.ngay_nghi_phep_nam = result['ngay_nghi_phep_nam_da_dung']
        payroll_record.ngay_phep_con_lai = result['phep_nam_kha_dung']
        
        db.session.commit()
        
        # ✅ NẾU LÀ AJAX REQUEST, TRẢ VỀ JSON THAY VÌ REDIRECT
        if is_ajax:
            return jsonify({
                'success': True,
                'message': f'Đã áp dụng điều chỉnh cho {emp.name}! Ngày công: {result["ngay_cong_cuoi"]}, Ngày nghỉ: {result["ngay_vang_cuoi"]}'
            })
        
        flash(f"Đã áp dụng điều chỉnh cho {emp.name}! Ngày công: {result['ngay_cong_cuoi']}, Ngày nghỉ: {result['ngay_vang_cuoi']}", "success")
        
    except Exception as e:
        db.session.rollback()
        print(f"ERROR in apply_adjustment: {e}")
        
        # ✅ XỬ LÝ LỖI CHO AJAX
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': False,
                'error': f"Lỗi khi áp dụng điều chỉnh: {e}"
            }), 500
        
        flash(f"Lỗi khi áp dụng điều chỉnh: {e}", "danger")
    
    # ✅ CHỈ REDIRECT NẾU KHÔNG PHẢI AJAX
    if filename and not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
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
            # ✅ KHÔI PHỤC VỀ GIÁ TRỊ GỐC TỪ PAYROLL RECORD
            payroll_record = PayrollRecord.query.filter_by(
                employee_code=employee_code,
                period=period
            ).first()
            
            if payroll_record:
                # KHÔNG cần cập nhật payroll_record vì chúng ta dùng adjustment để tính toán
                # Chỉ cần xóa adjustment là đủ
                pass
            
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
    
@bp.route("/add_paid_leave", methods=["POST"])
def add_paid_leave():
    try:
        employee_id = request.form.get("employee_id")
        period = request.form.get("period")
        leave_days = float(request.form.get("leave_days", 0))
        filename = request.form.get("filename")
        
        employee = Employee.query.get(employee_id)
        if not employee:
            flash("Không tìm thấy nhân viên!", "danger")
            return redirect(url_for("main.attendance_print", filename=filename))
        
        # ✅ KIỂM TRA SỐ NGÀY PHÉP TỐI ĐA
        thang_bat_dau_tinh_phep, so_thang_duoc_huong, _ = calculate_leave_info(employee, period)
        max_leave_days = so_thang_duoc_huong
        
        if leave_days > max_leave_days:
            flash(f"Số ngày phép không được vượt quá {max_leave_days} ngày!", "danger")
            return redirect(url_for("main.attendance_print", filename=filename))
        
        # ✅ TÌM HOẶC TẠO PAID_LEAVE RECORD
        paid_leave = PaidLeave.query.filter_by(
            employee_id=employee_id,
            period=period
        ).first()
        
        if paid_leave:
            paid_leave.leave_days_used = leave_days
            paid_leave.remaining_leave_days = max_leave_days - leave_days
            paid_leave.updated_at = datetime.utcnow()
        else:
            paid_leave = PaidLeave(
                employee_id=employee_id,
                period=period,
                leave_days_used=leave_days,
                remaining_leave_days=max_leave_days - leave_days
            )
            db.session.add(paid_leave)
        
        db.session.commit()
        flash(f"Đã cập nhật {leave_days} ngày phép năm cho {employee.name}!", "success")
        
    except Exception as e:
        db.session.rollback()
        flash(f"Lỗi khi cập nhật phép năm: {e}", "danger")
    
    return redirect(url_for("main.attendance_print", filename=filename))

@bp.route("/reset_paid_leave", methods=["POST"])
def reset_paid_leave():
    try:
        employee_id = request.form.get("employee_id")
        period = request.form.get("period")
        filename = request.form.get("filename")
        
        employee = Employee.query.get(employee_id)
        if not employee:
            flash("Không tìm thấy nhân viên!", "danger")
            return redirect(url_for("main.attendance_print", filename=filename))
        
        # ✅ SỬA: RESET TRONG PAYROLL_RECORDS THAY VÌ PAID_LEAVES
        payroll_record = PayrollRecord.query.filter_by(
            employee_id=employee_id,
            period=period
        ).first()
        
        if payroll_record:
            # Reset về 0
            payroll_record.ngay_nghi_phep_nam = 0
            
            # ✅ GIỮ NGUYÊN ngay_phep_con_lai (phép năm còn tồn)
            # payroll_record.ngay_phep_con_lai = ... (giữ nguyên)
            
            db.session.commit()
            flash(f"Đã reset ngày phép năm về 0 cho {employee.name}!", "success")
        else:
            flash("Không tìm thấy dữ liệu payroll để reset!", "warning")
            
    except Exception as e:
        db.session.rollback()
        flash(f"Lỗi khi reset phép năm: {e}", "danger")
    
    return redirect(url_for("main.attendance_print", filename=filename))