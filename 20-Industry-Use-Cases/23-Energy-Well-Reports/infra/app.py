#!/usr/bin/env python3
import os

import aws_cdk as cdk
import boto3
from stack import EnergyWellReportsStack

app = cdk.App()

default_account = boto3.client("sts").get_caller_identity()["Account"]

# -- Get environment variables or use defaults --
account = os.environ.get("CDK_DEFAULT_ACCOUNT", default_account)
region = os.environ.get("CDK_DEFAULT_REGION", "us-east-1")
environment = os.environ.get("ENVIRONMENT", "dev")

EnergyWellReportsStack(
    app,
    f"EnergyWellReports-{environment}",
    env=cdk.Environment(account=account, region=region),
    environment=environment,
)

app.synth()
