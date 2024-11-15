import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from google.oauth2 import service_account

# Must be the first Streamlit command
st.set_page_config(page_title="Interest Inventory Checklist", layout="wide")

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
    'R': """REALISTIC
• Likes to work with animals, tools, or machines; generally avoids social activities like teaching, healing, and informing others
• Has good skills in working with tools, mechanical or electrical drawings, machines, or plants and animals
• Values practical things you can see, touch, and use like plants and animals, tools, equipment, or machines
• Sees self as practical, mechanical, and realistic""",
    
    'I': """INVESTIGATIVE
• Likes to study and solve math or science problems; generally avoids leading, selling, or persuading people
• Is good at understanding and solving science and math problems
• Values science
• Sees self as precise, scientific, and intellectual""",
    
    'A': """ARTISTIC
• Likes to do creative activities like art, drama, crafts, dance, music, or creative writing; generally avoids highly ordered or repetitive activities
• Has good artistic abilities in creative writing, drama, crafts, music, or art
• Values the creative arts like drama, music, art, or the works of creative writers
• Sees self as expressive, original, and independent""",
    
    'S': """SOCIAL
• Likes to do things to help people like teaching, nursing, or giving first aid, providing information; generally avoids using machines, tools, or animals to achieve a goal
• Is good at teaching, counseling, nursing, or giving information
• Values helping people and solving social problems
• Sees self as helpful, friendly, and trustworthy""",
    
    'E': """ENTERPRISING
• Likes to lead and persuade people, and to sell things and ideas; generally avoids activities that require careful observation and scientific, analytical thinking
• Is good at leading people and selling things or ideas
• Values success in politics, leadership, or business
• Sees self as energetic, ambitious, and sociable""",
    
    'C': """CONVENTIONAL
• Likes to work with numbers, records, or machines in a set, orderly way; generally avoids ambiguous, unstructured activities
• Is good at working with written records and numbers in a systematic, orderly way
• Values success in business
• Sees self as orderly, and good at following a set plan"""
}

def main():
    st.title("Interest Inventory Checklist")
    st.write("Rate each activity based on how well it describes you:")
    
    # Display rating scale explanation
    with st.expander("Rating Scale Guide"):
        for k, v in RATING_SCALE.items():
            st.write(f"{k}: {v}")
    
    # Initialize session state for storing responses
    if 'responses' not in st.session_state:
        st.session_state.responses = {}

    # Create form
    with st.form("interest_inventory"):
        # Personal information
        st.subheader("Personal Information")
        name = st.text_input("Name")
        email = st.text_input("Email")
        
        st.subheader("Rate Your Interests")
        st.write("Please rate each activity from 1 to 6 based on how well it describes you.")
        
        # Create questions grid
        for row in range(1, 7):
            st.write(f"### Item {row}")
            
            # Create a container for better spacing
            container = st.container()
            cols = container.columns(6)
            
            for idx, (category, question) in enumerate(QUESTIONS[row].items()):
                with cols[idx]:
                    key = f"{category}_{row}"
                    st.write(question)
                    # Replace slider with number input
                    value = st.number_input(
                        f"Rating for {question}",
                        min_value=1,
                        max_value=6,
                        value=1,
                        key=key,
                        help="Enter a value between 1 and 6",
                        label_visibility="collapsed"
                    )
                    st.session_state.responses[key] = value
        
        # Add a note about valid ratings
        st.info("Please ensure all ratings are between 1 and 6.")
        
        submitted = st.form_submit_button("Submit")
        
        if submitted:
            # Validate inputs
            if not name or not email:
                st.error("Please fill in your name and email before submitting.")
                return
            
            # Validate all responses are within range
            invalid_responses = {k: v for k, v in st.session_state.responses.items() if v < 1 or v > 6}
            if invalid_responses:
                st.error("Please ensure all ratings are between 1 and 6.")
                return
                
            # Calculate totals
            totals = {'R': 0, 'A': 0, 'S': 0, 'I': 0, 'C': 0, 'E': 0}
            for key, value in st.session_state.responses.items():
                category = key.split('_')[0]
                totals[category] += value
            
            # Display results
            st.success("Form submitted successfully!")
            st.subheader("Your Results")
            
            # Create results visualization
            results_df = pd.DataFrame({
                'Category': list(totals.keys()),
                'Score': list(totals.values())
            })
            
            # Sort results by score in descending order
            results_df = results_df.sort_values('Score', ascending=False)
            
            # Display bar chart
            st.bar_chart(results_df.set_index('Category'))
            
            # Display scores in a table
            st.write("Your scores by category:")
            st.dataframe(results_df.style.highlight_max(subset=['Score']))
            
            # Display top 3 categories
            st.subheader("Your Top 3 Categories")
            top_3 = results_df.head(3)
            for _, row in top_3.iterrows():
                with st.expander(f"{row['Category']} - Score: {row['Score']}"):
                    st.write(DESCRIPTIONS[row['Category']])
            
            # Display remaining categories
            st.subheader("Other Categories")
            for _, row in results_df.tail(3).iterrows():
                with st.expander(f"{row['Category']} - Score: {row['Score']}"):
                    st.write(DESCRIPTIONS[row['Category']])
            
            # Here you would add the Google Forms integration
            try:
                # Add your Google Forms submission code here
                # You'll need to set up Google Forms API credentials
                st.success("Results have been submitted to Google Forms!")
            except Exception as e:
                st.error(f"Error submitting to Google Forms: {str(e)}")

if __name__ == "__main__":
    main()