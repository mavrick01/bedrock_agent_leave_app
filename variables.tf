
variable "aws_region" { 
  description = "value for aws region"
  default = "us-east-1"
}

# Enter you AIRS application API Key - You must insert one for it to work
variable "airs_api_key" {
  description = "Enter you AIRS application API Key"
  default = ""
} 
 
 # Enter you prompt profile name - You must insert one for it to work
variable "airs_prompt_profile" {
  description = "Enter you prompt profile name"
  default = ""
}

# Enter you AIRS response profile name - If you do not define it, it will use the same profile as the prompt profile
variable "airs_response_profile" {
  description = "Enter you AIRS response profile name"
  default = ""
}

# Use locals to determine the effective value
locals {
  # actual_airs_response_profile will be override_value if airs_prompt_profile is not null.
  # Otherwise, it will be primary_value.
    actual_airs_response_profile = var.airs_response_profile != "" ? var.airs_response_profile : var.airs_prompt_profile
}

#Define the model to use
variable "aws_bedrock_model" {
  description = "AWS LLM Model to use, defaults to the Claude 3 Haiku"
  default = "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-haiku-20240307-v1:0"
}