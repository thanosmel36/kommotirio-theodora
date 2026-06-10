import streamlit as st
import sqlite3
from datetime import datetime, timedelta, date

# ---------------- UI ----------------
st.set_page_config(page_title="Κομμώσεις Θεοδώρα", layout="wide")

st.markdown("""
<style>
    h1 {text-align:center; color:#6a1b9a;}
    .card {
        background:white;
        padding:15px;
        border-radius:12px;
        box-shadow:0 2px 10px rgba(0,0,0,0.1);
        margin-bottom:10px;
    }
</style>
""", unsafe_allow_html=True)

# ---------------- DB ----------------
conn = sqlite3.connect("appointments.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS appointments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    phone TEXT,
    service TEXT,
    duration INTEGER,
    price REAL,
    date TEXT,
    start_time TEXT,
    end_time TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS customers (
    phone TEXT PRIMARY KEY,
    name TEXT,
    visits INTEGER DEFAULT 0
)
""")
conn.commit()

# ---------------- SERVICES ----------------
services = {
    "Ανδρικό κούρεμα": {"duration": 30, "price": 12},
    "Μούσι": {"duration": 15, "price": 5},
    "Ανδρικό + Μούσι": {"duration": 45, "price": 15},
    "Γυναικείο κούρεμα": {"duration": 60, "price": 20},
    "Χτένισμα": {"duration": 45, "price": 15},
    "Βαφή": {"duration": 120, "price": 35}
}

st.title("💇 Κομμώσεις Θεοδώρα")

st.write("  2324093752")
st.write("  Παλαιοκωμη Σερρων")

# ---------------- INPUT ----------------
col1, col2, col3 = st.columns(3)

with col1:
    name = st.text_input("👤 Όνομα")

with col2:
    phone = st.text_input("📞 Τηλέφωνο")

with col3:
    service = st.selectbox("✂ Υπηρεσία", list(services.keys()))

selected_date = st.date_input("📅 Ημερομηνία", value=date.today())

duration = services[service]["duration"]
price = services[service]["price"]

st.info(f"⏱ {duration} λεπτά | 💶 {price} €")

# ---------------- LOAD BOOKINGS ----------------
c.execute("SELECT * FROM appointments WHERE date=?", (str(selected_date),))
bookings = c.fetchall()

def conflict(start_new, end_new):
    for b in bookings:
        s_old = datetime.strptime(b[7], "%H:%M")
        e_old = datetime.strptime(b[8], "%H:%M")
        if start_new < e_old and end_new > s_old:
            return True
    return False

# ---------------- SLOTS ----------------
work = [(9,14),(17,21)]
slots = []

for s,e in work:
    current = datetime.combine(selected_date, datetime.min.time()).replace(hour=s)

    while current + timedelta(minutes=duration) <= datetime.combine(selected_date, datetime.min.time()).replace(hour=e):
        start = current
        end = current + timedelta(minutes=duration)

        if not conflict(start,end):
            slots.append(start.strftime("%H:%M"))

        current += timedelta(minutes=30)

time = st.selectbox("🕒 Διαθέσιμη ώρα", slots if slots else ["Καμία διαθεσιμότητα"])

# ---------------- SAVE ----------------
with st.form("booking_form"):
    name = st.text_input("Όνομα")
    phone = st.text_input("Τηλέφωνο")

    submit = st.form_submit_button("✔ Κλείσιμο Ραντεβού")

    if submit:

        if name and phone and time:

         start_dt = datetime.strptime(time, "%H:%M")
        
         end_dt = start_dt + timedelta(minutes=duration)

        c.execute(
            "SELECT * FROM appointments WHERE phone=? AND date=? AND start_time=?",
            (phone, str(selected_date), time)
            )
        exists = c.fetchone()

            if exists:
                st.error("Υπάρχει ήδη αυτό το ραντεβού")
            else:
                c.execute(
                "INSERT INTO appointments (name, phone, service, duration, price, date, start_time, end_time) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",

                (name, phone, service, duration, price, str(selected_date), time, end_dt.strftime("%H:%M"))
                 )
                 conn.commit()
                st.success("Το ραντεβού καταχωρήθηκε")

        # update customer
        c.execute("SELECT * FROM customers WHERE phone=?", (phone,))
        customer = c.fetchone()

        if customer:
            c.execute("UPDATE customers SET visits = visits + 1 WHERE phone=?", (phone,))
        else:
            c.execute("INSERT INTO customers (phone, name, visits) VALUES (?, ?, 1)", (phone, name))

        conn.commit()
        st.success("✔ Ραντεβού καταχωρήθηκε!")
        st.rerun()

st.markdown("---")

# ---------------- DASHBOARD ----------------
col1, col2 = st.columns(2)

with col1:
    st.subheader("📅 Ραντεβού ημέρας")
    total_income = 0

    for b in bookings:
        total_income += b[5]
        st.markdown(f"""
        <div class="card">
            <b>{b[1]}</b> | {b[2]}<br>
            {b[3]} | {b[7]} - {b[8]}<br>
            💶 {b[5]}€
        </div>
        """, unsafe_allow_html=True)
is_admin=False        
if is_admin:
    st.metric("💰 Έσοδα ημέρας", f"{total_income} €")

with col2:
    st.subheader("👥 Πελάτες")

    c.execute("SELECT * FROM customers ORDER BY visits DESC")
    customers = c.fetchall()

    for cst in customers:
        st.write(f"👤 {cst[1]} | 📞 {cst[0]} | 🔁 {cst[2]} επισκέψεις")
