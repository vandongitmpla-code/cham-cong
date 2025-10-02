from flask import Blueprint, render_template, request, redirect, url_for, flash
import os
from werkzeug.utils import secure_filename
from app.utils.cleaning import clean_attendance_data
import datetime
import pandas as pd
from flask import send_file
import io
from app.models import Employee, AttendanceLog, Payroll, db
import re