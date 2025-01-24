import streamlit as st
from database import  clear_all, insert, insert2
from forms import task_input_form, shift_input_form, worker_input_form, task_template_download, upload_tasks_excel, shift_template_download, upload_shifts_excel
from dynamic_programming.optimizer import optimize_tasks_with_gurobi 
from dynamic_programming.visualization import display_tasks_and_shifts

def show_home():
    # st.set_page_config(page_title="Hospital Scheduler", layout="wide")
    # Input forms
    task_input_form()
    shift_input_form()
    # worker_input_form()
 
    # Buttons for example data
 
    if st.button("Clear All Tasks1"):
        clear_all("TasksTable2")
        st.success("All tasks have been cleared!")
 
    if st.button("Clear All Shifts"):
        clear_all("ShiftsTable5")
        st.success("All shifts have been cleared!")



    # 1. Download Template
    st.subheader("Download Template")
    task_template_download()

    st.markdown("---")

    # 2. Upload user file
    st.subheader("Upload Your Tasks")
    upload_tasks_excel()

    # if st.button("Clear All Workers"):
    #     clear_all("Workers")
    #     st.success("All workers have been cleared!")

 
    st.subheader("Download Example Shift Template")
    shift_template_download()

    st.markdown("---")
    
    st.subheader("Upload Your Shifts File")
    upload_shifts_excel()

    # Buttons for example data
    colA, colB = st.columns(2)
    with colA:
        if st.button("Data Example"):
            insert()
            st.success("Data Example 1 inserted!")
    with colB:
        if st.button("Data Example2"):
            insert2()
            st.success("Data Example 2 inserted!")

    # First optimization
    if st.button("Optimize Task Assignment"):
        optimize_tasks_with_gurobi()

    ## Second optimization: Assign workers to shifts
    # if st.button("Assign Workers to Shifts"):
    #     optimize_workers_for_shifts()


    # Visualization
    display_tasks_and_shifts()
