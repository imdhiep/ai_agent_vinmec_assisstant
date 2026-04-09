const state = {
  facilities: [],
  departments: [],
  doctors: [],
  selectedDepartmentId: "",
  selectedDoctorId: "",
  selectedSlotId: ""
};

async function boot() {
  const response = await fetch("/api/bootstrap");
  const data = await response.json();
  state.facilities = data.facilities;
  state.departments = data.departments;
  state.doctors = data.doctors;
  hydrateFacilities();
  bindEvents();
}

function hydrateFacilities() {
  const select = document.getElementById("facility_id");
  select.innerHTML = '<option value="">Chon co so kham</option>';
  state.facilities.forEach((facility) => {
    const option = document.createElement("option");
    option.value = facility.id;
    option.textContent = `${facility.name} - ${facility.city}`;
    select.appendChild(option);
  });
}

function bindEvents() {
  document.getElementById("recommend-btn").addEventListener("click", onRecommend);
  document.getElementById("booking-form").addEventListener("submit", onBookingSubmit);
}

async function onRecommend() {
  const payload = {
    symptom_text: document.getElementById("symptom_text").value,
    gender: document.getElementById("gender").value || null,
    age: parseInt(document.getElementById("age").value || "0", 10) || null,
    facility_id: document.getElementById("facility_id").value || null
  };

  const response = await fetch("/api/copilot/recommend", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  const data = await response.json();
  renderRecommendation(data);
}

function renderRecommendation(data) {
  const panel = document.getElementById("recommendation-panel");
  panel.classList.remove("hidden");

  if (data.suggested_department?.id) {
    state.selectedDepartmentId = data.suggested_department.id;
    document.getElementById("department_id").value = data.suggested_department.id;
  }

  let html = `
    <p><strong>Trang thai:</strong> ${data.status}</p>
    <p><strong>Thong diep:</strong> ${data.message}</p>
    <p class="helper"><strong>Disclaimer:</strong> ${data.disclaimer}</p>
    <p><strong>Confidence:</strong> ${(data.confidence * 100).toFixed(0)}%</p>
  `;

  if (data.suggested_department) {
    html += `<p><strong>Chuyen khoa de xuat:</strong> ${data.suggested_department.name}</p>`;
  }

  if (data.follow_up_questions?.length) {
    html += '<div class="state-warning"><strong>Can xac nhan them:</strong><ul>';
    data.follow_up_questions.forEach((question) => {
      html += `<li>${question}</li>`;
    });
    html += "</ul></div>";
  }

  if (data.status === "emergency") {
    html += '<p class="state-emergency"><strong>Khuyen nghi:</strong> dung luong booking tu dong va lien he cap cuu/nhan vien that.</p>';
  }

  if (data.recommended_doctors?.length) {
    html += "<div><strong>Danh sach bac si goi y:</strong></div>";
    data.recommended_doctors.forEach((doctor) => {
      const nextSlotText = doctor.next_slot
        ? `${new Date(doctor.next_slot.start_at).toLocaleString("vi-VN")}`
        : "Tam het lich";
      const tags = doctor.specialties.map((tag) => `<span class="tag">${tag}</span>`).join("");
      html += `
        <div class="doctor-card">
          <h4>${doctor.title} ${doctor.doctor_name}</h4>
          <p class="doctor-meta">${doctor.bio}</p>
          <p><strong>Match score:</strong> ${doctor.match_score}</p>
          <p><strong>Tinh trang lich:</strong> ${doctor.available ? "Con lich" : "Het lich"}</p>
          <p><strong>Next slot:</strong> ${nextSlotText}</p>
          <div class="tag-row">${tags}</div>
          <p class="helper">${doctor.fallback_label}</p>
          <button type="button" onclick="selectDoctor('${doctor.doctor_id}', '${doctor.next_slot ? doctor.next_slot.id : ""}')">
            Chon bac si nay
          </button>
        </div>
      `;
    });
  }

  if (data.fallback_options?.length) {
    html += "<div><strong>Phuong an neu bac si khong ranh:</strong><ul>";
    data.fallback_options.forEach((item) => {
      html += `<li>${item}</li>`;
    });
    html += "</ul></div>";
  }

  panel.innerHTML = html;
}

function selectDoctor(doctorId, slotId) {
  state.selectedDoctorId = doctorId;
  state.selectedSlotId = slotId;
  document.getElementById("doctor_id").value = doctorId;
  document.getElementById("slot_id").value = slotId;
  const result = document.getElementById("booking-result");
  result.innerHTML = `<p><strong>Da chon bac si:</strong> ${doctorId}</p><p class="muted">Neu slot rong, he thong se dat ngay. Neu khong, backend se tim phuong an thay the.</p>`;
}

async function onBookingSubmit(event) {
  event.preventDefault();

  const payload = {
    facility_id: document.getElementById("facility_id").value,
    department_id: document.getElementById("department_id").value,
    doctor_id: document.getElementById("doctor_id").value || null,
    slot_id: document.getElementById("slot_id").value || null,
    patient_name: document.getElementById("patient_name").value,
    gender: document.getElementById("gender").value || "other",
    phone: document.getElementById("phone").value,
    birth_date: document.getElementById("birth_date").value,
    email: document.getElementById("email").value || null,
    symptom_text: document.getElementById("symptom_text").value
  };

  const response = await fetch("/api/booking/create", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  const data = await response.json();
  renderBookingResult(data);
}

function renderBookingResult(data) {
  const result = document.getElementById("booking-result");
  if (data.status === "confirmed") {
    const booking = data.booking;
    result.innerHTML = `
      <h4>Yeu cau dat lich da tao</h4>
      <p><strong>Khach hang:</strong> ${booking.patient_name}</p>
      <p><strong>Co so:</strong> ${booking.facility}</p>
      <p><strong>Chuyen khoa:</strong> ${booking.department}</p>
      <p><strong>Bac si:</strong> ${booking.doctor}</p>
      <p><strong>Thoi gian:</strong> ${new Date(booking.start_at).toLocaleString("vi-VN")}</p>
      <p><strong>Phi du kien:</strong> ${Number(booking.fee).toLocaleString("vi-VN")} VND</p>
      <p class="muted">${booking.note}</p>
    `;
    return;
  }

  if (data.alternatives?.length) {
    const list = data.alternatives.map((item) => `<li>${item.doctor_name} - ${item.fallback_label}</li>`).join("");
    result.innerHTML = `
      <p><strong>${data.message}</strong></p>
      <ul>${list}</ul>
    `;
    return;
  }

  result.innerHTML = `<p><strong>${data.message}</strong></p>`;
}

window.selectDoctor = selectDoctor;
boot();
