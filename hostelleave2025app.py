import streamlit as st
import random
import io
import pandas as pd
import qrcode
from io import BytesIO
from PIL import Image
import os
import datetime
hide_streamlit_style="""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
[data-testid="stToolbar"]{
    visibility: hidden;
    display: none;
}
</style>
"""
USERS = {
    "student": {"id": "student123", "password": "pass123"},
    "teacher_dileep": {"id": "dileep123", "password": "pass456", "name": "Dileep Kumar"},
    "teacher_bagal": {"id": "bagal123", "password": "pass789", "name": "Bagal"},
    "teacher_sugam": {"id": "sugam123", "password": "pass101", "name": "Sugam Shivare"},
    "teacher_rajshekhar": {"id": "raj123", "password": "pass102", "name": "Rajshekhar Pothala"},
    "teacher_dj": {"id": "dj123", "password": "pass103", "name": "DJ"},
    "teacher_ashok": {"id": "ashok123", "password": "pass104", "name": "ASHOK PANIGRAHI"},
    "teacher_sachin": {"id": "sachin123", "password": "pass105", "name": "Sachin Bhandari"},
    "teacher_rehan": {"id": "rehan123", "password": "pass106", "name": "Rehan"},
    "teacher_suraj": {"id": "suraj123", "password": "pass107", "name": "Suraj Patil"},

    "hod_1": {"id": "hod1_id", "password": "hod1_pass", "name": "HOD BTech/MBA"},
    "hod_2": {"id": "hod2_id", "password": "hod2_pass", "name": "HOD BPharm/Textile"},

    "dean": {"id": "dean_id", "password": "dean_pass", "name": "Dean of Academics"},
}

DATABASE = "leave_request.csv"

LEAVE_STATUS_PENDING = "Pending"
LEAVE_STATUS_TEACHER_APPROVED = "Teacher Approved"
LEAVE_STATUS_HOD_APPROVED = "HOD Approved" 
LEAVE_STATUS_GRANTED = "Granted" 
LEAVE_STATUS_REJECTED = "Rejected"

st.set_page_config(page_title="Smart Hostel Leave App", layout="centered")

if "LI_AS" not in st.session_state:
    st.session_state.LI_AS = None 
if "T_NAME" not in st.session_state:
    st.session_state.T_NAME = None 
if "HOD_NAME" not in st.session_state:
    st.session_state.HOD_NAME = None 
if "DEAN_NAME" not in st.session_state:
    st.session_state.DEAN_NAME = None 

def login(role):
    st.subheader(f"{role.capitalize()} Login")
    u_id = st.text_input("ID", key=f"{role}_id",placeholder="Login ID")
    pwd = st.text_input("Password", type="password", key=f"{role}_password", placeholder="Password")
    login_btn = st.button("Login", key=f"{role}_login")

    if login_btn:
        if role == "student":
            if u_id == USERS["student"]["id"] and pwd == USERS["student"]["password"]:
                st.session_state.LI_AS = "student"
                st.success(f"Welcome, you're logged in as a student!")
                st.rerun()
            else:
                st.error("Invalid Student ID or Password. Please try again.")
        elif role == "teacher":
            found = False
            for t_key, t_info in USERS.items():
                if t_key.startswith("teacher") and u_id == t_info["id"] and pwd == t_info["password"]:
                    st.session_state.LI_AS = "teacher"
                    st.session_state.T_NAME = t_info["name"]
                    st.success(f"Welcome, {t_info['name']}! You're logged in as a teacher.")
                    found = True
                    st.rerun()
                    break
            if not found:
                st.error("Invalid Teacher ID or Password. Please try again.")
        elif role == "hod":
            found = False
            for hod_key, hod_info in USERS.items():
                if hod_key.startswith("hod") and u_id == hod_info["id"] and pwd == hod_info["password"]:
                    st.session_state.LI_AS = "hod"
                    st.session_state.HOD_NAME = hod_info["name"]
                    st.success(f"Welcome, {hod_info['name']}! You're logged in as an HOD.")
                    found = True
                    st.rerun()
                    break
            if not found:
                st.error("Invalid HOD ID or Password. Please try again.")
        elif role == "dean":
            if u_id == USERS["dean"]["id"] and pwd == USERS["dean"]["password"]:
                st.session_state.LI_AS = "dean"
                st.session_state.DEAN_NAME = USERS["dean"]["name"]
                st.success(f"Welcome, {USERS['dean']['name']}! You're logged in as the Dean.")
                st.rerun()
            else:
                st.error("Invalid Dean ID or Password. Please try again.")

@st.cache_data(show_spinner="Loading leave requests...")
def load_leave_requests():
    exp_cols_dtypes = {
        "student_name": str,
        "attendance": float,
        "year": str,
        "student_id": str,
        "branch": str,
        "batch": str,
        "email": str,
        "leave_days": int,
        "start_date": str,
        "end_date": str,
        "reason": str,
        "teacher": str,
        "hod_assigned": str, 
        "teacher_approved": bool,
        "hod_approved": bool,     
        "dean_approved": bool,    
        "status": str,
        "qr_code_data": str
    }

    if os.path.exists(DATABASE):
        try:
            df = pd.read_csv(DATABASE)
            for col, dtype in exp_cols_dtypes.items():
                if col not in df.columns:
                    if dtype == bool:
                        df.insert(loc=df.shape[-1], column=col, value=False)
                    else:
                        df.insert(loc=df.shape[-1], column=col, value=None)
                try:
                    if dtype == int:
                        df.loc[:, col] = pd.to_numeric(df.loc[:, col], errors='coerce').fillna(0).astype(int)
                    elif dtype == float:
                        df.loc[:, col] = pd.to_numeric(df.loc[:, col], errors='coerce').fillna(0.0).astype(float)
                    elif dtype == bool:
                        df.loc[:, col] = df.loc[:, col].apply(lambda x: True if str(x).lower() == 'true' else False)
                    else:
                        df.loc[:, col] = df.loc[:, col].astype(str).replace('nan', None)
                except Exception as e:
                    st.warning(f"Couldn't fully convert column '{col}' to {dtype}: {e}. It is not possible.")
                    df.loc[:, col] = df.loc[:, col].astype(str)

            if 'qr_code_data' in df.columns:
                df.loc[:, 'qr_code_data'] = df.loc[:, 'qr_code_data'].astype(str).replace(['None', 'nan'], [None, None])

            return df
        except pd.errors.EmptyDataError:
            st.warning("The leave requests file is empty.")
            initial_df = pd.DataFrame(columns=exp_cols_dtypes.keys())
            for col, dtype in exp_cols_dtypes.items():
                if dtype == bool:
                    initial_df[col] = initial_df[col].astype(bool)
                elif dtype == int:
                    initial_df[col] = initial_df[col].astype(int)
                elif dtype == float:
                    initial_df[col] = initial_df[col].astype(float)
                else:
                    initial_df[col] = initial_df[col].astype(object) 
            return initial_df

        except Exception as e:
            st.error(f"It had trouble loading leave requests: {e}. Starting with an empty list.")
            initial_df = pd.DataFrame(columns=exp_cols_dtypes.keys())
            for col, dtype in exp_cols_dtypes.items():
                if dtype == bool:
                    initial_df[col] = initial_df[col].astype(bool)
                elif dtype == int:
                    initial_df[col] = initial_df[col].astype(int)
                elif dtype == float:
                    initial_df[col] = initial_df[col].astype(float)
                else:
                    initial_df[col] = initial_df[col].astype(object) 
            return initial_df
    else:
        initial_df = pd.DataFrame(columns=exp_cols_dtypes.keys())
        for col, dtype in exp_cols_dtypes.items():
            if dtype == bool:
                initial_df[col] = initial_df[col].astype(bool)
            elif dtype == int:
                initial_df[col] = initial_df[col].astype(int)
            elif dtype == float:
                initial_df[col] = initial_df[col].astype(float)
            else:
                initial_df[col] = initial_df[col].astype(object) 
        return initial_df

def save_leave_request(new_req, existing_reqs):
    new_req_df = pd.DataFrame([new_req])
    updated_reqs = pd.concat([existing_reqs, new_req_df], ignore_index=True)

    try:
        updated_reqs.to_csv(DATABASE, index=False)
        load_leave_requests.clear() 
        return True
    except Exception as e:
        st.error(f"Couldn't save your request: {e}")
        return False

def update_leave_request(index, column, value):
    global L_DF
    try:
        L_DF.loc[index, column] = value
        L_DF.to_csv(DATABASE, index=False)
        load_leave_requests.clear() 
        return True
    except Exception as e:
        st.error(f"Error updating request: {e}")
        return False

def generate_qr_code(data: str, box_size=6) -> Image.Image:
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=box_size,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
    return img

def image_to_bytes(img):
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    return img_byte_arr.getvalue()

L_DF = load_leave_requests() 

def student_page():
    global L_DF

    st.title("Welcome to Nmims Leave Application🧳!")
    st.write("---")

    st.header("Leave Application Form")
    s_name = st.text_input("Enter your full name", placeholder="Your name")
    s_id = st.text_input("Enter your student ID", placeholder="Your SAP ID ")

    if not s_id:
        st.info("Please enter your **Student ID** to proceed.")
    else:
        st.write(f"Your Student ID is: **{s_id}**", placeholder="Student ID")

    yr = st.text_input("Which year are you in (e.g., 1, 2, 3, 4)?", placeholder="Year")
    yr_valid = False
    if yr:
        try:
            yr_int = int(yr)
            if 1 <= yr_int <= 4:
                yr_valid = True
            else:
                st.error("Please enter a valid year (like 1, 2, 3, or 4).")
        except ValueError:
            st.error("Enter a valid number for the year!")
    else:
        st.info("Please enter your academic year.")

    attn = st.number_input("Enter your average attendance percentage?", min_value=0.0, max_value=100.0, value=85.0, step=0.1, format="%.1f")
    st.write(f"Your attendance is: **{attn:.2f}%**")
    if attn <= 80:
        st.warning("Your attendance is below 80%. You might need to talk with your Mentor about this.")

    email = st.text_input("Your Email ID:", placeholder="youremail@example.com")

    col_a, col_b = st.columns(2)
    auth_leave = False
    spec_leave = False
    with col_a:
        auth_leave = st.checkbox('Authorized Leave')
    with col_b:
        spec_leave = st.checkbox('Special Leave')

    leave_type_sel = False
    if auth_leave and spec_leave:
        st.error("Please pick only one type of leave.")
    elif not auth_leave and not spec_leave:
        st.error("Don't forget to select a leave type!")
    else:
        leave_type_sel = True

    reason = st.text_area("Why are you requesting leave?", height=100, placeholder="Enter your reason here")
    if reason:
        st.info("Your reason will be reviewed by your mentor.")
    else:
        st.warning("Please provide a reason for your leave.")

    st.subheader("Your Branch and Batch")
    mentors = ['Dileep Kumar', 'Bagal', 'Sugam Shivare', 'Rajshekhar Pothala', 'DJ', 'ASHOK PANIGRAHI', 'Sachin Bhandari', 'Rehan', 'Suraj Patil']
    branches = ['BTECH CS', 'BTECH CE', 'BTECH AI-ML', 'BTECH IT', 'MBA TECH CE', 'B-PHARM', 'TEXTILE']
    sel_branch = st.selectbox("Choose your Branch:", branches, index=0)

    batches = []
    if sel_branch == "BTECH CS":
        batches = ['A1','A2','B1','B2']
    elif sel_branch == "BTECH CE":
        batches = ['C1','C2','D1','D2']
    elif sel_branch == "BTECH AI-ML":
        batches = ['F1','F2']
    elif sel_branch == "BTECH IT":
        batches = ['E1','E2']
    elif sel_branch == "MBA TECH CE":
        batches = ['AB1','AB2']
    elif sel_branch == "B-PHARM":
        batches = ['P1','P2','P3']
    elif sel_branch == "TEXTILE":
        batches = ['T1','T2','T3','T4']

    sel_batch = None
    if not batches:
        st.warning("Pick your branch to see your batch options.")
    else:
        sel_batch = st.selectbox("Choose your Batch:", batches)
        if sel_batch:
            st.write(f"You're in batch: **{sel_batch}**, from the **{sel_branch}** branch.")
        else:
            st.info("Please select your batch.")

    st.subheader("Your Mentor's Details")

    sel_mentor = st.selectbox("Select Your Mentor:", mentors)

    mentor_batch_map = {
        'A1': 'Sugam Shivare', 'A2': 'Dileep Kumar', 'B1': 'Rajshekhar Pothala', 'B2': 'DJ',
        'C1': 'ASHOK PANIGRAHI', 'C2': 'Sachin Bhandari', 'D1': 'Suraj Patil', 'D2': 'Rehan',
        'F1': 'Dileep Kumar', 'F2': 'DJ',
        'E1': 'Bagal', 'E2': 'Dileep Kumar',
        'AB1': 'Sachin Bhandari', 'AB2': 'Rehan',
        'P1': 'Dileep Kumar', 'P2': 'Dileep Kumar', 'P3': 'Dileep Kumar',
        'T1': 'DJ', 'T2': 'DJ', 'T3': 'DJ', 'T4': 'DJ'
    }

    mentor_verified = False
    if sel_batch and sel_mentor:
        if mentor_batch_map.get(sel_batch) == sel_mentor:
            st.success("Mentor and batch details verified")
            mentor_verified = True
        else:
            st.error(f"Please check if  '{sel_mentor}' is the correct mentor for batch '{sel_batch}'?")
    elif not sel_batch:
        st.warning("Please pick your batch to help verify your mentor.")

    st.subheader("When are you applying for leave? 📅")
    today = datetime.date.today()
    s_date = st.date_input("Leave From:", today)
    e_date = st.date_input("Till:", max(today, s_date))

    num_days = 0
    date_range_valid = False
    if s_date > e_date:
        st.error("The 'End' date must be after or on the 'From' date.")
    else:
        num_days = (e_date - s_date).days + 1
        st.success(f"You're applying for **{num_days}** day(s) of leave.")
        date_range_valid = True

    ah = None
    if sel_branch in ['BTECH CS', 'BTECH CE', 'BTECH AI-ML', 'BTECH IT', 'MBA TECH CE']:
        ah= USERS["hod_1"]["name"]
    elif sel_branch in ['B-PHARM', 'TEXTILE']:
        ah= USERS["hod_2"]["name"]
    else:
        st.warning("Could not determine the HOD for your selected branch.")


    st.write("-------")
    if st.button("Submit My Leave Request"):
        if all([
            s_name, s_id, attn is not None, yr_valid, sel_branch, sel_batch,
            email, sel_mentor, reason,
            leave_type_sel, date_range_valid, mentor_verified, num_days > 0,
            ah 
        ]):
            is_dup = False
            spr = L_DF.loc[(L_DF["student_id"] == s_id) &
                                      (L_DF["status"] == LEAVE_STATUS_PENDING)].copy()

            if not spr.empty:
                new_s_dt = s_date
                new_e_dt = e_date

                spr.loc[:, 'existing_start_dt'] = pd.to_datetime(spr['start_date']).dt.date
                spr[:, 'existing_end_dt'] = pd.to_datetime(spr['end_date']).dt.date

                for idx, er in spr.iterrows():
                    do = (new_s_dt <= er['existing_end_dt']) and \
                                    (er['existing_start_dt'] <= new_e_dt)
                    rm = (str(er['reason']).strip().lower() == reason.strip().lower())

                    if do and rm:
                        is_dup = True
                        break

            if is_dup:
                st.warning("You already have a similar pending leave request for these dates and reason. Please wait for your previous request to be processed by your teacher and HOD.")
            else:
                nr = {
                    "student_name": s_name,
                    "attendance": attn,
                    "year": yr,
                    "student_id": s_id,
                    "branch": sel_branch,
                    "batch": sel_batch,
                    "email": email,
                    "leave_days": num_days,
                    "start_date": s_date.isoformat(),
                    "end_date": e_date.isoformat(),
                    "reason": reason,
                    "teacher": sel_mentor,
                    "hod_assigned": ah, 
                    "teacher_approved": False,    
                    "hod_approved": False,        
                    "dean_approved": False,       
                    "status": LEAVE_STATUS_PENDING,
                    "qr_code_data": None
                }
                if save_leave_request(nr, L_DF):
                    st.success("Your leave request has been submitted for approval by your teacher and HOD.")
                    L_DF = load_leave_requests()
                else:
                    st.error("Couldn't save your request. Something went wrong.")
        else:
            st.error("Please fill in all the required details correctly and fix any errors before submitting.")

    st.write("------")
    st.subheader("Your Leave Request Status and Gate Pass")
    if s_id:
        s_reqs = L_DF.loc[(L_DF["student_id"] == s_id)].copy()

        if not s_reqs.empty:
            st.write("Your Leave Request History:")

            display_cols = ['start_date', 'end_date', 'leave_days', 'reason',
                            'status', 'teacher', 'hod_assigned',
                            'teacher_approved', 'hod_approved', 'dean_approved']
            st.dataframe(s_reqs[display_cols])

            s_reqs.loc[:, 'start_date_dt'] = pd.to_datetime(s_reqs['start_date']).dt.date
            s_reqs.loc[:, 'end_date_dt'] = pd.to_datetime(s_reqs['end_date']).dt.date

            active_granted_reqs = s_reqs.loc[
                (s_reqs["status"] == LEAVE_STATUS_GRANTED) &
                (s_reqs["end_date_dt"] >= today)
            ].sort_values(by="end_date_dt", ascending=True)

            if not active_granted_reqs.empty:
                cr= active_granted_reqs.iloc[[0]]

                if pd.notna(cr["qr_code_data"].iloc[0]):
                    st.success(f"Your leave request for **{cr['start_date'].iloc[0]}** to **{cr['end_date'].iloc[0]}** has been **GRANTED.** This pass is valid until **{cr['end_date_dt'].iloc[0]}**.")
                    st.subheader("Your Active Gate Pass:")
                    try:
                        qr_data = cr["qr_code_data"].iloc[0]
                        qr_image = generate_qr_code(qr_data, box_size=4)
                        qr_bytes = image_to_bytes(qr_image)
                        st.image(qr_image, caption="Your Approved Leave Gate Pass", use_container_width=False)
                        st.download_button(
                            label="Download Your Gate Pass QR Code",
                            data=qr_bytes,
                            file_name=f"gatepass_{s_id}_{cr['start_date'].iloc[0]}.png",
                            mime="image/png",
                        )
                    except Exception as e:
                        st.error(f"Something went wrong displaying your QR code: {e}. Please contact your teacher or administrator.")
                else:
                    st.info("Your leave request is approved, but the QR code data seems to be missing. Please talk to your teacher/HOD/Dean.")
            else:
                st.info("No active or future approved leave requests found for your Student ID. Your previous passes have expired or none are pending.")
        else:
            st.info("No leave requests found for your Student ID. Submit one above.")
    else:
        st.info("Enter your Student ID above to check your leave status and get your pass.")

def teacher_page():
    global L_DF

    ct = st.session_state.get("T_NAME")
    if ct:
        st.title(f"Welcome, {ct} (Teacher Portal)!")
    else:
        st.title("Welcome to the Teacher Portal!")

    st.write("--------")

    st.subheader("Pending Leave Requests (Awaiting Your Review)")

    pending_reqs_teacher = L_DF.loc[(L_DF["status"] == LEAVE_STATUS_PENDING) &
                                     (L_DF["teacher"] == ct)]
    if not pending_reqs_teacher.empty:
        for od, req in pending_reqs_teacher.iterrows():
            with st.container(border=True):
                st.info(f"**Student Name:** {req['student_name']}\n"
                        f"**Student ID:** {req['student_id']}\n"
                        f"**Branch/Batch:** {req['branch']}/{req['batch']}\n"
                        f"**Leave Days:** {req['leave_days']} ({req['start_date']} to {req['end_date']})\n"
                        f"**Reason:** {req['reason']}\n"
                        f"**Requested Teacher:** {req['teacher']}\n"
                        f"**Assigned HOD:** {req['hod_assigned']}\n"
                        f"**Attendance:** {req['attendance']}%")

                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"✅ Approve {req['student_id']}", key=f"teacher_approve_{req['student_id']}_{od}"):
                        if update_leave_request(od, "teacher_approved", True):
                            st.success(f"Teacher approval recorded for Student ID: {req['student_id']}. Request now awaiting HOD approval.")
                
                            L_DF.loc[od, "status"] = LEAVE_STATUS_TEACHER_APPROVED
                            L_DF.to_csv(DATABASE, index=False)
                            load_leave_requests.clear()
                            st.rerun()
                        else:
                            st.error("Failed to record teacher approval.")

                with col2:
                    if st.button(f"❌ Reject {req['student_id']}", key=f"teacher_reject_{req['student_id']}_{od}"):
                        if update_leave_request(od, "status", LEAVE_STATUS_REJECTED):
                            update_leave_request(od, "teacher_approved", False) 
                            update_leave_request(od, "hod_approved", False) 
                            update_leave_request(od, "dean_approved", False) 
                            update_leave_request(od, "qr_code_data", None) 
                            st.warning(f"Leave rejected for Student ID: {req['student_id']}.")
                            st.rerun()
                        else:
                            st.error("Failed to reject leave request.")
    else:
        st.info("No pending leave requests for you at the moment.")

    st.write("--------")
    st.subheader("Your Reviewed Leave Requests History")
    thr = L_DF.loc[
        (L_DF["teacher"] == ct) &
        (L_DF["status"] != LEAVE_STATUS_PENDING)
    ]

    if not thr.empty:
        st.dataframe(thr[['student_name', 'student_id', 'start_date', 'end_date', 'status', 'teacher_approved', 'hod_approved', 'dean_approved']])
    else:
        st.info("No reviewed leave requests found for you yet.")


def hod_page():
    global L_DF

    cnm= st.session_state.get("HOD_NAME")
    if cnm:
        st.title(f"Welcome, {cnm} (HOD Portal)!")
    else:
        st.title("Welcome to the HOD Portal!")

    st.write("---")

    st.subheader("Pending Leave Requests (Awaiting Your Review)")

    hob = []
    if cnm == USERS["hod_1"]["name"]:
        hob= ['BTECH CS', 'BTECH CE', 'BTECH AI-ML', 'BTECH IT', 'MBA TECH CE']
    elif cnm == USERS["hod_2"]["name"]:
        hob = ['B-PHARM', 'TEXTILE']

    prh= L_DF.loc[
        (L_DF["teacher_approved"] == True) &
        (L_DF["hod_approved"] == False) & 
        (L_DF["dean_approved"] == False) & 
        (L_DF["status"] != LEAVE_STATUS_REJECTED) & 
        (L_DF["hod_assigned"] == cnm)
    ]

    if not prh.empty:
        for oid, req in prh.iterrows():
            with st.container(border=True):
                st.info(f"**Student Name:** {req['student_name']}\n"
                        f"**Student ID:** {req['student_id']}\n"
                        f"**Branch/Batch:** {req['branch']}/{req['batch']}\n"
                        f"**Leave Days:** {req['leave_days']} ({req['start_date']} to {req['end_date']})\n"
                        f"**Reason:** {req['reason']}\n"
                        f"**Teacher:** {req['teacher']} (Approved: {'Yes' if req['teacher_approved'] else 'No'})\n"
                        f"**Assigned HOD:** {req['hod_assigned']}\n"
                        f"**Attendance:** {req['attendance']}%")

                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"✅ Approve {req['student_id']}", key=f"hod_approve_{req['student_id']}_{oid}"):
                        if update_leave_request(oid, "hod_approved", True):
                            if req['leave_days'] > 3:
                                st.success(f"HOD approval recorded for Student ID: {req['student_id']}. Request now awaiting Dean approval.")
                                L_DF.loc[oid, "status"] = LEAVE_STATUS_HOD_APPROVED 
                            else:
                                st.success(f"HOD approval recorded for Student ID: {req['student_id']}. Leave fully GRANTED!")
                                L_DF.loc[oid, "status"] = LEAVE_STATUS_GRANTED

                                qr_data = (f"LEAVE_GRANTED_ID:{req['student_id']}|"
                                           f"NAME:{req['student_name']}|"
                                           f"FROM:{req['start_date']}|"
                                           f"TO:{req['end_date']}|"
                                           f"TEACHER_APP:YES|"
                                           f"HOD_APP:YES|"
                                           f"TS:{datetime.datetime.now().timestamp()}")
                                L_DF.loc[oid, "qr_code_data"] = qr_data
                            L_DF.to_csv(DATABASE, index=False)
                            load_leave_requests.clear()
                            st.rerun()
                        else:
                            st.error("Failed to record HOD approval.")

                with col2:
                    if st.button(f"❌ Reject {req['student_id']}", key=f"hod_reject_{req['student_id']}_{oid}"):
                        if update_leave_request(oid, "status", LEAVE_STATUS_REJECTED):
                            update_leave_request(oid, "hod_approved", False) 
                            update_leave_request(oid, "dean_approved", False)
                            update_leave_request(oid, "qr_code_data", None) 
                            st.warning(f"Leave rejected for Student ID: {req['student_id']}.")
                            st.rerun()
                        else:
                            st.error("Failed to reject leave request.")
    else:
        st.info("No pending leave requests for you at the moment.")

    st.write("---")
    st.subheader("Your Reviewed Leave Requests History")

    hhr= L_DF.loc[
        (L_DF["hod_assigned"] == cnm) &
        (L_DF["hod_approved"] == True) | (L_DF["status"] == LEAVE_STATUS_REJECTED)
    ]

    if not hhr.empty:
        st.dataframe(hhr[['student_name', 'student_id', 'start_date', 'end_date', 'status', 'teacher_approved', 'hod_approved', 'dean_approved']])
    else:
        st.info("No approved or rejected leave requests found for you yet.")

def dean_page():
    global L_DF

    cdn = st.session_state.get("DEAN_NAME")
    if cdn:
        st.title(f"Welcome, {cdn} (Dean Portal)!")
    else:
        st.title("Welcome to the Dean Portal!")

    st.write("-----------")

    st.subheader("Pending Leave Requests (Awaiting Your Review)")

    prd= L_DF.loc[
        (L_DF["teacher_approved"] == True) &
        (L_DF["hod_approved"] == True) &
        (L_DF["dean_approved"] == False) & 
        (L_DF["leave_days"] > 3) & 
        (L_DF["status"] != LEAVE_STATUS_REJECTED) 
    ]

    if not prd.empty:
        for oid, req in prd.iterrows():
            with st.container(border=True):
                st.info(f"**Student Name:** {req['student_name']}\n"
                        f"**Student ID:** {req['student_id']}\n"
                        f"**Branch/Batch:** {req['branch']}/{req['batch']}\n"
                        f"**Leave Days:** {req['leave_days']} ({req['start_date']} to {req['end_date']})\n"
                        f"**Reason:** {req['reason']}\n"
                        f"**Teacher:** {req['teacher']} (Approved: {'Yes' if req['teacher_approved'] else 'No'})\n"
                        f"**Assigned HOD:** {req['hod_assigned']} (Approved: {'Yes' if req['hod_approved'] else 'No'})\n"
                        f"**Attendance:** {req['attendance']}%")

                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"✅ Approve {req['student_id']}", key=f"dean_approve_{req['student_id']}_{oid}"):
                        if update_leave_request(oid, "dean_approved", True):
                            st.success(f"Dean approval recorded for Student ID: {req['student_id']}. Leave fully GRANTED!")
                            L_DF.loc[oid, "status"] = LEAVE_STATUS_GRANTED

                            qr_data = (f"LEAVE_GRANTED_ID:{req['student_id']}|"
                                       f"NAME:{req['student_name']}|"
                                       f"FROM:{req['start_date']}|"
                                       f"TO:{req['end_date']}|"
                                       f"TEACHER_APP:YES|"
                                       f"HOD_APP:YES|"
                                       f"DEAN_APP:YES|"
                                       f"TS:{datetime.datetime.now().timestamp()}")
                            L_DF.loc[oid, "qr_code_data"] = qr_data
                            L_DF.to_csv(DATABASE, index=False)
                            load_leave_requests.clear()
                            st.rerun()
                        else:
                            st.error("Failed to record Dean approval.")

                with col2:
                    if st.button(f"❌ Reject {req['student_id']}", key=f"dean_reject_{req['student_id']}_{oid}"):
                        if update_leave_request(oid, "status", LEAVE_STATUS_REJECTED):
                            update_leave_request(oid, "dean_approved", False) 
                            update_leave_request(oid, "qr_code_data", None) 
                            st.warning(f"Leave rejected for Student ID: {req['student_id']}.")
                            st.rerun()
                        else:
                            st.error("Failed to reject leave request.")
    else:
        st.info("No pending leave requests for you at the moment.")

    st.write("---")
    st.subheader("Your Reviewed Leave Requests History")
    dhr = L_DF.loc[
        (L_DF["dean_approved"] == True) | (L_DF["status"] == LEAVE_STATUS_REJECTED) 
    ]

    if not dhr.empty:
        st.dataframe(dhr[['student_name', 'student_id', 'start_date', 'end_date', 'status', 'teacher_approved', 'hod_approved', 'dean_approved']])
    else:
        st.info("No approved or rejected leave requests found for you yet.")

def logout():
    if st.sidebar.button("Logout"):
        st.session_state.LI_AS = None
        st.session_state.T_NAME = None
        st.session_state.HOD_NAME = None
        st.session_state.DEAN_NAME = None
        st.rerun()

if st.session_state.LI_AS is None:
    st.sidebar.title("Login to Your Portal")
    page = st.sidebar.radio("Select Role", ["🧑‍🎓Student", "🧑‍🏫Teacher", "👨‍💼HOD", "🏛️Dean"], key="role_selection_radio")

    if page == "🧑‍🎓Student":
        login("student")
    elif page == "🧑‍🏫Teacher":
        login("teacher")
    elif page == "👨‍💼HOD":
        login("hod")
    elif page == "🏛️Dean":
        login("dean")
else:
    logout()
    if st.session_state.LI_AS == "student":
        student_page()
    elif st.session_state.LI_AS == "teacher":
        teacher_page()
    elif st.session_state.LI_AS == "hod":
        hod_page()
    elif st.session_state.LI_AS == "dean":
        dean_page()
