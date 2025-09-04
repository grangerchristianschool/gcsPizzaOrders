import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
import json
import os, numpy as np
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, PageBreak
from reportlab.lib import colors
from io import BytesIO

# Assuming convert_df_to_csv is defined elsewhere; if not, here's a simple version
def convert_df_to_csv(df):
    return df.to_csv(index=False).encode('utf-8')

def create_pdf(orders_by_grade, date_selection):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []

    # Table style for all grades
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ])

    for grade, df in orders_by_grade.items():
        # Prepare data for the table
        data = [df.columns.tolist()] + df.values.tolist()
        table = Table(data)
        table.setStyle(table_style)  # Apply style after table creation
        
        # Create title table with inline style (corrected syntax)
        title_data = [[f"{grade} - Orders for {date_selection}"]]
        title_table = Table(title_data)
        title_table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 14),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 20)
        ]))
        
        # Add title and table to PDF
        elements.append(title_table)
        elements.append(table)
        elements.append(PageBreak())

    doc.build(elements)
    buffer.seek(0)
    return buffer
###

base_dir = os.path.dirname(__file__)
file_path = os.path.join(base_dir, 'Files')
logo = "{}/gcs_logo_transparent.png".format(file_path)

pizza_pricing = {1: 3, 2: 5, 3: 8, 4: 10, 5: 13, 
                6:16,7:18, 8: 20, 9: 24, 10: 26}

def loadOrderSheetLocal():
    ordersheet = pd.read_csv(f'{file_path}/sample_data.csv')
    return(ordersheet)

def convert_df_to_csv(df):
    return df.to_csv(index=False).encode('utf-8')


# Page configuration
st.set_page_config(
    page_title="Google Sheets to DataFrame",
    page_icon="🍕",
    layout="wide"
)

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
    headcol1, headcol2, headcol3 = st.columns([1,3,1])
    with headcol1:
        st.image(logo, width=175)
    with headcol2:
        st.markdown("<h1><center>🍕 GCS Pizza Order Tracker 🍕</center></h1>",unsafe_allow_html=True)
    with headcol3:
        st.image(logo, width=175)
    
    sheet_id = '1alsiI627AS_fQPTJ6BrgCElAIGBE-T-GU2XKIvo0GJk'
    worksheet_name = 'Form Responses 1'

    ### CHANGE FOR TESTING LOCALLY ###
    ordersheet = load_orders(sheet_id, worksheet_name)
    ordersheet['A La Cart'] = np.where(ordersheet['A La Cart']=='','x',ordersheet['A La Cart'])
    ordersheet['Slices of Cheese'] = ordersheet['Slices of Cheese'].fillna(0)
    ordersheet['Slices of Cheese'] = np.where(ordersheet['Slices of Cheese']=='',0,ordersheet['Slices of Cheese'])
    ordersheet['Slices of Pepperoni'] = ordersheet['Slices of Pepperoni'].fillna(0)
    ordersheet['Slices of Pepperoni'] = np.where(ordersheet['Slices of Pepperoni']=='',0,ordersheet['Slices of Pepperoni'])
    ordersheet['Slices of Sausage'] = ordersheet['Slices of Sausage'].fillna(0)
    ordersheet['Slices of Sausage'] = np.where(ordersheet['Slices of Sausage']=='',0,ordersheet['Slices of Sausage'])

    ordersheet['Slices of Cheese'] = ordersheet['Slices of Cheese'].astype(int)
    ordersheet['Slices of Pepperoni'] = ordersheet['Slices of Pepperoni'].astype(int)
    ordersheet['Slices of Sausage'] = ordersheet['Slices of Sausage'].astype(int)
        
    ###################################
    
    #ordersheet = loadOrderSheetLocal()
    
    ordersheet['Confirm Order Date'] = pd.to_datetime(ordersheet['Confirm Order Date'])
    ordersheet['Confirm Order Date'] = ordersheet['Confirm Order Date'].dt.date
    ordersheet = ordersheet.sort_values(by='Confirm Order Date',ascending=False)
    ordersheet = ordersheet.fillna(0)

    all_dates = list(ordersheet['Confirm Order Date'].unique())
    date_selection = st.selectbox('Orders For', all_dates)

    maincol1, maincol2 = st.columns([1.5,1])

    with maincol1: 
        
        week_orders = ordersheet[ordersheet['Confirm Order Date']==date_selection]

        week_orders['A La Cart'] = np.where(week_orders['Meal Deal?']=='Yes',0,week_orders['A La Cart'])
        week_orders['Total'] = week_orders['Slices of Cheese']+week_orders['Slices of Pepperoni']+week_orders['Slices of Sausage']
        week_orders['Pizza $'] = week_orders['Total'].map(pizza_pricing)
        week_orders['Meal Deal $'] = np.where(week_orders['Meal Deal?']=='Yes', 3, 0)
        week_orders['A La Cart'] = week_orders['A La Cart'].fillna('x')
        week_orders['A La Cart'] = week_orders['A La Cart'].astype(str)
        week_orders['Cart $'] = week_orders['A La Cart'].str.count('\$')
        week_orders['Cart $'] = week_orders['Cart $'].fillna(0)
        week_orders['Total $'] = week_orders['Pizza $']+week_orders['Meal Deal $']+week_orders['Cart $']
        parent_owed = week_orders.groupby(['Parent Name','Parent Email','Confirm Order Date'],as_index=False)['Total $'].sum()
        parent_owed = parent_owed[parent_owed['Total $']>0].sort_values(by='Parent Email')
        parent_owed.columns=['Parent','Email','Date','Owes $']

        # payment methods
        pay_methods = ordersheet[['Parent Name','Parent Email','How Will You Pay?']]
        pay_methods.columns=['Parent','Email','Pay Method Raw']
        pay_methods['Pay Method'] = np.where(pay_methods['Pay Method Raw'].str.contains('Cash'), 'Cash', 
                                             np.where(pay_methods['Pay Method Raw'].str.contains('Credit'), 'Credit', 
                                                      np.where(pay_methods['Pay Method Raw'].str.contains('Check'), 'Check', '0')))
        
        pay_methods = pay_methods[['Parent','Email','Pay Method']]
        st.markdown("<h2>Money Owed Summary</h2>", unsafe_allow_html=True)

        parent_owed = pd.merge(parent_owed, pay_methods, how='left', on=['Parent','Email'])
        parent_owed_nogroup = parent_owed.copy()
        parent_owed = parent_owed_nogroup.groupby(['Parent','Email','Date','Pay Method'], as_index=False)['Owes $'].sum()
        
        if len(parent_owed)<=10:
            st.dataframe(parent_owed, hide_index=True, width=575)
        else:
            st.dataframe(parent_owed, hide_index=True, height=570,width=575)

        file_name = 'paymentsowed.csv'#st.text_input("Download Data as CSV:", value="projdata.csv")
        #@st.cache_data
        #def convert_df_to_csv(df):
            #return df.to_csv(index=False).encode('utf-8')

        csv = convert_df_to_csv(parent_owed)
        st.download_button(label="Download CSV", data=csv, file_name=file_name, mime='text/csv')

        st.markdown("<h3>Staff Orders</h3>",unsafe_allow_html=True)
        staff_orders = ordersheet[ordersheet['Grade']=='Staff']
        st.write(staff_orders.columns)
        #[['Parent Name','Confirm Order Date','Slices of Cheese','Slices of Pepperoni','Slices of Sausage','Meal Deal','A La Cart','How Will You Pay?']]
        #staff_orders.columns=['Person','Date','Cheese','Pepperoni','Sausage','Meal?','Cart','Payment']
        st.dataframe(staff_orders,hide_index=True)


    with maincol2:
        st.markdown("<h2>Pizza Order Info</h2>",unsafe_allow_html=True)
        pizzas_needed = week_orders[['Slices of Cheese','Slices of Pepperoni','Slices of Sausage']].sum().reset_index()
        pizzas_needed.columns=['Type','Slices Ordered']
        pizzas_needed['Type'] = pizzas_needed['Type'].str.replace('Slices of ','')
        pizzas_needed['Pizzas Needed'] = np.ceil(pizzas_needed['Slices Ordered']/8)
        st.dataframe(pizzas_needed, hide_index=True)
    
        st.markdown("<h2>Download Orders by Grade</h2>", unsafe_allow_html=True)

        week_orders = ordersheet[ordersheet['Confirm Order Date'] == date_selection]
        
        grades = {'K': 'Kindergarten', '1st': '1st Grade', '2nd': '2nd Grade', '3rd': '3rd Grade',
                '4th': '4th Grade', '5th': '5th Grade', '6th': '6th Grade', '7th': '7th Grade',
                '8th': '8th Grade', '9th': '9th Grade', '10th': '10th Grade', '11th': '11th Grade',
                '12th': '12th Grade'}
        columns_to_select = ['Confirm Order Date', 'Student Name', 'Slices of Cheese', 
                            'Slices of Pepperoni', 'Slices of Sausage', 'Meal Deal?', 'A La Cart']
        display_columns = ['Date', 'Student', 'Cheese', 'Pepp', 'Sausage', 'Meal', 'A La Cart']
        
        orders_by_grade = {}
        
        for grade, display_name in grades.items():
            orders_grade = week_orders[week_orders['Grade'] == grade][columns_to_select]
            orders_grade.columns = display_columns
            orders_by_grade[display_name] = orders_grade
        
        pdf_buffer = create_pdf(orders_by_grade, date_selection)
        st.download_button(
            label="Download PDF",
            data=pdf_buffer,
            file_name=f"Orders_{date_selection}.pdf",
            mime="application/pdf"
        )

    st.markdown("<hr>", unsafe_allow_html=True)
    
    show_orders = st.checkbox('Show All Orders')
    if show_orders:
        parent_names = list(ordersheet['Parent Name'].unique())
        parent_names = ['All'] + parent_names
        student_names = list(ordersheet['Student Name'].unique())
        student_names = ['All'] + student_names
        all_dates = list(ordersheet['Confirm Order Date'].unique())
        all_dates = ['All'] + all_dates
        
        a_col1, a_col2, a_col3, a_col4, a_col5 = st.columns([1,1,1,1,1])
        with a_col2:
            date_selection = st.selectbox('Select Date to View', all_dates)
        with a_col3:
            parent_selection = st.selectbox('Search by Parent', parent_names)
        with a_col4:
            student_selection = st.selectbox('Search by Student', student_names)
        
        # Create a copy of the DataFrame
        show_orders = ordersheet.copy()
        
        # Apply filters based on selections
        if date_selection != 'All':
            show_orders = show_orders[show_orders['Confirm Order Date'] == date_selection]
        if parent_selection != 'All':
            show_orders = show_orders[show_orders['Parent Name'] == parent_selection]
        if student_selection != 'All':
            show_orders = show_orders[show_orders['Student Name'] == student_selection]
        
        # Drop Timestamp column if it exists
        show_orders = show_orders.drop(['Timestamp'], axis=1, errors='ignore')
        
        # Display the filtered DataFrame
        st.dataframe(show_orders, hide_index=True)

if __name__ == "__main__":
    main()
