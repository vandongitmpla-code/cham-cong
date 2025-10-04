from flask_sqlalchemy import SQLAlchemy
from app import db
db = SQLAlchemy()
from app.extensions import db
from app.extensions import db

class Employee(db.Model):
    __tablename__ = "employees"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)    # Mã nhân viên
    name = db.Column(db.String(100), nullable=False)                # Họ và tên
    team = db.Column(db.String(100))                                # Tổ
    department = db.Column(db.String(100))                          # Phòng ban
    contract_type = db.Column(db.String(50))                        # Loại HĐ
    salary_base = db.Column(db.Float, default=0)                    # Lương cơ bản
    att_code = db.Column(db.String(50), unique=True)                # Mã chấm công (máy chấm công)

    # Quan hệ (chỉ để sẵn, nếu chưa có bảng AttendanceLog / Payroll thì comment lại)
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
    date = db.Column(db.Date, nullable=False, unique=True)   # ngày lễ
    name = db.Column(db.String(100))                         # mô tả, ví dụ "Quốc khánh"

    def __repr__(self):
        return f"<Holiday {self.date} - {self.name}>"
