import gspread
from oauth2client.service_account import ServiceAccountCredentials
import streamlit as st
import pandas as pd
from datetime import datetime

# Authenticate and connect to Google Sheets
def connect_to_gsheet(creds_json, spreadsheet_name, sheet_name):
    scope = ["https://spreadsheets.google.com/feeds", 
             'https://www.googleapis.com/auth/spreadsheets',
             "https://www.googleapis.com/auth/drive.file", 
             "https://www.googleapis.com/auth/drive"]
    
    credentials = ServiceAccountCredentials.from_json_keyfile_name(creds_json, scope)
    client = gspread.authorize(credentials)
    spreadsheet = client.open(spreadsheet_name)  
    return spreadsheet.worksheet(sheet_name)  # Access specific sheet by name

# Google Sheet credentials
SPREADSHEET_NAME = 'Data Entry Sheet'
CREDENTIALS_FILE = './credentials.json'

# Connect to Google Sheets
sheet_data = connect_to_gsheet(CREDENTIALS_FILE, SPREADSHEET_NAME, sheet_name='Sheet1')
sheet_tasks = connect_to_gsheet(CREDENTIALS_FILE, SPREADSHEET_NAME, sheet_name='Tasks')

st.title("Multi-Functional Data Entry App")

# Sidebar navigation
page = st.sidebar.radio("Select Page", ["Data Entry", "Task Form"])

if page == "Data Entry":
    st.header("Simple Data Entry Form")
    
    # Read Data from Google Sheets
    def read_data():
        data = sheet_data.get_all_records()
        return pd.DataFrame(data)

    # Add Data to Google Sheets
    def add_data(row):
        sheet_data.append_row(row)

    # Data Entry Form
    with st.sidebar:
        st.header("Enter New Data")
        with st.form(key="data_form"):
            name = st.text_input("Name")
            age = st.number_input("Age", min_value=0, max_value=120)
            email = st.text_input("Email")
            submitted = st.form_submit_button("Submit")
            if submitted:
                if name and email:
                    add_data([name, age, email])
                    st.success("Data added successfully!")
                else:
                    st.error("Please fill out the form correctly.")

    # Display Data
    st.header("Data Table")
    df = read_data()
    st.dataframe(df, width=800, height=400)

elif page == "Task Form":
    st.header("Tasks Form")

    # Form Schema
    form_schema = {
        "task_name": {"type": "text", "label": "Task Name", "required": True, "validation": {"min_length": 3, "max_length": 50, "message": "Task name must be between 3 and 50 characters."}},
        "project": {"type": "select", "label": "Project", "required": True, "options": ["Project A", "Project B", "Project C"], "validation": {"message": "Please select a project."}},
        "due_date": {"type": "date", "label": "Due Date", "required": True, "validation": {"message": "Due date must be a valid date in the future."}},
        "description": {"type": "textarea", "label": "Description", "required": False, "validation": {"max_length": 200, "message": "Description cannot exceed 200 characters."}}
    }

    # Read Task Data
    def read_tasks():
        data = sheet_tasks.get_all_records()
        return pd.DataFrame(data)

    # Add Task Data
    def add_task(row):
        sheet_tasks.append_row(row)

    # Render Task Form
    def render_form(schema):
        form_data = {}
        st.sidebar.header("Task Form")
        with st.sidebar.form(key="task_form"):
            for field, properties in schema.items():
                field_type = properties["type"]
                label = properties["label"]

                if field_type == "text":
                    form_data[field] = st.text_input(label)
                elif field_type == "select":
                    options = properties["options"]
                    form_data[field] = st.selectbox(label, options)
                elif field_type == "date":
                    form_data[field] = st.date_input(label, datetime.today())
                elif field_type == "textarea":
                    form_data[field] = st.text_area(label)
            
            submitted = st.form_submit_button("Submit")

        return form_data, submitted

    # Validate Task Form
    def validate_form(form_data, schema):
        errors = []
        for field, value in form_data.items():
            properties = schema[field]
            if properties.get("required") and not value:
                errors.append(f"{properties['label']} is required.")

            if properties["type"] == "text":
                min_len = properties["validation"].get("min_length", 0)
                max_len = properties["validation"].get("max_length", float('inf'))
                if not (min_len <= len(value) <= max_len):
                    errors.append(properties["validation"]["message"])
            elif properties["type"] == "date":
                if value < datetime.today().date():
                    errors.append(properties["validation"]["message"])

        return errors

    # Form Processing
    form_data, submitted = render_form(form_schema)

    if submitted:
        errors = validate_form(form_data, form_schema)
        if errors:
            for error in errors:
                st.sidebar.error(error)
        else:
            st.success("Task added successfully!")
            row = [form_data['task_name'], form_data['project'], form_data['due_date'].strftime('%Y-%m-%d'), form_data.get('description', "")]
            add_task(row)

    # Display Task Data
    st.header("Tasks Table")
    df_tasks = read_tasks()
    st.dataframe(df_tasks, width=900, height=600)
