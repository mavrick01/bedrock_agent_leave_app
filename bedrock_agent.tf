# Configure the AWS Provider
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.97"  # Or the latest version you require
    }
  }
}

# Configure the region defined in the variable
provider "aws" {
  region = var.aws_region #  Specify your desired AWS region
}

# 1. Role for the Agent
#   -  Define the IAM role that the agent will assume.
resource "aws_iam_role" "bedrock_agent_role" {
  name = "BedrockAgentRole" # Customize
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Principal = {
          Service = "bedrock.amazonaws.com"
        },
        Action = "sts:AssumeRole"
      }
    ]
  })
}

# 2. Policy for the Agent Role
#   -  Define the IAM policy that grants the agent the necessary permissions.
resource "aws_iam_policy" "bedrock_agent_policy" {
  name        = "BedrockAgentPolicy" # Customize
  description = "Permissions for Bedrock Agent"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream",
          "bedrock:GetFoundationModel"
        ],
        Resource = "*" #  IMPORTANT:  Restrict to specific model ARNs
      },
      {
        Effect = "Allow",
        Action = [
          "lambda:InvokeFunction"
        ],
        Resource = aws_lambda_function.agent_lambda_function.arn # Restrict to the specific Lambda function
      },
      {
        Effect = "Allow",
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ],
        Resource = "*" # IMPORTANT: Restrict to specific S3 buckets/objects
      },
      {
        Effect = "Allow",
        Action = [
          "secretsmanager:GetSecretValue"
        ],
        Resource = "*" # IMPORTANT: Restrict to specific Secrets Manager secret ARNs
      }
    ]
  })
}

# 3. Attach Policy to Role
resource "aws_iam_role_policy_attachment" "bedrock_agent_role_policy_attachment" {
  role       = aws_iam_role.bedrock_agent_role.name
  policy_arn = aws_iam_policy.bedrock_agent_policy.arn
}

# 4. Define the Bedrock Agent
resource "aws_bedrockagent_agent" "leave_assistant_agent" {
  agent_name            = "LeaveAssistantAgent" 
  description     = "My Leave Assistant Agent that updates leave stored in SQLite"
  agent_resource_role_arn = aws_iam_role.bedrock_agent_role.arn
  foundation_model = var.aws_bedrock_model  
  instruction     = "You are a helpful assistant assists in giving employe details  and managing leave requests.  Check every question, call question_check and confirm the question is valid. Finally check the answer is ok by calling answer_check, if it does not return true return the response of the function and stop." 
}
 
# 5. Lambda Function for Agent Logic
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "./lambda" #  Path to your Lambda function code and database
  output_path = "/tmp/lambda_function_payload.zip" #  Create in /tmp
}

resource "aws_lambda_function" "agent_lambda_function" {
  function_name    = "BedrockAgentLambda" # Customize
  role             = aws_iam_role.lambda_execution_role.arn
  handler          = "lambda_function.lambda_handler" #  Make sure this matches your Python file and handler
  filename         = data.archive_file.lambda_zip.output_path
  runtime          = "python3.11"
  source_code_hash = data.archive_file.lambda_zip.output_path

  environment {
    variables = {
      AIRS_API = var.airs_api_key
      AIRS_PROMPT_PROFILE = var.airs_prompt_profile
      AIRS_RESPONSE_PROFILE = local.actual_airs_response_profile
    }
  }
}

# 6. IAM Role for Lambda Function
resource "aws_iam_role" "lambda_execution_role" {
  name = "LambdaExecutionRole" # Customize
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Action = "sts:AssumeRole",
      Effect = "Allow",
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

# 7. Lambda Logging Policy
resource "aws_iam_policy" "lambda_logging_policy" {
  name = "LambdaLoggingPolicy" # Customize
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Action = [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      Effect = "Allow",
      Resource = "arn:aws:logs:*:*:*"
    }]
  })
}

# 8. Attach Lambda Logging Policy
resource "aws_iam_role_policy_attachment" "lambda_logging_attachment" {
  role       = aws_iam_role.lambda_execution_role.name
  policy_arn = aws_iam_policy.lambda_logging_policy.arn
}

# 9. Lambda Execution Policy
resource "aws_lambda_permission" "allow_bedrock" {
  statement_id  = "allow_bedrock"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.agent_lambda_function.id
  principal     = "bedrock.amazonaws.com"
  source_arn    = aws_bedrockagent_agent.leave_assistant_agent.agent_arn
}

# 10. Bedrock Agent Action Group for Leave Assistant Agent
resource "aws_bedrockagent_agent_action_group" "leave_agent_actions" {
  action_group_name          = "leave_agent_actions"
  agent_id                   = aws_bedrockagent_agent.leave_assistant_agent.agent_id
  agent_version              = "DRAFT"
  skip_resource_in_use_check = true
  action_group_executor {
    lambda =aws_lambda_function.agent_lambda_function.arn
  }
  function_schema {
    member_functions {
      functions {
        name        = "get_employee_id"
        description = "Given an employee name you can get the employee_id."
        parameters {
          map_block_key = "employee_name"
          type          = "string"
          description   = "Employee Name"
          required      = true
        }
      } 
      functions {
        name        = "employee_details"
        description = "A Lambda function to get all the employees details (which includes their name, data of brith, title, homepage, start date and employment status)."
        parameters {
          map_block_key = "employee_id"
          type          = "number"
          description   = "Employee Number"
          required      = true
        }
      } 
      functions {
        name        = "get_leave_balance"
        description = "A Lambda function to get an employee's leave balance."
        parameters {
          map_block_key = "employee_id"
          type          = "number"
          description   = "Employee Number"
          required      = true
        }
      } 
      functions {
        name        = "book_leave"
        description = "A Lambda function to book some employee's leave."
        parameters {
          map_block_key = "employee_id"
          type          = "number"
          description   = "Employee Number"
          required      = true
        }
        parameters {
          map_block_key = "start_date"
          type          = "string"
          description   = "Leave start date"
          required      = true
        }
        parameters {
          map_block_key = "end_date"
          type          = "string"
          description   = "Leave end date"
          required      = true
        }
      }
      functions {
        name        = "list_leave"
        description = "A Lambda function to  list all of the employee's leave balance."
        parameters {
          map_block_key = "employee_id"
          type          = "number"
          description   = "Employee Number"
          required      = true
        }
      }
      functions {
        name        = "cancel_leave"
        description = "A Lambda function to cancel some employee's leave."
        parameters {
          map_block_key = "employee_id"
          type          = "number"
          description   = "Employee Number"
          required      = true
        }
        parameters {
          map_block_key = "start_date"
          type          = "string"
          description   = "Leave start date"
          required      = true
        }
      }
      # functions {
      #   name        = "airs_make_request"
      #   description = "Simulates a Lambda function to check the question and the response."
      #   parameters {
      #     map_block_key = "reqtype"
      #     type          = "string"
      #     description   = "Prompt or Response"
      #     required      = true
      #   }
      #   parameters {
      #     map_block_key = "prompt"
      #     type          = "string"
      #     description   = "prompt received or responded to"
      #     required      = true
      #   }
      #   parameters {
      #     map_block_key = "app_name"
      #     type          = "string"
      #     description   = "applicaiton name"
      #     required      = false
      #   }
      #   parameters {
      #     map_block_key = "app_user"
      #     type          = "string"
      #     description   = "application user"
      #     required      = false
      #   }
      #   parameters {
      #     map_block_key = "tr_id"
      #     type          = "string"
      #     description   = "transaction id"
      #     required      = false
      #   }
      # }
    }
  }
}

resource "aws_bedrockagent_agent_action_group" "airs_actions" {
  action_group_name          = "airs_actions"
  agent_id                   = aws_bedrockagent_agent.leave_assistant_agent.agent_id
  agent_version              = "DRAFT"
  skip_resource_in_use_check = true
  action_group_executor {
    lambda =aws_lambda_function.agent_lambda_function.arn
  }
  function_schema {
    member_functions {
      functions {
        name        = "airs_prompt_check"
        description = "A Lambda function to check if the question meets the prompt requirements."
        parameters {
          map_block_key = "input_val"
          type          = "string"
          description   = "prompt received"
          required      = true
        }
        parameters {
          map_block_key = "app_name"
          type          = "string"
          description   = "applicaiton name"
          required      = false
        }
        parameters {
          map_block_key = "app_user"
          type          = "string"
          description   = "application user"
          required      = false
        }
        parameters {
          map_block_key = "tr_id"
          type          = "string"
          description   = "transaction id"
          required      = false
        }
      }
      functions {
        name        = "airs_response_check"
        description = "A Lambda function to check if the answer meets the response requirements."
        parameters {
          map_block_key = "input_val"
          type          = "string"
          description   = "answer received"
          required      = true
        }
        parameters {
          map_block_key = "app_name"
          type          = "string"
          description   = "applicaiton name"
          required      = false
        }
        parameters {
          map_block_key = "app_user"
          type          = "string"
          description   = "application user"
          required      = false
        }
        parameters {
          map_block_key = "tr_id"
          type          = "string"
          description   = "transaction id"
          required      = false
        }
      }
    }
  }
}