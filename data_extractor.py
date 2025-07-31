import os, requests, fitz, pdfplumber, io, json, re
from excel import save_csr_data
from bs4 import BeautifulSoup
from PIL import Image
import pytesseract
from dotenv import load_dotenv
from openai import OpenAI 
#from anthropic import Anthropic

load_dotenv(dotenv_path=r"C:\Users\saumy\OneDrive - UPES\VS Code\csr_extractor\OPENROUTER_API_KEY.env")
api_key = os.getenv("OPENROUTER_API_KEY")


def ocr_from_bytes(image_bytes):
    try:
        img = Image.open(io.BytesIO(image_bytes))
        return pytesseract.image_to_string(img, lang='eng').strip()
    except:
        return ""

def extract_pdf_data(path):
    text = ""
    # Extract regular text
    with pdfplumber.open(path) as pdf:
        text = "\n".join(filter(None, [p.extract_text() for p in pdf.pages]))
    
    # Extract text from images using OCR
    doc = fitz.open(path)
    for i, page in enumerate(doc, 1):
        for j, img in enumerate(page.get_images(), 1):
            xref = img[0]
            base = doc.extract_image(xref)
            ocr_text = ocr_from_bytes(base['image'])
            if ocr_text.strip():
                text += f"\n[OCR - PDF Page {i} Image {j}]\n{ocr_text}\n"
    doc.close()
    return text

def extract_web_data(url):
    text = ""
    soup = BeautifulSoup(requests.get(url).content, "html.parser")
    text = soup.get_text("\n", strip=True)
    
    # Extract text from images using OCR
    for i, img in enumerate(soup.find_all("img"), 1):
        src = img.get("src")
        if src and not src.startswith("data:"):
            src = src if src.startswith("http") else f"https://{url.split('//')[-1].split('/')[0]}{src}"
            try:
                img_bytes = requests.get(src, timeout=5).content
                ocr_text = ocr_from_bytes(img_bytes)
                if ocr_text.strip():
                    text += f"\n[OCR - Web Image {i}]\n{ocr_text}\n"
            except:
                pass
    return text


def chunk_text(text, max_chars=400000, overlap=1000):
    chunks = []
    start = 0
    while start < len(text):
        end = start + max_chars
        chunks.append(text[start:end])
        start = end - overlap
    return chunks


def filter_education_csr(text):
    chunks = chunk_text(text)
    extracted_data = []

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY")
    )

    for i, chunk in enumerate(chunks):
        print(f"🔄 Processing chunk {i+1}/{len(chunks)}...")
        
        prompt = f"""You are an expert in analyzing CSR (Corporate Social Responsibility) reports.

From the following content, extract **only the Education-themed CSR data** and return it strictly in this JSON format:

{{
    "Company Name": "",
    "Company HQ": "",
    "Fiscal Year": "",
    "CSR Budget": "",
    "Budget for Education": "",
    "No. of Beneficiaries": "",
    "CSR Theme": "Education",
    "Projects": "",
    "Type of Beneficiaries": "",
    "Literacy Rate": "",
    "Type of Intervention": "",
    "Location Covered": "",
    "Partner Organization": "",
    "Govt. Schemes": "",
    "Outcomes": ""
}}

Fill in as many fields as you can based on the given text below. If a field is not available, leave it as an empty string.
Respond **only** with valid JSON, no explanation or markdown formatting. Do not wrap it in ```json.

--- TEXT START ---
{chunk}
--- TEXT END ---
"""

        try:
            response = client.chat.completions.create(
                model="deepseek/deepseek-r1-0528:free",
                messages=[
                    {"role": "system", "content": "You extract structured data from CSR documents."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                extra_headers={
                    "HTTP-Referer": "http://localhost",
                    "X-Title": "CSR Extractor"
                }
            )
            if response is None or response.choices is None:
                raise ValueError("API returned no choices")

            result = response.choices[0].message.content
            if result is None:
                raise ValueError("API returned no content.")

            try:
                parsed = json.loads(result)
                extracted_data.append(parsed)
            except:
                print(f"⚠️ Failed to parse chunk {i+1} as JSON. Saving raw.")
                extracted_data.append({"raw_output": result})

        except Exception as e:
            print(f"❌ Error in chunk {i+1}: {e}")
            extracted_data.append({"error": str(e)})
        # except Exception as e:
        #     print(f"⚠️ Failed to parse chunk {i+1} as JSON: {e}")
        #     print("🔍 Raw result:\n", result[:500])  # Print start of response
        #     extracted_data.append({"raw_output": result})

    return extracted_data

# def main():
#     choice = input("Enter 1 for PDF or 2 for Website: ").strip()
#     source = input("Enter PDF path or Website URL: ").strip()
#     text = (extract_pdf_data(source) if choice == '1' else extract_web_data(source)) if choice in ['1', '2'] else None
#     if text is None: 
#         print("Invalid choice!")
#         return

#     filtered_text = filter_education_csr(text)

#     # Clean and unify all parsed outputs
#     unified_data = []
#     for item in filtered_text:
#         if isinstance(item, dict) and "raw_output" in item:
#             try:
#         # Try to extract JSON string inside triple backticks
#                 match = re.search(r'\{[\s\S]*\}', item["raw_output"])
#                 if match:
#                     parsed = json.loads(match.group(0))
#                     unified_data.append(parsed)
#                 else:
#                     raise ValueError("No valid JSON found")
#             except Exception as e:
#                 print("⚠️ Couldn't parse raw_output into JSON:", e)
       

#     # ✅ Remove duplicates using set of JSON strings
#     unique_jsons = []
#     seen = set()

#     for obj in unified_data:
#         json_str = json.dumps(obj, sort_keys=True)  # sort_keys for consistent comparison
#         if json_str not in seen:
#             seen.add(json_str)
#             unique_jsons.append(obj)

#     # ✅ Save only the first unique JSON object
#     if unique_jsons:
#         with open("education_csr_output.txt", "w", encoding="utf-8") as f:
#             json.dump(unique_jsons[0], f, indent=2, ensure_ascii=False)
#         print("\n✅ Saved first unique JSON entry to education_csr_output.txt")
#     else:
#         print("❌ No unique entries to save.")




    # # ✅ Save as a single JSON array
    # with open("education_csr_output.txt", "w", encoding="utf-8") as f:
    #     json.dump(unique_jsons, f, indent=2, ensure_ascii=False)

    # print(f"\n✅ Saved {len(unique_jsons)} unique entries to education_csr_output.txt")

    # ✅Excel 
    with open('education_csr_output.txt', 'r', encoding='utf-8') as f:
    # Skip possible markdown code block markers
        lines = f.readlines()
        json_str = ''.join(line for line in lines if not line.strip().startswith('```'))
        extracted_data = json.loads(json_str)

    save_csr_data(extracted_data)


def main():
    choice = input("Enter 1 for PDF or 2 for Website: ").strip()

    if choice == '1':
        # ✅ Multiple PDFs
        pdf_paths = input("Enter PDF paths (comma-separated): ").strip().split(",")
        all_data = []

        for path in map(str.strip, pdf_paths):
            print(f"\n📄 Processing file: {path}")
            try:
                text = extract_pdf_data(path)
                filtered_text = filter_education_csr(text)

                for item in filtered_text:
                    if isinstance(item, dict) and "raw_output" in item:
                        try:
                            match = re.search(r'\{[\s\S]*\}', item["raw_output"])
                            if match:
                                parsed = json.loads(match.group(0))
                                all_data.append(parsed)
                        except Exception as e:
                            print("⚠️ Couldn't parse raw_output:", e)
                    elif isinstance(item, dict):
                        all_data.append(item)

            except Exception as e:
                print(f"❌ Failed to process {path}: {e}")

        # ✅ Deduplicate
        unique_data = []
        seen = set()
        for obj in all_data:
            json_str = json.dumps(obj, sort_keys=True)
            if json_str not in seen:
                seen.add(json_str)
                unique_data.append(obj)

        if unique_data:
            with open("education_csr_output.txt", "w", encoding="utf-8") as f:
                json.dump(unique_data, f, indent=2, ensure_ascii=False)
            print(f"\n✅ Saved {len(unique_data)} unique entries to education_csr_output.txt")

            # ✅ Save to Excel
            save_csr_data(unique_data)
        else:
            print("❌ No valid CSR data extracted.")

    elif choice == '2':
        # ✅ Single website
        url = input("Enter website URL: ").strip()
        text = extract_web_data(url)
        filtered_text = filter_education_csr(text)

        unified_data = []
        for item in filtered_text:
            if isinstance(item, dict) and "raw_output" in item:
                try:
                    parsed = json.loads(item["raw_output"])
                    unified_data.append(parsed)
                except:
                    pass
            elif isinstance(item, dict):
                unified_data.append(item)

        unique_data = []
        seen = set()
        for obj in unified_data:
            json_str = json.dumps(obj, sort_keys=True)
            if json_str not in seen:
                seen.add(json_str)
                unique_data.append(obj)

        if unique_data:
            with open("education_csr_output.txt", "w", encoding="utf-8") as f:
                json.dump(unique_data, f, indent=2, ensure_ascii=False)
            print("\n✅ Saved website data to education_csr_output.txt")
            save_csr_data(unique_data)
        else:
            print("❌ No unique entries to save.")
    else:
        print("❌ Invalid choice! Please enter 1 or 2.")


def run_extraction(source, source_type):
    text = extract_pdf_data(source) if source_type == 'pdf' else extract_web_data(source)
    filtered_data = filter_education_csr(text)

    unified_data = []
    for item in filtered_data:
        if isinstance(item, dict) and "raw_output" in item:
            try:
                parsed = json.loads(item["raw_output"])
                unified_data.append(parsed)
            except:
                pass
        elif isinstance(item, dict):
            unified_data.append(item)

    # Remove duplicates
    seen = set()
    unique_jsons = []
    for obj in unified_data:
        json_str = json.dumps(obj, sort_keys=True)
        if json_str not in seen:
            seen.add(json_str)
            unique_jsons.append(obj)

    # ✅ Return only the first one
    return unique_jsons[0] if unique_jsons else {}


if __name__ == "__main__":
    main()