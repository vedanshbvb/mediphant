import streamlit as st
import pandas as pd
import openpyxl
import time
import smtplib
from email.message import EmailMessage
from pipeline import get_greeting  # Assumes pipeline.py exposes this
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# --- Helper Functions ---
def load_patient_db():
    return pd.read_csv('patient_database.csv')

def save_patient_db(df):
    df.to_csv('patient_database.csv', index=False)

def load_doctor_schedule():
    return pd.read_excel('doctor_schedule.xlsx')

def save_doctor_schedule(df):
    df.to_excel('doctor_schedule.xlsx', index=False)

def lookup_patient(df, patientid):
    if pd.notna(patientid) and str(patientid) in df['patientid'].astype(str).values:
        return 'returning', df[df['patientid'].astype(str) == str(patientid)].iloc[0]
    return 'new', None

def update_patient_db(df, info):
    # info: dict with Name, DOB, Email, Location, doctorid, patientid, InsuranceCarrier, MemberID, Group
    if 'patientid' in info and pd.notna(info['patientid']):
        idx = df[df['patientid'].astype(str) == str(info['patientid'])].index
        if not idx.empty:
            for k, v in info.items():
                df.at[idx[0], k] = v
        else:
            df = pd.concat([df, pd.DataFrame([info])], ignore_index=True)
    else:
        df = pd.concat([df, pd.DataFrame([info])], ignore_index=True)
    return df

def available_slots(schedule_df, doctor_id, required_slots):
    # Returns list of available slot indices for a doctor that can fit required_slots consecutive
    slots = [col for col in schedule_df.columns if '-' in col]
    doc_row = schedule_df[schedule_df['doctorid'] == doctor_id]
    if doc_row.empty:
        return []
    doc_row = doc_row.iloc[0]
    free = [i for i, s in enumerate(slots) if pd.isna(doc_row[slots[i]])]
    # Find consecutive slots
    for i in range(len(free) - required_slots + 1):
        if all(free[j] == free[i] + j for j in range(required_slots)):
            return [slots[free[i] + j] for j in range(required_slots)]
    return []

def book_slots(schedule_df, doctor_id, slot_names, patient_name):
    idx = schedule_df[schedule_df['doctorid'] == doctor_id].index
    for slot in slot_names:
        schedule_df.at[idx[0], slot] = patient_name
    return schedule_df

def send_email(to_email, subject, body, attachment_path=None):
    EMAIL = os.getenv("EMAIL")
    PASS = os.getenv("PASS")
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = EMAIL
    msg['To'] = to_email
    msg.set_content(body)
    if attachment_path:
        with open(attachment_path, 'rb') as f:
            msg.add_attachment(f.read(), maintype='application', subtype='pdf', filename=attachment_path)
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
            smtp.starttls()
            smtp.login(EMAIL, PASS)
            smtp.send_message(msg)
    except Exception as e:
        st.warning(f"Email failed: {e}")

def send_reminder(to_email, message):
    # For demo, just print or show in Streamlit
    st.info(f"Reminder sent to {to_email}: {message}")

# --- Streamlit App ---
st.set_page_config(page_title="Medical Appointment Scheduler", layout="centered")
st.title("AI Medical Appointment Scheduler")

if 'step' not in st.session_state:
    st.session_state['step'] = 0
if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []

# 1. Chatbox for greeting
if st.session_state['step'] == 0:
    user_input = st.chat_input("Say hello to start...")
    if user_input:
        st.session_state['chat_history'].append(("user", user_input))
        if user_input.lower().strip() == "hello":
            greeting = get_greeting()
            st.session_state['chat_history'].append(("agent", greeting))
            st.session_state['step'] = 1
        else:
            st.session_state['chat_history'].append(("agent", "Please type 'hello' to begin."))
    for who, msg in st.session_state['chat_history']:
        st.chat_message(who).write(msg)

# 2. Patient Intake Form
if st.session_state['step'] == 1:
    st.subheader("Patient Intake Form")
    with st.form("intake_form"):
        name = st.text_input("Name")
        dob = st.date_input("Date of Birth")
        email = st.text_input("Email")
        location = st.text_input("Location")
        doctorid = st.text_input("doctorid (optional)")
        patientid = st.text_input("patientid (optional)")
        submitted = st.form_submit_button("Submit")
    if submitted:
        df = load_patient_db()
        status, patient_row = lookup_patient(df, patientid)
        st.session_state['patient_status'] = status
        st.session_state['patient_info'] = {
            'Name': name, 'DOB': dob, 'Email': email, 'Location': location,
            'doctorid': doctorid, 'patientid': patientid
        }
        df = update_patient_db(df, st.session_state['patient_info'])
        save_patient_db(df)
        st.session_state['step'] = 2
        st.success(f"{status.title()} patient. Proceed to scheduling.")

# 3. Scheduling
if st.session_state['step'] == 2:
    st.subheader("Schedule Appointment")
    schedule_df = load_doctor_schedule()
    st.dataframe(schedule_df)
    required_slots = 2 if st.session_state['patient_status'] == 'new' else 1
    doctorid = st.session_state['patient_info']['doctorid']
    if not doctorid:
        doctorid = st.selectbox("Select doctorid", schedule_df['doctorid'])
    slots = [col for col in schedule_df.columns if '-' in col]
    available = available_slots(schedule_df, doctorid, required_slots)
    if available:
        slot_choice = st.selectbox("Select available slot(s)", [', '.join(available)])
        if st.button("Book Appointment"):
            schedule_df = book_slots(schedule_df, doctorid, available, st.session_state['patient_info']['Name'])
            save_doctor_schedule(schedule_df)
            # Update patient DB with doctor assignment
            df = load_patient_db()
            st.session_state['patient_info']['doctorid'] = doctorid
            df = update_patient_db(df, st.session_state['patient_info'])
            save_patient_db(df)
            st.session_state['step'] = 3
            st.success("Appointment booked!")
    else:
        st.warning("No available slots for this doctor.")

# 4. Insurance Form
if st.session_state['step'] == 3:
    st.subheader("Insurance Information")
    with st.form("insurance_form"):
        carrier = st.text_input("Insurance Carrier (type 'NA' if none)")
        memberid = st.text_input("Member ID (type 'NA' if none)")
        group = st.text_input("Group (type 'NA' if none)")
        ins_submit = st.form_submit_button("Submit Insurance Info")
    if ins_submit:
        df = load_patient_db()
        st.session_state['patient_info'].update({
            'InsuranceCarrier': carrier,
            'MemberID': memberid,
            'Group': group
        })
        df = update_patient_db(df, st.session_state['patient_info'])
        save_patient_db(df)
        st.session_state['step'] = 4
        st.success("Insurance info saved.")

# 5. Confirmation and Email
if st.session_state['step'] == 4:
    st.subheader("Confirmation")
    st.write("Appointment confirmed! Patient intake form will be emailed.")
    send_email(
        st.session_state['patient_info']['Email'],
        "Your Appointment Confirmation",
        "Thank you for booking. Please fill the attached intake form and bring it to your appointment.",
        attachment_path='patient_intake_form.pdf'
    )
    st.session_state['step'] = 5
    st.success("Confirmation email sent.")

# 6. Reminders
if st.session_state['step'] == 5:
    st.subheader("Reminders")
    email = st.session_state['patient_info']['Email']
    # First reminder
    time.sleep(5)
    send_reminder(email, "Reminder: Please fill your intake form.")
    # Second reminder
    time.sleep(5)
    filled = st.radio("Did you fill the form?", ("Yes", "No"))
    if filled:
        # Third reminder
        time.sleep(5)
        attending = st.radio("Will you attend the appointment?", ("Yes", "No"))
        if attending == "No":
            reason = st.text_input("Please provide a reason for cancellation:")
            st.write(f"Cancellation reason logged: {reason}")
        else:
            st.write("Thank you! See you at your appointment.")
