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
    date = db.Column(db.Date, nullable=False, unique=True)
    name = db.Column(db.String(100))

    def __repr__(self):
        return f"<Holiday {self.date} - {self.name}>"
    
    
class PayrollRecord(db.Model):
    __tablename__ = "payroll_records"

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id"), nullable=False)

    # Kỳ công, ví dụ "2025-09"
    period = db.Column(db.String(7), nullable=False)

    # Các cột chính từ payroll.html
    ngay_cong = db.Column(db.Float, default=0)              # Số ngày công
    ngay_vang = db.Column(db.Float, default=0)              # Số ngày vắng
    chu_nhat = db.Column(db.Float, default=0)               # Số CN làm việc
    le_tet = db.Column(db.Float, default=0)                 # Số ngày lễ/tết
    tang_ca_nghi = db.Column(db.Float, default=0)           # Giờ tăng ca (CN)
    tang_ca_tuan = db.Column(db.Float, default=0)           # Giờ tăng ca (trong tuần)

    # Tổng hợp & mô tả
    ghi_chu = db.Column(db.Text)                            # Ghi chú chi tiết (VD: "Tăng ca 2 CN: 7,14 / Nghỉ ngày: 15,16/09/2025")
    raw_data = db.Column(db.JSON)                           # JSON gốc (danh sách ngày, dữ liệu theo ngày, v.v.)

    # Thông tin tổ, phòng ban, loại hợp đồng (snapshot để lưu theo thời điểm)
    to = db.Column(db.String(100))
    phong_ban = db.Column(db.String(100))
    loai_hd = db.Column(db.String(50))

    created_at = db.Column(db.DateTime, server_default=db.func.now())

    # Quan hệ
    employee = db.relationship("Employee", backref="payroll_records")

    def __repr__(self):
        return f"<PayrollRecord emp={self.employee_id}, period={self.period}, cong={self.ngay_cong}>"
