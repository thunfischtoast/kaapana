from datetime import timedelta
from kaapana.operators.KaapanaBaseOperator import KaapanaBaseOperator, default_registry, default_platform_abbr, default_platform_version

from airflow.utils.trigger_rule import TriggerRule


class BasicTorchTransformationOperator(KaapanaBaseOperator):

    def __init__(self,
                 dag,
                 env_vars=None,
                 execution_timeout=timedelta(hours=3),
                 *args, **kwargs
                 ):

        super().__init__(
            dag=dag,
            name='basic-torch-transformations',
            image=f"{default_registry}/basic-transformations:{default_platform_abbr}_{default_platform_version}__0.1.0",
            image_pull_secrets=["registry-secret"],
            execution_timeout=execution_timeout,
            env_vars=env_vars,      # forward newly set env variables to container
            ram_mem_mb=10000,        # and RAM memory specs to avoid K8s' OMMKilled errros; default=2000
            image_pull_policy="Always",
            *args,
            **kwargs
        )
