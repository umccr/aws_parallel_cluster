from aws_cdk import (
    aws_s3_assets as assets,
    aws_imagebuilder as imagebuilder,
    aws_ec2 as ec2,
    aws_ssm as ssm,
    core
)

from pathlib import Path
import tempfile


def replace_string_in_file(file_path, pattern, repl):
    """
    Takes an input file, returns a tmp file name
    """

    # New tmp file object
    new_file = tempfile.NamedTemporaryFile(delete=False)

    with open(file_path, "r") as in_file_h, open(new_file.name, "w") as out_file_h:
        for line in in_file_h:
            out_file_h.write(line.replace(pattern, repl))

    return new_file.name


def create_asset_from_component(stack_obj, component_path, role):
    """
    Creates an s3 asset attribute from a yaml component config file
    :param component_path:
    :return:
    """

    component_name = component_path.name

    asset_obj = assets.Asset(
        stack_obj,
        component_name,
        path=component_path
    )

    asset_obj.grant_read(role)

    return asset_obj


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


class AmiStack(core.Stack):
    def __init__(self, scope: core.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here
        s3_read_role = core.CfnParameter(self, id="s3_read_role", type="String")
        parent_image = core.CfnParameter(self, id="parent_image", type="String")
        infrastructure_type = core.CfnParameter(self, id="infrastructure_type", type="String")
        component_version = core.CfnParameter(self, id="component_version", type="String")
        recipe_version = core.CfnParameter(self, id="recipe_version", type="String")
        tags_str = core.CfnParameter(self, id="tags", type="String")
        s3_config_root_ssm_key = core.CfnParameter(self, id="ssm_s3_config_root", type="String")

        # Set tags as list of dicts instead
        tags_list = tags_str_to_list(tags_str)

        # Get SSM value for S3 Config Root
        s3_config_root_ssm_value = ssm.StringParameter.value_for_string_parameter(self, s3_config_root_ssm_key.value_as_string)

        # Get yaml components in upper directory.
        sorted_component_paths = sorted(Path("../components/").glob('**/*.yml'))

        # Make this into a function - can be created with the tmpfile command
        # - sub out with the collection of the ssm parameter
        component_s3_asset_objs = []

        # Add components
        for component_path in sorted_component_paths:
            tmp_component_path = Path(replace_string_in_file(component_path, "__S3_CONFIG_ROOT__", s3_config_root_ssm_value))
            component_s3_asset_objs.append(create_asset_from_component(self, component_path, s3_read_role))

        component_objs = []
        for s3_asset_obj in component_s3_asset_objs:
            component_objs.append(imagebuilder.CfnComponent(self,
                                                            s3_asset_obj.name,
                                                            name=s3_asset_obj.name,
                                                            platform="Linux",
                                                            version=component_version.value_as_string,
                                                            uri=s3_asset_obj.attr_arn,
                                                            ))

        # Create recipe
        recipe_obj = imagebuilder.CfnImageRecipe(self,
                                                 "parallelClusterImageRecipe",
                                                 name="parallelClusterImageRecipe",
                                                 version=recipe_version.value_as_string,
                                                 components=component_objs,
                                                 parent_image=parent_image.value_as_string,
                                                 )
        # Add tags to recipe object
        for tag_dict in tags_list:
            core.Tags.of(recipe_obj).add(tag_dict["Key"], tag_dict["Value"])

        # Get VPC
        vpc = ec2.Vpc.from_lookup(self, "VPC", vpc_name="main")

        # Get first public subnet
        subnet = vpc.public_subnets[0]

        # Create security group object
        sg = ec2.SecurityGroup(self, id="parallelClusterImageCreationSecurityGroup", vpc=vpc)
        # Tag security group
        for tag_dict in tags_list:
            core.Tags.of(sg).add(tag_dict["Key"], tag_dict["Value"])

        # Create infrastructure
        infrastructure_obj = imagebuilder.CfnInfrastructureConfiguration(self,
                                                                         "parallelClusterInfrastructure",
                                                                         name="parallelClusterInfrastructure",
                                                                         instance_profile_name="parallelClusterInstanceProfile",
                                                                         instance_types=[infrastructure_type.value_as_string],
                                                                         subnet_id=subnet.subnet_id,
                                                                         security_group_ids=[sg.security_group_id])
        # Add tags to infrastructure object
        for tag_dict in tags_list:
            core.Tags.of(infrastructure_obj).add(tag_dict["Key"], tag_dict["Value"])

        # Create Pipeline
        pipeline_obj = imagebuilder.CfnImagePipeline(self,
                                                     "parallelClusterImagePipeline",
                                                     name="parallelClusterImagePipeline",
                                                     image_recipe_arn=recipe_obj.attr_arn,
                                                     infrastructure_configuration_arn=infrastructure_obj.attr_arn)
        # Tag pipeline
        for tag_dict in tags_list:
            core.Tags.of(infrastructure_obj).add(tag_dict["Key"], tag_dict["Value"])

        # Return pipeline object attribute arn
        core.CfnOutput(self, "Output",
                       value=pipeline_obj.attr_arn)






