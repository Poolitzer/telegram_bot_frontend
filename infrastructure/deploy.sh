#!/bin/bash
set -e
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY no_proxy
export AWS_DEFAULT_PROFILE='evg'
export AWS_DEFAULT_REGION='eu-central-1'

TEMPLATE='ec2-for-bot.template'
STACK_NAME='common-bot-test'

echo $(date)' - Validate CF Template'
aws cloudformation validate-template --template-body file://$TEMPLATE

#used ami: amzn2-ami-hvm-2.0.20200304.0-x86_64-gp2

echo $(date)' - Deploy CF Template'
aws cloudformation deploy --template-file $TEMPLATE --stack-name $STACK_NAME \
    --parameter-overrides \
        imageId='<insert-ami-id-here>' \
        instanceSize='t2.micro' \
        keyName='<insert-aws-keypair-name-here>' \
        subnetId='<insert-aws-subnet-id-here>' \
        vpcId='<insert-aws-vpc-id-here>'

