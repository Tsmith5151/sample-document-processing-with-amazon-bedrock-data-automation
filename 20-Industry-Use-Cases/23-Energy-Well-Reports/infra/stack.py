import os

from aws_cdk import CfnOutput, CfnParameter, Duration, RemovalPolicy, Stack
from aws_cdk import aws_ecr as ecr
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as _lambda
from aws_cdk import aws_logs as logs
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_s3_notifications as s3n
from constructs import Construct


class EnergyWellReportsStack(Stack):

    def __init__(
        self, scope: Construct, construct_id: str, environment: str, **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.env_name = environment

        # Look up ECR Repo for Lambda
        ecr_repo = ecr.Repository.from_repository_name(
            self,
            "ECR-BDA-Report-Processor",
            "bda-report-processor",
        )

        image_tag = CfnParameter(
            self,
            "ImageTag",
            type="String",
            description="Image tag for the Lambda function",
            default="latest",
        )

        self.document_bucket = s3.Bucket(
            self,
            "DocumentBucket",
            bucket_name=f"energy-well-reports-{self.env_name}-{self.account}",
            versioned=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=(
                RemovalPolicy.DESTROY
                if self.env_name == "dev"
                else RemovalPolicy.RETAIN
            ),
            auto_delete_objects=True if self.env_name == "dev" else False,
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="DeleteIncompleteMultipartUploads",
                    abort_incomplete_multipart_upload_after=Duration.days(1),
                )
            ],
        )

        lambda_role = iam.Role(
            self,
            "LambdaExecutionRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                )
            ],
            inline_policies={
                "BedrockDataAutomationPolicy": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "bedrock:InvokeModel",
                                "bedrock:InvokeDataAutomationAsync",
                                "bedrock:GetDataAutomationProject",
                                "bedrock:ListDataAutomationProjects",
                                "bedrock:StartIngestionJob",
                                "bedrock:GetIngestionJob",
                                "bedrock:ListIngestionJobs"
                            ],
                            resources=["*"],
                        ),
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "s3:GetObject",
                                "s3:GetObjectVersion",
                                "s3:PutObject",
                                "s3:DeleteObject",
                            ],
                            resources=[
                                self.document_bucket.bucket_arn,
                                f"{self.document_bucket.bucket_arn}/*",
                            ],
                        ),
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "logs:CreateLogGroup",
                                "logs:CreateLogStream",
                                "logs:PutLogEvents",
                            ],
                            resources=["*"],
                        ),
                    ]
                )
            },
        )

        # Create Lambda function using ECR image
        self.processing_function = _lambda.DockerImageFunction(
            self,
            "ProcessingFunction",
            function_name=f"bda-report-processor",
            code=_lambda.DockerImageCode.from_ecr(
                repository=ecr_repo, tag=image_tag.value_as_string
            ),
            timeout=Duration.minutes(5),
            memory_size=1024,
            role=lambda_role,
            environment={
                "ENVIRONMENT": self.env_name,
                "BUCKET_NAME": self.document_bucket.bucket_name,
                "PROJECT_ARN": "",  # This will be set after BDA project creation
                "LOG_LEVEL": "INFO",
            },
            log_retention=(
                logs.RetentionDays.ONE_WEEK
                if self.env_name == "dev"
                else logs.RetentionDays.ONE_MONTH
            ),
        )

        # -- Add S3 event notification to trigger Lambda --
        self.document_bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED,
            s3n.LambdaDestination(self.processing_function),
            s3.NotificationKeyFilter(prefix="reports/", suffix=".pdf"),
        )

        # -- Also trigger for other document types (for future use-cases) --
        for suffix in [".docx", ".doc", ".txt", ".png", ".jpg", ".jpeg"]:
            self.document_bucket.add_event_notification(
                s3.EventType.OBJECT_CREATED,
                s3n.LambdaDestination(self.processing_function),
                s3.NotificationKeyFilter(prefix="reports/", suffix=suffix),
            )

        # Outputs
        CfnOutput(
            self,
            "BucketName",
            value=self.document_bucket.bucket_name,
            description="S3 bucket for document uploads",
        )

        CfnOutput(
            self,
            "LambdaFunctionName",
            value=self.processing_function.function_name,
            description="Lambda function name for processing",
        )

        CfnOutput(
            self,
            "LambdaFunctionArn",
            value=self.processing_function.function_arn,
            description="Lambda function ARN",
        )
