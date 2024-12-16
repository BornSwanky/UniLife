import streamlit as st
from jamaibase import JamAI, protocol as p
from PIL import Image
from tempfile import NamedTemporaryFile
import streamlit.components.v1 as components
from streamlit_option_menu import option_menu

# Initialize JamAI Base client
jamai = JamAI(
    api_key="INSERT_API_KEY_HERE",
    project_id="INSERT_PROJECT_ID_HERE",
)


# Function to submit user data to JamAI Base
def submit_user_data(data):
    try:
        completion = jamai.add_table_rows(
            "action",
            p.RowAddRequest(
                table_id="student_details",  # Match your JamAI table ID
                data=[data],
                stream=False,
            )
        )
        return completion.rows is not None
    except Exception as e:
        st.error(f"❌ An error occurred: {e}")
        return False


# Function to upload and verify student card
def verify_student_card(signup_data):
    st.title("🎓 Upload Your Student Card for Verification")
    st.subheader("Please upload your student card to complete the verification process.")

    uploaded_file = st.file_uploader("Upload your Student Card (JPEG/PNG)", type=["jpg", "jpeg", "png"])

    if uploaded_file is not None:
        st.write("Filename:", uploaded_file.name)

        # Temporarily store the uploaded file
        with NamedTemporaryFile(delete=False, suffix=".jpeg") as temp_file:
            image = Image.open(uploaded_file)
            image = image.convert("RGB")
            image.save(temp_file, format="JPEG")
            temp_file_path = temp_file.name

        try:
            # Upload the file to JamAI
            upload_response = jamai.file.upload_file(temp_file_path)

            # Add file URI to the verification table (can be used for backend analysis later)
            completion = jamai.add_table_rows(
                "action",
                p.RowAddRequest(
                    table_id="student_verification",  # Match your verification table name
                    data=[{
                        "student_card_image": upload_response.uri,
                        "signup_email": signup_data["email"],
                        "signup_name": signup_data["full_name"],
                        "signup_university": signup_data["university_name"],
                    }],
                    stream=False,
                ),
            )

            # Display the uploaded image
            st.image(uploaded_file, caption="Uploaded Student Card", use_container_width=True)

            # Automatically make verification successful
            st.success("🎉 Verification Successful! Welcome to UniLife!")
            if st.button("Start Exploring"):
                st.session_state.page = "main_page"
        except Exception as e:
            st.error(f"❌ An error occurred: {e}")


# Events Page
def events_page(user_programme):
    try:
        # Fetch all rows from the table
        response = jamai.table.list_table_rows(
            table_type="action",  # Specify the table type (e.g., "action")
            table_id="personalized_events"
        )

        if not response.items:
            st.error("No events found.")
            return

        # Filter events based on the user's programme
        events = [
            {
                "event_title": item["event_title"]["value"],
                "event_description": item["event_description"]["value"],
                "event_date": item["event_date"]["value"],
                "event_time": item["event_time"]["value"],
                "event_location": item["event_location"]["value"],
                "state": item["state"]["value"],
                "event_format": item["event_format"]["value"],
                "tags": item["tags"]["value"],

            }
            for item in response.items
            if user_programme.lower() in item["target_programmes"]["value"].lower()
        ]

        if not events:
            st.error("No events found for your programme.")
            return

        # Initialize session state
        if "current_event" not in st.session_state:
            st.session_state.current_event = 0  # Start with the first event
        if "selected_event" not in st.session_state:
            st.session_state.selected_event = None  # Initially no event selected

        # Get the current event based on index
        current_event_index = st.session_state.current_event
        current_event = events[current_event_index]

        # Display the event title
        st.markdown(f"<h1 style='font-size: 40px; text-align: left;'>{current_event['event_title']}</h1>",
                    unsafe_allow_html=True)

        # Create side-by-side columns for "Yes" and "Next"
        col1, col2 = st.columns(2)

        with col1:  # Left column for "Yes" button
            if st.button("Yes", key="event_yes"):
                # Lock the selected event and navigate to the details page
                st.session_state.selected_event = current_event
                st.session_state.page = "event_details"

        with col2:  # Right column for "Next" button
            if st.button("Next", key="event_next"):
                # Advance to the next event
                st.session_state.current_event = (current_event_index + 1) % len(events)

        # Add space for layout
        st.markdown("<br>", unsafe_allow_html=True)

        # Directly set the page to "main_page" for the return button
        # Create three columns
        col1, col2, col3 = st.columns([1, 2, 1])  # Adjust the ratios for desired widths

        # Add the button in the middle column
        with col3:
            if st.button("Return", key="event_return"):
                st.session_state.page = "main_page"

    except Exception as e:
        st.error(f"An error occurred: {e}")


# Event Details Page
def event_details_page():
    selected_event = st.session_state.get("selected_event")
    if not selected_event:
        st.error("No event selected.")
        return

    # Display full details of the selected event
    st.markdown(f"<h1 style='font-size: 40px;'>{selected_event['event_title']}</h1>", unsafe_allow_html=True)
    st.markdown(
        f"""
        <div style="border: 1px solid #ddd; padding: 15px; border-radius: 10px; margin-bottom: 20px;">
            <p style='font-size: 20px;'>{selected_event['event_description']}</p>
            <p style='font-size: 20px;'>Date: {selected_event['event_date']}</p>
            <p style='font-size: 20px;'>Time: {selected_event['event_time']}</p>
            <p style='font-size: 20px;'>Location: {selected_event['event_location']}</p>
            <p style='font-size: 20px;'>State: {selected_event['state']}</p>
            <p style='font-size: 20px;'>Event Format: {selected_event['event_format']}</p>
            <p style='font-size: 20px;'>Tags: {selected_event['tags']}</p>
        """,
        unsafe_allow_html=True
    )

    if st.button("Return"):
        # Go back to the swiping interface
        st.session_state.page = "events"


# Competitions Page
def competitions_page(user_programme):
    try:

        # Fetch all rows from the table
        response = jamai.table.list_table_rows(
            table_type="action",  # Specify the table type
            table_id="personalized_competitions"
        )

        if not response.items:
            st.error("No competitions found.")
            return

        # Filter competitions based on the user's programme
        competitions = [
            {
                "competition_title": item["competition_title"]["value"],
                "competition_description": item["competition_description"]["value"],
                "competition_date": item["competition_date"]["value"],
                "competition_time": item["competition_time"]["value"],
                "competition_location": item["competition_location"]["value"],
                "state": item["state"]["value"],
                "tags": item["tags"]["value"],
            }
            for item in response.items
            if user_programme.lower() in item["target_programmes"]["value"].lower()
        ]

        if not competitions:
            st.error("No competitions found for your programme.")
            return

        # Initialize session state
        if "current_competition" not in st.session_state:
            st.session_state.current_competition = 0  # Start with the first competition
        if "selected_competition" not in st.session_state:
            st.session_state.selected_competition = None  # Initially no competition selected

        # Get the current competition based on index
        current_competition_index = st.session_state.current_competition
        current_competition = competitions[current_competition_index]

        # Display the competition title
        st.markdown(
            f"<h1 style='font-size: 40px;'>{current_competition['competition_title']}</h1>",
            unsafe_allow_html=True
        )

        # Navigation buttons with increased size
        col1, col2 = st.columns(2)

        with col1:
            if st.button("Yes", key="yes_button"):
                # Lock the selected competition and navigate to the details page
                st.session_state.selected_competition = current_competition
                st.session_state.page = "competition_details"

        with col2:
            if st.button("Next", key="next_button"):
                # Advance to the next competition
                st.session_state.current_competition = (current_competition_index + 1) % len(competitions)

        # Return button with increased size
        # Directly set the page to "main_page" for the return button
        # Create three columns
        col1, col2, col3 = st.columns([1, 2, 1])  # Adjust the ratios for desired widths

        # Add the button in the middle column
        with col3:
            if st.button("Return", key="event_return"):
                st.session_state.page = "main_page"

    except Exception as e:
        st.error(f"An error occurred: {e}")


# Competition Details Page
def competition_details_page():
    selected_competition = st.session_state.get("selected_competition")
    if not selected_competition:
        st.error("No competition selected.")
        return

        # Display full details of the selected competition
    st.markdown(
        f"<h1 style='font-size: 40px;'>{selected_competition['competition_title']}</h1>",
        unsafe_allow_html=True
    )

    # Use the same structure as event_details_page
    st.markdown(
        f"""  
        <div style="border: 1px solid #ddd; padding: 15px; border-radius: 10px; margin-bottom: 20px;">  
            <p style='font-size: 20px;'>{selected_competition['competition_description']}</p>  
            <p style='font-size: 20px;'>Date: {selected_competition['competition_date']}</p>  
            <p style='font-size: 20px;'>Time: {selected_competition['competition_time']}</p>  
            <p style='font-size: 20px;'>Location: {selected_competition['competition_location']}</p>  
            <p style='font-size: 20px;'>State: {selected_competition['state']}</p>  
            <p style='font-size: 20px;'>Tags: {selected_competition.get('tags', 'No tags available')}</p>  
        </div>  
        """,
        unsafe_allow_html=True
    )

    if st.button("Return"):
        # Go back to the swiping interface
        st.session_state.page = "competitions"

        # Deals Page


def deals_page():
    try:
        # Fetch all rows from the table
        response = jamai.table.list_table_rows(
            table_type="action",  # Specify the table type
            table_id="personalized_deals"
        )

        if not response.items:
            st.error("No deals available.")
            return

        # Iterate through the deals and display them
        for deal in response.items:
            deal_title = deal["deal_title"]["value"]
            deal_description = deal["deal_description"]["value"]
            deal_expiry_date = deal["deal_expiry_date"]["value"]
            deal_location = deal["deal_location"]["value"]
            promo_code = deal["promo_code"]["value"]

            # Display the deal in a styled card
            st.markdown(
                f"""
                <div style="border: 1px solid #ddd; padding: 15px; border-radius: 10px; margin-bottom: 20px;">
                    <h2 style="margin-bottom: 10px; font-size: 28px;">{deal_title}</h2>
                    <p style="margin: 5px 0; font-size: 18px;"></strong> {deal_description}</p>
                    <p style="margin: 5px 0; font-size: 18px;"><strong>Expiry Date:</strong> {deal_expiry_date}</p>
                    <p style="margin: 5px 0; font-size: 18px;"><strong>Location:</strong> {deal_location}</p>
                    <p style="margin: 10px 0; font-size: 22px; font-weight: bold; color: #FF4500;">
                        Promo Code: <span style="font-size: 26px; font-weight: bold; color: #32CD32;">{promo_code}</span>
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )

        # Add a "Return to Main Page" button
        if st.button("Return to Main Page"):
            st.session_state.page = "main_page"

    except Exception as e:
        st.error(f"An error occurred: {e}")


# Welcome Page
import streamlit as st


def welcome_page():
    # Add Bootstrap CSS for styling
    st.markdown(
        """
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.1/dist/css/bootstrap.min.css" rel="stylesheet">
        """,
        unsafe_allow_html=True,
    )

    # Display the welcome text
    st.markdown(
        """
        <div class="container text-center" style="margin-top: 20%;">
            <h1 class="display-1 fw-bold mb-3">UniLife</h1>
            <h3 class="text-success mb-5">You Need A Life</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Display the centered image
    st.markdown(
        """
        <div class="container d-flex justify-content-center mb-5">
            <img src="https://img.freepik.com/free-photo/young-students-sitting-studying-outdoors-while-talking_171337-13342.jpg?t=st=1734153322~exp=1734156922~hmac=738f2e3fe1d06629c0783324a8a5d8818a3ccf0925c0a3380429b598f110a3e7&w=1800"
                 alt="Young Students" class="img-fluid rounded" style="max-width: 80%;">
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Create three columns with specified widths
    col1, col2, col3 = st.columns([1, 3, 1])  # 1: Left column, 3: Center column, 1: Right column

    with col3:  # Place button in the left column
        if st.button("Get Started", key="welcome_get_started"):
            st.session_state.page = "signup"


# Sign-Up Page
def sign_up_page():
    st.title("🎓 UniLife - Student Sign-Up")
    st.subheader("Join the UniLife community!")

    with st.form(key="signup_form"):
        email = st.text_input("Email Address")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        full_name = st.text_input("Full Name")
        university_name = st.text_input("University Name")
        programme = st.text_input("Programme/Course of Study")
        state = st.text_input("State")
        graduation_year = st.number_input(
            "Graduation Year", min_value=2020, max_value=2100, step=1
        )

        submit_button = st.form_submit_button("Submit")

    if submit_button:
        if not all([email, password, confirm_password, full_name, university_name, programme, graduation_year]):
            st.error("⚠️ Please fill in all required fields!")
        elif password != confirm_password:
            st.error("⚠️ Passwords do not match!")
        else:
            student_data = {
                "email": email,
                "password": password,
                "full_name": full_name,
                "university_name": university_name,
                "programme": programme,
                "graduation_year": str(graduation_year),
            }
            if submit_user_data(student_data):
                st.session_state.page = "verify"
                st.session_state.signup_data = student_data
            else:
                st.error("❌ Failed to save your details. Please try again.")


# Main Page
def main_page():
    # Title
    st.title("Hi, what's on your mind today?")

    # CSS styles for buttons
    st.markdown(
        """
        <style>
        /* Common button styles */
        div.stButton > button {
            font-size: 16px;
            border-radius: 5px;
            padding: 10px 20px;
            width: 100%;
        }

        """,
        unsafe_allow_html=True,
    )

    # Layout with 3 columns
    col1, col2, col3 = st.columns(3)

    # button for EVENTS
    with col1:
        if st.button("EVENTS", key="events"):
            st.session_state.page = "events"

    # button for COMPETITION
    with col2:
        if st.button("COMPETITION", key="competitions"):
            st.session_state.page = "competitions"

    # button for DEALS
    with col3:
        if st.button("DEALS", key="deals"):
            st.session_state.page = "deals"


# Navigation Logic
if "page" not in st.session_state:
    st.session_state.page = "welcome"

# Render the appropriate page
if st.session_state.page == "welcome":
    welcome_page()
elif st.session_state.page == "signup":
    sign_up_page()
elif st.session_state.page == "verify":
    verify_student_card(st.session_state.signup_data)
elif st.session_state.page == "main_page":
    main_page()
elif st.session_state.page == "events":
    events_page(user_programme="Computer Science")
elif st.session_state.page == "event_details":
    event_details_page()
elif st.session_state.page == "competitions":
    competitions_page(user_programme="Computer Science")
elif st.session_state.page == "competition_details":
    competition_details_page()
elif st.session_state.page == "deals":
    deals_page()

