from datetime import timedelta
from kaapana.operators.KaapanaBaseOperator import KaapanaBaseOperator, default_registry, default_platform_abbr, default_platform_version

from airflow.utils.trigger_rule import TriggerRule


class BreastDensityClassifierOperator(KaapanaBaseOperator):

    def __init__(self,
                 dag,
                 env_vars=None,
                 second_input_operator=None,
                 minio_operator=None,   # additional argument to make outputs of minio operator also available in container of BreastDensityClassifierOperator
                 execution_timeout=None,
                 *args, **kwargs
                 ):

        # set minio operator's output dir as env variable
        if env_vars is None:
            env_vars = {}
        envs = {
            "MINIO_OPERATOR_OUT_DIR" : minio_operator.operator_out_dir if minio_operator is not None else '',
            "MINIO_OPERATOR_BUCKETNAME": minio_operator.bucket_name if minio_operator is not None else '',
            # "DAG_CONF": kwargs['run_id'].conf
            # "BATCH_SIZE": dag.default_args['ui_forms']['batch_size']
            # "CUDA_VISIBLE_DEVICES": '1',
            "SECOND_OPERATOR_OUT_DIR": second_input_operator.operator_out_dir if second_input_operator is not None else '',
        }
        env_vars.update(envs)
        
        super().__init__(
            dag=dag,
            name='breast_density_classifier',
            image=f"{default_registry}/simple-classification:{default_platform_abbr}_{default_platform_version}__0.1.0",
            image_pull_secrets=["registry-secret"],
            execution_timeout=execution_timeout,
            env_vars=env_vars,      # forward newly set env variables to container
            gpu_mem_mb=10000,        # define GPU memory; default=6000
            ram_mem_mb=8000,        # and RAM memory specs to avoid K8s' OMMKilled errros; default=2000
            ram_mem_mb_lmt=24000,   # default=12000
            image_pull_policy="Always",
            *args,
            **kwargs
        )