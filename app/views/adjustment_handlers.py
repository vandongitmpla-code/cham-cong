# app/views/attendance_helpers.py
import calendar
from datetime import datetime
from app.models import Holiday, db
import re

def get_attendance_period(att_meta):
    """
    Lấy kỳ công từ metadata
    """
    period_str = ""
    if att_meta and len(att_meta) > 0:
        header_row = att_meta[0]
        for cell in header_row:
            if isinstance(cell, str):
                # Tìm pattern YYYY-MM-DD ~ YYYY-MM-DD hoặc YYYY-MM
                m = re.search(r'\d{4}-\d{2}-\d{2}\s*~\s*\d{4}-\d{2}-\d{2}', cell)
                if m:
                    period_str = m.group(0)
                    break
                # Fallback: tìm pattern YYYY-MM
                m = re.search(r'\d{4}-\d{2}', cell)
                if m:
                    period_str = m.group(0)
                    break
    
    return period_str

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

def calculate_adjustment_details(original_days, standard_days, overtime_hours, current_absence):
    """
    Tính toán chi tiết điều chỉnh - CÔNG THỨC MỚI
    """
    overtime_days = overtime_hours / 8
    
    # 1. Gộp toàn bộ tăng ca vào ngày công
    adjusted_days = original_days + overtime_days
    
    # 2. Dùng tăng ca để bù ngày nghỉ
    ngay_vang_sau_gop = current_absence
    remaining_hours = overtime_hours
    
    if current_absence > 0:
        # Số ngày có thể bù từ tăng ca
        so_ngay_co_the_bu = min(overtime_days, current_absence)
        
        # Giảm ngày nghỉ
        ngay_vang_sau_gop = current_absence - so_ngay_co_the_bu
        
        # Tính giờ tăng ca đã dùng để bù
        gio_da_dung_de_bu = so_ngay_co_the_bu * 8
        remaining_hours = overtime_hours - gio_da_dung_de_bu
    
    used_hours = overtime_hours - remaining_hours
    
    return adjusted_days, ngay_vang_sau_gop, remaining_hours, used_hours

def create_attendance_rows(records, period):
    """
    Tạo dữ liệu rows cho template attendance_print - THEO CÔNG THỨC MỚI
    """
    from datetime import datetime
    from app.models import WorkAdjustment
    
    rows = []
    stt = 1

    # Tính ngày công chuẩn cho period
    year, month = map(int, period.split('-'))
    standard_days = calculate_standard_work_days(year, month)

    for rec in records:
        # Kiểm tra xem có điều chỉnh không
        adjustment = WorkAdjustment.query.filter_by(
            employee_code=rec.employee_code, 
            period=period
        ).first()
        
        if adjustment:
            # ✅ ĐÃ ĐIỀU CHỈNH: HIỂN THỊ THEO CÔNG THỨC MỚI
            ngay_cong_quy_dinh = adjustment.adjusted_work_days  # = ngày công + ngày CN
            ngay_cong_thuc_te = adjustment.adjusted_work_days   # = ngày công + ngày CN
            ngay_vang_hien_thi = adjustment.ngay_vang_sau_gop   # Ngày vắng sau gộp
            tang_ca_nghi_hien_thi = adjustment.remaining_overtime_hours
            adjustment_info = adjustment.used_overtime_hours
            original_days = adjustment.original_work_days
            ngay_vang_ban_dau = adjustment.ngay_vang_ban_dau
        else:
            # ✅ CHƯA ĐIỀU CHỈNH: HIỂN THỊ DỮ LIỆU GỐC
            ngay_cong_quy_dinh = rec.ngay_cong  # Cột quy định  
            ngay_cong_thuc_te = rec.ngay_cong   # Cột thực tế
            ngay_vang_hien_thi = rec.ngay_vang
            tang_ca_nghi_hien_thi = rec.tang_ca_nghi
            adjustment_info = 0
            original_days = rec.ngay_cong
            ngay_vang_ban_dau = rec.ngay_vang

        # Kiểm tra có thể áp dụng điều chỉnh không
        has_adjustment_option = (
            adjustment is None and 
            rec.tang_ca_nghi > 0  # Có giờ tăng ca CN
        )

        rows.append([
            stt, rec.employee_code, rec.employee_name, rec.phong_ban, rec.loai_hd,
            ngay_cong_quy_dinh,   # ✅ "Số ngày/giờ làm việc quy định trong tháng"
            "", 
            ngay_vang_hien_thi,   # ✅ "Số ngày nghỉ không lương" (sau gộp)
            ngay_cong_thuc_te,    # ✅ "Số ngày/giờ làm việc thực tế trong tháng"  
            tang_ca_nghi_hien_thi, # ✅ "Số giờ làm việc tăng ca (ngày nghỉ hàng tuần)"
            rec.le_tet_gio, 
            rec.tang_ca_tuan, 
            rec.ghi_chu or "", 
            "", 
            "", 
            rec.to,
            {
                'has_adjustment_option': has_adjustment_option,
                'adjustment_info': adjustment_info,
                'original_days': original_days,
                'current_days': rec.ngay_cong,
                'standard_days': standard_days,
                'ngay_vang_ban_dau': ngay_vang_ban_dau,  # ✅ Thêm để hiển thị tooltip
                'ngay_vang_sau_gop': ngay_vang_hien_thi   # ✅ Thêm để hiển thị tooltip
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