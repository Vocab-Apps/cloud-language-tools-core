import logging
import schedule
import time
import datetime
import boto3
import json
import os
import redisdb
import user_utils

def backup_redis_db():
    scp_username = os.environ['RSYNC_NET_USER']
    scp_hostname = os.environ['RSYNC_NET_HOST']

    logging.info('backing up redis db')
    connection = redisdb.RedisDb()

    session = boto3.session.Session()
    client = session.client('s3',
                            region_name=os.environ['SPACE_REGION'],
                            endpoint_url=os.environ['SPACE_ENDPOINT_URL'],
                            aws_access_key_id=os.environ['SPACE_KEY'],
                            aws_secret_access_key=os.environ['SPACE_SECRET'])    
    bucket_name = 'cloud-language-tools-redis-backups'

    full_db_dump = connection.full_db_dump()
    time_str = datetime.datetime.now().strftime('%H')
    file_name = f'redis_backup_{time_str}.json'
    client.put_object(Body=str(json.dumps(full_db_dump)), Bucket=bucket_name, Key=file_name)
    logging.info(f'wrote {file_name} to {bucket_name}')


def update_airtable():
    logging.info('updating airtable')
    utils = user_utils.UserUtils()
    utils.update_airtable_all()
    logging.info('finished updating airtable')

def report_getcheddar_usage():
    logging.info('reporting getcheddar usage')
    utils = user_utils.UserUtils()
    utils.report_getcheddar_usage_all_users()
    logging.info('finished reporting getcheddar usage')

def setup_tasks():
    logging.info('running tasks once')
    report_getcheddar_usage()
    backup_redis_db()
    update_airtable()
    logging.info('setting up tasks')
    schedule.every(1).hour.do(backup_redis_db)
    schedule.every(1).hours.do(update_airtable)
    schedule.every(6).hours.do(report_getcheddar_usage)


def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(5)

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s', 
                        datefmt='%Y%m%d-%H:%M:%S',
                        level=logging.INFO)    
    setup_tasks()
    run_scheduler()