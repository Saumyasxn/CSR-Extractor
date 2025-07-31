import pandas as pd
import os

# EXCEL_FILE = "education_csr_data.xlsx"

# def save_csr_data(data_dict):
#     new_data = pd.DataFrame([data_dict])

#     if os.path.exists(EXCEL_FILE):
#         try:
#             existing_data = pd.read_excel(EXCEL_FILE)
#             updated_data = pd.concat([existing_data, new_data], ignore_index=True)
#         except Exception as e:
#             print("Error reading Excel file:", e)
#             return
#     else:
#         updated_data = new_data

#     try:
#         updated_data.to_excel(EXCEL_FILE, index=False)
#         print("Data successfully written to Excel.")
#     except Exception as e:
#         print("Error writing to Excel:", e)

EXCEL_FILE = "education_csr_data.xlsx"

def save_csr_data(data_dict):
    # ✅ Support both single dict and list of dicts
    new_data = pd.DataFrame(data_dict if isinstance(data_dict, list) else [data_dict])

    if os.path.exists(EXCEL_FILE):
        try:
            existing_data = pd.read_excel(EXCEL_FILE)
            updated_data = pd.concat([existing_data, new_data], ignore_index=True)
        except Exception as e:
            print("Error reading Excel file:", e)
            return
    else:
        updated_data = new_data

    try:
        updated_data.to_excel(EXCEL_FILE, index=False)
        print("Data successfully written to Excel.")
    except Exception as e:
        print("Error writing to Excel:", e)
