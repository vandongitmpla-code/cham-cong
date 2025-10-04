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

        # ---- Lấy kỳ công ----
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

        # ---- Tạo danh sách ngày dựa vào kỳ công ----
        weekdays = {}
        day_numbers = []
        start_date = end_date = None
        try:
            if period_str and "~" in period_str:
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
            print("Lỗi tạo weekdays:", e, flush=True)

        # fallback: nếu không đọc được kỳ công thì lấy từ file
        if not day_numbers:
            day_numbers = sorted([int(c) for c in df.columns if str(c).isdigit()])

        if not day_numbers:
            flash("Không tìm thấy cột ngày hợp lệ trong file", "danger")
            return redirect(url_for("main.index"))

        # ---- Hàm render_status ----
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

        # ---- Tạo dữ liệu rows ----
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

        # Sắp xếp theo tên
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

