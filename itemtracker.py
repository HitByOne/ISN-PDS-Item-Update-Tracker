import streamlit as st
import pandas as pd
from datetime import datetime
import re
from pymongo import MongoClient
import pymongo
import os

# Securely fetch the connection string
mongo_conn_str = os.getenv("MONGO_CONN_STR")
if not mongo_conn_str:
    st.error("MongoDB connection string not set in environment variables.")
    st.stop()
client = MongoClient(mongo_conn_str)
db = client['isn_change_log']
changes_collection = db.pdsitemchangelog

def log_changes_to_db(item_numbers, changes, name, item_status, notes):
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for item in item_numbers:
        document = {
            "item_number": item,
            "date": date,
            "entered_by": name,
            "item_status": item_status,
            **{change: 'Yes' if change in changes else 'No' for change in change_options},
            "notes": notes
        }
        try:
            changes_collection.insert_one(document)
        except pymongo.errors.OperationFailure as e:
            st.error(f"Failed to log changes: {str(e)}")
            return False
    return True

def fetch_changes(limit=100):
    return pd.DataFrame(list(changes_collection.find({}, {'_id': 0}).limit(limit)))

# Streamlit app layout
st.title("Item Change Tracker")

cols1 = st.columns((1,1))
names = ["McKenna Santucci", "Andrea Fritz", "Michael Harris", "Iris Kearney", "Tim Clarkson"]
name = cols1[0].selectbox("Select Your Name", sorted(names))
item_numbers_input = cols1[1].text_area("Enter Item Numbers (space, comma, or newline separated)", height=300)

item_status_options = ["Active", "Obsolete", "Reactivate", "Supersede", "New Item", "Promotional Item", "Quick Sale"]
item_status = st.selectbox("Select Item Status", item_status_options)

change_options = [
    "ISN Category", "Autocare Category", "Product Title", "Masterpack Descriptions",
    "Descriptive Paragraph", "Features and Benefits", "Marketing Brand Name",
    "Web Key Search Words", "Marketing Date", "Pack Size - MOQ", "Dimensions", "UPC",
    "Cost", "Country of Origin", "Harmonized Tariff Code (HTS)", "Hazardous Material Code",
    "LTL", "Cartonize", "Guaranteed Return", "Warranty Policy", "Is Repairable",
    "Prop 65", "DOT Regulation", "Lithium", "UN Number", "Price Group", "Inventory Group",
    "Inventory Category (Prefix)", "Drop Ship Only", "Stocking", "Supplier Review", "Image", "No Updates"
]
changes = st.multiselect("Item Updates", change_options)

notes = st.text_area("Enter Additional Notes", height=150)

if st.button("Log Changes"):
    # Updated regex to split based on commas, spaces, or newlines and include more complex item number patterns
    item_numbers = re.split(r'\s*[,;\s]\s*', item_numbers_input.strip())
    # Updated validation to accept alphanumeric characters and those starting with specific prefixes like 'MLW'
    item_numbers = [item.strip() for item in item_numbers if re.match(r'^MLW\d+|\d+|[A-Za-z0-9]+$', item)]
    if item_numbers and changes and name:
        if log_changes_to_db(item_numbers, changes, name, item_status, notes):
            st.success("Changes have been logged successfully.")
            df = fetch_changes()
            st.subheader("Updated Change Log")
            st.dataframe(df)
        else:
            st.error("Failed to log changes. Please check your input.")
    else:
        st.error("Please ensure all required fields are filled out.")
