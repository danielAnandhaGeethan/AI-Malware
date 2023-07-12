import pyodbc
import pandas as pd

# Connect to Azure SQL database
def upload_data_to_sql_database(values):
    server = 'malwarebi.database.windows.net'
    database = 'business-intelligence'
    username = 'Tarunp08'
    password = 'Darshan@1709'
    driver= '{ODBC Driver 18 for SQL Server}'
    table_name = "result" 
    string = f"Driver={driver};Server=tcp:malwarebi.database.windows.net,1433;Database=business-intelligence;Uid=Tarunp08;Pwd={password};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
    print(string)
    cnxn = pyodbc.connect(string)
    
    # Create a cursor object
    cursor = cnxn.cursor()

    query = f"INSERT INTO {table_name} values('{values[0]}', {values[1]}, {values[2]}, {values[3]}, {values[4]}, '{values[5]}')"
    print(query)
    cursor.execute(query)

    # Commit the transaction
    cnxn.commit()

    # Close the cursor and connection
    cursor.close()
    cnxn.close()

if __name__ == '__main__':
    values = ["tarrrruuuunnnnn == Dani", 0.96, 0.91, 0.87, 0.76, "Malware Name Tarun&Dani"]
    upload_data_to_sql_database(values)