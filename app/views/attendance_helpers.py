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
    Tính toán điều chỉnh - DÙNG PHÉP NĂM TÍCH LŨY
    """
    print(f"🧮 CALCULATION INPUT:")
    print(f"  - original_days: {original_days}")
    print(f"  - standard_days: {standard_days}")
    print(f"  - ngay_vang_ban_dau: {ngay_vang_ban_dau}")
    print(f"  - overtime_hours: {overtime_hours} ({overtime_hours/8} ngày)")
    print(f"  - ngay_nghi_phep_nam_da_dung: {ngay_nghi_phep_nam_da_dung}")  # ĐÃ DÙNG
    print(f"  - phep_nam_kha_dung: {phep_nam_kha_dung}")  # CÒN LẠI TÍCH LŨY
    print(f"  - use_extra_leave: {use_extra_leave}")
    
    # Chuyển giờ tăng ca sang ngày
    overtime_days = overtime_hours / 8
    
    # TÍNH TOÁN BAN ĐẦU - DÙNG PHÉP NĂM CÒN LẠI TÍCH LŨY
    # 1. Dùng phép năm bù ngày vắng (tối đa = ngày vắng VÀ tối đa = phép năm còn lại)
    ngay_phep_su_dung = min(ngay_vang_ban_dau, phep_nam_kha_dung)
    
    # 2. Ngày vắng còn lại sau khi dùng phép năm
    ngay_vang_con_sau_phep = ngay_vang_ban_dau - ngay_phep_su_dung
    
    # 3. Dùng tăng ca bù ngày vắng còn lại
    ngay_tang_ca_su_dung = min(overtime_days, ngay_vang_con_sau_phep)
    
    # 4. Tính ngày công tạm thời
    ngay_cong_tam = original_days + ngay_phep_su_dung + ngay_tang_ca_su_dung
    
    # 5. KIỂM TRA GIỚI HẠN: Không được vượt quá ngày công chuẩn
    if ngay_cong_tam > standard_days:
        vuot_qua = ngay_cong_tam - standard_days
        
        if ngay_tang_ca_su_dung >= vuot_qua:
            ngay_tang_ca_su_dung -= vuot_qua
            vuot_qua = 0
        else:
            vuot_qua -= ngay_tang_ca_su_dung
            ngay_tang_ca_su_dung = 0
            
        if vuot_qua > 0 and ngay_phep_su_dung >= vuot_qua:
            ngay_phep_su_dung -= vuot_qua
            vuot_qua = 0
        
        ngay_cong_cuoi = original_days + ngay_phep_su_dung + ngay_tang_ca_su_dung
    else:
        ngay_cong_cuoi = ngay_cong_tam
    
    # 6. Tính ngày vắng cuối cùng BAN ĐẦU
    ngay_vang_cuoi = ngay_vang_ban_dau - ngay_phep_su_dung - ngay_tang_ca_su_dung
    
    print(f"📊 BEFORE EXTRA LEAVE:")
    print(f"  - ngay_vang_cuoi: {ngay_vang_cuoi}")
    print(f"  - ngay_phep_su_dung: {ngay_phep_su_dung}")
    
    # 7. XỬ LÝ XÁC NHẬN THÊM PHÉP NĂM (nếu được yêu cầu)
    if use_extra_leave and ngay_vang_cuoi > 0:
        # ✅ SỬA: Tính số phép năm còn lại có thể dùng = phép năm tích lũy - phép năm đã dùng trong lần này
        phep_nam_con_lai_kha_dung = phep_nam_kha_dung - ngay_phep_su_dung
        
        print(f"  - EXTRA LEAVE - phep_nam_con_lai_kha_dung: {phep_nam_con_lai_kha_dung}")
        
        if phep_nam_con_lai_kha_dung >= ngay_vang_cuoi:
            # Dùng hết phép năm còn lại để bù nốt
            ngay_phep_su_dung += ngay_vang_cuoi
            ngay_vang_cuoi = 0
            ngay_cong_cuoi = original_days + ngay_phep_su_dung + ngay_tang_ca_su_dung
            
            # Kiểm tra lại không vượt quá chuẩn
            if ngay_cong_cuoi > standard_days:
                ngay_cong_cuoi = standard_days
                
            print(f"  - AFTER EXTRA LEAVE - ngay_phep_su_dung: {ngay_phep_su_dung}")
            print(f"  - AFTER EXTRA LEAVE - ngay_vang_cuoi: {ngay_vang_cuoi}")
        else:
            # Chỉ dùng được một phần phép năm còn lại
            ngay_phep_su_dung += phep_nam_con_lai_kha_dung
            ngay_vang_cuoi -= phep_nam_con_lai_kha_dung
            ngay_cong_cuoi = original_days + ngay_phep_su_dung + ngay_tang_ca_su_dung
            
            # Kiểm tra lại không vượt quá chuẩn
            if ngay_cong_cuoi > standard_days:
                ngay_cong_cuoi = standard_days
                
            print(f"  - AFTER EXTRA LEAVE - ngay_phep_su_dung: {ngay_phep_su_dung}")
            print(f"  - AFTER EXTRA LEAVE - ngay_vang_cuoi: {ngay_vang_cuoi}")
    
    # 8. Tính toán kết quả cuối - PHÉP NĂM CÒN LẠI TÍCH LŨY
    tang_ca_con_lai = overtime_hours - (ngay_tang_ca_su_dung * 8)
    phep_nam_con_lai_tich_luy = phep_nam_kha_dung - ngay_phep_su_dung  # ✅ TÍNH LẠI TỪ PHÉP NĂM TÍCH LŨY

    final_result = {
        'ngay_cong_cuoi': ngay_cong_cuoi,
        'ngay_vang_cuoi': ngay_vang_cuoi,
        'tang_ca_con_lai': tang_ca_con_lai,
        'so_ngay_bu_tu_tang_ca': ngay_tang_ca_su_dung,
        'ngay_nghi_phep_nam_da_dung': ngay_phep_su_dung,
        'gio_tang_ca_da_dung': ngay_tang_ca_su_dung * 8,
        'phep_nam_con_lai': phep_nam_con_lai_tich_luy,
        'can_xac_nhan_them_phep': (ngay_vang_cuoi > 0) and (phep_nam_con_lai_tich_luy > 0) and not use_extra_leave,
        'ngay_vang_con_lai': ngay_vang_cuoi,
        'phep_nam_kha_dung': phep_nam_con_lai_tich_luy  # ✅ TRẢ VỀ PHÉP NĂM CÒN LẠI MỚI
    }
    
    print(f"🎯 FINAL RESULT:")
    print(f"  - ngay_cong_cuoi: {final_result['ngay_cong_cuoi']}")
    print(f"  - ngay_vang_cuoi: {final_result['ngay_vang_cuoi']}")
    print(f"  - phep_nam_kha_dung: {final_result['phep_nam_kha_dung']}")
    print(f"  - can_xac_nhan_them_phep: {final_result['can_xac_nhan_them_phep']}")
    
    return final_result

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
            stt, rec.employee_code, rec.employee_name, rec.phong_ban, rec.loai_hd,
            standard_days,
            ngay_nghi_phep_nam_da_dung,
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
                'ngay_nghi_phep_nam_da_dung': ngay_nghi_phep_nam_da_dung,
                'so_thang_duoc_huong': so_thang_duoc_huong,
                'employee_id': employee.id,
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