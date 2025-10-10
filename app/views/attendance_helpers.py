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

def calculate_adjustment_details(original_days, standard_days, ngay_vang_ban_dau, overtime_hours, ngay_nghi_phep_nam_da_dung):
    """
    Tính toán điều chỉnh theo logic mới
    """
    # Chuyển giờ tăng ca sang ngày
    overtime_days = overtime_hours / 8
    
    # Tính số ngày có thể bù từ tăng ca
    ngay_vang_con_lai_sau_phep = max(0, ngay_vang_ban_dau - ngay_nghi_phep_nam_da_dung)
    so_ngay_bu_tu_tang_ca = min(overtime_days, ngay_vang_con_lai_sau_phep)
    
    # Tính ngày công tạm thời
    ngay_cong_tam = original_days + ngay_nghi_phep_nam_da_dung + so_ngay_bu_tu_tang_ca
    
    # GIỚI HẠN KHÔNG VƯỢT QUÁ NGÀY CÔNG CHUẨN
    ngay_nghi_phep_nam_da_dung_final = ngay_nghi_phep_nam_da_dung
    so_ngay_bu_tu_tang_ca_final = so_ngay_bu_tu_tang_ca
    
    if ngay_cong_tam > standard_days:
        # Tính số ngày thừa
        ngay_thua = ngay_cong_tam - standard_days
        
        # Giảm số ngày bù từ tăng ca trước
        if so_ngay_bu_tu_tang_ca_final >= ngay_thua:
            so_ngay_bu_tu_tang_ca_final -= ngay_thua
            ngay_thua = 0
        else:
            ngay_thua -= so_ngay_bu_tu_tang_ca_final
            so_ngay_bu_tu_tang_ca_final = 0
            
        # Nếu vẫn thừa, giảm phép năm đã dùng
        if ngay_thua > 0:
            ngay_nghi_phep_nam_da_dung_final -= ngay_thua
        
        ngay_cong_cuoi = standard_days
    else:
        ngay_cong_cuoi = ngay_cong_tam
    
    # Tính kết quả cuối
    ngay_vang_cuoi = max(0, ngay_vang_ban_dau - ngay_nghi_phep_nam_da_dung_final - so_ngay_bu_tu_tang_ca_final)
    tang_ca_con_lai = overtime_hours - (so_ngay_bu_tu_tang_ca_final * 8)
    
    return {
        'ngay_cong_cuoi': ngay_cong_cuoi,
        'ngay_vang_cuoi': ngay_vang_cuoi,
        'tang_ca_con_lai': tang_ca_con_lai,
        'so_ngay_bu_tu_tang_ca': so_ngay_bu_tu_tang_ca_final,
        'ngay_nghi_phep_nam_da_dung': ngay_nghi_phep_nam_da_dung_final,
        'gio_tang_ca_da_dung': so_ngay_bu_tu_tang_ca_final * 8
    }


def create_attendance_rows(records, period):
    """
    Tạo dữ liệu rows cho template - LOGIC ĐƠN GIẢN: HIỂN THỊ GIÁ TRỊ GỐC KHI CHƯA ĐIỀU CHỈNH
    """
    from app.models import WorkAdjustment, PaidLeave
    
    rows = []
    stt = 1

    for rec in records:
        standard_days = rec.standard_work_days

        # ✅ TÍNH TOÁN THÔNG TIN PHÉP NĂM
        employee = rec.employee
        thang_bat_dau_tinh_phep, so_thang_duoc_huong, so_ngay_phep_con_lai = calculate_leave_info(employee, period)
        
        paid_leave = PaidLeave.query.filter_by(
            employee_id=employee.id,
            period=period
        ).first()
        
        if paid_leave:
            ngay_nghi_phep_nam_da_dung = paid_leave.leave_days_used
            so_ngay_phep_con_lai = paid_leave.remaining_leave_days
        else:
            ngay_nghi_phep_nam_da_dung = 0
            so_ngay_phep_con_lai = so_thang_duoc_huong

        # ✅ QUAN TRỌNG: LẤY GIÁ TRỊ GỐC TỪ PAYROLL RECORD (KHÔNG ĐIỀU CHỈNH)
        ngay_cong_ban_dau = rec.ngay_cong  # Giá trị gốc từ import
        ngay_vang_ban_dau = rec.ngay_vang  # Giá trị gốc từ import
        
        # ✅ SỬA QUAN TRỌNG: TÍNH TỔNG GIỜ TĂNG CA TỪ SỐ NGÀY CHỦ NHẬT
        # rec.chu_nhat là số ngày CN đã làm, mỗi ngày = 8 giờ tăng ca
        tong_gio_tang_ca = rec.chu_nhat * 8  # ✅ TÍNH TỔNG GIỜ TĂNG CA
        gio_tang_ca_con_lai = rec.tang_ca_nghi  # Giờ tăng ca còn lại

        adjustment = WorkAdjustment.query.filter_by(
            employee_code=rec.employee_code, 
            period=period
        ).first()
        
        if adjustment:
            # ✅ ĐÃ CÓ ĐIỀU CHỈNH - DÙNG GIÁ TRỊ ĐÃ TÍNH TOÁN
            ngay_cong_hien_thi = adjustment.adjusted_work_days
            ngay_vang_hien_thi = adjustment.adjusted_absence_days
            tang_ca_nghi_hien_thi = adjustment.remaining_overtime_hours
            
            has_adjustment = True
            adjustment_info = adjustment.used_overtime_hours
            
        else:
            # ✅ CHƯA ĐIỀU CHỈNH - DÙNG GIÁ TRỊ GỐC (KHÔNG TÍNH TOÁN)
            ngay_cong_hien_thi = ngay_cong_ban_dau
            ngay_vang_hien_thi = ngay_vang_ban_dau
            tang_ca_nghi_hien_thi = gio_tang_ca_con_lai  # Dùng giờ còn lại
            
            has_adjustment = False
            adjustment_info = 0

        # ✅ SỬA QUAN TRỌNG: has_overtime DỰA VÀO TỔNG GIỜ TĂNG CA
        has_overtime = tong_gio_tang_ca > 0

        rows.append([
            stt, rec.employee_code, rec.employee_name, rec.phong_ban, rec.loai_hd,
            standard_days,  # Số ngày/giờ làm việc quy định trong tháng
            ngay_nghi_phep_nam_da_dung,  # Số ngày nghỉ phép năm ĐÃ DÙNG
            ngay_vang_hien_thi,  # Số ngày nghỉ không lương
            ngay_cong_hien_thi,  # Số ngày/giờ làm việc thực tế
            tang_ca_nghi_hien_thi,  # Số giờ tăng ca CN còn lại
            rec.le_tet_gio, 
            rec.tang_ca_tuan, 
            rec.ghi_chu or "", 
            thang_bat_dau_tinh_phep,  # ✅ CỘT NÀY SẼ HIỂN THỊ
            so_ngay_phep_con_lai,     # ✅ CỘT NÀY SẼ HIỂN THỊ
            rec.to,
            {
                'has_adjustment': has_adjustment,
                'has_overtime': has_overtime,
                'adjustment_info': adjustment_info,
                'original_days': ngay_cong_ban_dau,
                'current_days': ngay_cong_hien_thi,
                'standard_days': standard_days,
                'ngay_vang_ban_dau': ngay_vang_ban_dau,
                'ngay_nghi_phep_nam_da_dung': ngay_nghi_phep_nam_da_dung,
                'so_thang_duoc_huong': so_thang_duoc_huong,
                'employee_id': employee.id,
                'tong_gio_tang_ca': tong_gio_tang_ca,  # ✅ THÊM TỔNG GIỜ TĂNG CA
                'gio_tang_ca_con_lai': gio_tang_ca_con_lai
            }
        ])
        stt += 1
    
    return rows

def calculate_leave_info(employee, period):
    """
    Tính toán thông tin phép năm từ start_month đến period hiện tại
    """
    if not employee.start_month:
        return "", 0, 0
    
    try:
        # Parse start_month và period
        start_date = datetime.strptime(employee.start_month + "-01", "%Y-%m-%d")
        current_date = datetime.strptime(period + "-01", "%Y-%m-%d")
        
        # Kiểm tra nếu start_month sau period
        if start_date > current_date:
            return "", 0, 0
        
        # Tính số tháng từ start_month đến period
        months = []
        total_months = 0
        
        temp_date = start_date
        while temp_date <= current_date:
            months.append(temp_date.month)
            total_months += 1
            # Tăng tháng
            if temp_date.month == 12:
                temp_date = temp_date.replace(year=temp_date.year + 1, month=1)
            else:
                temp_date = temp_date.replace(month=temp_date.month + 1)
        
        # Format months: "6,7,8,9,10"
        months_str = ",".join(map(str, months))
        
        return months_str, total_months, total_months  # months_str, total_months, remaining_days
    
    except Exception as e:
        print(f"Error calculating leave info: {e}")
        return "", 0, 0
    
    
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