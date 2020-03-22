#!/bin/bash
set -e

if [ -z "$1" ]
  then
    echo "Req. just one argument - telegram bot token"
    exit 1
fi

unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY no_proxy
export AWS_DEFAULT_PROFILE='evg'
export AWS_DEFAULT_REGION='eu-central-1'

TEMPLATE='ec2-for-bot.template'
STACK_NAME='common-bot-test'

echo $(date)' - Validate CF Template'
aws cloudformation validate-template --template-body file://$TEMPLATE

echo $(date)' - Deploy CF Template'
aws cloudformation deploy --template-file $TEMPLATE --stack-name $STACK_NAME \
    --parameter-overrides \
        imageId='<insert-ami-id-here>' \
        instanceSize='t2.micro' \
        keyName='<insert-aws-keypair-name-here>' \
        subnetId='<insert-aws-subnet-id-here>' \
        vpcId='<insert-aws-vpc-id-here>'
        telegramBotToken=$1



