# Bedrock Leave Agent with AIRS protection

The terraform will deploy a AWS Bedock agent that can act as a simple leave agent.

It has an employee database that it runs in memory and will respond and book/cancel/list leave 



Some utilties also exist:
* `utils\local_lambda_test.py` : This script contains calls the lambda functions directly. It helps to test the function. Note you will have to install the `requirements.txt`, create the environment variables AIRS_API, AIRS_PROMPT_PROFILE and AIRS_RESPONSE_PROFILE and copy the `employee_database.db` to `/tmp` (it is hardcoded in the lambda function)
* `utils\create_sample_db.py` : This script will populate the employee_database.db with some sample data
* `utils\dumple_sqllite_db.py` : this dumps the entire employee_database.db
* `lambda_test` directory : This contains the json for differemt lambda function tests (you create lambda tests, or youcan input them into `local_lambda_test.py`)


---
## Task 0. Bedrock Foundation Model Access
Ensure you have access to your bedrock agent. by default we use Claude 3 Haiku model, but if you change it ensure you have permission (AWS Console -> Amazon Bedrock -> Bedrock Configurations -> Model Access)

## Task 1. Enter Variable
Copy `terraform.tfvars.example` to `terraform.tfvars` and edit the variables.  You will need your Prisma AIRS API Key and at least the prompt profile name (if you do not define the response profile it will use the same profile name as the prompt profile)

By default this agent uses the Claude 3 Haiku model, change the variable `aws_bedrock_model` will change the agent used.

## Task 2. Deploy Terraform
Deploy terraform with `terraform init` and `terraform apply`

## Task 3. Test the Agent
As this is a demo you will show it is in the AWS Console. Go to AWS Console -> Amazon Bedrock -> Builder Tools -> Agents -> LeaveAssistantAgent

You can test it and follow the traces.

If you want to see more details on the excution of the Lambda Scripts. Go to AWS Console -> CloudWatch -> Log groups -> /aws/lambda/BedrockAgentLambda -> Log Stream. You can see the latest log there.

Key items to look for are:
* Ensure the API Call went successfully and got a response : `API call successful. Response: {'action': ...`
* See that it responded correctly : `Response: {'response': {'actionGroup': 'leave_agent_actions', 'function': 'airs_make_request', 'functionResponse': {'responseBody': ...`


> [!NOTE]
>  The `lambda` directory contains the lambda python script, the sample database and the requests library (this is not available by default in AWS lambda)


[!NOTE]
Some utilties also exist:
* `utils\local_security_processing.py` : This script contains the same functiosn as the lambda script. It helps to test the function. Note you will have to install the `requirements.txt` and create the environment variables AIRS_API, AIRS_PROMPT_PROFILE and AIRS_RESPONSE_PROFILE
* `utils\create_sample_db.py` : This script will populate the employee_database.db with some sample data
* `utils\dumple_sqllite_db.py` : this dumps the entire employee_database.db
* `lambda_test` directory : This contains the json for diffrent lambda function tests

