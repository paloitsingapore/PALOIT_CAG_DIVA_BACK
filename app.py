#!/usr/bin/env python3
import os

import aws_cdk as cdk

from assisted_wayfinding_backend.assisted_wayfinding_backend_stack import AssistedWayfindingBackendStack
from assisted_wayfinding_backend.config import get_config

app = cdk.App()

# Get account and region from environment variables
account = os.environ.get('CDK_DEFAULT_ACCOUNT')
region = os.environ.get('CDK_DEFAULT_REGION')

# Get the environment name from context, default to 'dev' if not specified
env_name = app.node.try_get_context('env') or 'dev'

# Get the configuration for the specified environment
config = get_config(env_name)

AssistedWayfindingBackendStack(app, f"{config['project_name']}Stack-{env_name}",
    env=cdk.Environment(account=account, region=region),
    config=config,
)

app.synth()
