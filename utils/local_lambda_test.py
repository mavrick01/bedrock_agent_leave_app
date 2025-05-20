import json
import sys
import argparse
sys.path.append('./lambda')
import lambda_function

import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-f", "--filename", required=False, type=str, help="Enter a lambda json file")
parser.add_argument('-d', '--employeedetails', required=False, type=str, help="Enter the Employee Number")
parser.add_argument('-n', '--employeename', required=False, type=str, help="Enter the Employee Name")
parser.add_argument('-a', '--availableleave', required=False, type=str, help="Enter the Employee ID for their leave balance")
parser.add_argument('-l', '--listleave', required=False, type=str, help="Enter the Employee ID for their leave ")
parser.add_argument('-b', '--bookleave', required=False, type=str, help="Enter the Employee ID for their leave - you must also specify the start and end date")
parser.add_argument('-c', '--cancelleave', required=False, type=str, help="Enter the Employee ID for their leave - you must also specify the start date")
parser.add_argument('-s', '--startdate', required=False, type=str, help="Enter the Start date in the formate YYYY-MM-DD")
parser.add_argument('-e', '--enddate', required=False, type=str, help="Enter the End date in the formate YYYY-MM-DD")
parser.add_argument('-r', '--prismaairs', required=False, type=str, choices=['prompt', 'response'], help="Enter Prompt or Response - you must also specific the prompt")
parser.add_argument('-p', '--prompt', required=False, type=str, help="The prompt/response to evaluate")
if len(sys.argv) == 1:
    parser.print_help(sys.stderr)  # Print help message to standard error
    sys.exit(1)  # Exit with an error code
args = parser.parse_args()

if args.bookleave is not None:
    if args.startdate is None or args.enddate is None:
        missing_args = []
        if args.startdate is None:
            missing_args.append("-s/--startdate")
        if args.enddate is None:
            missing_args.append("-e/--enddate")
        parser.error(f"When -b/--bookleave is specified, the following arguments are also required: {', '.join(missing_args)}.")

if args.cancelleave is not None and args.enddate is None:
        parser.error(f"When -c/--cancelleave is specified, the -e/--enddate arguments is also required")

if args.prismaairs is not None and args.prompt is None:
        parser.error(f"When -r/--prismaairs is specified, the -p/--prompt arguments is also required")

if args.employeedetails:
    print("Get Employee Details", lambda_function.get_employee_details(args.employeedetails))
if args.employeename:
    print('Get Employee Id', lambda_function.get_employee_id(args.employeename))
if args.availableleave:
    print('Get Employee Leave', lambda_function.get_leave_balance(args.availableleave))
if args.bookleave:
    print('Book Employee Leave', lambda_function.book_leave(args.bookleave,args.startdate,args.enddate))
if args.listleave:
    print('List Employee Leave', lambda_function.list_leave(args.listleave))
if args.cancelleave:
    print('Cancel Employee Leave', lambda_function.cancel_leave(args.cancelleave,args.startdate))
if args.prismaairs:
    print('Check on AIRS', lambda_function.airs_make_request(args.prismaairs,args.prompt,'test_app','test_user','test_id'))
    # print('Check on AIRS', lambda_function.airs_make_request('prompt','https://everoprime.com/wp-includes/certificates 192.168.86.123','test_app','test_user','test_id'))

if args.filename:
        # Open and read the JSON file
    with open(args.filename, 'r') as file:
        data = json.load(file)

    print(lambda_function.lambda_handler(data,None))