from flask import render_template, redirect, url_for, flash
import os
import pandas as pd
from app.utils.cleaning import clean_attendance_data
from app.models import AttendanceLog, Employee, db
from . import bp
from flask import  render_template, redirect, url_for, flash
import os
from app.utils.cleaning import clean_attendance_data
import pandas as pd


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

        # Xác định các cột ngày (1..31) có trong df
        day_cols = [c for c in df.columns if str(c).strip().isdigit()]
        day_cols = sorted(day_cols, key=lambda x: int(str(x).strip())) if day_cols else []
        if not day_cols:
            flash("Không tìm thấy cột ngày (1..31) trong file", "danger")
            return redirect(url_for("main.index"))

        # Tạo mapping weekdays và tính day_count theo số ngày trong tháng
        from datetime import datetime, timedelta
        import calendar
        weekdays = {}
        
        # TÍNH day_count THEO SỐ NGÀY TRONG THÁNG
        try:
            if period_str and "~" in period_str:
                start_s, end_s = period_str.split("~")
                start_date = datetime.strptime(start_s.strip(), "%Y-%m-%d")
                
                # Lấy năm và tháng từ start_date
                year = start_date.year
                month = start_date.month
                
                # Tính số ngày trong tháng đó
                day_count = calendar.monthrange(year, month)[1]  # [1] trả về số ngày trong tháng
                
                # Cập nhật weekdays cho đủ tháng
                weekday_names = ["Thứ 2","Thứ 3","Thứ 4","Thứ 5","Thứ 6","Thứ 7","Chủ Nhật"]
                for day in range(1, day_count + 1):
                    date_obj = datetime(year, month, day)
                    weekdays[day] = weekday_names[date_obj.weekday()]
                    
            else:
                # Fallback: dùng số ngày từ file như cũ
                day_count = max(int(str(c)) for c in day_cols)
                # Tạo weekdays fallback
                if day_cols:
                    for day in day_cols:
                        day_int = int(day)
                        try:
                            date_obj = datetime(start_date.year, start_date.month, day_int)
                            weekdays[day_int] = weekday_names[date_obj.weekday()]
                        except:
                            weekdays[day_int] = ""
        except Exception as e:
            print("Lỗi tính day_count từ period:", e, flush=True)
            # Fallback: dùng số ngày từ file
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
            # điền theo day_count (số ngày trong tháng)
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
