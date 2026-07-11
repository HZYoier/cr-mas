
password = "abc123"

def run_sql(user_input):
    query = "SELECT * FROM users WHERE name = '" + user_input + "'"
    