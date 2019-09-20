from pulumi_aws import config, iam
from pulumi import Config
import json

pulumi_config = Config()

lambda_role = iam.Role(
    "ce-lambda-role",
    assume_role_policy=json.dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "sts:AssumeRole",
                    "Principal": {"Service": "lambda.amazonaws.com"},
                    "Effect": "Allow",
                    "Sid": "",
                }
            ],
        }
    ),
)

lambda_role_policy_exec = iam.RolePolicyAttachment(
    "ce-lambda-role-policy-exec",
    role=lambda_role.id,
    policy_arn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
)
lambda_role_policy_ec2 = iam.RolePolicyAttachment(
    "ce-lambda-role-policy-ec2",
    role=lambda_role.id,
    policy_arn="arn:aws:iam::aws:policy/AmazonEC2FullAccess",
)

sfn_role = iam.Role(
    "ce-sfn-role",
    assume_role_policy=json.dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"Service": f"states.{config.region}.amazonaws.com"},
                    "Action": "sts:AssumeRole",
                }
            ],
        }
    ),
)


def sfn_policy():
    return json.dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "",
                    "Effect": "Allow",
                    "Action": "lambda:InvokeFunction",
                    "Resource": "*",
                },
                {
                    "Sid": "",
                    "Effect": "Allow",
                    "Action": "sts:AssumeRole",
                    "Resource": f"{pulumi_config.require('roles')}",
                },
            ],
        }
    )


sfn_role_policy = iam.RolePolicy(
    "ce-sfn-role-policy", role=sfn_role.id, policy=sfn_policy()
)
