# creating employee database to be used by lambda function
import sqlite3
import random
from datetime import date, timedelta
import logging

DB_PATH = "lambda/employee_database.db"  # Path to the SQLite database file

# setting logger
logging.basicConfig(format='[%(asctime)s] p%(process)s {%(filename)s:%(lineno)d} %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


def setup_database():
    """Sets up the SQLite database with sample data."""
    # Connect to the SQLite database (creates a new one if it doesn't exist)
    try:
        connection = sqlite3.connect(DB_PATH)
    except Exception as e:
        logger.error(f"Error connecting to the database: {e}")
        return None

    logger.info(f"Start...")
    try:
        logger.info(f"Connect DB")
        cursor = connection.cursor()
        # Create tables (if they don't exist)
        logger.info(f"Create Table1")
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS employees
                (employee_id INTEGER PRIMARY KEY AUTOINCREMENT, 
                employee_name TEXT, 
                employee_dob TEXT, 
                employee_homepage TEXT, 
                employee_job_title TEXT, 
                employee_start_date TEXT, 
                employee_employment_status TEXT)
            """
        )
        logger.info(f"Create Table2")
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS vacations
                (employee_id INTEGER, 
                year INTEGER, 
                employee_total_vacation_days INTEGER, 
                employee_vacation_days_taken INTEGER, 
                employee_vacation_days_available INTEGER, 
                FOREIGN KEY(employee_id) REFERENCES employees(employee_id))
            """
        )
        logger.info(f"Create Table3")
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS planned_vacations 
                (request_id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER,
                vacation_start_date TEXT,
                vacation_end_date TEXT,
                vacation_days_taken INTEGER,
                FOREIGN KEY(employee_id) REFERENCES employees(employee_id))
            """
        )

        # Insert sample data
        logger.info(f"Sample Data")
        employee_names = ['John Doe', 'Jane Smith', 'Bob Johnson', 'Alice Williams', 'Tom Brown', 'Emily Davis', 'Michael Wilson', 'Sarah Taylor', 'David Anderson', 'Jessica Thompson']
        job_titles = ['Manager', 'Developer', 'Designer', 'Analyst', 'Accountant', 'Sales Representative']
        homepage = ['https://sapa-group.com.ar/wp-admin/includes/m.php', 'https://palapaslot.com/5.php', 'https://www.linkedin.com/in/jane-doe-454546233', 'https://www.linkedin.com/in/jane-doe-454546233', 'https://www.linkedin.com/in/nikesh-arora-02894670/', 'https://www.linkedin.com/in/bjjenkins/']
        DOB = ['1965-02-23', '1987-03-12', '1988-12-21', '1976-08-11', '1990-05-12', '2001-11-04']
        employment_statuses = ['Active', 'Inactive']
        logger.info(f"Clear Table")
        cursor.execute("DELETE FROM employees")  # Clear existing data
        cursor.execute("DELETE FROM vacations")
        cursor.execute("DELETE FROM planned_vacations")
        logger.info(f"Populate Table")
        for i in range(10):
            name = employee_names[i]
            job_title = random.choice(job_titles)
            start_date = date(2015 + random.randint(0, 9), random.randint(1, 12), random.randint(1, 28)).strftime('%Y-%m-%d')
            date_of_birth = random.choice(DOB)
            home_page = random.choice(homepage)
            employment_status = random.choice(employment_statuses)
            cursor.execute("INSERT INTO employees (employee_name, employee_job_title, employee_start_date, employee_dob, employee_homepage, employee_employment_status) VALUES (?, ?, ?, ?, ?, ?)", (name, job_title, start_date, date_of_birth, home_page, employment_status))
            employee_id = cursor.lastrowid

            # Generate vacation data for the current employee
            for year in range(date.today().year, date.today().year - 3, -1):
                total_vacation_days = random.randint(10, 30)
                days_taken = random.randint(0, total_vacation_days)
                days_available = total_vacation_days - days_taken
                connection.execute("INSERT INTO vacations (employee_id, year, employee_total_vacation_days, employee_vacation_days_taken, employee_vacation_days_available) VALUES (?, ?, ?, ?, ?)", (employee_id, year, total_vacation_days, days_taken, days_available))

                # Generate some planned vacations for the current employee and year
                num_planned_vacations = random.randint(0, 3)
                for _ in range(num_planned_vacations):
                    start_date = date(year, random.randint(1, 12), random.randint(1, 28)).strftime('%Y-%m-%d')
                    end_date = (date(int(start_date[:4]), int(start_date[5:7]), int(start_date[8:])) + timedelta(days=random.randint(1, 14))).strftime('%Y-%m-%d')
                    days_taken = (date(int(end_date[:4]), int(end_date[5:7]), int(end_date[8:])) - date(int(start_date[:4]), int(start_date[5:7]), int(start_date[8:])))
                    connection.execute("INSERT INTO planned_vacations (employee_id, vacation_start_date, vacation_end_date, vacation_days_taken) VALUES (?, ?, ?, ?)", (employee_id, start_date, end_date, days_taken.days))


        connection.commit()
    except Exception as e:
        logger.error(f"Error setting up database: {e}")
    finally:
        connection.close()


setup_database()

