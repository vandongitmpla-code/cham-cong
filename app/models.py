from flask_sqlalchemy import SQLAlchemy
from app.extensions import db  # ✅ CHỈ IMPORT MỘT LẦN
from datetime import datetime

class Employee(db.Model):
    __tablename__ = "employees"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    team = db.Column(db.String(100))
    department = db.Column(db.String(100))
    contract_type = db.Column(db.String(50))
    salary_base = db.Column(db.Float, default=0)
    att_code = db.Column(db.String(50), unique=True)
    start_month = db.Column(db.String(7)) 
    insurance_start_month = db.Column(db.String(7))  

    # Quan hệ
    attendances = db.relationship("AttendanceLog", backref="employee", lazy=True)
    payrolls = db.relationship("Payroll", backref="employee", lazy=True)

    def __repr__(self):
        return f"<Employee {self.code} - {self.name}>"

class AttendanceLog(db.Model):
    __tablename__ = "attendance_logs"

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id"), nullable=False)
    date = db.Column(db.Date, nullable=False)
    checkin = db.Column(db.Time)
    checkout = db.Column(db.Time)

class Payroll(db.Model):
    __tablename__ = "payrolls"

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id"), nullable=False)
    month = db.Column(db.String(7), nullable=False)
    working_days = db.Column(db.Float, default=0)
    salary = db.Column(db.Float, default=0)

    def __repr__(self):
        return f"<Payroll emp={self.employee_id}, month={self.month}, days={self.working_days}, salary={self.salary}>"

class Holiday(db.Model):
    __tablename__ = "holidays"

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, unique=True)
    name = db.Column(db.String(100))

    def __repr__(self):
        return f"<Holiday {self.date} - {self.name}>"
#----------------------------------------------bảng công tính lương---------------------------------------------------------------
class PayrollRecord(db.Model):
    __tablename__ = "payroll_records"

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id"), nullable=False)
    
    employee_code = db.Column(db.String(50))
    employee_name = db.Column(db.String(100))
    period = db.Column(db.String(7), nullable=False)
    ngay_cong = db.Column(db.Float, default=0)
    standard_work_days = db.Column(db.Float, default=0)
    ngay_vang = db.Column(db.Float, default=0)
    chu_nhat = db.Column(db.Float, default=0)
    le_tet = db.Column(db.Float, default=0)
    le_tet_gio = db.Column(db.Float, default=0)
    tang_ca_nghi = db.Column(db.Float, default=0)
    tang_ca_tuan = db.Column(db.Float, default=0)
    ghi_chu = db.Column(db.Text)
    raw_data = db.Column(db.JSON)
    to = db.Column(db.String(100))
    phong_ban = db.Column(db.String(100))
    loai_hd = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    
    employee = db.relationship("Employee", backref="payroll_records")

    def __repr__(self):
        return f"<PayrollRecord {self.employee_code} - {self.employee_name} ({self.period})>"
#-----------------------ngày công và ngày vắng--------------------------------------------------------------------------------
class WorkAdjustment(db.Model):
    __tablename__ = "work_adjustments"  # ✅ TABLE NAME ĐÚNG

    id = db.Column(db.Integer, primary_key=True)
    payroll_record_id = db.Column(db.Integer, db.ForeignKey("payroll_records.id", ondelete="CASCADE"), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id"), nullable=False)
    period = db.Column(db.String(7), nullable=False)
    employee_code = db.Column(db.String(50))
    employee_name = db.Column(db.String(100))
    
    # DỮ LIỆU GỐC
    original_work_days = db.Column(db.Float, default=0)
    original_absence_days = db.Column(db.Float, default=0)
    original_overtime_hours = db.Column(db.Float, default=0)
    
    # DỮ LIỆU SAU ĐIỀU CHỈNH
    adjusted_work_days = db.Column(db.Float, default=0)
    adjusted_absence_days = db.Column(db.Float, default=0)
    remaining_overtime_hours = db.Column(db.Float, default=0)
    used_overtime_hours = db.Column(db.Float, default=0)
    ngay_vang_ban_dau = db.Column(db.Float, default=0)      # Tham chiếu từ payroll_record.ngay_vang
    ngay_vang_sau_gop = db.Column(db.Float, default=0)      # Ngày vắng sau khi gộp
    
    standard_work_days = db.Column(db.Float, default=0)
    adjustment_type = db.Column(db.String(50), default="overtime_compensation")
    adjustment_reason = db.Column(db.Text)
    calculated_at = db.Column(db.DateTime, default=datetime.utcnow)

    payroll_record = db.relationship("PayrollRecord", backref="work_adjustments")

    def __repr__(self):
        return f"<WorkAdjustment {self.employee_code} - {self.period}>"
#-------------------phép năm--------------------------------------------------
class PaidLeave(db.Model):
    __tablename__ = "paid_leaves"

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id"), nullable=False)
    period = db.Column(db.String(7), nullable=False)  # YYYY-MM
    leave_days_used = db.Column(db.Float, default=0)  # Số ngày phép đã sử dụng
    remaining_leave_days = db.Column(db.Float, default=0)  # Số ngày phép còn lại
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    employee = db.relationship("Employee", backref="paid_leaves")

    def __repr__(self):
        return f"<PaidLeave {self.employee_id} - {self.period}>"
    