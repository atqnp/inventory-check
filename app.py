import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import json
import altair as alt

# Must be the first Streamlit command
st.set_page_config(page_title="Interest Inventory Check")

# Constants for the rating scale
RATING_SCALE = {
    1: "Memang bukan saya",
    2: "Bukan saya",
    3: "Mungkin bukan saya",
    4: "Mungkin saya",
    5: "Saya",
    6: "Memang saya"
}

# Questions matrix
QUESTIONS = {
    1: {
        'R': "Bersukan di padang",
        'A': "Bermain muzik",
        'S': "Memberi nasihat kepada orang lain",
        'I': "Menyelesaikan soalan matematik",
        'C': "Menyusun bantal selepas bangun tidur",
        'E': "Minum kopi bersama rakan"
    },
    2: {
        'R': "Memperbaiki alatan yang rosak",
        'A': "Melukis gambar pemandangan",
        'S': "Melakukan tugas sukarelawan",
        'I': "Menyertai pertandingan chess",
        'C': "Mengumpulkan nama peserta pertandingan",
        'E': "Menyertai majlis perwakilan pelajar"
    },
    3: {
        'R': "Menjadi jawatankuasa teknikal hari guru",
        'A': "Membuat persembahan drama atau nyanyian",
        'S': "Merancang aktiviti kelas",
        'I': "Memberikan idea dan pandangan",
        'C': "Menjaga kewangan keluar dan masuk",
        'E': "Mengetuai jawatankuasa sempena hari guru"
    },
    4: {
        'R': "Membina model kereta dengan lego",
        'A': "Merakam video sempena hari guru",
        'S': "Menyertai pembimbing rakan sebaya",
        'I': "Melakukan ujikaji / eksperimen",
        'C': "Mengambil minit mesyuarat",
        'E': "Melakukan promosi"
    },
    5: {
        'R': "Bercucuk tanam sekitar sekolah",
        'A': "Menghias kelas",
        'S': "Bersama dalam program gotong royong",
        'I': "Mengira bilangan pelajar yang tidak hadir",
        'C': "Beratur dalam barisan seperti yang di arahkan",
        'E': "Mengajak rakan dalam aktiviti kelas"
    },
    6: {
        'R': "Belajar cara mencabut tombol pintu di Youtube",
        'A': "Menonton persembahan seni dan budaya",
        'S': "Mengajarkan ilmu baharu kepada rakan",
        'I': "Membuat peta minda",
        'C': "Bertindak berdasarkan maklumat yang diterima",
        'E': "Mencuba perkara baru"
    }
}

# Descriptions for each category
DESCRIPTIONS = {
    'R': "REALISTIC: Likes to work with animals, tools, or machines. <br> \
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Generally avoids social activities like teaching, healing, and informing others. <br> \
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Has good skills in working with tools, mechanical or electrical drawings, machines, or plants and animals. <br> \
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Values practical things you can see, touch, and use like plants and animals, tools, equipment, or machines. <br>\
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Sees self as practical, mechanical, and realistic.",
    'A': "ARTISTIC: Likes to do creative activities like art, drama, crafts, dance, music, or creative writing. <br> \
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Generally avoids highly ordered or repetitive activities. <br> \
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Has good artistic abilities -- in creative writing, drama, crafts, music, or art. <br> \
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Values the creative arts -- like drama, music, art, or the works of creative writers. <br> \
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Sees self as expressive, original, and independent.",
    'S': "SOCIAL: Likes to do things to help people-- like, teaching, nursing, or giving first aid, providing information. <br> \
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Generally avoids using machines, tools, or animals to achieve a goal. <br> \
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Is good at teaching, counseling, nursing, or giving information. <br> \
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Values helping people and solving social problems. <br> \
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Sees self as helpful, friendly, and trustworthy.",
    'I': "INVESTIGATIVE: Likes to study and solve math or science problems. <br> \
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Generally avoids leading, selling, or persuading people. <br> \
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Is good at understanding and solving science and math problems. <br> \
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Values science. <br> \
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Sees self as precise, scientific, and intellectual.",
    'C': "CONVENTIONAL: Likes to work with numbers, records, or machines in a set, orderly way. <br> \
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Generally avoids ambiguous, unstructured activities. <br> \
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Is good at working with written records and numbers in a systematic, orderly way. <br> \
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Values success in business. <br> \
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Sees self as orderly, and good at following a set plan.",
    'E': "ENTERPRISING: Likes to lead and persuade people, and to sell things and ideas. <br> \
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Generally avoids activities that require careful observation and scientific, analytical thinking. <br> \
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Is good at leading people and selling things or ideas. <br> \
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Values success in politics, leadership, or business. <br> \
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Sees self as energetic, ambitious, and sociable."

}

def init_google_sheets():
    """Initialize Google Sheets connection"""
    try:
        # Create credentials from streamlit secrets
        credentials = {
            "type": "service_account",
            "project_id": st.secrets["gcp_service_account"]["project_id"],
            "private_key_id": st.secrets["gcp_service_account"]["private_key_id"],
            "private_key": st.secrets["gcp_service_account"]["private_key"],
            "client_email": st.secrets["gcp_service_account"]["client_email"],
            "client_id": st.secrets["gcp_service_account"]["client_id"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": st.secrets["gcp_service_account"]["client_x509_cert_url"]
        }
        
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        
        creds = Credentials.from_service_account_info(credentials, scopes=scopes)
        client = gspread.authorize(creds)
        
        # Open the Google Sheet
        sheet = client.open(st.secrets["gcp_service_account"]["sheet_name"]).sheet1
        return sheet
    except Exception as e:
        st.error(f"Error connecting to Google Sheets: {str(e)}")
        return None

def save_to_sheets(sheet, data):
    """Save form data to Google Sheets"""
    try:
        # If sheet is empty, add headers
        if len(sheet.get_all_values()) == 0:
            headers = [
                "Timestamp", "Name", "IPT",
                "R_Score", "I_Score", "A_Score", "S_Score", "E_Score", "C_Score",
                "Highest_Categories", "All_Responses"
            ]
            sheet.append_row(headers)
        
        # Prepare row data
        row_data = [
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            data["name"],
            data["ipt"],
            data["totals"]["R"],
            data["totals"]["A"],
            data["totals"]["S"],
            data["totals"]["I"],
            data["totals"]["C"],
            data["totals"]["E"],
            ", ".join(data["highest_categories"]),
            json.dumps(data["responses"])
        ]
        
        sheet.append_row(row_data)
        return True
    except Exception as e:
        st.error(f"Error saving to Google Sheets: {str(e)}")
        return False

def check_row_ratings(responses, row):
    """Check if ratings in a row use each number 1-6 exactly once"""
    row_ratings = []
    for category in ['R', 'A', 'S', 'I', 'C', 'E']:
        key = f"{category}_{row}"
        if key in responses:
            row_ratings.append(responses[key])
    return sorted(row_ratings) == [1, 2, 3, 4, 5, 6]

def main():
    st.title("Interest Inventory")
    st.write("Letakkan 'rating' (1-6) bagi setiap aktiviti yang menghuraikan diri anda:")
    
    # Initialize Google Sheets
    sheet = init_google_sheets()
    if sheet is None:
        st.error("Failed to connect to Google Sheets. Please check your configuration.")
        return
    
    # Display rating scale explanation
    with st.expander("Rating Scale Guide"):
        for k, v in RATING_SCALE.items():
            st.write(f"{k}: {v}")
        st.write("NOTE: Untuk setiap baris, Setiap 'rating' (1-6) harus digunakan sekali sahaja bagi setiap Item.")
    
    # Initialize session state for storing responses
    if 'responses' not in st.session_state:
        st.session_state.responses = {}

    # Create form
    with st.form("holland_inventory"):
        # Personal information
        st.subheader("Personal Information")
        name = st.text_input("Nama")
        ipt = st.text_input("IPT")
        
        st.subheader("Rate Your Interests")
        st.write("Letakkan 'rating' (1-6) bagi setiap aktiviti. Gunakan satu nombor sahaja bagi setiap Item.")
        
        # Create questions grid
        for row in range(1, 7):
            st.write(f"### Item {row}")
            container = st.container(border=True)
            
            # Add a note about rating distribution
            st.write("⚠️ Setiap 'rating' (1-6) harus digunakan sekali sahaja bagi setiap Item")
            
            cols = container.columns(6)
            
            # Create a row of selectboxes instead of number inputs
            for idx, (category, question) in enumerate(QUESTIONS[row].items()):
                with cols[idx]:
                    key = f"{category}_{row}"
                    st.write(question)
                    # Use selectbox instead of number_input for better UX
                    value = st.selectbox(
                        f"'Rating' untuk {question}",
                        options=list(range(1, 7)),
                        key=key,
                        help="Pilih 'rating' antara 1 hingga 6",
                        label_visibility="collapsed"
                    )
                    st.session_state.responses[key] = value
        
        submitted = st.form_submit_button("Submit")
        
        if submitted:
            # Validate inputs
            if not name or not ipt:
                st.error("Isikan nama dan IPT.")
                return
            
            # Validate rating distribution for each row
            invalid_rows = []
            for row in range(1, 7):
                if not check_row_ratings(st.session_state.responses, row):
                    invalid_rows.append(row)
            
            if invalid_rows:
                st.error(f"Semak 'rating' pada Item {', '.join(map(str, invalid_rows))}. " 
                        "Setiap Item mesti menggunakan 'rating' (1-6) sekali sahaja.")
                return
            
            # Calculate totals
            totals = {'R': 0, 'A': 0, 'S': 0, 'I': 0, 'C': 0, 'E': 0}
            for key, value in st.session_state.responses.items():
                category = key.split('_')[0]
                totals[category] += value
            
            # Determine the highest score(s)
            max_score = max(totals.values())
            highest_categories = [cat for cat, score in totals.items() if score == max_score]
            
            # Prepare data for Google Sheets
            form_data = {
                "name": name,
                "ipt": ipt,
                "totals": totals,
                "highest_categories": highest_categories,
                "responses": st.session_state.responses
            }
            
            # Save to Google Sheets
            if save_to_sheets(sheet, form_data):
                st.success("Form submitted successfully and saved to Google Sheets!")
            else:
                st.error("Form submitted but failed to save to Google Sheets.")
            
            # Display results
            st.subheader("Your Results")
            
            # Create results visualization
            results_df = pd.DataFrame({
                'Category': list(totals.keys()),
                'Score': list(totals.values())
            })

            results_df = results_df.sort_values(by='Score', ascending=False)
            
            # Display bar chart
            st.write(alt.Chart(results_df).mark_bar().encode(
                        x=alt.X('Score'),
                        y=alt.Y('Category', sort=list(results_df)),
                    ))
            
            # Display scores in a table with descriptions
            st.subheader("Detailed Interpretations")
            sorted_totals = sorted(totals.items(), key=lambda x: x[1], reverse=True)

            for category, score in sorted_totals:
                if score == max_score and category in highest_categories:
                    st.markdown(
                        f"<div style='padding:10px; background-color:#f1c232; border-radius:5px;'>"
                        f"<strong>{category} - Score: {score}</strong><br>{DESCRIPTIONS[category]}</div><br>",
                        unsafe_allow_html=True
                    )
                else:
                    with st.expander(f"{category} - Score: {score}"):
                        st.markdown(DESCRIPTIONS[category], unsafe_allow_html=True)

if __name__ == "__main__":
    main()
