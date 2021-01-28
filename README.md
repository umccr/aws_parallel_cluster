# UMCCR's AWS Parallel Cluster <!-- omit in toc -->

[AWS Parallel cluster][aws_parallel_cluster] is a Cloud-HPC system designed to bring traditional HPC practices to the cloud.

UMCCR's intent is to onboard users to AWS, first on HPC and then steadily **transitioning to more cloud-native, efficient alternatives where suitable. This includes but is not limited to Illumina Access Platform (IAP).**

- [Other announcements](#other-announcements)
  - [Migration clean-up tips](#migration-clean-up-tips)
  - [Blog post](#blog-post)



Head to our [wiki home page][wiki_home_page] for more information on getting started and guides.

> Latest aws parallel cluster version: 2.10.1

## Other announcements

### Migration clean-up tips 

After installing the latest version please run the following.

```shell
conda activate pcluster
rm -f \
  "${CONDA_PREFIX}/bin/start_cluster.sh" \
  "${CONDA_PREFIX}/bin/stop_cluster.sh" \
  "${CONDA_PREFIX}/bin/list_clusters.sh"
```

### Blog post

> Coming soon


[wiki_home_page]: https://github.com/umccr/aws_parallel_cluster/wiki