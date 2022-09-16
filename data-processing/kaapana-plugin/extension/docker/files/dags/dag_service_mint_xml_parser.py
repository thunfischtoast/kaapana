from airflow.utils.log.logging_mixin import LoggingMixin
from airflow.utils.dates import days_ago
from datetime import timedelta
from airflow.models import DAG
from kaapana.operators.LocalGetInputDataOperator import LocalGetInputDataOperator
from kaapana.operators.LocalWorkflowCleanerOperator import LocalWorkflowCleanerOperator
from kaapana.operators.LocalMinioOperator import LocalMinioOperator
from kaapana.operators.MintXmlParserOperator import MintXmlParserOperator
from kaapana.operators.MintInputValidationOperator import MintInputValidationOperator

log = LoggingMixin().log

args = {
    'ui_visible': False,
    'owner': 'system',
    'start_date': days_ago(0),
    'retries': 2,
    'retry_delay': timedelta(seconds=30),
}

dag = DAG(
    dag_id='service-mint-xml-parser',
    default_args=args,
    schedule_interval=None,
    tags=['service']
)
get_input = LocalGetInputDataOperator(dag=dag)
validate = MintInputValidationOperator(dag=dag, input_operator=get_input)
parse = MintXmlParserOperator(dag=dag, input_operator=validate)
put_to_minio_csv = LocalMinioOperator(dag=dag, action='put', action_operators=[validate, parse],
                                      file_white_tuples=('.csv', '.xml'))
clean = LocalWorkflowCleanerOperator(dag=dag, clean_workflow_dir=True)

get_input >> validate >> parse >> put_to_minio_csv >> clean
