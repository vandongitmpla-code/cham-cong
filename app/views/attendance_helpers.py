from datetime import datetime
from app.models import WorkAdjustment




def create_attendance_rows(records, period):
    """
    Tạo dữ liệu rows cho template attendance_print - THEO LOGIC MỚI
    """

    
    rows = []
    stt = 1

    for rec in records:
        # Kiểm tra xem có điều chỉnh không
        adjustment = WorkAdjustment.query.filter_by(
            employee_code=rec.employee_code, 
            period=period
        ).first()
        
        # THEO LOGIC MỚI: Cả hai cột đều từ payroll_record.ngay_cong
        if adjustment:
            # Đã điều chỉnh: HIỂN THỊ adjusted_work_days cho CẢ HAI CỘT
            ngay_cong_quy_dinh = adjustment.adjusted_work_days  # Cột quy định
            ngay_cong_thuc_te = adjustment.adjusted_work_days   # Cột thực tế
            tang_ca_nghi_hien_thi = adjustment.remaining_overtime_hours
            adjustment_info = adjustment.used_overtime_hours
            original_days = adjustment.original_work_days
        else:
            # Chưa điều chỉnh: HIỂN THỊ ngay_cong cho CẢ HAI CỘT
            ngay_cong_quy_dinh = rec.ngay_cong  # Cột quy định  
            ngay_cong_thuc_te = rec.ngay_cong   # Cột thực tế
            tang_ca_nghi_hien_thi = rec.tang_ca_nghi
            adjustment_info = 0
            original_days = rec.ngay_cong

        # Kiểm tra có thể áp dụng điều chỉnh không
        has_adjustment_option = (
            adjustment is None and 
            rec.tang_ca_nghi > 0
        )

        rows.append([
            stt, rec.employee_code, rec.employee_name, rec.phong_ban, rec.loai_hd,
            ngay_cong_quy_dinh,   # ✅ Cột "Số ngày/giờ làm việc quy định trong tháng"
            "", rec.ngay_vang, 
            ngay_cong_thuc_te,    # ✅ Cột "Số ngày/giờ làm việc thực tế trong tháng"  
            tang_ca_nghi_hien_thi,
            rec.le_tet_gio, rec.tang_ca_tuan, rec.ghi_chu or "", "", "", rec.to,
            {
                'has_adjustment_option': has_adjustment_option,
                'adjustment_info': adjustment_info,
                'original_days': original_days,
                'current_days': rec.ngay_cong  # Ngày công hiện tại trong payroll_record
            }
        ])
        stt += 1
    
    return rows