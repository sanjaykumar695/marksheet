import re
from utils.subject_list import get_subjects

def parse_details(raw_text, board):
    subjects = get_subjects(board)
    lines = raw_text.splitlines()

    name = ""
    subject_marks = {}
    total = 0

    for line in lines:
        if "name" in line.lower():
            name = line.split(":")[-1].strip()
        for subj in subjects:
            if subj.lower() in line.lower():
                digits = re.findall(r'\d+', line)
                if digits:
                    mark = int(digits[-1])
                    subject_marks[subj] = mark
                    total += mark

    percentage = round(total / (len(subject_marks) * 100) * 100, 2) if subject_marks else 0
    return {
        "Name": name,
        "Subjects": subject_marks,
        "Total Marks": total,
        "Percentage": f"{percentage}%"
    }
