// static/js/timesheet.js
document.addEventListener("DOMContentLoaded", function () {
  const modal = document.getElementById("detailModal");
  const closeBtn = document.querySelector(".modal-close");
  const modalTitle = document.getElementById("modalTitle");
  const modalTableWrapper = document.getElementById("modalTableWrapper");

  const cfg = window.__TIMESHEET__ || {};
  const weekdays = cfg.weekdays || {};
  const dayCount = parseInt(cfg.day_count || 31, 10);

  function extractTimesFromCell(cellValue) {
    if (!cellValue) return [];
    try {
      const s = String(cellValue);
      const matches = s.match(/\d{1,2}:\d{2}/g);
      return matches || [];
    } catch (e) {
      return [];
    }
  }

  function timeStrToMinutes(t) {
    const parts = t.split(":").map((x) => parseInt(x, 10));
    if (parts.length < 2 || isNaN(parts[0]) || isNaN(parts[1])) return null;
    return parts[0] * 60 + parts[1];
  }

  function minutesFromFirstToLast(timesArr) {
    const mins = timesArr
      .map(timeStrToMinutes)
      .filter((v) => v !== null && !Number.isNaN(v));
    if (!mins.length) return 0;
    const first = Math.min(...mins);
    let last = Math.max(...mins);
    if (last < first) last += 24 * 60;
    return last - first;
  }

  function renderCellByRules(cellValue) {
    const times = extractTimesFromCell(cellValue);
    if (!times.length) return "v"; // không có dữ liệu
    if (times.length === 1) return "warn"; // chỉ có 1 lần chấm

    const minutes = minutesFromFirstToLast(times);
    if (minutes >= 7 * 60) return "x";
    if (minutes >= 3 * 60) return "0.5";
    return "";
  }

  function cellHtmlSafe(s) {
    return s || "";
  }

  document.querySelectorAll(".btn-detail").forEach((btn) => {
    btn.addEventListener("click", function () {
      const emp = JSON.parse(this.dataset.emp || "{}");
      modalTitle.textContent = `${emp["Tên"] || ""} - ${emp["Phòng ban"] || ""}`;

      // --- Đếm ngày công, ngày vắng, chủ nhật ---
      let workDays = 0;
      let absentDays = 0;
      let sundayWork = 0;

      const daysArr = Array.isArray(emp.days) ? emp.days : [];
      for (let i = 0; i < dayCount; i++) {
        const raw = daysArr[i] !== undefined ? daysArr[i] : "";
        const display = renderCellByRules(raw);

        if (display === "x") {
          workDays++;
          const wd = (weekdays[i + 1] || "").toLowerCase();
          if (
            wd.includes("cn") ||
            wd.includes("chủ nhật") ||
            wd.includes("sun")
          ) {
            sundayWork++;
          }
        } else if (display === "v") {
          absentDays++;
        }
      }

      // --- Header số ngày ---
      let headerDays = `<tr>
        <th>Mã</th>
        <th>Tên</th>
        <th>Phòng ban</th>
        <th class="highlight-col">Ngày công</th>
        <th class="highlight-col">Ngày vắng</th>
        <th class="highlight-col">Chủ nhật</th>`;
      for (let d = 1; d <= dayCount; d++) {
        const isSunday =
          (weekdays[d] || "").toLowerCase().includes("cn") ||
          (weekdays[d] || "").toLowerCase().includes("chủ nhật") ||
          (weekdays[d] || "").toLowerCase().includes("sun");
        headerDays += `<th ${isSunday ? 'class="highlight-sunday"' : ""}>${d}</th>`;
      }
      headerDays += `</tr>`;

      // --- Header thứ ---
      let headerWeekdays = `<tr><td></td><td></td><td></td><td></td><td></td><td></td>`;
      for (let d = 1; d <= dayCount; d++) {
        const isSunday =
          (weekdays[d] || "").toLowerCase().includes("cn") ||
          (weekdays[d] || "").toLowerCase().includes("chủ nhật") ||
          (weekdays[d] || "").toLowerCase().includes("sun");
        headerWeekdays += `<td ${isSunday ? 'class="highlight-sunday"' : ""}>${
          weekdays[d] || ""
        }</td>`;
      }
      headerWeekdays += `</tr>`;

      // --- Dữ liệu nhân viên ---
      let rowData = `<tr>
        <td>${cellHtmlSafe(emp["Mã"])}</td>
        <td>${cellHtmlSafe(emp["Tên"])}</td>
        <td>${cellHtmlSafe(emp["Phòng ban"])}</td>
        <td class="highlight-col">${workDays}</td>
        <td class="highlight-col">${absentDays}</td>
        <td class="highlight-col">${sundayWork}</td>`;

      for (let i = 0; i < dayCount; i++) {
        const raw = daysArr[i] !== undefined ? daysArr[i] : "";
        const display = renderCellByRules(raw);

        if (display === "x") {
          rowData += `<td class="timesheet-day-x text-center"><strong>x</strong></td>`;
        } else if (display === "0.5") {
          rowData += `<td class="timesheet-day-half text-center">0.5</td>`;
        } else if (display === "v") {
          rowData += `<td class="timesheet-day-v text-center">v</td>`;
        } else if (display === "warn") {
          rowData += `<td class="timesheet-day-warn text-center">
                        <i class="bi bi-exclamation-triangle-fill text-warning blink-red"
                           data-bs-toggle="tooltip"
                           data-bs-placement="top"
                           title="Chỉ có 1 lần chấm công, cần kiểm tra lại"></i>
                      </td>`;
        } else {
          rowData += `<td></td>`;
        }
      }
      rowData += `</tr>`;

      const table = `
        <div class="modal-table-container">
          <table class="modal-table table table-bordered text-center">
            <thead>${headerDays}${headerWeekdays}</thead>
            <tbody>${rowData}</tbody>
          </table>
        </div>
      `;

      modalTableWrapper.innerHTML = table;
      modal.style.display = "block";

      // Kích hoạt tooltip
      const tooltipTriggerList = [].slice.call(
        modalTableWrapper.querySelectorAll('[data-bs-toggle="tooltip"]')
      );
      tooltipTriggerList.forEach(function (tooltipTriggerEl) {
        new bootstrap.Tooltip(tooltipTriggerEl, { container: "body" });
      });
    });
  });

  // Đóng modal
  closeBtn.onclick = () => (modal.style.display = "none");
  window.onclick = (e) => {
    if (e.target == modal) modal.style.display = "none";
  };
});
