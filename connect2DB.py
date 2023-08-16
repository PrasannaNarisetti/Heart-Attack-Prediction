import json
import psycopg2

# Define the filename
filename = "C:/Users/ekodh/OneDrive/Desktop/Heart/db.json"

print("Reading configuration from:", filename)

def connectDB():
    try:
        print("Reading database configuration...")  
        with open(filename) as config_file:
            config = json.load(config_file)
        print("Connecting to the database...")
        db_connection = psycopg2.connect(
            host=config['host'],
            dbname=config['dbname'],
            user=config['user'],
            password=config['password'],
            port=config['port']
        )
        print("Database connection established.")
        return db_connection
    except Exception as error:
        print('Error while connecting to the database:', error)
        return None

if __name__ == "__main__":
    connection = connectDB()
    if connection is not None:
        try:
            cursor = connection.cursor()

            # Create users table
            create_users_table = """
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(100) NOT NULL,
                password VARCHAR(100) NOT NULL,
                gender VARCHAR(10),
                email VARCHAR(100) NOT NULL,
                phone VARCHAR(20)
            )
            """
            cursor.execute(create_users_table)

            # Create contact_form table
            create_contact_form_table = """
            CREATE TABLE IF NOT EXISTS contact_form (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) NOT NULL,
                message TEXT
            )
            """
            cursor.execute(create_contact_form_table)

            # Commit the changes
            connection.commit()
            print("Tables created successfully.")

        except psycopg2.Error as e:
            print("Error creating tables:", e)
            connection.rollback()
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
    else:
        print('Database connection could not be established.')
