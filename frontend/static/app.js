// Minimal JS for demo. In this project most behavior is handled server-side.
// This file is extended to support dynamic state -> district selection.

console.log('App loaded');

// Simple state -> district mapping for India.
// NOTE: For a real production system you may want to load this from
// a separate JSON file or API. Here it is embedded for simplicity.
const indiaDistricts = {
  'Andhra Pradesh': [
    'Anantapur', 'Chittoor', 'East Godavari', 'Guntur', 'Krishna',
    'Kurnool', 'Nellore', 'Prakasam', 'Srikakulam', 'Visakhapatnam',
    'Vizianagaram', 'West Godavari', 'YSR Kadapa'
  ],
  'Karnataka': [
    'Bagalkot', 'Ballari', 'Belagavi', 'Bengaluru Rural',
    'Bengaluru Urban', 'Bidar', 'Chamarajanagar', 'Chikkaballapur',
    'Chikkamagaluru', 'Chitradurga', 'Dakshina Kannada', 'Davangere',
    'Dharwad', 'Gadag', 'Hassan', 'Haveri', 'Kalaburagi', 'Kodagu',
    'Kolar', 'Koppal', 'Mandya', 'Mysuru', 'Raichur', 'Ramanagara',
    'Shivamogga', 'Tumakuru', 'Udupi', 'Uttara Kannada', 'Vijayapura',
    'Yadgir'
  ],
  'Jharkhand': [
    'Bokaro', 'Chatra', 'Deoghar', 'Dhanbad', 'Dumka', 'East Singhbhum',
    'Garhwa', 'Giridih', 'Godda', 'Gumla', 'Hazaribagh', 'Jamtara',
    'Khunti', 'Koderma', 'Latehar', 'Lohardaga', 'Pakur', 'Palamu',
    'Ramgarh', 'Ranchi', 'Sahibganj', 'Seraikela Kharsawan',
    'Simdega', 'West Singhbhum'
  ],
  'Maharashtra': [
    'Ahmednagar', 'Akola', 'Amravati', 'Aurangabad', 'Beed', 'Bhandara',
    'Buldhana', 'Chandrapur', 'Dhule', 'Gadchiroli', 'Gondia',
    'Hingoli', 'Jalgaon', 'Jalna', 'Kolhapur', 'Latur', 'Mumbai City',
    'Mumbai Suburban', 'Nagpur', 'Nanded', 'Nandurbar', 'Nashik',
    'Osmanabad', 'Palghar', 'Parbhani', 'Pune', 'Raigad', 'Ratnagiri',
    'Sangli', 'Satara', 'Sindhudurg', 'Solapur', 'Thane', 'Wardha',
    'Washim', 'Yavatmal'
  ],
  'Tamil Nadu': [
    'Chennai', 'Coimbatore', 'Cuddalore', 'Dharmapuri', 'Dindigul',
    'Erode', 'Kancheepuram', 'Kanniyakumari', 'Karur', 'Krishnagiri',
    'Madurai', 'Nagapattinam', 'Namakkal', 'Perambalur', 'Pudukkottai',
    'Ramanathapuram', 'Salem', 'Sivaganga', 'Thanjavur', 'The Nilgiris',
    'Theni', 'Thiruvallur', 'Thiruvarur', 'Thoothukudi',
    'Tiruchirappalli', 'Tirunelveli', 'Tiruppur', 'Tiruvannamalai',
    'Vellore', 'Viluppuram', 'Virudhunagar'
  ],
  'Uttar Pradesh': [
    'Agra', 'Aligarh', 'Allahabad', 'Ambedkar Nagar', 'Amethi',
    'Amroha', 'Auraiya', 'Azamgarh', 'Baghpat', 'Bahraich', 'Ballia',
    'Balrampur', 'Banda', 'Barabanki', 'Bareilly', 'Basti', 'Bhadohi',
    'Bijnor', 'Budaun', 'Bulandshahr', 'Chandauli', 'Chitrakoot',
    'Deoria', 'Etah', 'Etawah', 'Faizabad', 'Farrukhabad', 'Fatehpur',
    'Firozabad', 'Gautam Buddha Nagar', 'Ghaziabad', 'Ghazipur',
    'Gonda', 'Gorakhpur', 'Hamirpur', 'Hardoi', 'Hathras', 'Jalaun',
    'Jaunpur', 'Jhansi', 'Kannauj', 'Kanpur Dehat', 'Kanpur Nagar',
    'Kasganj', 'Kaushambi', 'Kheri', 'Kushinagar', 'Lalitpur', 'Lucknow',
    'Maharajganj', 'Mahoba', 'Mainpuri', 'Mathura', 'Mau', 'Meerut',
    'Mirzapur', 'Moradabad', 'Muzaffarnagar', 'Pilibhit', 'Pratapgarh',
    'Rae Bareli', 'Rampur', 'Saharanpur', 'Sambhal', 'Sant Kabir Nagar',
    'Shahjahanpur', 'Shamli', 'Shravasti', 'Siddharthnagar', 'Sitapur',
    'Sonbhadra', 'Sultanpur', 'Unnao', 'Varanasi'
  ],
  'Delhi': [
    'Central Delhi', 'East Delhi', 'New Delhi', 'North Delhi',
    'North East Delhi', 'North West Delhi', 'Shahdara', 'South Delhi',
    'South East Delhi', 'South West Delhi', 'West Delhi'
  ],
  // Add further states and districts here as needed.
};

function setupStateDistrictDropdowns() {
  const stateSelect = document.getElementById('state');
  const districtSelect = document.getElementById('district');
  // If district is not a <select> (e.g. manual text input), do nothing.
  if (!stateSelect || !districtSelect || districtSelect.tagName !== 'SELECT') return;

  stateSelect.addEventListener('change', () => {
    const state = stateSelect.value;
    const districts = indiaDistricts[state] || [];

    // Clear old options
    districtSelect.innerHTML = '';
    const defaultOpt = document.createElement('option');
    defaultOpt.value = '';
    defaultOpt.textContent = districts.length ? 'Select district' : 'No districts configured';
    districtSelect.appendChild(defaultOpt);

    districts.forEach((d) => {
      const opt = document.createElement('option');
      opt.value = d;
      opt.textContent = d;
      districtSelect.appendChild(opt);
    });
  });
}

function setupDoctorOwnVisitsFilter() {
  const table = document.getElementById('doctor-history-table');
  const checkbox = document.getElementById('only-my-visits');
  if (!table || !checkbox) return;

  const currentId = parseInt(table.getAttribute('data-current-doctor-id'), 10);
  if (!currentId) return;

  const rows = Array.from(table.querySelectorAll('tbody tr'));

  checkbox.addEventListener('change', () => {
    const onlyMine = checkbox.checked;
    rows.forEach((row) => {
      const rowDoctorId = parseInt(row.getAttribute('data-doctor-id'), 10);
      if (!onlyMine || rowDoctorId === currentId) {
        row.style.display = '';
      } else {
        row.style.display = 'none';
      }
    });
  });
}

function setupDoctorUseLastTreatment() {
  const btn = document.getElementById('use-last-treatment');
  const form = document.getElementById('add-record-form');
  if (!btn || !form) return;

  const diagnosisInput = form.querySelector('#diagnosis');
  const medicinesInput = form.querySelector('#medicines');
  const dosageInput = form.querySelector('#dosage');
  const statusSelect = form.querySelector('#treatment_status');
  const prescriptionText = form.querySelector('#prescription_text');

  btn.addEventListener('click', () => {
    if (diagnosisInput) diagnosisInput.value = btn.getAttribute('data-latest-diagnosis') || '';
    if (medicinesInput) medicinesInput.value = btn.getAttribute('data-latest-medicines') || '';
    if (dosageInput) dosageInput.value = btn.getAttribute('data-latest-dosage') || '';
    if (statusSelect) statusSelect.value = btn.getAttribute('data-latest-treatment-status') || '';
    if (prescriptionText) prescriptionText.value = btn.getAttribute('data-latest-prescription-text') || '';
  });
}

function setupHospitalVisitSearch() {
  const table = document.getElementById('hospital-visit-table');
  const input = document.getElementById('visit-search');
  if (!table || !input) return;

  const rows = Array.from(table.querySelectorAll('tbody tr'));

  input.addEventListener('input', () => {
    const q = input.value.toLowerCase().trim();
    rows.forEach((row) => {
      const text = (row.getAttribute('data-visit-search') || '').toLowerCase();
      row.style.display = !q || text.includes(q) ? '' : 'none';
    });
  });
}

function setupHospitalPatientSearch() {
  const table = document.getElementById('hospital-patient-table');
  const input = document.getElementById('patient-search');
  if (!table || !input) return;

  const rows = Array.from(table.querySelectorAll('tbody tr'));

  input.addEventListener('input', () => {
    const q = input.value.toLowerCase().trim();
    rows.forEach((row) => {
      const text = (row.getAttribute('data-patient-search') || '').toLowerCase();
      row.style.display = !q || text.includes(q) ? '' : 'none';
    });
  });
}

// Run immediately so the listener is attached as soon as script loads.
setupStateDistrictDropdowns();

// --- Doctor dashboard: client-side filter for medical history by status ---

function setupDoctorStatusFilter() {
  const table = document.getElementById('doctor-history-table');
  const filter = document.getElementById('status-filter');
  if (!table || !filter) return;

  const rows = Array.from(table.querySelectorAll('tbody tr'));

  filter.addEventListener('change', () => {
    const value = filter.value;
    rows.forEach((row) => {
      const status = (row.getAttribute('data-record-status') || '').trim();
      if (value === 'all' || status === value) {
        row.style.display = '';
      } else {
        row.style.display = 'none';
      }
    });
  });
}

// --- Hospital dashboard: emergency stats + doctor search filter ---

function setupHospitalEmergencyStats() {
  const target = document.getElementById('emergency-avg-text');
  if (!target) return;

  fetch('/analytics/ambulance')
    .then((res) => res.json())
    .then((data) => {
      const avg = data && typeof data.avg_response_time !== 'undefined'
        ? data.avg_response_time
        : null;
      if (avg !== null && avg !== undefined) {
        target.textContent = `Avg response: ${avg} min`;
      } else {
        target.textContent = 'Avg response: N/A';
      }
    })
    .catch(() => {
      target.textContent = 'Avg response: N/A';
    });
}

function setupHospitalDoctorSearch() {
  const table = document.getElementById('hospital-doctor-table');
  const input = document.getElementById('doctor-search');
  if (!table || !input) return;

  const rows = Array.from(table.querySelectorAll('tbody tr'));

  input.addEventListener('input', () => {
    const q = input.value.toLowerCase().trim();
    rows.forEach((row) => {
      const text = (row.getAttribute('data-doctor-search') || '').toLowerCase();
      row.style.display = !q || text.includes(q) ? '' : 'none';
    });
  });
}

function setupDoctorDeleteConfirm() {
  const forms = document.querySelectorAll('.doctor-delete-form');
  forms.forEach((form) => {
    form.addEventListener('submit', (e) => {
      const ok = window.confirm('Are you sure you want to delete this doctor? This cannot be undone.');
      if (!ok) {
        e.preventDefault();
      }
    });
  });
}

function setupDoctorMedicinePicker() {
  const form = document.getElementById('add-record-form');
  if (!form) return;

  const searchInput = document.getElementById('medicine-search');
  const selectEl = document.getElementById('medicine-select');
  const infoEl = document.getElementById('medicine-info');
  const addBtn = document.getElementById('add-medicine-btn');
  const clearBtn = document.getElementById('clear-medicine-btn');
  const medicinesTextarea = document.getElementById('medicines');
  const dosageTextarea = document.getElementById('dosage');

  if (!searchInput || !selectEl || !infoEl || !addBtn || !clearBtn || !medicinesTextarea || !dosageTextarea) return;

  let medicines = [];
  try {
    const jsonEl = document.getElementById('inventory-medicines-data');
    medicines = jsonEl ? JSON.parse(jsonEl.textContent || '[]') : [];
  } catch (e) {
    medicines = [];
  }

  const byId = new Map();
  medicines.forEach((m) => {
    if (m && typeof m.id !== 'undefined') byId.set(String(m.id), m);
  });

  function optionLabel(m) {
    const mg = m && m.strength_mg !== null && typeof m.strength_mg !== 'undefined' && String(m.strength_mg).trim() !== ''
      ? `${m.strength_mg}mg`
      : '';
    const type = m && m.medicine_type ? String(m.medicine_type) : '';
    const meta = [type, mg].filter(Boolean).join(' • ');
    return meta ? `${m.item_name} (${meta})` : `${m.item_name}`;
  }

  function renderOptions(filterText) {
    const q = (filterText || '').toLowerCase().trim();

    // Preserve the first "Select" option
    selectEl.innerHTML = '<option value="">Select a medicine</option>';

    const filtered = medicines.filter((m) => {
      if (!q) return true;
      const hay = [
        m.item_name,
        m.medicine_type,
        m.strength_mg,
      ].filter((v) => v !== null && typeof v !== 'undefined').join(' ').toLowerCase();
      return hay.includes(q);
    });

    filtered.forEach((m) => {
      const opt = document.createElement('option');
      opt.value = String(m.id);
      opt.textContent = optionLabel(m);
      selectEl.appendChild(opt);
    });
  }

  function setInfo(m) {
    if (!m) {
      infoEl.textContent = 'Search and select to see availability, type, and strength.';
      return;
    }
    const qty = typeof m.quantity === 'number' ? m.quantity : parseInt(m.quantity, 10);
    const unit = m.unit ? String(m.unit) : 'units';
    const type = m.medicine_type ? String(m.medicine_type) : '-';
    const mg = m.strength_mg !== null && typeof m.strength_mg !== 'undefined' && String(m.strength_mg).trim() !== ''
      ? `${m.strength_mg} mg`
      : '-';

    infoEl.textContent = `Available: ${Number.isFinite(qty) ? qty : 0} ${unit} | Type: ${type} | Strength: ${mg}`;
  }

  function selectedMedicine() {
    const id = selectEl.value;
    if (!id) return null;
    return byId.get(String(id)) || null;
  }

  function appendLine(textarea, line) {
    const current = (textarea.value || '').trim();
    if (!current) {
      textarea.value = line;
      return;
    }
    // Prefer newline-separated list for readability.
    textarea.value = `${current}\n${line}`;
  }

  // Initial render
  renderOptions('');
  setInfo(null);

  searchInput.addEventListener('input', () => {
    renderOptions(searchInput.value);
    setInfo(selectedMedicine());
  });

  selectEl.addEventListener('change', () => {
    setInfo(selectedMedicine());
  });

  addBtn.addEventListener('click', () => {
    const m = selectedMedicine();
    if (!m) {
      setInfo(null);
      return;
    }

    // Add to medicines list
    appendLine(medicinesTextarea, optionLabel(m));

    // Provide a basic dosage template so doctor can edit.
    const mgPart = m.strength_mg !== null && typeof m.strength_mg !== 'undefined' && String(m.strength_mg).trim() !== '' ? `${m.strength_mg}mg` : '';
    const unit = m.unit ? String(m.unit) : '';
    const stockPart = unit ? ` (Available: ${m.quantity} ${unit})` : ` (Available: ${m.quantity})`;
    const doseTemplate = `${m.item_name}${mgPart ? ' ' + mgPart : ''} - dosage: ______${stockPart}`;
    appendLine(dosageTextarea, doseTemplate);
  });

  clearBtn.addEventListener('click', () => {
    searchInput.value = '';
    renderOptions('');
    selectEl.value = '';
    setInfo(null);
  });
}

// Initialize dashboard helpers
setupHospitalVisitSearch();
setupHospitalPatientSearch();
setupDoctorStatusFilter();
setupDoctorOwnVisitsFilter();
setupDoctorUseLastTreatment();
setupHospitalEmergencyStats();
setupHospitalDoctorSearch();
setupDoctorDeleteConfirm();
setupDoctorMedicinePicker();

function setupThemeToggle() {
    const toggleBtn = document.getElementById('theme-toggle-btn');
    if (!toggleBtn) return;
    
    const iconSun = toggleBtn.querySelector('.icon-sun');
    const iconMoon = toggleBtn.querySelector('.icon-moon');
    
    const currentTheme = document.documentElement.getAttribute('data-theme');
    if (currentTheme === 'dark') {
        iconSun.style.display = 'none';
        iconMoon.style.display = 'block';
    } else {
        iconSun.style.display = 'block';
        iconMoon.style.display = 'none';
    }
    
    toggleBtn.addEventListener('click', () => {
        const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        if (isDark) {
            document.documentElement.removeAttribute('data-theme');
            localStorage.setItem('swasthya_theme', 'light');
            iconSun.style.display = 'block';
            iconMoon.style.display = 'none';
        } else {
            document.documentElement.setAttribute('data-theme', 'dark');
            localStorage.setItem('swasthya_theme', 'dark');
            iconSun.style.display = 'none';
            iconMoon.style.display = 'block';
        }
    });
}
setupThemeToggle();
