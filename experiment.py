import streamlit as st
import pandas as pd
from streamlit_option_menu import option_menu  # pip install streamlit-option-menu


# -------------- SETTINGS --------------

DATABASE_NAME  = "experiment"
PROGRAM_OPTIONS = ("Email", "Home phone", "Mobile phone")
LEVER_OPTIONS = ("timing", "phone", "ll")
ATTRIBUTE_OPTIONS = ('Green', 'Yellow', 'Red', 'Blue')

LEVEL_EXTRA = ['intervention', 'cohort']
# -------------------------

def drop_collection(collection_name):
    # Drops a collection from the MongoDB database.
    try:
        if collection_name in st.session_state["experiment_data"]:
            # Remove the collection from session state
            del st.session_state["experiment_data"][collection_name]
            st.success(f"Collection '{collection_name}' dropped successfully!")

    except Exception as e:
        st.error(f"Error dropping collection: {str(e)}")

def filter_documents(data,query):
    matched_docs = [] 
    for doc_id, doc_data in data.items():
        # Check if the document matches the query criteria  
        if all(item in doc_data["Attributes"]. items() for item in query.items()):
            matched_docs.append((doc_id, doc_data))
    return matched_docs

def generate_unique_id(program, lever):
  # Generates a unique TableName for an experiment .  
    version_id = 1  # Start with version 1 (or adjust based on versioning logic)
    existing_id = f"{program}_{lever}_{version_id}"
    while existing_id in st.session_state["experiment_data"]:
        version_id += 1  # Increment version if conflict found
        existing_id = f"{program}_{lever}_{version_id}"
    return version_id

# Initialize session state
if "experiment_data" not in st.session_state:
     st.session_state["experiment_data"] = {}

def add_row_data():
    if "row_data" not in st.session_state:
        st.session_state["row_data"] = []
    st.session_state["row_data"].append({"levels": [f"{item}_{len(st.session_state['row_data']) + 1}" for item in LEVEL_EXTRA]})


# -------------------------
def main():
    st.set_page_config(page_title="Experimentation", layout="centered")
    st.title("Experimentation")
    # Hide Streamlit branding
    hide_st_style = """
              <style>
              #MainMenu {visibility: hidden;}
              footer {visibility: hidden;}
              header {visibility: hidden;}
              </style>
              """
    st.markdown(hide_st_style, unsafe_allow_html=True)

    # --- NAVIGATION MENU ---
    selected = option_menu(
        menu_title=None,
        options=["create new Experiment", "List and Test Experiment"],
        icons=["pencil-fill", "bar-chart-fill"],  # https://icons.getbootstrap.com/
        orientation="horizontal",
    )
     

    if selected == "create new Experiment":
        st.header("Data Entry")

        program = st.selectbox(
            "Program",
            PROGRAM_OPTIONS,
            index=None,
            placeholder="Select program...", key="program_name"
        )
        if program is None:
                st.error("Please select a program.")
        lever = st.selectbox(
            "Lever",
            LEVER_OPTIONS,
            index=None,
            placeholder="Select lever...", key="lever_name"
        )
        if lever is None:
                st.error("Please select a lever.")
        attributes = st.multiselect('Attributes', ATTRIBUTE_OPTIONS,placeholder="Select list of attributes...", key="attributes")

       
        stages = st.number_input("Insert a number", value=1, step=1, key="levels")
        if stages <= 0:
            st.error("Please enter a positive number of stages.")
        c1 = [f"{item}_{i + 1}" for i in range(int(stages)) for item in LEVEL_EXTRA]

        version_id= generate_unique_id(program, lever)
        
        print(version_id)
        print(st.session_state["experiment_data"])
        "---"

        add_row_button = st.button("Add Experiment")
        if add_row_button:
            add_row_data()
        
        if "row_data" not in st.session_state:
            st.session_state["row_data"] = []

        for i in enumerate(st.session_state["row_data"], start=0):
            num = i[0]
            st.subheader(f"Row: {num}")
               
            with st.expander("List of Attributes"):
                level_attr = {attr: st.text_input(f"{attr}:", key=f"attribute_{attr}_{num}") for attr in attributes}

            with st.expander("Levels"):
                level_stage = {stage: st.text_input(f"{stage}:", key=f"attribute_{stage}_{num}") for stage in c1}

            with st.expander("Lever"):
                timing = st.text_input(f"{lever}", key=f"{lever}_{num}")
                champion_lever = st.text_input(f"Champion_{lever}", key=f"champion_{lever}_{num}")
                start_date = st.date_input("Start_Date", key=f"start_date_{num}")
                end_date = st.date_input("End_Date", key=f"end_date_{num}")
                if start_date > end_date:
                    st.error("Start date cannot be after end date.")
            Table_name=f"{program}_{lever}_V{version_id}"
            print(Table_name)
            if Table_name not in st.session_state["experiment_data"]:
                    st.session_state["experiment_data"][Table_name] = {}
            data = {
                f"{lever}":timing,
                f"Champion_{lever}": champion_lever,
                "Attributes": level_attr,
                "Levels": level_stage,
                "Start_date": str(start_date),
                "End_date": str(end_date)
                }
            st.session_state["experiment_data"][Table_name][i[0]] = data 
        
        if st.session_state["row_data"]:
            review_button = st.button("Review Data")
            if review_button:
                st.subheader("Review Data:")
                for key, data in st.session_state["experiment_data"].items():
                    st.subheader(f"{key}:")
                    st.write(data)
                
            if st.button("Submit"):
                try:
                    st.success("Experiment data saved successfully!")
                except Exception as e:
                    st.error(f"An error occurred while saving data: {str(e)}")
                
    elif selected == "List and Test Experiment":
        tab1, tab2 = st.tabs(["List Experiment", "Test Experiment"])
        collist=list(st.session_state["experiment_data"].keys())
        with tab1:
            st.header("Existing Experiments",divider='rainbow')
            # Display existing tables if any
            if st.session_state["experiment_data"]:
                data = []
                for key, value in st.session_state["experiment_data"].items():
                    program, lever, version_id = key.split("_")  # Assuming key format "program_lever_version_id"
                    data.append({"Program": program, "Lever": lever, "Version ID": version_id})

                    # Create a Pandas DataFrame from the data
                df = pd.DataFrame(data)

                # Display the DataFrame as a table
                st.write("Existing Experimentation Data:")
                st.table(df)
                
                collection_to_drop = st.selectbox("Enter table name to drop:",collist, key="collection_to_drop",index=None,)
                if st.button("Delete experiment"):
                    if collection_to_drop:
                        drop_collection(collection_to_drop)
                    else:
                        st.error("Please enter a collection name.")
            else:
                st.write("No existing experimentation data.")
        with tab2:
            with st.form("Test data"):
                st.header("Test Experiments",divider='rainbow')
                selected_collection = st.selectbox("Enter experiment name to Test:",collist, key="collection_to_Test",index=None,placeholder="program_lever_version")
                
                if st.form_submit_button("generate value"):
                    Patient_id=st.text_input("Enter patient id")
                    experiment_data = st.session_state["experiment_data"].get(selected_collection, {})
                    version=list(experiment_data.keys())
                    attributes = experiment_data[0].get("Attributes", {})
                    

                    # Display only the keys of the attributes object
                    
                    st.subheader("Enter Attribute Values:")
                    entered_values = {}
                    for key, value in attributes.items():
                        entered_values[key]=st.text_input(key, key=f"input_{key}")
                    query = {"Attributes": entered_values}
                    
                    all_matched_docs = []
                    for version, doc_data in experiment_data.items():
                        attributes1 = doc_data.get("Attributes", {})
                        matched = True
                        for key, value in attributes1.items():
                            if entered_values.get(key) != value:
                                matched = False
                                break
                        if matched:
                            all_matched_docs.append((version, doc_data))

                    if all_matched_docs:
                        st.subheader("Matched Experiments:")
                        for version, doc_data in all_matched_docs:
                            st.write(f"Version: {version}")
                            st.write(doc_data)
                    else:
                        st.write("No experiments match the entered attribute values.")
if __name__ == '__main__':
    main()
