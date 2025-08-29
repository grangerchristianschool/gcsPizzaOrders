import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
import json
import os

base_dir = os.path.dirname(__file__)
file_path = os.path.join(base_dir, 'Files')
#hitterproj = pd.read_csv(f'{file_path}/hitter_proj_withids.csv')
with open(f'{file_path}/service_account.json') as f:
    SERVICE_ACCOUNT_CREDS = json.load(f)

# Page configuration
st.set_page_config(
    page_title="Google Sheets to DataFrame",
    page_icon="📊",
    layout="wide"
)

@st.cache_resource
def get_gspread_client_local():
    try:
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_CREDS, scopes=scope)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Error authenticating with Google Sheets: {str(e)}")
        return None
    
@st.cache_resource
def get_gspread_client():
    try:
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Error authenticating with Google Sheets: {str(e)}")
        return None

def load_orders(sheet_id, worksheet_name='Form Responses 1'):
    gc = get_gspread_client()
    sheet = gc.open_by_key(sheet_id)
    worksheet = sheet.worksheet(worksheet_name)

    data = worksheet.get_all_values()
    if not data or len(data) == 0:
        st.warning("No data found in the worksheet.")
        return None
        
    df = pd.DataFrame(data[1:], columns=data[0])
    return(df)

def main():
    st.title("📊 GCS Pizza Order Tool")
    sheet_id = '1alsiI627AS_fQPTJ6BrgCElAIGBE-T-GU2XKIvo0GJk'
    worksheet_name = 'Form Responses 1'
    ordersheet = load_orders(sheet_id, worksheet_name)

    st.dataframe(ordersheet)

if __name__ == "__main__":
    main()