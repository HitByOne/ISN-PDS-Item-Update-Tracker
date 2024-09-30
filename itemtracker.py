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

cols1 = st.columns((1, 1))
names = ["McKenna Santucci", "Andrea Fritz", "Michael Harris", "Iris Kearney", "Tim Clarkson"]
name = cols1[0].selectbox("Select Your Name", sorted(names))

# New Requestor input
requestor = cols1[1].text_input("Requestor")

item_numbers_input = st.text_area("Enter Item Numbers (space, comma, or newline separated)", height=300)

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
    item_numbers_input = item_numbers_input.strip()
    # Directly use the input without regex validation
    item_numbers = re.split(r'\s*[,;\s]\s*', item_numbers_input)

    # Strip any whitespace from each item
    item_numbers = [item.strip() for item in item_numbers if item.strip()]

    # Input validation
    if not item_numbers:
        st.error("No item numbers were provided. Please enter at least one item number.")
    elif not changes:
        st.error("Please select at least one change option.")
    elif not name:
        st.error("Please select your name.")
    elif not requestor:
        st.error("Please enter the Requestor's name.")
    else:
        # Log the changes to the database
        if log_changes_to_db(item_numbers, changes, name, item_status, notes):
            st.success("Changes have been logged successfully.")
            df = fetch_changes()
            st.subheader("Updated Change Log")
            st.dataframe(df)
        else:
            st.error("Failed to log changes. Please check your input.")

