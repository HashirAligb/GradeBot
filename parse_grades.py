import pandas as pd
from bs4 import BeautifulSoup
import json
from io import StringIO

def parse_grades_html():
    # Read the HTML file
    with open('raw_data2022.html .html', 'r', encoding='utf-8') as file:
        html_content = file.read()

    # Parse HTML
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find all tables
    tables = soup.find_all('table')
    print(f"Found {len(tables)} tables in the HTML file")
    
    # Convert tables to pandas DataFrames
    dfs = []
    for table in tables:
        try:
            df = pd.read_html(StringIO(str(table)))[0]
            dfs.append(df)
        except Exception as e:
            continue
    
    # Find all tables with a 'PROF' column and grade columns
    grade_columns = ["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D", "F", "W"]
    all_prof_rows = []
    for df in dfs:
        cols = [str(col).strip() for col in df.columns]
        if 'PROF' in cols and any(g in cols for g in grade_columns):
            df = df.rename(columns=lambda x: str(x).strip())
            all_prof_rows.append(df)
    
    if not all_prof_rows:
        raise ValueError("Could not find any tables with professor and grade breakdown")
    
    # Concatenate all relevant tables
    all_data = pd.concat(all_prof_rows, ignore_index=True)
    
    # Filter for Computer Science (CSCI) only
    if 'SUBJECT' in all_data.columns:
        all_data = all_data[all_data['SUBJECT'] == 'CSCI']
    
    # Aggregate by professor and course
    grades_dict = {}
    for (prof, course_nbr), group in all_data.groupby(['PROF', 'NBR']):
        prof_key = prof.lower()
        course_key = str(course_nbr)
        course_name = group['COURSE NAME'].iloc[0] if 'COURSE NAME' in group.columns else ''
        grades = {}
        total_students = 0
        weighted_gpa_sum = 0
        gpa_col = None
        # Find GPA column
        for col in group.columns:
            if "GPA" in col and "AVG" in col.upper():
                gpa_col = col
                break
        # Sum grades
        for grade in grade_columns:
            if grade in group.columns:
                grades[grade] = int(group[grade].fillna(0).sum())
            else:
                grades[grade] = 0
        # Weighted average GPA
        if gpa_col and 'TOTAL' in group.columns:
            for _, row in group.iterrows():
                try:
                    gpa = float(row[gpa_col]) if pd.notnull(row[gpa_col]) else 0
                    count = int(row['TOTAL']) if pd.notnull(row['TOTAL']) else 0
                    weighted_gpa_sum += gpa * count
                    total_students += count
                except:
                    continue
            avg_gpa = round(weighted_gpa_sum / total_students, 3) if total_students > 0 else None
        else:
            avg_gpa = None
        # Add to professor's courses
        if prof_key not in grades_dict:
            grades_dict[prof_key] = {
                'name': prof,
                'courses': {}
            }
        grades_dict[prof_key]['courses'][course_key] = {
            'course_name': course_name,
            'avg_gpa': avg_gpa,
            'grades': grades
        }
    
    # Save to JSON file
    with open('grade_data.json', 'w') as f:
        json.dump(grades_dict, f, indent=2)
    
    return grades_dict

if __name__ == "__main__":
    try:
        grades_dict = parse_grades_html()
        print("Successfully parsed grades data!")
        print(f"Found data for {len(grades_dict)} professors")
    except Exception as e:
        print(f"Error: {str(e)}") 