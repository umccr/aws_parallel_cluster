# UMCCR's AWS Parallel Cluster <!-- omit in toc -->

[AWS Parallel cluster][aws_parallel_cluster] is a Cloud-HPC system designed to bring traditional HPC practices to the cloud.

UMCCR's intent is to onboard users to AWS, first on HPC and then steadily **transitioning to more cloud-native, efficient alternatives where suitable. This includes but is not limited to Illumina Access Platform (IAP).**

Head to our [wiki home page][wiki_home_page] for more information on getting started and guides.

> Latest aws parallel cluster version: 2.10.1

- [Other announcements](#other-announcements)
  - [Migration clean-up tips](#migration-clean-up-tips)
  - [Blog post](#blog-post)
  

## Other announcements

### Finding the IP/Domain addresses of a recently started cluster

This will list the head node:

```shell
aws ec2 describe-instances --filters Name=tag:UseCase,Values=ParallelCluster Name=tag:Name,Values=ParallelCluster --query "Reservations[*].Instances[*].PublicDnsName"
```

And this will list all nodes, including the head node too:

```shell
aws ec2 describe-instances --filters Name=tag:UseCase,Values=ParallelCluster --query "Reservations[*].Instances[*].PublicDnsName"
```

### Migration clean-up tips 

If you've installed a version of parallel cluster prior to 29/01/2021 please run the following command.

```shell
conda activate pcluster
rm -f \
  "${CONDA_PREFIX}/bin/start_cluster.sh" \
  "${CONDA_PREFIX}/bin/stop_cluster.sh" \
  "${CONDA_PREFIX}/bin/list_clusters.sh"
```

### Blog post

> :construction: Coming soon

[aws_parallel_cluster]: https://github.com/aws/aws-parallelcluster
[wiki_home_page]: https://github.com/umccr/aws_parallel_cluster/wiki
