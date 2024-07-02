import gradio as gr
from scheduler import *

def update_input_data(input_file):
    if input_file is None:
        return None, None, pd.DataFrame(), ""
    
    # Save the uploaded file
    input_path = "input_data.xlsx"
    with open(input_path, "wb") as file:
        file.write(open(input_file.name, "rb").read())

    # Create a Scheduler instance with the input data
    scheduler = Scheduler(input_path)

    # Get the input data as DataFrames
    timeslots_df, student_preferences_df = scheduler.get_data()

    return timeslots_df, student_preferences_df, pd.DataFrame(), ""

def schedule_courses(input_file, timeslots_df, student_preferences_df):
    # Save the input data to a file
    input_path = "input_data.xlsx"
    with pd.ExcelWriter(input_path) as writer:
        timeslots_df.to_excel(writer, sheet_name="timeslots", index=False)
        student_preferences_df.to_excel(writer, sheet_name="student preferences", index=False)

    # Create a Scheduler instance with the input data
    scheduler = Scheduler(input_path)

    # Run the scheduling process
    success = scheduler.schedule()

    # If the scheduling is successful, read the result file and log file
    if success:
        result_df = pd.read_excel("result.xlsx")
        with open("log.txt", "r") as file:
            log_text = file.read()
        return result_df, log_text, "result.xlsx"
    else:
        error_df = pd.DataFrame({"Error": ["An error occurred during scheduling."]})
        return error_df, "An error occurred during scheduling.", ""

# Create a Gradio interface using Blocks
with gr.Blocks() as iface:
    gr.Markdown("# Fast Course Scheduler")
    
    with gr.Row():
        with gr.Column():
            gr.Markdown("""In this column:\n
                        1. upload the timeslots and student preferences file then click "submit" to update the input data.\n
                        1. click "schedule" to run the scheduling process.\n
                        1. modify the input data in the table and schedule again.""")
        with gr.Column():
            gr.Markdown("""In this column:\n
                        1. view the log to see a summary of the scheduling results.\n
                        1. view the scheduled courses for each student.""")
    
    with gr.Row():
        with gr.Column():
            input_file = gr.File(label="Timeslots & Student Preferences File")
            submit_button = gr.Button("Submit")
            timeslots_output = gr.Dataframe(label="Timeslots")
            schedule_button = gr.Button("Schedule")
            student_preferences_output = gr.Dataframe(label="Student Preferences")
        with gr.Column():
            log_output = gr.Textbox(label="Log")
            download_button = gr.File(interactive=False, label="Download Results")
            scheduled_courses_output = gr.Dataframe(label="Scheduling Results")
    
    
    submit_button.click(
        fn=update_input_data,
        inputs=input_file,
        outputs=[timeslots_output, student_preferences_output, scheduled_courses_output, log_output],
    )
    
    schedule_button.click(
        fn=schedule_courses,
        inputs=[input_file, timeslots_output, student_preferences_output],
        outputs=[scheduled_courses_output, log_output, download_button],
    )


iface.launch()