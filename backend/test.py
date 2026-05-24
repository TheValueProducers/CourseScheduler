YEAR_ORDER = ["Freshman", "Sophomore", "Junior", "Senior"]
TERM_ORDER = ["Fall", "Spring"]
TOTAL_SEMESTERS = 8
def _remaining_semester_indices(current_term: str, year: str):
    if year not in YEAR_ORDER:
        raise ValueError(f"Invalid year: {year}. Expected one of {YEAR_ORDER}.")
    if current_term not in TERM_ORDER:
        raise ValueError(f"Invalid current_term: {current_term}. Expected one of {TERM_ORDER}.")

    current_year_idx = YEAR_ORDER.index(year)
    current_term_idx = TERM_ORDER.index(current_term)
    current_semester_number = current_year_idx * 2 + current_term_idx
    remaining = TOTAL_SEMESTERS - current_semester_number
    if remaining <= 0:
        raise ValueError("No semesters remain based on current_term and year.")
    return list(range(remaining)), current_semester_number

print(_remaining_semester_indices("Spring", "Sophomore"))