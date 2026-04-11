// ================= GLOBAL =================

let lineChartInstance = null;
let pieChartInstance = null;
let currentEditingId = null;

let currentProfile = {};
let profilePhotoFile = null;

// ================= LOGIN / REGISTER =================

function showRegister() {
    document.getElementById("loginForm").style.display = "none";
    document.getElementById("registerForm").style.display = "block";
}

function showLogin() {
    document.getElementById("registerForm").style.display = "none";
    document.getElementById("loginForm").style.display = "block";
}

function registerUser() {
    const fullName = document.getElementById("reg_name").value.trim();
    const email = document.getElementById("reg_email").value;
    const password = document.getElementById("reg_password").value;

    if (!fullName || !email || !password) {
        alert("All fields required");
        return;
    }

    const parts = fullName.split(" ");
    const first_name = parts[0];
    const last_name = parts.slice(1).join(" ");

    fetch("/register", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ first_name, last_name, email, password })
    })
    .then(() => {
        alert("Registered successfully");
        showLogin();
    });
}

function loginUser() {
    const email = document.getElementById("login_email").value;
    const password = document.getElementById("login_password").value;

    if (!email || !password) {
        alert("Enter email and password");
        return;
    }

    fetch("/login", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ email, password })
    })
    .then(res => res.json())
    .then(data => {
        if (data.user_id) {
            window.location.href = "/dashboard";
        } else {
            alert("Invalid credentials");
        }
    });
}

// ================= ADMIN =================

// Redirect to admin page
function goToAdmin() {
    window.location.href = "/admin";
}

// Admin login (for admin page)
function adminLogin() {

    console.log("Admin login clicked");

    const adminId = document.getElementById("admin_email")?.value.trim();
    const password = document.getElementById("admin_password")?.value;

    if (!adminId || !password) {
        alert("Please enter admin ID and password");
        return;
    }

    fetch("/admin-login", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            admin_id: adminId,
            password: password
        })
    })
    .then(res => res.json())
    .then(data => {
        console.log("Admin response:", data);

        if (data.status === "success") {
            window.location.href = "/admin-dashboard";
        } else {
            alert("Invalid admin credentials");
            document.getElementById("admin_password").value = "";
        }
    })
    .catch(err => {
        console.error(err);
        alert("Admin login failed");
    });
}

// ================= DASHBOARD =================

function loadDashboard() {

    fetch("/dashboard-data")
    .then(res => {
        if (res.status === 401) {
            window.location.href = "/";
            return;
        }
        return res.json();
    })
    .then(data => {

        if (!data) return;

        console.log("Dashboard data:", data);

        // SUMMARY
        document.getElementById("totalSpent").innerText = "₹" + data.total_spent;
        document.getElementById("todaySpent").innerText = "₹" + data.today_spent;
        document.getElementById("monthlyBudget").innerText = "₹" + data.monthly_budget;
        document.getElementById("remainingBudget").innerText = "₹" + data.remaining_budget;

        document.getElementById("budgetPercent").innerText =
            data.budget_percentage + "% of budget";

        document.getElementById("budgetBar").style.width =
            data.budget_percentage + "%";

        document.getElementById("userGreeting").innerText =
            `Welcome, ${data.user.name}`;

        // CHARTS
        createLineChart(data.daily_sums_7days);
        createPieChart(data.categories_7days);

        // TRANSACTIONS
        renderTransactions(data.recent_transactions);

        // OTHER
        loadPredictions();
        loadProfile();
    });
}

// ================= CHARTS =================

function createLineChart(data) {

    if (lineChartInstance) lineChartInstance.destroy();

    if (!data || data.length === 0) return;

    lineChartInstance = new Chart(
        document.getElementById("lineChart"),
        {
            type: "line",
            data: {
                labels: data.map(d => d[0]),
                datasets: [{
                    label: "Last 7 Days Spending",
                    data: data.map(d => d[1] || 0),
                    borderColor: "#00ffc3",
                    fill: true,
                    tension: 0.3
                }]
            }
        }
    );
}

function createPieChart(data) {

    if (pieChartInstance) pieChartInstance.destroy();

    if (!data || data.length === 0) return;

    pieChartInstance = new Chart(
        document.getElementById("pieChart"),
        {
            type: "doughnut",
            data: {
                labels: data.map(c => c[0]),
                datasets: [{
                    data: data.map(c => c[1])
                }]
            }
        }
    );
}

// ================= TRANSACTIONS =================

function renderTransactions(data) {

    const list = document.getElementById("transactionList");
    list.innerHTML = "";

    if (!data || data.length === 0) {
        list.innerHTML = "<li>No transactions</li>";
        return;
    }

    data.forEach(item => {

        const li = document.createElement("li");
        li.style.cssText =
            "display:flex; justify-content:space-between; padding:8px; border-bottom:1px solid #333;";

        li.innerHTML = `
            <div>
                <strong>${item[3]}</strong><br>
                <small>${item[2]}</small>
            </div>
            <div>
                ₹${item[1]}
                <button onclick='openEditModal(${JSON.stringify(item)})'>✏️</button>
                <button onclick='deleteExpense(${item[0]})'>🗑️</button>
            </div>
        `;

        list.appendChild(li);
    });
}

// ================= ADD EXPENSE =================

function openModal() {
    document.getElementById("expenseModal").style.display = "block";
    document.getElementById("date").value =
        new Date().toISOString().split("T")[0];
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
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ category, amount, date })
    })
    .then(() => {
        closeModal();
        loadDashboard();
    });
}

// ================= EDIT / DELETE =================

function openEditModal(item) {
    currentEditingId = item[0];
    document.getElementById("editCategory").value = item[3];
    document.getElementById("editAmount").value = item[1];
    document.getElementById("editDate").value = item[2];
    document.getElementById("editModal").style.display = "block";
}

function closeEditModal() {
    document.getElementById("editModal").style.display = "none";
}

function saveEdit() {

    const category = document.getElementById("editCategory").value;
    const amount = document.getElementById("editAmount").value;
    const date = document.getElementById("editDate").value;

    fetch(`/update-expense/${currentEditingId}`, {
        method: "PUT",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ category, amount, date })
    })
    .then(() => {
        closeEditModal();
        loadDashboard();
    });
}

function deleteExpense(id) {
    fetch(`/delete-expense/${id}`, { method: "DELETE" })
    .then(() => loadDashboard());
}

// ================= PROFILE =================

function loadProfile() {
    fetch("/get-profile")
    .then(res => res.json())
    .then(data => {
        currentProfile = data;
    });
}

// ================= PREDICTIONS =================

function loadPredictions() {

    fetch("/predict")
    .then(res => res.json())
    .then(data => {

        document.getElementById("predictedTotal").innerText =
            "₹" + (data.predicted_total || 0);

        document.getElementById("predictedWeek").innerText =
            "₹" + (data.predicted_week || 0);

        document.getElementById("trendInfo").innerText =
            "Trend: " + (data.trend || "--");

        document.getElementById("savingPrediction").innerText =
            "Savings: ₹" + (data.predicted_savings || 0);
    });
}

// ================= BUDGET =================

function setBudget() {

    const budget = prompt("Enter monthly budget:");

    if (!budget || isNaN(budget)) {
        alert("Enter valid amount");
        return;
    }

    fetch("/set-budget", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ budget: parseFloat(budget) })
    })
    .then(() => loadDashboard());
}

// ================= LOGOUT =================

function logoutUser() {
    fetch("/logout")
    .then(() => window.location.href = "/");
}

// ================= AUTO LOAD =================

window.onload = () => {
    if (window.location.pathname === "/dashboard") {
        loadDashboard();
    }
};