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

def calculate_adjustment_details(original_days, standard_days, ngay_vang_ban_dau, overtime_hours, ngay_nghi_phep_nam_da_dung, phep_nam_kha_dung, use_extra_leave=False):
    """
    Tính toán điều chỉnh - LOGIC ĐƠN GIẢN
    """
    print(f"🧮 CALCULATION INPUT:")
    print(f"  - original_days: {original_days}")
    print(f"  - standard_days: {standard_days}")
    print(f"  - ngay_vang_ban_dau: {ngay_vang_ban_dau}")
    print(f"  - overtime_hours: {overtime_hours} ({overtime_hours/8} ngày)")
    print(f"  - ngay_nghi_phep_nam_da_dung: {ngay_nghi_phep_nam_da_dung}")  # PHÉP NĂM ĐÃ DÙNG
    print(f"  - phep_nam_kha_dung: {phep_nam_kha_dung}")  # PHÉP NĂM CÒN LẠI
    print(f"  - use_extra_leave: {use_extra_leave}")
    
    # Chuyển giờ tăng ca sang ngày
    overtime_days = overtime_hours / 8
    
    # ✅ 1. TÍNH TOÁN CƠ BẢN
    # Tổng số ngày có thể bù = Phép năm đã dùng + Tăng ca CN
    tong_ngay_bu = ngay_nghi_phep_nam_da_dung + overtime_days
    
    # Ngày công sau gộp = Ngày công ban đầu + Tổng bù
    ngay_cong_cuoi = original_days + tong_ngay_bu
    
    # Ngày nghỉ còn lại = Ngày nghỉ ban đầu - Tổng bù
    ngay_vang_cuoi = ngay_vang_ban_dau - tong_ngay_bu
    
    # ✅ 2. KIỂM TRA GIỚI HẠN NGÀY CÔNG CHUẨN
    if ngay_cong_cuoi > standard_days:
        # Nếu vượt quá, chỉ được tối đa = standard_days
        vuot_qua = ngay_cong_cuoi - standard_days
        ngay_cong_cuoi = standard_days
        # Điều chỉnh ngày nghỉ còn lại
        ngay_vang_cuoi = ngay_vang_ban_dau - (standard_days - original_days)
    
    # Đảm bảo ngày nghỉ không âm
    if ngay_vang_cuoi < 0:
        ngay_vang_cuoi = 0
    
    # ✅ 3. XỬ LÝ THÊM PHÉP NĂM NẾU ĐƯỢC YÊU CẦU
    if use_extra_leave and ngay_vang_cuoi > 0 and phep_nam_kha_dung > 0:
        # Dùng thêm phép năm để bù nốt ngày nghỉ còn lại
        so_ngay_them = min(ngay_vang_cuoi, phep_nam_kha_dung)
        ngay_nghi_phep_nam_da_dung += so_ngay_them
        ngay_vang_cuoi -= so_ngay_them
        phep_nam_kha_dung -= so_ngay_them
        ngay_cong_cuoi = original_days + ngay_nghi_phep_nam_da_dung + overtime_days
        
        # Kiểm tra lại giới hạn
        if ngay_cong_cuoi > standard_days:
            ngay_cong_cuoi = standard_days
    
    # ✅ 4. TÍNH TOÁN KẾT QUẢ CUỐI
    tang_ca_con_lai = 0  # Đã dùng hết tăng ca
    gio_tang_ca_da_dung = overtime_hours

    final_result = {
        'ngay_cong_cuoi': ngay_cong_cuoi,
        'ngay_vang_cuoi': ngay_vang_cuoi,
        'tang_ca_con_lai': tang_ca_con_lai,
        'so_ngay_bu_tu_tang_ca': overtime_days,
        'ngay_nghi_phep_nam_da_dung': ngay_nghi_phep_nam_da_dung,
        'gio_tang_ca_da_dung': gio_tang_ca_da_dung,
        'phep_nam_con_lai': phep_nam_kha_dung,
        'can_xac_nhan_them_phep': (ngay_vang_cuoi > 0) and (phep_nam_kha_dung > 0) and not use_extra_leave,
        'ngay_vang_con_lai': ngay_vang_cuoi,
        'phep_nam_kha_dung': phep_nam_kha_dung
    }
    
    print(f"🎯 FINAL RESULT:")
    print(f"  - ngay_cong_cuoi: {final_result['ngay_cong_cuoi']}")
    print(f"  - ngay_vang_cuoi: {final_result['ngay_vang_cuoi']}")
    print(f"  - phep_nam_kha_dung: {final_result['phep_nam_kha_dung']}")
    print(f"  - can_xac_nhan_them_phep: {final_result['can_xac_nhan_them_phep']}")
    
    return final_result

def create_attendance_rows(records, period):
    """
    Tạo dữ liệu rows cho template - ĐẢM BẢO TRUYỀN ĐÚNG PHÉP NĂM ĐÃ DÙNG
    """
    from app.models import WorkAdjustment
    
    rows = []
    stt = 1

    for rec in records:
        standard_days = rec.standard_work_days

        # ✅ LẤY THÔNG TIN PHÉP NĂM TỪ PAYROLL_RECORDS
        ngay_nghi_phep_nam_da_dung = rec.ngay_nghi_phep_nam or 0  # PHÉP NĂM ĐÃ "+"
        so_ngay_phep_con_lai = rec.ngay_phep_con_lai or 0
        thang_bat_dau_tinh_phep = rec.thang_bat_dau_tinh_phep or ""

        # ✅ QUAN TRỌNG: LẤY GIÁ TRỊ GỐC TỪ PAYROLL RECORD (KHÔNG ĐIỀU CHỈNH)
        ngay_cong_ban_dau = rec.ngay_cong
        ngay_vang_ban_dau = rec.ngay_vang
        tang_ca_nghi_ban_dau = rec.tang_ca_nghi

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
            tang_ca_nghi_hien_thi = tang_ca_nghi_ban_dau
            
            has_adjustment = False
            adjustment_info = 0

        has_overtime = tang_ca_nghi_ban_dau > 0

        rows.append([
            stt, 
            rec.employee_code, 
            rec.employee_name, 
            rec.phong_ban, 
            rec.loai_hd,
            standard_days,
            ngay_nghi_phep_nam_da_dung,  # ✅ HIỂN THỊ PHÉP NĂM ĐÃ "+"
            ngay_vang_hien_thi,
            ngay_cong_hien_thi,
            tang_ca_nghi_hien_thi,
            rec.le_tet_gio, 
            rec.tang_ca_tuan, 
            rec.ghi_chu or "", 
            thang_bat_dau_tinh_phep,
            so_ngay_phep_con_lai,
            rec.to,
            {
                'has_adjustment': has_adjustment,
                'has_overtime': has_overtime,
                'adjustment_info': adjustment_info,
                'original_days': ngay_cong_ban_dau,
                'current_days': ngay_cong_hien_thi,
                'standard_days': standard_days,
                'ngay_vang_ban_dau': ngay_vang_ban_dau,
                'ngay_nghi_phep_nam_da_dung': ngay_nghi_phep_nam_da_dung,  # ✅ TRUYỀN ĐÚNG
                'so_thang_duoc_huong': so_ngay_phep_con_lai,
                'employee_id': rec.employee_id,
                'tang_ca_nghi_ban_dau': tang_ca_nghi_ban_dau
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
        
        return months_str, total_months, total_months
    
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