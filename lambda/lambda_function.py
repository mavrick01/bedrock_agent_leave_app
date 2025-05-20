import os
import json
import shutil
import sqlite3
import logging
import requests
from datetime import datetime

# setting logger
logging.basicConfig(format='[%(asctime)s] p%(process)s {%(filename)s:%(lineno)d} %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

DB_PATH = "/tmp/employee_database.db"  # Path to the SQLite database file

def create_db_connection():
    """Creates a connection to the SQLite database."""
    try:
        connection = sqlite3.connect(DB_PATH)
        return connection
    except Exception as e:
        return None

def get_employee_id(employee_name: str)  -> int:
    """Simulates a Lambda function to lookup an employee's id based on their name."""
    connection = create_db_connection()
    if connection is None:
        return {"error": "Failed to connect to database"}

    try:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT employee_id FROM employees WHERE employee_name = ?",
            (employee_name,),
        )
        result = cursor.fetchone()
        if result:
            return {"employee_name": employee_name, "employee_id": result[0]}
        else:
            return {"error": "Employee not found"}
    except Exception as e:
        return {"error": f"Error fetching leave balance: {e}"}
    finally:
        connection.close()
    
def employee_details(employee_number: int) -> dict[str, any]:
    """Simulates a Lambda function to get all the employees details."""
    connection = create_db_connection()
    if connection is None:
        return {"error": "Failed to connect to database"}

    try:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT * FROM employees WHERE employee_id = ?",
            (employee_number,),
        )
        result = cursor.fetchone()
        logger.info(f"Result : {result}")
        if result:
            employee_file = {
                    "employee_id": result[0],
                    "employee_name": result[1],
                    "employee_dob": result[2],
                    "employee_homepage": result[3],
                    "employee_job_title": result[4],
                    "employee_start_date": result[5],
                    "employee_employement_status": result[6]
                }
            return  employee_file
        else:
             return {"error": "Employee not found"}
    except Exception as e:
        return {"error": f"Error fetching employee details: {e}"}
    finally:
        connection.close()

def get_leave_balance(employee_number: int) -> dict[str, any]:
    """Simulates a Lambda function to get an employee's leave balance."""
    connection = create_db_connection()
    if connection is None:
        return {"error": "Failed to connect to database"}

    try:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT employee_vacation_days_available FROM vacations WHERE employee_id = ?",
            (employee_number,),
        )
        result = cursor.fetchone()
        if result:
            return {"employee_number": employee_number, "employee_vacation_days_available": result[0]}
        else:
            return {"error": "Employee not found"}
    except Exception as e:
        return {"error": f"Error fetching leave balance: {e}"}
    finally:
        connection.close()

def book_leave(employee_number: int, start_date_str: str, end_date_str: str) -> dict[str, any]:
    """Simulates a Lambda function to book leave for an employee."""
    connection = create_db_connection()
    if connection is None:
        return {"error": "Failed to connect to database"}

    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        today = datetime.now().date()
        if start_date < today or end_date < today:
            return {"error": "Cannot book leave in the past"}
        if end_date < start_date:
            return {"error": "End date must be after start date"}

        logger.info(f"{start_date}-{end_date} vs {today}")

        logger.info(f"Employee : {employee_number}")
        cursor = connection.cursor()
            # Check employee exists and has enough leave.
        cursor.execute(
                "SELECT employee_vacation_days_available FROM vacations WHERE employee_id = ?",
                (employee_number,),
            )
        result = cursor.fetchone()
        logger.info(f"Result : {result}")

        if not result:
            return {"error": "Employee not found"}
        leave_available = result[0]
        leave_duration = (end_date - start_date).days + 1  # Inclusive

        if leave_available < leave_duration:
            return {
                "error": "Insufficient leave available",
                "leave_available": leave_available,
            }

            # Book the leave
        cursor.execute(
                """
                INSERT INTO planned_vacations (employee_id, vacation_start_date, vacation_end_date, vacation_days_taken)
                VALUES (?, ?, ?,?)
                """,
                (employee_number, str(start_date), str(end_date),leave_duration),
            )
            #update the leave balance.
        cursor.execute(
                "UPDATE vacations SET employee_vacation_days_available = employee_vacation_days_available - ? WHERE employee_id = ?",
                (leave_duration, employee_number),
            )
        connection.commit()
        return {
                "message": "Leave booked successfully",
                "employee_number": employee_number,
                "start_date": start_date_str,
                "end_date": end_date_str,
                "leave_duration": leave_duration,
            }
    except ValueError:
        return {"error": "Invalid date format. Use YYYY-MM-DD"}
    except Exception as e:
        return {"error": f"Error booking leave: {e}"}
    finally:
        connection.close()


def list_leave(employee_number: int) -> dict[str, any]:
    """Simulates a Lambda function to list leave for an employee."""
    connection = create_db_connection()
    if connection is None:
        return {"error": "Failed to connect to database"}

    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT vacation_start_date, vacation_end_date, vacation_days_taken
            FROM planned_vacations
            WHERE employee_id = ?
            """,
            (employee_number,),
        )
        results = cursor.fetchall()
        if results:
            leave_list = [
                {
                    "start_date": row[0],
                    "end_date": row[1],
                    "days of vacation": row[2],
                }
                for row in results
            ]
            return {"employee_number": employee_number, "leave_requests": leave_list}
        else:
            return {"employee_number": employee_number, "leave_requests": []}
    except Exception as e:
        return {"error": f"Error listing leave: {e}"}
    finally:
        connection.close()


def cancel_leave(employee_number: int, start_date_str: str) -> dict[str, any]:
    """Simulates a Lambda function to cancel leave for an employee."""
    connection = create_db_connection()
    if connection is None:
        return {"error": "Failed to connect to database"}

    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()

        cursor = connection.cursor()
        # Check if the leave entry exists
        cursor.execute(
                "SELECT vacation_end_date FROM planned_vacations WHERE employee_id = ? AND vacation_start_date = ?",
                (employee_number, str(start_date)),
            )
        result = cursor.fetchone()
        if not result:
            return {"error": "Leave entry not found"}

        end_date = datetime.strptime(result[0], "%Y-%m-%d").date()
        leave_duration = (end_date - start_date).days + 1

        # Delete the leave entry
        cursor.execute(
                "DELETE FROM planned_vacations WHERE employee_id = ? AND vacation_start_date = ?",
                (employee_number, str(start_date)),
            )

            # Credit the leave back to the employee
        cursor.execute(
                "UPDATE vacations SET employee_vacation_days_available = employee_vacation_days_available + ? WHERE employee_id = ?",
                (leave_duration, employee_number),
            )
        connection.commit()
        return {"message": "Leave cancelled successfully"}
    except ValueError:
        return {"error": "Invalid date format. Use YYYY-MM-DD"}
    except Exception as e:
        return {"error": f"Error cancelling leave: {e}"}
    finally:
        connection.close()

# Call AIRS Must define the reqest type to be prompt or response, the body an app name app user and transcaction id. It will return True if it allowed, else will give a string with the reason.
def airs_make_request(reqtype, prompt_val, app_name, app_user, tr_id):
    try: 

        req = airs_construct_request(reqtype, prompt_val.replace("\n", " "), app_name, app_user, tr_id)
        # URL of the API endpoint
        url = "https://service.api.aisecurity.paloaltonetworks.com/v1/scan/sync/request"
        header = {
            "x-pan-token":os.environ['AIRS_API'], 
            "Content-Type": "application/json"
            }
        # Making the API call
        resp = requests.post(url, headers=header, json=req)
        json_resp = resp.json()
        #json_resp = json.loads(resp)
        # Checking the response
        if resp.status_code == 200:
            # Successful API call
            print(f"API call successful. Response: {json_resp}")
            if json_resp['action'] == "block":
                if reqtype == 'prompt':
                    return airs_construct_response(json_resp['prompt_detected'])
                else:
                    return airs_construct_response(json_resp['response_detected'])
            else:
                return True
        else:
            # Failed API call
            print(f"Failed to make API call. Status code: {resp.status_code}")
            print(resp.text)
            return f"Failed to make API call. Status code: {resp.status_code}  request: {req}"
    except Exception as e:
        print("Error: ", e)
        return f"Error: {e}"

# Construct the URL Request Json body
def airs_construct_request(reqtype, input_value, app_name, app_user, tr_id):
    # Set the right profile name
    profile_name = os.environ['AIRS_PROMPT_PROFILE'] if reqtype == 'prompt' else  os.environ['AIRS_RESPONSE_PROFILE']
    # JSON data for the API call
    

    try:
        req = '''
        {
            "metadata": {
            "ai_model": "Test AI model",
            "app_name": "%s",
            "app_user": "%s"
            },
            "contents": [
            {
            "%s": "%s"
            }
            ],
            "tr_id": "%s",
            "ai_profile": {
            "profile_name": "%s"
            }
        }
        ''' %(app_name, app_user, reqtype, input_value, tr_id, profile_name)
        print(f"Received prompt: {req}") 
        json_data = json.loads(req)
        return json_data
    except Exception as e:
        print("Error ", e)
        return False
    
# Return a more descriptive sentence based on the keys in the josn provided being true.
def airs_construct_response(response_json):
    response_mapping = {
        'url_cats': "The content includes URLs that have are malicous in nature or not in keeping with the company policy.",
        'dlp' : "The content has been identified to contain potential sensitive data.",
        'injection' : "Security protocols have flagged a potential malicous prompt.",
        'toxic_content' : "Toxic or harmful contne has been detected.",
        'malicious_code' : "Malicous code was detected.",
        'agent' : "Agent security issues have been detected.",
        'db_security' : "Security protocols have flagged potential illegal database calls.",
        'ungrounded' : "Ungrounded content has been detected.",
        'topic_violation' : "Topic violoations were detected."
    }

    response_parts = [response_mapping[key] for key in response_mapping if response_json.get(key)]

    if not response_parts:
        return ""

    return " ".join(response_parts)

# Lambda Handler for all functions
def lambda_handler(event, context):
    original_db_file = 'employee_database.db'
    target_db_file = '/tmp/employee_database.db'
    if not os.path.exists(target_db_file):
        shutil.copy2(original_db_file, target_db_file)
    
    print("Lambda function execution started.")
    print(f"Received event: {json.dumps(event)}") # Good for seeing the input
    
    agent = event['agent']
    actionGroup = event['actionGroup']
    function = event['function']
    parameters = event.get('parameters', [])
    responseBody =  {
        "TEXT": {
            "body": "Error, no function was called"
        }
    }
    
    if function == 'get_employee_id':
        employee_name = None
        for param in parameters:
            if param["name"] == "employee_name":
                employee_name = param["value"]

        if not employee_name:
            raise Exception("Missing mandatory parameter: employee_name")
        employee_id = get_employee_id(employee_name)
        responseBody =  {
            'TEXT': {
                "body": f"employees id for {employee_name}: {employee_id}"
            }
        }
    elif function == 'employee_details':
        employee_id = None
        for param in parameters:
            if param["name"] == "employee_id":
                employee_id = param["value"]

        if not employee_id:
            raise Exception("Missing mandatory parameter: employee_id")
        employee_file = employee_details(employee_id)
        responseBody =  {
            'TEXT': {
                "body": f"employee details: {employee_file}"
            }
        } 
    elif function == 'get_leave_balance':
        employee_id = None
        for param in parameters:
            if param["name"] == "employee_id":
                employee_id = param["value"]

        if not employee_id:
            raise Exception("Missing mandatory parameter: employee_id")
        vacation_days = get_leave_balance(employee_id)
        responseBody =  {
            'TEXT': {
                "body": f"available vacation days for employed_id {employee_id}: {vacation_days}"
            }
        } 
    elif function == 'book_leave':
        employee_id = None
        start_date = None
        end_date = None
        for param in parameters:
            if param["name"] == "employee_id":
                employee_id = param["value"]
            if param["name"] == "start_date":
                start_date = param["value"]
            if param["name"] == "end_date":
                end_date = param["value"]
            
        if not employee_id:
            raise Exception("Missing mandatory parameter: employee_id")
        if not start_date:
            raise Exception("Missing mandatory parameter: start_date")
        if not end_date:
            raise Exception("Missing mandatory parameter: end_date")
        
        completion_message = book_leave(employee_id, start_date, end_date)
        responseBody =  {
            'TEXT': {
                "body": json.dumps(completion_message)
            }
        }  
    elif function == 'list_leave':
        employee_id = None
        start_date = None
        end_date = None
        for param in parameters:
            if param["name"] == "employee_id":
                employee_id = param["value"]
            
        if not employee_id:
            raise Exception("Missing mandatory parameter: employee_id")
        
        completion_message = list_leave(employee_id)
        responseBody =  {
            'TEXT': {
                "body": json.dumps(completion_message)
            }
        }  
    elif function == 'cancel_leave':
        employee_id = None
        start_date = None
        for param in parameters:
            if param["name"] == "employee_id":
                employee_id = param["value"]
            if param["name"] == "start_date":
                start_date = param["value"]
        if not employee_id:
            raise Exception("Missing mandatory parameter: employee_id")
        if not start_date:
            raise Exception("Missing mandatory parameter: start_date")
        
        completion_message = cancel_leave(employee_id, start_date)
        responseBody =  {
            'TEXT': {
                "body": completion_message
            }
        }  
    elif function == 'airs_make_request':
        reqtype = None
        prompt_val = None
        app_name = None
        app_user = None
        tr_id = None
        for param in parameters:
            if param["name"] == "reqtype":
                reqtype = param["value"]
            if param["name"] == "prompt":
                prompt_val = param["value"]
            if param["name"] == "app_name":
                app_name = param["value"]
            if param["name"] == "app_user":
                app_user = param["value"]
            if param["name"] == "tr_id":
                tr_id = param["value"]
            
        if not reqtype:
            raise Exception("Missing mandatory parameter: reqtype")
        if not prompt_val:
            raise Exception("Missing mandatory parameter: prompt")
        if not app_name:
            app_name ="test app"
        if not app_user:
            app_user = "test user"
        if not tr_id:
            tr_id = "test id"

        
        completion_message = airs_make_request(reqtype, prompt_val.strip(), app_name, app_user, tr_id)
        responseBody =  {
            'TEXT': {
                "body": completion_message
            }
        }  
    
    
    action_response = {
        'actionGroup': actionGroup,
        'function': function,
        'functionResponse': {
            'responseBody': responseBody
        }

    }

    function_response = {'response': action_response, 'messageVersion': event['messageVersion']}
    print("Response: {}".format(function_response))

    return function_response
