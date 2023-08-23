echo "Running deploy.sh..."
cp /etl/etl.py /opt/prefect/etl.py
sleep 120

cd /opt/prefect/
prefect deployment build /opt/prefect/etl.py:etl_flow -n etl-deployment -q main --cron "0 0 * * *"
prefect deployment apply etl_flow-deployment.yaml

prefect agent start -q 'main'
echo "deploy.sh finished"