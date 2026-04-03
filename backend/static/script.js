it// ================= GLOBAL =================

let lineChartInstance = null;
let pieChartInstance = null;
let currentEditingId = null;

// Profile globals
let currentProfile = {name: '', email: '', profile_photo: ''};
let profilePhotoFile = null;

// ================= LOGIN / REGISTER =================

function showRegister() {
    document.getElementById("loginForm").style.display = "none";
    document.getElementById("registerForm").style.display = "block";
    document.getElementById("auth-message").innerText = "";
}

function showLogin() {
    document.getElementById("registerForm").style.display = "none";
    document.getElementById("loginForm").style.display = "block";
    document.getElementById("auth-message").innerText = "";
}

function registerUser() {

    const fullName = document.getElementById("reg_name").value.trim();
    const email = document.getElementById("reg_email").value;
    const password = document.getElementById("reg_password").value;

    if (!fullName || !email || !password) {
        document.getElementById("auth-message").innerText = "All fields required";
        return;
    }

    // Split full name: first word → first_name, rest → last_name
    const nameParts = fullName.split(' ');
    const first_name = nameParts[0];
    const last_name = nameParts.slice(1).join(' ') || '';

    fetch("/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ first_name, last_name, email, password })
    })
    .then(res => res.json())
    .then(() => {
        document.getElementById("auth-message").innerText =
            "Registration successful. Please login.";
        showLogin();
    });
}

function loginUser() {

    const email = document.getElementById("login_email").value;
    const password = document.getElementById("login_password").value;

    if (!email || !password) {
        document.getElementById("auth-message").innerText = "All fields required";
        return;
    }

    fetch("/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password })
    })
    .then(res => res.json())
    .then(data => {
        if (data.user_id) {
            window.location.href = "/dashboard";
        } else {
            document.getElementById("auth-message").innerText =
                "Invalid credentials";
        }
    });
}

function goToAdmin() {
    window.location.href = "/admin";
}

// ================= DASHBOARD LOAD =================

function loadDashboard() {

    fetch(`/dashboard-data`)
    .then(res => {
        if (res.status === 401) {
            window.location.replace("/");
            return;
        }
        return res.json();
    })
    .then(data => {

        if (!data) return;

        // Summary Cards
        document.getElementById("totalSpent").innerText =
            "₹" + Math.round(data.total_spent);

        document.getElementById("todaySpent").innerText =
            "₹" + Math.round(data.today_spent);

        document.getElementById("monthlyBudget").innerText =
            "₹" + Math.round(data.monthly_budget);

        document.getElementById("remainingBudget").innerText =
            "₹" + Math.round(data.remaining_budget);

        // Budget Progress Bar
        if (data.monthly_budget > 0) {
            document.getElementById("budgetBar").style.width =
                data.budget_percentage + "%";

            document.getElementById("budgetPercent").innerText =
                data.budget_percentage + "% of budget";
        }

        createPieChart(data.categories || []);
        createLineChart(data.last_week || []);
        renderTransactions(data.last_week || []);

        // Set user greeting
        if (data.user && data.user.name) {
            document.getElementById("userGreeting").innerText = `Welcome, ${data.user.name}!`;
        }

        // Load profile
        loadProfile();

        // Load predictions after charts
        loadPredictions();
    });
}

// ================= LOAD PROFILE =================

function loadProfile() {
    fetch("/get-profile")
    .then(res => res.json())
    .then(data => {
        if (data.name) {
            currentProfile = data;
            document.getElementById("profileFirstName").value = data.first_name || '';
            document.getElementById("profileLastName").value = data.last_name || '';
            document.getElementById("profileEmail").value = data.email || '';
            
            if (data.profile_photo) {
                document.getElementById("profilePreview").src = data.profile_photo;
                document.getElementById("profilePreview").style.display = 'block';
            }
        }
    })
    .catch(err => console.error('Profile load error:', err));
}

// ================= PROFILE MODAL =================

function openProfileModal() {
    loadProfile(); // Refresh
    document.getElementById("profileModal").style.display = "block";
}

function closeProfileModal() {
    document.getElementById("profileModal").style.display = "none";
    profilePhotoFile = null;
}

function fileToBase64(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.readAsDataURL(file);
        reader.onload = () => resolve(reader.result);
        reader.onerror = error => reject(error);
    });
}

document.getElementById("profilePhoto").addEventListener("change", function(e) {
    profilePhotoFile = e.target.files[0];
    if (profilePhotoFile) {
        fileToBase64(profilePhotoFile)
        .then(base64 => {
            document.getElementById("profilePreview").src = base64;
            document.getElementById("profilePreview").style.display = 'block';
        });
    }
});

function updateProfile() {
    const firstName = document.getElementById("profileFirstName").value;
    const lastName = document.getElementById("profileLastName").value;
    const email = document.getElementById("profileEmail").value;
    const updates = {};
    
    if (firstName !== currentProfile.first_name) updates.first_name = firstName;
    if (lastName !== currentProfile.last_name) updates.last_name = lastName;
    if (email !== currentProfile.email) updates.email = email;
    
    if (profilePhotoFile) {
        fileToBase64(profilePhotoFile).then(photo => {
            updates.profile_photo = photo;
            saveProfileUpdates(updates);
        });
    } else {
        saveProfileUpdates(updates);
    }
}

function saveProfileUpdates(updates) {
    if (Object.keys(updates).length === 0) {
        closeProfileModal();
        return;
    }
    
    fetch("/update-profile", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(updates)
    })
    .then(res => res.json())
    .then(data => {
        console.log('Profile updated:', data);
        closeProfileModal();
        loadDashboard(); // Refresh data & greeting
    })
    .catch(err => {
        console.error('Update error:', err);
        alert('Update failed');
    });
}

// ================= LOAD PREDICTIONS =================

function loadPredictions() {
    fetch('/predict', {cache: 'no-store'})
    .then(res => res.json())
    .then(data => {
        console.log('Predictions:', data);
        document.getElementById("predictedTotal").innerText = "₹" + Math.round(data.predicted_total || 0);
        document.getElementById("predictedWeek").innerText = "₹" + Math.round(data.predicted_week || 0);
        document.getElementById("trendInfo").innerText = "Spending trend: " + (data.trend || "--");
        document.getElementById("savingPrediction").innerText = "Predicted savings: ₹" + Math.round(data.predicted_savings || 0);
    })
    .catch(err => {
        console.error('Prediction load error:', err);
        document.getElementById("predictedTotal").innerText = "₹0";
        document.getElementById("trendInfo").innerText = "Load error";
    });
}

// ================= SET MONTHLY BUDGET =================

function setBudget() {

    const budget = prompt("Enter Monthly Budget:");

    if (!budget || isNaN(budget)) {
        alert("Enter valid amount");
        return;
    }

    fetch("/set-budget", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ budget: parseFloat(budget) })
    })
    .then(res => res.json())
    .then(() => {
        loadDashboard();
    });
}

// ================= ADD EXPENSE =================

function openModal() {
    document.getElementById("expenseModal").style.display = "block";
    document.getElementById("date").value = new Date().toISOString().split('T')[0];
}

function closeModal() {
    document.getElementById("expenseModal").style.display = "none";
}

function addExpense() {

    const category = document.getElementById("category").value;
    const amount = document.getElementById("amount").value;
    const date = document.getElementById("date").value;

    if (!category || !amount || !date) {
        alert("All fields required");
        return;
    }

    fetch("/add-expense", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            category,
            amount: parseFloat(amount),
            date
        })
    })
    .then(res => {
        if (res.status === 401) {
            window.location.replace("/");
            return;
        }
        return res.json();
    })
    .then(data => {
        console.log('Added expense:', data);
        
        // Reset form
        document.getElementById("category").value = "";
        document.getElementById("amount").value = "";
        document.getElementById("date").value = "";
        
        closeModal();
        loadDashboard();  // Reload everything including retrained predictions
    })
    .catch(err => {
        console.error('Error:', err);
        alert('Failed to add expense');
        loadDashboard();
    });
}

// ================= EDIT EXPENSE =================

function openEditModal(expense) {
    currentEditingId = expense[0];  // id
    document.getElementById("editCategory").value = expense[3] || '';  // category
    document.getElementById("editAmount").value = expense[1];  // amount
    document.getElementById("editDate").value = expense[2];  // date
    document.getElementById("editModal").style.display = "block";
}

function closeEditModal() {
    document.getElementById("editModal").style.display = "none";
    currentEditingId = null;
}

function saveEdit() {
    const category = document.getElementById("editCategory").value;
    const amount = document.getElementById("editAmount").value;
    const date = document.getElementById("editDate").value;

    if (!category || !amount || !date) {
        alert("All fields required");
        return;
    }

    fetch(`/update-expense/${currentEditingId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            category,
            amount: parseFloat(amount),
            date
        })
    })
    .then(res => res.json())
    .then(data => {
        console.log('Updated:', data);
        closeEditModal();
        loadDashboard();
    })
    .catch(err => {
        console.error('Update error:', err);
        alert('Update failed');
    });
}

function deleteExpense(expenseId) {
    if (!confirm("Delete this expense?")) return;

    fetch(`/delete-expense/${expenseId}`, {
        method: "DELETE"
    })
    .then(res => res.json())
    .then(data => {
        console.log('Deleted:', data);
        loadDashboard();
    })
    .catch(err => {
        console.error('Delete error:', err);
        alert('Delete failed');
    });
}

// ================= CHARTS =================

function createPieChart(categories) {

    if (!categories.length) return;

    if (pieChartInstance) pieChartInstance.destroy();

    pieChartInstance = new Chart(
        document.getElementById("pieChart"),
        {
            type: "doughnut",
            data: {
                labels: categories.map(c => c[0]),
                datasets: [{
                    data: categories.map(c => c[1])
                }]
            }
        }
    );
}

function createLineChart(lastWeek) {

    if (!lastWeek.length) return;

    if (lineChartInstance) lineChartInstance.destroy();

    lineChartInstance = new Chart(
        document.getElementById("lineChart"),
        {
            type: "line",
            data: {
                labels: lastWeek.map(d => d[2]),  // date
                datasets: [{
                    label: "Spending",
                    data: lastWeek.map(d => d[1]),  // amount
                    fill: false
                }]
            }
        }
    );
}

// ================= TRANSACTIONS =================

function renderTransactions(data) {

    const list = document.getElementById("transactionList");
    if (!list) return;

    list.innerHTML = "";

    data.forEach(item => {
        const li = document.createElement("li");
        li.style.cssText = "display:flex; justify-content:space-between; align-items:center; padding:8px 0; border-bottom:1px solid #333;";
        
        const info = document.createElement("div");
        info.style.cssText = "flex:1;";
        info.innerHTML = `<strong>${item[3] || 'Other'}</strong><br><small>${item[2]} - ₹${Math.round(item[1])}</small>`;
        
        const actions = document.createElement("div");
        actions.style.cssText = "display:flex; gap:5px;";
        
        const editBtn = document.createElement("button");
        editBtn.innerText = "✏️";
        editBtn.style.cssText = "background:#ffa500; color:black; border:none; padding:5px 8px; border-radius:4px; cursor:pointer; font-size:12px;";
        editBtn.onclick = () => openEditModal(item);
        
        const delBtn = document.createElement("button");
        delBtn.innerText = "🗑️";
        delBtn.style.cssText = "background:#ff4d4d; color:white; border:none; padding:5px 8px; border-radius:4px; cursor:pointer; font-size:12px;";
        delBtn.onclick = () => deleteExpense(item[0]);
        
        actions.appendChild(editBtn);
        actions.appendChild(delBtn);
        
        li.appendChild(info);
        li.appendChild(actions);
        
        list.appendChild(li);
    });
}

// ================= ADMIN LOGIN =================

function adminLogin() {

    const adminId = document.getElementById("admin_email").value;
    const password = document.getElementById("admin_password").value;

    fetch("/admin-login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            admin_id: adminId,
            password: password
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === "success") {
            window.location.href = "/admin-dashboard";
        } else {
            alert("Invalid Admin Credentials");
        }
    });
}

// ================= LOGOUT =================

function logoutUser() {
    fetch("/logout")
    .then(() => {
        window.location.replace("/");
    });
}

// ================= AUTO LOAD =================

window.onload = function () {
    if (window.location.pathname === "/dashboard") {
        loadDashboard();
    } else if (window.location.pathname === "/profile") {
        initProfilePage();
    }
};
