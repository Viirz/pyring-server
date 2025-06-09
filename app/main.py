from app import create_app
from app.utils.scheduler import scheduler

scheduler.start()
print("Scheduler started with jobs:", scheduler.print_jobs())

application = create_app()

if __name__ == "__main__":
    # This will only run when called directly (not with Gunicorn)
    application.run(host='0.0.0.0', port=5000, debug=False)