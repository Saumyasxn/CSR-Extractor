from flask import Flask, render_template, request, jsonify, send_file
from data_extractor import run_extraction
from werkzeug.utils import secure_filename
import os
import pandas as pd

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
excel_path = "extracted_data.xlsx"

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/extract', methods=['POST'])
# def extract_data():
#     try:
#         # Check if a file is uploaded
#         file = request.files.get('pdfFile')
#         url = request.form.get('reportUrl', '').strip()

#         if file and file.filename.endswith('.pdf'):
#             filename = secure_filename(file.filename)
#             file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
#             file.save(file_path)
#             result = run_extraction(file_path, 'pdf')
#         elif url.startswith("http://") or url.startswith("https://"):
#             result = run_extraction(url, 'web')
#         else:
#             return jsonify({"status": "error", "message": "Invalid input"}), 400

#         if not result:
#             return jsonify({"status": "error", "message": "No data extracted"}), 200

#         # Save to Excel
#         df = pd.DataFrame([result])
#         if os.path.exists(excel_path):
#             df_existing = pd.read_excel(excel_path)
#             df_combined = pd.concat([df_existing, df], ignore_index=True)
#         else:
#             df_combined = df
#         df_combined.to_excel(excel_path, index=False)

#         # Reformat for frontend
#         formatted = {
#             "company": result.get("Company Name", ""),
#             "hq": result.get("Company HQ"), 
#             "year": result.get("Fiscal Year", ""),
#             "budget": result.get("CSR Budget", ""),
#             "theme": result.get("CSR Theme", ""),
#             "eduBudget": result.get("Budget for Education", ""),
#             "beneficiaries": result.get("No. of Beneficiaries", ""),
#             "type": result.get("Type of Beneficiaries", ""),
#             "literacy": result.get("Literacy Rate", ""),
#             "intervention": result.get("Type of Intervention", ""),
#             "projects": result.get("Projects", ""),
#             "location": result.get("Location Covered", ""),
#             "partners": result.get("Partner Organization", ""),
#             "scheme": result.get("Govt. Schemes", ""),
#             "outcome": result.get("Outcomes", "")
#         }

#         return jsonify({"status": "success", "data": [formatted]})
    
#     except Exception as e:
#         print(f"❌ Server Error: {e}")
#         return jsonify({"status": "error", "message": "Internal server error"}), 500

def extract_data():
    try:
        uploaded_files = request.files.getlist('pdfFile')  # Allow multiple PDFs
        url = request.form.get('reportUrl', '').strip()

        results = []

        if uploaded_files and all(f.filename.endswith('.pdf') for f in uploaded_files):
            for file in uploaded_files:
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)

                result = run_extraction(file_path, 'pdf')
                if result:
                    results.append(result)

        elif url.startswith("http://") or url.startswith("https://"):
            result = run_extraction(url, 'web')
            if result:
                results.append(result)

        else:
            return jsonify({"status": "error", "message": "Invalid input"}), 400

        if not results:
            return jsonify({"status": "error", "message": "No data extracted"}), 200

        # Save to Excel
        df = pd.DataFrame(results)
        if os.path.exists(excel_path):
            df_existing = pd.read_excel(excel_path)
            df_combined = pd.concat([df_existing, df], ignore_index=True)
        else:
            df_combined = df
        df_combined.to_excel(excel_path, index=False)

        # Format for frontend
        formatted = []
        for result in results:
            formatted.append({
                "company": result.get("Company Name", ""),
                "hq": result.get("Company HQ"),
                "year": result.get("Fiscal Year", ""),
                "budget": result.get("CSR Budget", ""),
                "theme": result.get("CSR Theme", ""),
                "eduBudget": result.get("Budget for Education", ""),
                "beneficiaries": result.get("No. of Beneficiaries", ""),
                "type": result.get("Type of Beneficiaries", ""),
                "literacy": result.get("Literacy Rate", ""),
                "intervention": result.get("Type of Intervention", ""),
                "projects": result.get("Projects", ""),
                "location": result.get("Location Covered", ""),
                "partners": result.get("Partner Organization", ""),
                "scheme": result.get("Govt. Schemes", ""),
                "outcome": result.get("Outcomes", "")
            })

        return jsonify({"status": "success", "data": formatted})

    except Exception as e:
        print(f"❌ Server Error: {e}")
        return jsonify({"status": "error", "message": "Internal server error"}), 500


@app.route('/download-excel')
def download_excel():
    if os.path.exists(excel_path):
        return send_file(excel_path, as_attachment=True)
    return "Excel file not found", 404


if __name__ == '__main__':
    app.run(debug=True)
