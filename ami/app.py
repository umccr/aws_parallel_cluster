#!/usr/bin/env python3

from aws_cdk import core

from ami.ami_stack import AmiStack


def tags_str_to_list(tags):
    """
    Convert tags from a "Key=a,Value=b Key=c,Value=d" string to
    [
     {"Key": "a",
      "Value": "b"
     },
     {"Key": "c",
      "Value": "d"
     }
    ]
    """

    tags = [
        {tag_item.split("=")[0]: tag_item.split("=")[-1]
         for tag_item in tag.split(",", 1)
         }
        for tag in tags.split(" ")
    ]

    return tags


app = core.App()

# Create stack
AmiStack(app,
         "ami",
         env={
                     # ENV Values
                     "account": app.node.try_get_context("ACCOUNT"),
                     "region": app.node.try_get_context("REGION"),
         },
         props={
                     # Context variables
                     "tags": tags_str_to_list(app.node.try_get_context("TAGS")),
                     "s3_read_role": app.node.try_get_context("S3_READ_ROLE"),
                     "parent_image": app.node.try_get_context("PARENT_IMAGE"),
                     "infrastructure_type": app.node.try_get_context("INFRASTRUCTURE_TYPE"),
                     "s3_config_root": app.node.try_get_context("S3_CONFIG_ROOT"),
                     "git_tag": app.node.try_get_context("GIT_TAG")
         }
)

app.synth()
