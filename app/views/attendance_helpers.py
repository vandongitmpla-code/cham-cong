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

#  CÔNG THỨC TÍNH ĐIỀU CHỈNH THEO LOGIC MỚI
def calculate_adjustment_details(original_days, standard_days, overtime_hours, current_absence):
    """
    Tính toán chi tiết điều chỉnh - CHỈ GỘP VÀO NGÀY CÔNG, KHÔNG BÙ NGÀY NGHỈ
    """
    overtime_days = overtime_hours / 8
    
    # 1. Gộp toàn bộ tăng ca vào ngày công (KHÔNG VƯỢT CHUẨN)
    adjusted_days = original_days + overtime_days
    if adjusted_days > standard_days:
        adjusted_days = standard_days
    
    # 2. ✅ KHÔNG DÙNG TĂNG CA ĐỂ BÙ NGÀY NGHỈ - GIỮ NGUYÊN
    ngay_vang_sau_gop = current_absence  # Giữ nguyên ngày nghỉ
    
    # Tính giờ tăng ca đã sử dụng
    used_days = adjusted_days - original_days
    used_hours = used_days * 8
    remaining_hours = overtime_hours - used_hours
    
    return adjusted_days, ngay_vang_sau_gop, remaining_hours, used_hours

def create_attendance_rows(records, period):
    """
    Tạo dữ liệu rows cho template attendance_print - SỬA LỖI GỘP SAI CỘT
    """
    from datetime import datetime
    from app.models import WorkAdjustment
    
    rows = []
    stt = 1

    for rec in records:
        # Lấy standard_days từ database
        standard_days = rec.standard_work_days

        # Kiểm tra xem có điều chỉnh không
        adjustment = WorkAdjustment.query.filter_by(
            employee_code=rec.employee_code, 
            period=period
        ).first()
        
        if adjustment:
            # ✅ SỬA: CHỈ ÁP DỤNG ĐIỀU CHỈNH CHO CỘT "THỰC TẾ"
            ngay_cong_quy_dinh = standard_days           # Cột quy định = NGÀY CÔNG CHUẨN
            ngay_cong_thuc_te = adjustment.adjusted_work_days   # Cột thực tế = ĐÃ ĐIỀU CHỈNH
            ngay_vang_hien_thi = adjustment.ngay_vang_sau_gop
            tang_ca_nghi_hien_thi = adjustment.remaining_overtime_hours
            adjustment_info = adjustment.used_overtime_hours
            original_days = adjustment.original_work_days
            ngay_vang_ban_dau = adjustment.ngay_vang_ban_dau
            has_adjustment = True
        else:
            # ✅ CHƯA ĐIỀU CHỈNH: CẢ HAI CỘT BẰNG NHAU
            ngay_cong_quy_dinh = standard_days           # Cột quy định = NGÀY CÔNG CHUẨN
            ngay_cong_thuc_te = rec.ngay_cong            # Cột thực tế = NGÀY CÔNG THỰC TẾ
            ngay_vang_hien_thi = rec.ngay_vang
            tang_ca_nghi_hien_thi = rec.tang_ca_nghi
            adjustment_info = 0
            original_days = rec.ngay_cong
            ngay_vang_ban_dau = rec.ngay_vang
            has_adjustment = False

        # LUÔN CHO PHÉP ĐIỀU CHỈNH NẾU CÓ GIỜ TĂNG CA
        has_overtime = rec.tang_ca_nghi > 0

        rows.append([
            stt, rec.employee_code, rec.employee_name, rec.phong_ban, rec.loai_hd,
            ngay_cong_quy_dinh,   # "Số ngày/giờ làm việc quy định trong tháng" = STANDARD
            "", 
            ngay_vang_hien_thi,   # "Số ngày nghỉ không lương"
            ngay_cong_thuc_te,    # "Số ngày/giờ làm việc thực tế trong tháng" = ĐIỀU CHỈNH/GỐC
            tang_ca_nghi_hien_thi, # "Số giờ làm việc tăng ca (ngày nghỉ hàng tuần)"
            rec.le_tet_gio, 
            rec.tang_ca_tuan, 
            rec.ghi_chu or "", 
            "", 
            "", 
            rec.to,
            {
                'has_adjustment': has_adjustment,
                'has_overtime': has_overtime,
                'adjustment_info': adjustment_info,
                'original_days': original_days,
                'current_days': rec.ngay_cong,
                'standard_days': standard_days,
                'ngay_vang_ban_dau': ngay_vang_ban_dau,
                'ngay_vang_sau_gop': ngay_vang_hien_thi
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