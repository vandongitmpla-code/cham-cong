from flask import Blueprint

bp = Blueprint("main", __name__)

from . import upload, timesheet, payroll, employees, attendance_print
