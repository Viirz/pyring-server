from apscheduler.schedulers.background import BackgroundScheduler
from app.utils.jwt_utils import cleanup_blacklist
from app.utils.agent_utils import check_and_update_agent_status

# Initialize the scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(check_and_update_agent_status, 'interval', minutes=1)  # Run every 5 minutes
scheduler.add_job(cleanup_blacklist, 'interval', minutes=1)  # Run every 10 minutes