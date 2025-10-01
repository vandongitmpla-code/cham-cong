# app/utils/cleaning.py
import pandas as pd
import unicodedata
import re
import difflib
from typing import Dict, List

TARGET_SHEETS = ["Att.log report", "Exception Stat."]

def normalize_name(s: str) -> str:
    if s is None:
        return ""
    s = unicodedata.normalize("NFKC", str(s))
    s = s.replace("\u00A0", " ")
    return s.strip()

def alnum_only(s: str) -> str:
    return re.sub(r'[\W_]+', '', str(s)).lower()

def find_sheet(actual_names: List[str], target: str):
    # try exact / normalized / alnum / substring / fuzzy
    for a in actual_names:
        if a == target:
            return a
    for a in actual_names:
        if normalize_name(a).lower() == normalize_name(target).lower():
            return a
    t2 = alnum_only(target)
    for a in actual_names:
        if alnum_only(a) == t2:
            return a
    for a in actual_names:
        if t2 and t2 in alnum_only(a):
            return a
    choices = [normalize_name(a).lower() for a in actual_names]
    matches = difflib.get_close_matches(normalize_name(target).lower(), choices, n=1, cutoff=0.6)
    if matches:
        for a in actual_names:
            if normalize_name(a).lower() == matches[0]:
                return a
    return None

def read_sheet_safely(file_path: str, sheet_name):
    last_exc = None
    for engine in ("openpyxl", "xlrd"):
        try:
            return pd.read_excel(file_path, sheet_name=sheet_name, engine=engine, dtype=str)
        except Exception as e:
            last_exc = e
    raise last_exc

def clean_attendance_data(file_path: str) -> Dict:
    """
    Đọc sheet 'Att.log report' và 'Exception Stat.'.
    Trả về dict:
      - att_meta: [header_row_values, day_row_values]
      - att_log: DataFrame (Mã, Tên, Phòng ban, '1'..'31') mỗi nhân viên 1 hàng,
                 mỗi ô ngày chứa giờ (nối bằng '<br>' nếu nhiều).
      - exception: DataFrame của sheet Exception Stat.
    """
    # --- đọc raw sheet (không header) để phân tích cấu trúc ---
    raw = pd.read_excel(file_path, sheet_name="Att.log report", header=None, dtype=str).fillna("")
    nrows, ncols = raw.shape

    # tìm hàng header (mặc định hàng 0 theo mô tả, nhưng robust: tìm 'Att. Time' nếu có)
    header_row = None
    for i in range(min(6, nrows)):
        rowvals = [str(x).strip() for x in raw.iloc[i].tolist()]
        joined = " ".join([v for v in rowvals if v])
        if "Att. Time" in joined or "Att. Time" in " ".join(rowvals):
            header_row = i
            break
    if header_row is None:
        header_row = 0
    day_row = header_row + 1 if header_row + 1 < nrows else header_row

    # lấy metadata header + days
    header = raw.iloc[header_row].tolist()
    days = raw.iloc[day_row].tolist()

    # Xác định các cột chứa "ngày" bằng cách đọc giá trị ở day_row
    day_col_map = {}  # col_index -> day_number (int)
    for j in range(ncols):
        val = str(raw.iat[day_row, j]).strip()
        if val.isdigit():
            d = int(val)
            if 1 <= d <= 31:
                day_col_map[j] = d

    # Nếu không tìm được day columns, fallback: dùng cột index bắt đầu từ 2 tới 32
    if not day_col_map:
        # fallback: choose columns 2..(2+30)
        start = 2 if ncols >= 3 else 0
        for j in range(start, min(ncols, start + 31)):
            day_col_map[j] = j - start + 1

    # lọc data rows (bắt đầu từ sau day_row)
    data_start = day_row + 1
    employees = []
    current = None

    for r in range(data_start, nrows):
        # lấy toàn bộ các ô trên hàng r (list)
        row_cells = raw.iloc[r].tolist()
        # make one string to detect Mã/Tên/Phòng Ban
        row_str = " ".join([str(x).strip() for x in row_cells if str(x).strip()])

        # nếu có dòng bắt đầu block nhân viên
        if re.search(r'\bMã[:\s]', row_str, flags=re.I) and re.search(r'\bTên[:\s]', row_str, flags=re.I):
            # push previous
            if current:
                employees.append(current)

            # parse Mã, Tên, Phòng ban (robust)
            m_m = re.search(r'Mã[:\s]*([0-9A-Za-z\-]+)', row_str, flags=re.I)
            m_n = re.search(r'Tên[:\s]*([^P\n\r]+?)(?=Phòng\s*Ban:|$)', row_str, flags=re.I)
            m_d = re.search(r'Phòng\s*Ban[:\s]*([^\n\r]+)', row_str, flags=re.I)

            emp_id = m_m.group(1).strip() if m_m else ""
            emp_name = m_n.group(1).strip() if m_n else ""
            emp_dept = m_d.group(1).strip() if m_d else ""

            # bắt đầu block mới; khởi tạo ngày 1..31 => danh sách rỗng
            current = {"Mã": emp_id, "Tên": emp_name, "Phòng ban": emp_dept}
            for dd in range(1, 32):
                current[str(dd)] = []

            # NOTE: important — AFTER Mã row, the times for this employee are in subsequent rows
            continue

        # nếu đang trong block nhân viên, collect times từ các cột day_col_map
        if current is not None:
            # iterate day columns and take cell at (r, col) => extract times
            for col_idx, daynum in day_col_map.items():
                try:
                    cell = raw.iat[r, col_idx]
                except IndexError:
                    cell = ""
                if cell is None:
                    continue
                cell_str = str(cell).strip()
                if not cell_str:
                    continue
                # extract all time patterns in that cell
                times = re.findall(r'\d{1,2}:\d{2}', cell_str)
                if times:
                    # append times found to that day for current employee
                    current[str(daynum)].extend(times)

    # push last employee
    if current:
        employees.append(current)

    # tạo DataFrame từ employees
    df_clean = pd.DataFrame(employees)

    # đảm bảo tồn tại các cột '1'..'31'
    for d in range(1, 32):
        col = str(d)
        if col not in df_clean.columns:
            df_clean[col] = ""

    # join list -> string với <br>
    def join_times_cell(v):
        if isinstance(v, list):
            return "<br>".join(v)
        if pd.isna(v) or str(v).strip().lower() in ["", "nan"]:
            return ""
        # nếu là chuỗi, tách time rồi join
        found = re.findall(r'\d{1,2}:\d{2}', str(v))
        if found:
            return "<br>".join(found)
        return str(v)

    for d in range(1, 32):
        col = str(d)
        df_clean[col] = df_clean[col].apply(join_times_cell)

    # đọc Exception Stat.
    try:
        df_exc = pd.read_excel(file_path, sheet_name="Exception Stat.", dtype=str).dropna(how="all")
    except Exception:
        # nếu không tìm thấy sheet
        df_exc = pd.DataFrame()

    return {
        "att_meta": [header, days],
        "att_log": df_clean,
        "exception": df_exc
    }
