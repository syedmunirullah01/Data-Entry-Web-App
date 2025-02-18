import gspread
from oauth2client.service_account import ServiceAccountCredentials
import streamlit as st
import pandas as pd
from datetime import datetime

# Authenticate and connect to Google Sheets
def connect_to_gsheet(creds_json, spreadsheet_name, sheet_name):
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/drive"
    ]
    credentials = ServiceAccountCredentials.from_json_keyfile_name(creds_json, scope)
    client = gspread.authorize(credentials)
    spreadsheet = client.open(spreadsheet_name)
    return spreadsheet.worksheet(sheet_name)

# Google Sheet credentials and details
SPREADSHEET_NAME = 'Data Entry Sheet'
CREDENTIALS_FILE = './credentials.json'

# Connect to Google Sheets
sheet_data_entry = connect_to_gsheet(CREDENTIALS_FILE, SPREADSHEET_NAME, sheet_name='Sheet1')
sheet_tasks = connect_to_gsheet(CREDENTIALS_FILE, SPREADSHEET_NAME, sheet_name='Tasks')

st.title("Data Entry & Task Management")

# Read Data from Google Sheets
def read_data(sheet):
    data = sheet.get_all_records()
    return pd.DataFrame(data)

# Add Data to Google Sheets
def add_data(sheet, row):
    sheet.append_row(row)

# Sidebar form for data entry
with st.sidebar:
    st.header("Enter New Data")
    with st.form(key="data_form"):
        name = st.text_input("Name")
        age = st.number_input("Age", min_value=0, max_value=120)
        email = st.text_input("Email")
        submitted = st.form_submit_button("Submit")
        if submitted and name and email:
            add_data(sheet_data_entry, [name, age, email])
            st.success("Data added successfully!")
        elif submitted:
            st.error("Please fill out the form correctly.")

# Task form schema
task_form_schema = {
    "task_name": {"type": "text", "label": "Task Name", "required": True},
    "project": {"type": "select", "label": "Project", "required": True, "options": ["Project A", "Project B", "Project C"]},
    "due_date": {"type": "date", "label": "Due Date", "required": True},
    "description": {"type": "textarea", "label": "Description", "required": False}
}

def render_task_form(schema):
    form_data = {}
    st.sidebar.header("Task Form")
    with st.sidebar.form(key="task_form"):
        for field, properties in schema.items():
            if properties["type"] == "text":
                form_data[field] = st.text_input(properties["label"])
            elif properties["type"] == "select":
                form_data[field] = st.selectbox(properties["label"], properties["options"])
            elif properties["type"] == "date":
                form_data[field] = st.date_input(properties["label"], datetime.today())
            elif properties["type"] == "textarea":
                form_data[field] = st.text_area(properties["label"])
        submitted = st.form_submit_button("Submit")
    return form_data, submitted

def validate_task_form(form_data):
    errors = []
    if not form_data["task_name"]:
        errors.append("Task Name is required.")
    if not form_data["project"]:
        errors.append("Please select a project.")
    if form_data["due_date"] < datetime.today().date():
        errors.append("Due date must be in the future.")
    return errors

form_data, task_submitted = render_task_form(task_form_schema)
if task_submitted:
    errors = validate_task_form(form_data)
    if errors:
        for error in errors:
            st.sidebar.error(error)
    else:
        add_data(sheet_tasks, [form_data['task_name'], form_data['project'], form_data['due_date'].strftime('%Y-%m-%d'), form_data.get('description', "")])
        st.success("Task added successfully!")

# Display data tables
st.header("Data Entry Table")
st.dataframe(read_data(sheet_data_entry))

st.header("Tasks Table")
st.dataframe(read_data(sheet_tasks))
