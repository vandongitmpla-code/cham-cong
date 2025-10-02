from flask import render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
import os
from . import bp

ALLOWED_EXT = {".xls", ".xlsx"}

def allowed_filename(filename):
    _, ext = os.path.splitext(filename.lower())
    return ext in ALLOWED_EXT