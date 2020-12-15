from aws_cdk import (
    aws_s3_assets as assets,
    aws_imagebuilder as imagebuilder,
    aws_ec2 as ec2,
    core
)

from pathlib import Path


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
    # FIXME - how are props defined? Could we use this to hardcode in roles/sg/buckets? for each account
    def __init__(self, scope: core.Construct, construct_id: str, props, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here
        # TODO - look at umccrise batch to create components
        s3_read_role = None  # FIXME - add s3 read role through props or
        parent_image = None  # FIXME - could be hardcoded or through props?
        infrastructure_type = "t2.medium"  # FIXME - should this go through props?
        security_group_id = None  # FIXME - to go through props
        component_version = None  # FIXME - to go through props
        recipe_version = None  # FIXME - to go through props

        # Get yaml components in upper directory.
        sorted_component_paths = sorted(Path("../components/").glob('**/*.yaml'))

        component_s3_asset_objs = []

        # Add components
        for component_path in sorted_component_paths:
            component_s3_asset_objs.append(create_asset_from_component(self, component_path, s3_read_role))

        component_objs = []
        for s3_asset_obj in component_s3_asset_objs:
            component_objs.append(imagebuilder.CfnComponent(self,
                                                            s3_asset_obj.name,
                                                            name=s3_asset_obj.name,
                                                            platform="Linux",
                                                            version=component_version,
                                                            uri=s3_asset_obj.attr_arn
                                                            ))

        # Create recipe
        recipe_obj = imagebuilder.CfnImageRecipe(self,
                                                 "parallelClusterImageRecipe",
                                                 name="parallelClusterImageRecipe",
                                                 version=recipe_version,
                                                 components=component_objs,
                                                 parent_image=parent_image)

        # Get VPC
        vpc = ec2.Vpc.from_lookup(self, "VPC", vpc_name="main")

        # Get first public subnet
        subnet = vpc.public_subnets[0]

        # Get security group object
        sg = ec2.SecurityGroup.from_security_group_id(self,
                                                      "SG",
                                                      security_group_id=security_group_id)

        # Create infrastructure
        infrastructure_obj = imagebuilder.CfnInfrastructureConfiguration(self,
                                                                         "parallelClusterInfrastructure",
                                                                         name="parallelClusterInfrastructure",
                                                                         instance_types=[infrastructure_type],
                                                                         subnet_id=subnet.subnet_id,
                                                                         security_group_ids=[sg.security_group_id])

        # Create Pipeline
        pipeline_obj = imagebuilder.CfnImagePipeline(self,
                                                     "parallelClusterImagePipeline",
                                                     name="parallelClusterImagePipeline",
                                                     image_recipe_arg=recipe_obj.attr_arn,
                                                     infrastructure_configuration_arn=infrastructure_obj.attr_arn)










