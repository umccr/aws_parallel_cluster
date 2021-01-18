from aws_cdk import (
    aws_s3_assets as assets,
    aws_imagebuilder as imagebuilder,
    aws_ec2 as ec2,
    aws_ssm as ssm,
    core
)

from pathlib import Path
import tempfile


def replace_string_in_file(file_path, patterns, repls):
    """
    Takes an input file, returns a tmp file name
    """

    # New tmp file object
    new_file = tempfile.NamedTemporaryFile(delete=False)

    with open(file_path, "r") as in_file_h, open(new_file.name, "w") as out_file_h:
        for line in in_file_h:
            new_line = line
            for pattern, repl in zip(patterns, repls):
                new_line = line.replace(pattern, repl)
            out_file_h.write(new_line)

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


class AmiStack(core.Stack):
    def __init__(self, scope: core.Construct, construct_id: str, props: dict, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Set tags as list of dicts instead

        # Get yaml components in upper directory.
        sorted_component_paths = sorted(Path("../components/").glob('**/*.yml'))

        # Make this into a function - can be created with the tmpfile command
        # - sub out with the collection of the ssm parameter
        component_s3_asset_objs = []

        # Add components
        for component_path in sorted_component_paths:
            tmp_component_path = Path(replace_string_in_file(component_path,
                                                             ["__S3_CONFIG_ROOT__", "__VERSION__"],
                                                             [props["s3_config_root"], props["git_tag"]]))
            component_s3_asset_objs.append(create_asset_from_component(self, tmp_component_path, props["s3_read_role"]))

        component_objs = []
        for s3_asset_obj in component_s3_asset_objs:
            component_objs.append(imagebuilder.CfnComponent(self,
                                                            s3_asset_obj.name,
                                                            name=s3_asset_obj.name,
                                                            platform="Linux",
                                                            version=props["git_tag"],
                                                            uri=s3_asset_obj.attr_arn,
                                                            ))

        # Create recipe
        recipe_obj = imagebuilder.CfnImageRecipe(self,
                                                 "parallelClusterImageRecipe",
                                                 name="parallelClusterImageRecipe",
                                                 version=props["git_tag"],
                                                 components=component_objs,
                                                 parent_image=props["parent_image"],
                                                 tags={"Stack": "ParallelCluster",
                                                       "GitTag": props["git_tag"]},
                                                 )
        # Add tags to recipe object
        for tag_dict in props["tags"]:
            core.Tags.of(recipe_obj).add(tag_dict["Key"], tag_dict["Value"])

        # Get VPC
        vpc = ec2.Vpc.from_lookup(self, "VPC", vpc_name="main")

        # Get first public subnet
        subnet = vpc.public_subnets[0]

        # Create security group object
        sg = ec2.SecurityGroup(self, id="parallelClusterImageCreationSecurityGroup", vpc=vpc)
        # Tag security group
        for tag_dict in props["tags"]:
            core.Tags.of(sg).add(tag_dict["Key"], tag_dict["Value"])

        # Create infrastructure
        infrastructure_obj = imagebuilder.CfnInfrastructureConfiguration(self,
                                                                         "parallelClusterInfrastructure",
                                                                         name="parallelClusterInfrastructure",
                                                                         instance_profile_name="parallelClusterInstanceProfile",
                                                                         instance_types=[props["infrastructure_type"]],
                                                                         subnet_id=subnet.subnet_id,
                                                                         security_group_ids=[sg.security_group_id])
        # Add tags to infrastructure object
        for tag_dict in props["tags"]:
            core.Tags.of(infrastructure_obj).add(tag_dict["Key"], tag_dict["Value"])

        # Create Pipeline
        pipeline_obj = imagebuilder.CfnImagePipeline(self,
                                                     "parallelClusterImagePipeline",
                                                     name="parallelClusterImagePipeline",
                                                     image_recipe_arn=recipe_obj.attr_arn,
                                                     infrastructure_configuration_arn=infrastructure_obj.attr_arn)
        # Tag pipeline
        for tag_dict in props["tags"]:
            core.Tags.of(infrastructure_obj).add(tag_dict["Key"], tag_dict["Value"])

        # Return pipeline object attribute arn
        core.CfnOutput(self, "Output",
                       value=pipeline_obj.attr_arn)






