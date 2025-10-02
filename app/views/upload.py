from flask import render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
import os
from . import bp
from flask import  render_template, request, redirect, url_for, flash
import os
from werkzeug.utils import secure_filename
import datetime
import pandas as pd


ALLOWED_EXT = {".xls", ".xlsx"}

def allowed_filename(filename):
    _, ext = os.path.splitext(filename.lower())
    return ext in ALLOWED_EXT
@bp.route("/report/<filename>")
def report(filename):
    return render_template("report.html", filename=filename)


@bp.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files.get("file")
        if not file:
            flash("Vui lòng chọn file", "danger")
            return redirect(url_for("main.index"))

        filename = secure_filename(file.filename)
        upload_folder = os.path.abspath(os.path.join(os.getcwd(), "uploads"))
        os.makedirs(upload_folder, exist_ok=True)
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)

        flash("Upload thành công!", "success")
        return redirect(url_for("main.report", filename=filename))

    return render_template("upload.html")



@bp.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        flash("Không có file gửi lên.", "danger")
        return redirect(url_for("main.index"))

    f = request.files["file"]
    if f.filename == "":
        flash("Bạn chưa chọn file.", "warning")
        return redirect(url_for("main.index"))

    if not allowed_filename(f.filename):
        flash("Chỉ chấp nhận file .xls hoặc .xlsx", "warning")
        return redirect(url_for("main.index"))

    filename = secure_filename(f.filename)
    upload_folder = os.path.abspath(os.path.join(os.getcwd(), "uploads"))
    os.makedirs(upload_folder, exist_ok=True)
    save_path = os.path.join(upload_folder, filename)
    f.save(save_path)

    # Sau khi upload thành công -> render report.html
    return render_template("report.html", filename=filename)



def format_cell(cell):
    """Chuẩn hoá cell cho report.html (không phải timesheet)."""
    if cell is None or cell == "" or str(cell).lower() == "nan":
        return ""
    if isinstance(cell, (datetime.time, datetime.datetime, pd.Timestamp)):
        return cell.strftime("%H:%M")
    if isinstance(cell, (int, float)):
        try:
            return pd.to_datetime(cell, unit="d", origin="1899-12-30").strftime("%H:%M")
        except Exception:
            return str(cell)
    if isinstance(cell, str):
        import re

        times = re.findall(r"\d{1,2}:\d{2}", cell)
        if times:
            return "<br>".join(times)
    return str(cell)