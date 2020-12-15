#!/usr/bin/env python3

from aws_cdk import core

from ami.ami_stack import AmiStack


app = core.App()
AmiStack(app, "ami")

app.synth()
