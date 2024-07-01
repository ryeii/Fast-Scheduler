import pandas as pd
from collections import defaultdict
from itertools import product, combinations
import os

class Scheduler:
    def __init__(self, data_path):
        self.path = data_path

    def get_data(self):
        df = pd.read_excel(self.path, sheet_name=['timeslots', 'student preferences'])
        return df.get('timeslots'), df.get('student preferences')
    
    def preprocess(self):
        '''
        This preprocess is implemented specifically for Beijing Aidi School and may not be applicable to other schools.
        '''
        timeslots, student_preferences = self.get_data()

        print('Preprocessing...')

        # create new dataframe student_preferences_processed
        student_preferences_processed = pd.DataFrame(columns=['Student name', 'Fixed class 1', 'Fixed class 2', 
                                                              'Fixed class 3', 'Fixed class 4', 'Elective 1', 
                                                              'Elective 2', 'Elective 3', ])

        # for each row of the student preferences, if the number of classes is larger than the number of timeslots
        for _, row in student_preferences.iterrows():
            electives = row[5:].dropna()
            fixed = row[1:5].dropna()
            name = row[0]
            # for each combinations of three classes in electives, create a new row with the same fixed classes and the combination of three classes. the combinations are without repetition.
            for combination in combinations(electives, 3):
                    student_preferences_processed.loc[len(student_preferences_processed)] = [name, *fixed, *combination]
            if len(electives) < 3:
                student_preferences_processed.loc[len(student_preferences_processed)] = [name, *fixed, *electives, *[None for _ in range(3-len(electives))]]

        print('Number of students after preprocessing: ', len(set(student_preferences_processed['Student name'])))
        
        return timeslots, student_preferences_processed
                

    def schedule(self, save_path='result.xlsx'):

        try:
            print('Scheduling...')
            timeslots, student_preferences = self.preprocess()

            # Create a dictionary to map classes to their available slots
            class_to_slots = {}
            for col_number, classes in enumerate(timeslots.columns, start=1):
                for class_name in timeslots[classes].dropna():
                    if class_name not in class_to_slots:
                        class_to_slots[class_name] = []
                    class_to_slots[class_name].append(col_number)

            # Compute the valid schedules for each student
            valid_schedules = {}
            list_failed = []
            for _, row in student_preferences.iterrows():
                student = row[0]
                classes = row[1:]

                # if len of classes is smaller than len col of timeslots, add the student to list_failed and skip to next student
                if (len(classes) < len(timeslots.columns)) or (not all([class_name in class_to_slots for class_name in classes])):
                    list_failed.append(student)
                    continue

                if student not in valid_schedules:
                    valid_schedules[student] = []

                # Compute the Cartesian product of the available slots for the chosen classes
                class_combinations = list(product(*[class_to_slots[class_name] for class_name in classes]))

                # Filter out combinations where not all slots are unique
                unique_combinations = [combination for combination in class_combinations if len(set(combination)) == len(combination)]
                if unique_combinations:
                    for combination in unique_combinations:
                        valid_schedules[student].append([f'{class_name} (slot {slot})' for class_name, slot in zip(classes, combination)])
                if (not valid_schedules[student]) and (student not in list_failed):
                    list_failed.append(student)
                
                # if there is an entry in valid_schedules for the student, take down all names of this student in list_failed
                if valid_schedules[student] and (student in list_failed):
                    while student in list_failed:
                        list_failed.remove(student)

            # Create a dataframe to save the results
            df = pd.DataFrame(columns=['Student name', *[f'course {i+1}' for i in range(len(timeslots.columns))]])
            for student, schedules in valid_schedules.items():
                for schedule in schedules:
                    df = df._append({'Student name': student, **{f'course {i+1}': course for i, course in enumerate(schedule)}}, ignore_index=True)
            for student in list_failed:
                df = df._append({'Student name': student, **{f'course {i+1}': 'No valid schedule' for i in range(len(timeslots.columns))}}, ignore_index=True)
            
            # Save the results to an excel file
            df.to_excel(save_path, index=False)
        
        except Exception as e:
            print(e)
            with open('log.txt', 'w') as f:
                f.write('\n')
                f.write('no log yet\n')
            return False

        # generate log. number of students, number of students with no solution, percentage of students with at least one solution. save to log.txt
        with open('log.txt', 'w') as f:
            f.write('\n')
            f.write(f'~ Schedule created for {self.path}\n')
            f.write(f'###   Schedule Log   #############################################################\n')
            # names = names of all students
            success_names = set(student_preferences['Student name'])
            f.write(f'~ Number of students: {len(success_names)}\n')
            f.write(f'~ Number of students with valid schedule(s): {len(success_names) - len(set(list_failed))}\n')
            f.write(f'~ Percentage of students with valid schedule(s): {100 - len(set(list_failed))/len(success_names)*100}%\n')
            f.write('Result saved.\n')
            # f.write(f'###   Info Dump   ################################################################\n')
            # # write df
            # f.write(f'~ Dataframe: \n{df}\n')
            f.write(f'###   Debug Info   ###############################################################\n')
            f.write(f'~ Timeslot No. = {len(timeslots.columns)}\n')
            f.write(f'~ Number of classes = {len(class_to_slots)}\n')
            f.write(f'~ List of classes = {list(class_to_slots.keys())}\n')
        
        return True