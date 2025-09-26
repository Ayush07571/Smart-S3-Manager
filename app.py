from flask import Flask, render_template, request, jsonify
from s3_lifecycle_policy import (
    get_s3_client, 
    create_s3_bucket, 
    upload_sample_file, 
    apply_lifecycle_policy
)
import logging
import os

# Initialize Flask app
app = Flask(__name__, static_folder='static', template_folder='templates') # Explicitly setting folders

# Setup logging
logging.basicConfig(filename='logs/lifecycle_logs.txt', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@app.route('/')
def index():
    """Renders the main frontend page."""
    # We no longer pass BUCKET_NAME from config, as the user will input it
    return render_template('index.html')

def execute_aws_action(data, action_func, *args):
    """A helper to abstract AWS client setup and error handling."""
    access_key = data.get('access_key')
    secret_key = data.get('secret_key')
    region = data.get('region')
    bucket_name = data.get('bucket_name')

    if not all([access_key, secret_key, region, bucket_name]):
        return jsonify({"status": "error", "message": "Missing required fields (Credentials, Region, or Bucket Name)."}), 400

    try:
        s3 = get_s3_client(access_key, secret_key, region)
        # Call the specific action function
        result = action_func(s3, *args)
        return jsonify(result), 200
    except Exception as e:
        error_msg = f"AWS Client Error (Check credentials/permissions): {e}"
        logging.error(error_msg)
        return jsonify({"status": "error", "message": error_msg}), 500


@app.route('/create_bucket', methods=['POST'])
def handle_create_bucket():
    data = request.json
    return execute_aws_action(data, lambda s3: create_s3_bucket(s3, data['bucket_name'], data['region']))


@app.route('/upload_file', methods=['POST'])
def handle_upload_file():
    data = request.json
    file_key = data.get('file_key', 'sample-media-file.txt')
    return execute_aws_action(data, lambda s3: upload_sample_file(s3, data['bucket_name'], file_key))


@app.route('/apply_custom_lifecycle', methods=['POST'])
def handle_apply_custom_lifecycle():
    data = request.json
    glacier_days = data.get('glacier_days')
    deep_archive_days = data.get('deep_archive_days')
    expiration_days = data.get('expiration_days')
    
    if not all([glacier_days, deep_archive_days, expiration_days]):
        return jsonify({"status": "error", "message": "Missing lifecycle policy days."}), 400

    return execute_aws_action(
        data, 
        lambda s3: apply_lifecycle_policy(s3, data['bucket_name'], glacier_days, deep_archive_days, expiration_days)
    )

# New dedicated function for Intelligent Tiering Configuration (uses a simpler Boto3 call)
@app.route('/enable_intelligent_tiering', methods=['POST'])
def handle_enable_intelligent_tiering():
    data = request.json
    
    def put_intelligent_tiering_config(s3):
        config = {
            'Id': 'ExhibitIntelligentTiering',
            'Status': 'Enabled',
            'TieringConfigurations': [
                {'AccessTier': 'ARCHIVE_ACCESS', 'Days': 90}, 
                {'AccessTier': 'DEEP_ARCHIVE_ACCESS', 'Days': 180}
            ]
        }
        try:
            # Note: This is the correct Boto3 operation for Intelligent Tiering
            s3.put_bucket_intelligent_tiering_configuration(
                Bucket=data['bucket_name'],
                Id=config['Id'],
                IntelligentTieringConfiguration=config
            )
            message = f"✅ Success: Intelligent-Tiering enabled on {data['bucket_name']} with Archive after 90 days."
            logging.info(message)
            return {"status": "success", "message": message}
        except Exception as e:
            message = f"❌ Error enabling Intelligent-Tiering: {e}"
            logging.error(message)
            return {"status": "error", "message": message}

    return execute_aws_action(data, put_intelligent_tiering_config)


@app.route('/get_logs', methods=['GET'])
def get_logs():
    """API endpoint to fetch the latest lifecycle logs."""
    log_file_path = 'logs/lifecycle_logs.txt'
    logs = "Log file not found."
    if os.path.exists(log_file_path):
        with open(log_file_path, 'r') as f:
            # Read the last 20 lines for a cleaner display
            logs = "".join(f.readlines()[-20:]) 
    
    return jsonify({"logs": logs})

if __name__ == '__main__':
    os.makedirs('logs', exist_ok=True) 
    app.run(debug=True)