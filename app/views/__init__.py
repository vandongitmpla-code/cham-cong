from flask import Blueprint

bp = Blueprint("main", __name__)

# Import tất cả route con
from . import upload, timesheet, payroll, employees, attendance_print
