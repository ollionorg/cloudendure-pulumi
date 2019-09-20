import pulumi
from pulumi_aws import lambda_, sfn
import iam
import json

find_instance = lambda_.Function(
    "ce-find-instance",
    role=iam.lambda_role.arn,
    runtime="python3.7",
    handler="find_instance.lambda_handler",
    code=pulumi.AssetArchive({".": pulumi.FileArchive("./lambda")}),
)

get_instance_status = lambda_.Function(
    "ce-get-instance-status",
    role=iam.lambda_role.arn,
    runtime="python3.7",
    handler="get_instance_status.lambda_handler",
    code=pulumi.AssetArchive({".": pulumi.FileArchive("./lambda")}),
)

create_image = lambda_.Function(
    "ce-create-image",
    role=iam.lambda_role.arn,
    runtime="python3.7",
    handler="create_image.lambda_handler",
    code=pulumi.AssetArchive({".": pulumi.FileArchive("./lambda")}),
)

get_image_status = lambda_.Function(
    "ce-get-image-status",
    role=iam.lambda_role.arn,
    runtime="python3.7",
    handler="get_image_status.lambda_handler",
    code=pulumi.AssetArchive({".": pulumi.FileArchive("./lambda")}),
)

share_image = lambda_.Function(
    "ce-share-image",
    role=iam.lambda_role.arn,
    runtime="python3.7",
    handler="share_image.lambda_handler",
    code=pulumi.AssetArchive({".": pulumi.FileArchive("./lambda")}),
)

copy_image = lambda_.Function(
    "ce-copy-image",
    role=iam.lambda_role.arn,
    runtime="python3.7",
    handler="copy_image.lambda_handler",
    code=pulumi.AssetArchive({".": pulumi.FileArchive("./lambda")}),
)

get_copy_status = lambda_.Function(
    "ce-get-copy-status",
    role=iam.lambda_role.arn,
    runtime="python3.7",
    handler="get_copy_status.lambda_handler",
    code=pulumi.AssetArchive({".": pulumi.FileArchive("./lambda")}),
)

split_image = lambda_.Function(
    "ce-split-image",
    role=iam.lambda_role.arn,
    runtime="python3.7",
    handler="split_image.lambda_handler",
    code=pulumi.AssetArchive({".": pulumi.FileArchive("./lambda")}),
)

image_cleanup = lambda_.Function(
    "ce-image-cleanup",
    role=iam.lambda_role.arn,
    runtime="python3.7",
    handler="image_cleanup.lambda_handler",
    code=pulumi.AssetArchive({".": pulumi.FileArchive("./lambda")}),
)

state_definition = pulumi.Output.all(
    find_instance.arn,
    get_instance_status.arn,
    create_image.arn,
    get_image_status.arn,
    share_image.arn,
    copy_image.arn,
    get_copy_status.arn,
    split_image.arn,
    image_cleanup.arn,
).apply(
    lambda arns: f"""
{{
  "Comment": "A state machine that finds for a converted CloudEndure instance, waits for it to become viable, creates an image, and shares it to a destination account",
  "StartAt": "Find Instance",
  "States": {{
    "Find Instance": {{
      "Type": "Task",
      "Resource": "{arns[0]}",
      "ResultPath": "$",
      "Next": "Instance Found?",
      "Retry": [
        {{
          "ErrorEquals": ["States.ALL"],
          "IntervalSeconds": 1,
          "MaxAttempts": 3,
          "BackoffRate": 2
        }}
      ]
    }},
    "Instance Found?": {{
      "Type": "Choice",
      "Choices": [
        {{
          "Variable": "$.instance_id",
          "StringEquals": "not-found",
          "Next": "Not A Migration Instance"
        }},
        {{
          "Variable": "$.instance_id",
          "StringEquals": "not-migration",
          "Next": "Not A Migration Instance"
        }}
      ],
      "Default": "Get Instance Status"
    }},
    "Not A Migration Instance": {{
      "Type": "Succeed"
    }},
    "Get Instance Status": {{
      "Type": "Task",
      "Resource": "{arns[1]}",
      "ResultPath": "$.instance_status",
      "Next": "Instance Ready?",
      "Retry": [
        {{
          "ErrorEquals": ["States.ALL"],
          "IntervalSeconds": 1,
          "MaxAttempts": 3,
          "BackoffRate": 2
        }}
      ]
    }},
    "Instance Ready?": {{
      "Type": "Choice",
      "Choices": [
        {{
          "Variable": "$.instance_status",
          "StringEquals": "running",
          "Next": "Create Image"
        }},
        {{
          "Or": [
            {{
            "Variable": "$.instance_status",
            "StringEquals": "stopped"
            }},
            {{
            "Variable": "$.instance_status",
            "StringEquals": "terminated"
            }}
          ],
          "Next": "Image Failed"
        }}
      ],
      "Default": "Wait For Instance"
    }},
    "Wait For Instance": {{
      "Type": "Wait",
      "Seconds": 60,
      "Next": "Get Instance Status"
    }},
    "Create Image": {{
      "Type": "Task",
      "Resource": "{arns[2]}",
      "ResultPath": "$.migrated_ami_id",
      "Next": "Get Image Status",
      "Retry": [
        {{
          "ErrorEquals": ["States.ALL"],
          "IntervalSeconds": 1,
          "MaxAttempts": 3,
          "BackoffRate": 2
        }}
      ]
    }},
    "Get Image Status": {{
      "Type": "Task",
      "Resource": "{arns[3]}",
      "ResultPath": "$.ami_status",
      "Next": "Image Complete?",
      "Retry": [
        {{
          "ErrorEquals": ["States.ALL"],
          "IntervalSeconds": 1,
          "MaxAttempts": 3,
          "BackoffRate": 2
        }}
      ]
    }},
    "Image Complete?": {{
      "Type": "Choice",
      "Choices": [
        {{
          "Or": [
            {{
            "Variable": "$.ami_status",
            "StringEquals": "failed"
            }},
            {{
            "Variable": "$.ami_status",
            "StringEquals": "error"
            }}
          ],
          "Next": "Image Failed"
        }},
        {{
          "Variable": "$.ami_status",
          "StringEquals": "available",
          "Next": "Share Image"
        }}
      ],
      "Default": "Wait For Image"
    }},
    "Wait For Image": {{
      "Type": "Wait",
      "Seconds": 60,
      "Next": "Get Image Status"
    }},
    "Image Failed": {{
      "Type": "Fail",
      "Cause": "Image Failed",
      "Error": "Create Image returned failed or error."
    }},
    "Share Image": {{
      "Type": "Task",
      "Resource": "{arns[4]}",
      "ResultPath": "$.shared",
      "Next": "Copy Image",
      "Retry": [
        {{
          "ErrorEquals": ["States.ALL"],
          "IntervalSeconds": 1,
          "MaxAttempts": 3,
          "BackoffRate": 2
        }}
      ]
    }},
    "Copy Image": {{
      "Type": "Task",
      "Resource": "{arns[5]}",
      "ResultPath": "$.copy_ami",
      "Next": "Wait For Copy",
      "Retry": [
        {{
          "ErrorEquals": ["States.ALL"],
          "IntervalSeconds": 1,
          "MaxAttempts": 3,
          "BackoffRate": 2
        }}
      ]
    }},
    "Wait For Copy": {{
      "Type": "Wait",
      "Seconds": 60,
      "Next": "Get Copy Status"
    }},
    "Get Copy Status": {{
      "Type": "Task",
      "Resource": "{arns[6]}",
      "ResultPath": "$.status",
      "Next": "Copy Complete?",
      "Retry": [
        {{
          "ErrorEquals": ["States.ALL"],
          "IntervalSeconds": 1,
          "MaxAttempts": 3,
          "BackoffRate": 2
        }}
      ]
    }},
    "Copy Complete?": {{
      "Type": "Choice",
      "Choices": [
        {{
          "Or": [
            {{
            "Variable": "$.status",
            "StringEquals": "failed"
            }},
            {{
            "Variable": "$.status",
            "StringEquals": "error"
            }}
          ],
          "Next": "Copy Failed"
        }},
        {{
          "Variable": "$.status",
          "StringEquals": "available",
          "Next": "Split Image"
        }}
      ],
      "Default": "Wait For Copy"
    }},
    "Copy Failed": {{
      "Type": "Fail",
      "Cause": "Copy Failed",
      "Error": "Copy Image returned failed or error."
    }},
    "Split Image": {{
      "Type": "Task",
      "Resource": "{arns[7]}",
      "ResultPath": "$.split_ami_id",
      "Next": "Image Cleanup",
      "Retry": [
        {{
          "ErrorEquals": ["States.ALL"],
          "IntervalSeconds": 1,
          "MaxAttempts": 3,
          "BackoffRate": 2
        }}
      ]
    }},
    "Image Cleanup": {{
      "Type": "Task",
      "Resource": "{arns[8]}",
      "ResultPath": "$.cleaned_up",
      "End": true,
      "Retry": [
        {{
          "ErrorEquals": ["States.ALL"],
          "IntervalSeconds": 1,
          "MaxAttempts": 3,
          "BackoffRate": 2
        }}
      ]
    }}
  }}
}}
"""
)

state_defn = state_machine = sfn.StateMachine(
    "stateMachine", role_arn=iam.sfn_role.arn, definition=state_definition
)

pulumi.export("state_machine_arn", state_machine.id)

