# app/views/attendance_helpers.py
import calendar
from datetime import datetime
from app.models import Holiday, db

def calculate_standard_work_days(year, month):
    """
    Tính ngày công chuẩn theo tháng
    """
    # Lấy số ngày lễ trong tháng
    holidays_count = Holiday.query.filter(
        db.extract("year", Holiday.date) == year,
        db.extract("month", Holiday.date) == month
    ).count()
    
    total_days = calendar.monthrange(year, month)[1]
    sunday_count = 0
    for day in range(1, total_days + 1):
        if datetime(year, month, day).weekday() == 6:
            sunday_count += 1
            
    standard_days = total_days - sunday_count - (holidays_count * 2)
    return standard_days

def calculate_adjustment_details(original_days, standard_days, overtime_hours):
    """
    Tính toán chi tiết điều chỉnh
    """
    ngay_thieu = standard_days - original_days
    if ngay_thieu <= 0:
        return original_days, overtime_hours, 0
    
    gio_can_bu = ngay_thieu * 8
    if overtime_hours >= gio_can_bu:
        adjusted_days = standard_days
        remaining_hours = overtime_hours - gio_can_bu
        used_hours = gio_can_bu
    else:
        ngay_duoc_bu = overtime_hours // 8
        adjusted_days = original_days + ngay_duoc_bu
        remaining_hours = overtime_hours % 8
        used_hours = overtime_hours - remaining_hours
    
    return adjusted_days, remaining_hours, used_hours

def get_attendance_period(att_meta):
    """
    Lấy kỳ công từ metadata
    """
    import re
    period_str = ""
    if att_meta and len(att_meta) > 0:
        header_row = att_meta[0]
        for cell in header_row:
            if isinstance(cell, str):
                m = re.search(r"\d{4}-\d{2}", cell)
                if m:
                    period_str = m.group(0)
                    break
    return period_str

def create_attendance_rows(records, period):
    """
    Tạo dữ liệu rows cho template attendance_print
    """
    from datetime import datetime
    from app.models import WorkAdjustment
    
    rows = []
    stt = 1
    
    # Tính ngày công chuẩn cho tháng
    start_date = datetime.strptime(period + "-01", "%Y-%m-%d")
    year, month = start_date.year, start_date.month
    standard_days = calculate_standard_work_days(year, month)

    for rec in records:
        # Kiểm tra xem có thể áp dụng điều chỉnh không
        has_adjustment_option = rec.tang_ca_nghi > 0 and rec.ngay_cong < standard_days
        
        # Sử dụng dữ liệu đã điều chỉnh nếu có adjustment
        adjustment = WorkAdjustment.query.filter_by(
            employee_code=rec.employee_code, 
            period=period
        ).first()
        
        if adjustment:
            ngay_cong_hien_thi = adjustment.adjusted_work_days
            tang_ca_nghi_hien_thi = adjustment.remaining_overtime_hours
        else:
            ngay_cong_hien_thi = rec.ngay_cong
            tang_ca_nghi_hien_thi = rec.tang_ca_nghi

        rows.append([
            stt, rec.employee_code, rec.employee_name, rec.phong_ban, rec.loai_hd,
            standard_days, "", rec.ngay_vang, ngay_cong_hien_thi, tang_ca_nghi_hien_thi,
            rec.le_tet_gio, rec.tang_ca_tuan, rec.ghi_chu or "", "", "", rec.to,
            {
                'has_adjustment_option': has_adjustment_option,
                'adjustment_info': adjustment.used_overtime_hours if adjustment else 0,
                'standard_days': standard_days,
                'original_days': rec.ngay_cong
            }
        ])
        stt += 1
    
    return rows

def get_attendance_columns():
    """
    Trả về danh sách columns cho attendance_print
    """
    return [
        "STT", "Mã số", "Họ và tên", "Phòng ban", "Loại HĐ",
        "Số ngày/giờ làm việc quy định trong tháng", 
        "Số ngày nghỉ phép năm",
        "Số ngày nghỉ không lương", 
        "Số ngày/giờ làm việc thực tế trong tháng",
        "Số giờ làm việc tăng ca (ngày nghỉ hàng tuần)",
        "Số giờ làm việc tăng ca (ngày lễ)",
        "Số giờ làm việc tăng ca (ngày làm trong tuần)",
        "Ghi chú", 
        "Bắt đầu tính phép từ tháng",
        "Số ngày phép còn tồn", 
        "Tổ"
    ]

def get_company_info(period):
    """
    Trả về thông tin công ty
    """
    return {
        "name": "CÔNG TY CP CÔNG NGHỆ OTANICS",
        "tax": "2001337320",
        "address": "KCN phường 8, phường Lý Văn Lâm, Tỉnh Cà Mau, Việt Nam",
        "title": f"BẢNG CHẤM CÔNG VÀ HIỆU SUẤT {period}"
    }