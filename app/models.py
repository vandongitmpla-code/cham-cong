from flask_sqlalchemy import SQLAlchemy
from app import db
db = SQLAlchemy()
from app.extensions import db
from app.extensions import db
from datetime import datetime

# app/models.py - Cập nhật class Employee
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
    start_month = db.Column(db.String(7))  # Format: YYYY-MM (ví dụ: 2025-07)
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
    month = db.Column(db.String(7), nullable=False)  # dạng YYYY-MM
    working_days = db.Column(db.Float, default=0)    # số ngày công (có thể lẻ 0.5)
    salary = db.Column(db.Float, default=0)          # lương thực lãnh (tính toán)

    # Quan hệ ngược đã có từ Employee.payrolls

    def __repr__(self):
        return f"<Payroll emp={self.employee_id}, month={self.month}, days={self.working_days}, salary={self.salary}>"

class Holiday(db.Model):
    __tablename__ = "holidays"

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, unique=True)
    name = db.Column(db.String(100))

    def __repr__(self):
        return f"<Holiday {self.date} - {self.name}>"
        


class PayrollRecord(db.Model):
    __tablename__ = "payroll_records"

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id"), nullable=False)
    
    # 👉 Các cột hiện có
    employee_code = db.Column(db.String(50))
    employee_name = db.Column(db.String(100))
    period = db.Column(db.String(7), nullable=False)
    ngay_cong = db.Column(db.Float, default=0)
    ngay_vang = db.Column(db.Float, default=0)
    chu_nhat = db.Column(db.Float, default=0)
    le_tet = db.Column(db.Float, default=0)  #  số ngày lễ
    le_tet_gio = db.Column(db.Float, default=0)  #  số giờ tăng ca ngày lễ
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
    

class WorkAdjustment(db.Model):
    __tablename__ = "work_adjustments"

    id = db.Column(db.Integer, primary_key=True)
    payroll_record_id = db.Column(db.Integer, db.ForeignKey("payroll_records.id"), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id"), nullable=False)
    period = db.Column(db.String(7), nullable=False)
    employee_code = db.Column(db.String(50))
    employee_name = db.Column(db.String(100))
    original_work_days = db.Column(db.Float, default=0)
    standard_work_days = db.Column(db.Float, default=0)
    original_overtime_hours = db.Column(db.Float, default=0)
    adjusted_work_days = db.Column(db.Float, default=0)
    remaining_overtime_hours = db.Column(db.Float, default=0)
    used_overtime_hours = db.Column(db.Float, default=0)
    
    # ✅ THÊM CÁC TRƯỜNG MỚI NẾU CẦN
    original_absence_days = db.Column(db.Float, default=0)  # Số ngày nghỉ gốc
    adjusted_absence_days = db.Column(db.Float, default=0)  # Số ngày nghỉ sau điều chỉnh
    
    adjustment_type = db.Column(db.String(50), default="overtime_compensation")
    adjustment_reason = db.Column(db.Text)
    calculated_at = db.Column(db.DateTime, default=datetime.utcnow)

    payroll_record = db.relationship("PayrollRecord", backref="work_adjustments")

    def __repr__(self):
        return f"<WorkAdjustment {self.employee_code} - {self.period}>"
    