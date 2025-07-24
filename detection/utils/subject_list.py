def get_subjects(board):
    if board == "CBSE":
        return ["English", "Mathematics", "Science", "Social Science", "Hindi", "Computer Science"]
    elif board == "State":
        return ["Tamil", "English", "Maths", "Science", "Social Science"]
    elif board == "ICSE":
        return ["English", "History", "Civics", "Geography", "Mathematics", "Science"]
    return []
