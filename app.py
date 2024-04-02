import streamlit as st
import pandas as pd
from streamlit_option_menu import option_menu  # pip install streamlit-option-menu
import pymongo

# -------------- SETTINGS --------------
MONGO_URI=st.secrets.MONGODB.MONGO_URI
DATABASE_NAME  = "experiment"
COLLECTION_NAME="experiment_data"
PROGRAM_OPTIONS = ("Email", "Home phone", "Mobile phone")
LEVER_OPTIONS = ("timing", "phone", "ll")
ATTRIBUTE_OPTIONS = ('Green', 'Yellow', 'Red', 'Blue')

LEVEL_EXTRA = ['intervention', 'cohort']
# -------------------------

@st.cache_resource
def init_connection():
    # Connects to the MongoDB database and handles potential connection errors.
    try:
        client=pymongo.MongoClient(MONGO_URI)
        db = client[DATABASE_NAME]
        collection = db[COLLECTION_NAME]
        print("Connected to MongoDB successfully!")
    except Exception as e:
        print(f"Error connecting to MongoDB: {str(e)}")
        st.stop()  # Halt execution if connection fails
    return collection


def save_experiment_data(data, collection):
    # Saves experiment data to the specified MongoDB collection
    try:
        collection.insert_one(data)
        st.success("Experiment data saved successfully!")
    except Exception as e:
        st.error(f"An error occurred while saving data: {str(e)}")

def drop_collection(collection, document_id):
    # Drops a collection from the MongoDB database.
    try:
        collection.delete_one({"_id": document_id})
        st.success(f"Collection '{document_id}' dropped successfully!")
    except Exception as e:
        st.error(f"Error dropping collection: {str(e)}")

def generate_unique_id(program, lever,collection):
  # Generates a unique TableName for an experiment
      
    version_id = 1  # Start with version 1 (or adjust based on versioning logic)
    existing_id = f"{program}_{lever}_V{version_id}"
    all_ids = collection.distinct("_id")
    while existing_id in all_ids:
        version_id += 1  # Increment version if conflict found
        existing_id = f"{program}_{lever}_V{version_id}"
    return existing_id
# Initialize session state
if "experiment_data" not in st.session_state:
     st.session_state["experiment_data"] = {}

if "row_data" not in st.session_state:
            st.session_state["row_data"] = []

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
    collection = init_connection()  

    if selected == "create new Experiment":
        st.header("Data Entry")

        program = st.selectbox(
            "Program",
            PROGRAM_OPTIONS,
            index=None,
            placeholder="Select program...", key="program"
        )
        if program is None:
                st.error("Please select a program.")
        lever = st.selectbox(
            "Lever",
            LEVER_OPTIONS,
            index=None,
            placeholder="Select lever...", key="lever"
        )
        if lever is None:
                st.error("Please select a lever.")
        attributes = st.multiselect('Attributes', ATTRIBUTE_OPTIONS,placeholder="Select list of attributes...", key="attributes")

       
        stages = st.number_input("Insert a number", value=1, step=1, key="levels")
        c1 = [f"{item}_{i + 1}" for i in range(int(stages)) for item in LEVEL_EXTRA]

        Table_name = generate_unique_id(program, lever,collection)
        
        "---"
        add_row_button = st.button("Add Experiment")
        if add_row_button:
            add_row_data()

        main_data={
                "_id":f"{Table_name}",
            }
        for i in enumerate(st.session_state["row_data"]):
            num = i[0] + 1
            st.subheader(f"Row: {num}")
                
            with st.expander("List of Attributes"):
                level_attr = {attr: st.text_input(f"{attr}:", key=f"attribute_{attr}_{i}") for attr in attributes}

            with st.expander("Levels"):
                level_stage = {stage: st.text_input(f"{stage}:", key=f"attribute_{stage}_{i}") for stage in c1}

            with st.expander("Lever"):
                timing = st.text_input(f"{lever}", key=f"{lever}_{i}")
                champion_lever = st.text_input(f"Champion_{lever}", key=f"champion_{lever}_{i}")
                start_date = st.date_input("Start_Date", key=f"start_date_{i}")
                end_date = st.date_input("End_Date", key=f"end_date_{i}")
               
            data = {
                    f"{lever}":timing,
                    f"Champion_{lever}": champion_lever,
                    "Attributes": level_attr,
                    "Levels": level_stage,
                    "Start_date": str(start_date),
                    "End_date": str(end_date)
                }
            
            main_data[f"row {i[0]}"] = data
            st.session_state["experiment_data"][COLLECTION_NAME] = main_data 
        print(st.session_state["experiment_data"] )
        if st.session_state["row_data"]:
            review_button = st.button("Review Data")
            if review_button:
                st.subheader("Review Data:")
                for key, data in st.session_state["experiment_data"].items():
                    st.subheader(f"{key}:")
                    st.write(data)
                
            if st.button("Submit"):
                try:
                    #for key, value in st.session_state["experiment_data"][COLLECTION_NAME].items():
                    save_experiment_data(main_data, collection)
                except Exception as e:
                    st.error(f"An error occurred while saving data: {str(e)}")
                
    elif selected == "List and Test Experiment":
        tab1, tab2 = st.tabs(["List Experiment", "Test Experiment"])
        collist = collection.distinct("_id")
        with tab1:
            st.header("Existing Experiments",divider='rainbow')
            # Display existing tables if any
            if collist:
                data = []
                for key in collist:
                    program, lever, version_id = key.split("_")  # Assuming key format "program_lever_version_id"
                    data.append({"Program": program, "Lever": lever, "Version ID": version_id})

                # Create a Pandas DataFrame from the data
                df = pd.DataFrame(data)

                # Display the DataFrame as a table
                st.table(df)
                collection_to_drop = st.selectbox("Enter table name to drop:",collist, key="collection_to_drop",index=None,)
                if st.button("Delete experiment"):
                    if collection_to_drop:
                        drop_collection(collection, collection_to_drop)
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
                    Test_document = collection.find_one({"_id": selected_collection})
                    #first_doc =Test_collection.find_one()
                    attributes_object = Test_document.get("Attributes", {})
                    

                    # Display only the keys of the attributes object
                    keys = list(attributes_object.keys()) 
                    for key in keys:
                        st.text_input(key, key=f"input_{key}")
                    
                    with st.spinner("please wait while processing.."):
                        entered_values = {key: st.session_state[f"input_{key}"] for key in keys}
                    
                        # Query to filter documents where the entered attribute values match
                        query = {"Attributes": entered_values}
                    
                        matched_docs = Test_document.find(query)
                        if matched_docs:
                            st.subheader("Test created:")
                            st.subheader(f"patient id : {Patient_id}" )
                            for doc in matched_docs:
                                st.write(doc)                        
                        else:
                            st.write("No documents match the entered attribute values.")                                       

if __name__ == '__main__':
    main()
