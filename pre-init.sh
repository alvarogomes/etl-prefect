echo "Running pre-init.sh..."
cp /etl/etl.py /opt/prefect/etl.py
sleep 15

cd /opt/prefect/
prefect deployment build /opt/prefect/etl.py:etl_flow -n etl-deployment -q main --cron "0 0 * * *"
prefect deployment apply etl_flow-deployment.yaml

prefect agent start -q 'main'
echo "pre-init.sh finished"