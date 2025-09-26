document.addEventListener('DOMContentLoaded', () => {
    const accessKeyInput = document.getElementById('accessKey');
    const secretKeyInput = document.getElementById('secretKey');
    const regionInput = document.getElementById('region');
    const bucketNameInput = document.getElementById('bucketName');
    
    // Policy Inputs
    const glacierDaysInput = document.getElementById('glacierDays');
    const deepArchiveDaysInput = document.getElementById('deepArchiveDays');
    const expirationDaysInput = document.getElementById('expirationDays');

    // Buttons
    const createBucketBtn = document.getElementById('createBucketBtn');
    const uploadFileBtn = document.getElementById('uploadFileBtn');
    const applyCustomLifecycleBtn = document.getElementById('applyCustomLifecycleBtn');
    const enableIntelligentTieringBtn = document.getElementById('enableIntelligentTieringBtn');
    const fetchLogsBtn = document.getElementById('fetchLogsBtn');
    
    const statusMessage = document.getElementById('statusMessage');
    const logOutput = document.getElementById('logOutput');


    // Helper to collect all dynamic data
    function getRequestData() {
        return {
            access_key: accessKeyInput.value.trim(),
            secret_key: secretKeyInput.value.trim(),
            region: regionInput.value.trim(),
            bucket_name: bucketNameInput.value.trim(),
        };
    }

    // Helper function to update the status message
    function updateStatus(message, status) {
        statusMessage.textContent = message;
        statusMessage.className = 'status-box'; 
        if (status === 'success') {
            statusMessage.classList.add('status-success');
        } else if (status === 'error') {
            statusMessage.classList.add('status-error');
        } else {
            statusMessage.classList.add('status-info');
        }
    }

    // Generic function to send a POST request to the API
    async function postAction(endpoint, dataToSend, buttonElement) {
        buttonElement.disabled = true;
        updateStatus(`⏳ Sending request to AWS via ${endpoint}...`, 'info');

        try {
            const fullData = { ...getRequestData(), ...dataToSend };
            
            if (!fullData.access_key || !fullData.secret_key || !fullData.region || !fullData.bucket_name) {
                updateStatus("🚫 Please enter all AWS credentials, region, and bucket name.", 'error');
                buttonElement.disabled = false;
                return;
            }

            const response = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(fullData)
            });

            const result = await response.json();

            if (response.ok && result.status === 'success') {
                updateStatus(result.message, 'success');
            } else {
                updateStatus(`Operation failed: ${result.message}`, 'error');
            }
        } catch (error) {
            console.error('API Request Error:', error);
            updateStatus(`🚫 An unexpected network error occurred: ${error.message}`, 'error');
        } finally {
            buttonElement.disabled = false;
            fetchLogs(); 
        }
    }

    // Function to fetch the recent logs (remains the same)
    async function fetchLogs() {
        // ... (Keep the original fetchLogs implementation from the previous response) ...
        logOutput.textContent = 'Fetching logs...';
        try {
            const response = await fetch('/get_logs');
            const result = await response.json();
            logOutput.textContent = result.logs || 'No recent log entries found.';
        } catch (error) {
            logOutput.textContent = 'Error fetching logs.';
            console.error('Log Fetch Error:', error);
        }
    }

    // Event Listeners
    createBucketBtn.addEventListener('click', () => {
        postAction('/create_bucket', {}, createBucketBtn);
    });

    uploadFileBtn.addEventListener('click', () => {
        postAction('/upload_file', {}, uploadFileBtn);
    });

    applyCustomLifecycleBtn.addEventListener('click', () => {
        const policyData = {
            glacier_days: glacierDaysInput.value,
            deep_archive_days: deepArchiveDaysInput.value,
            expiration_days: expirationDaysInput.value,
        };
        postAction('/apply_custom_lifecycle', policyData, applyCustomLifecycleBtn);
    });

    enableIntelligentTieringBtn.addEventListener('click', () => {
        postAction('/enable_intelligent_tiering', {}, enableIntelligentTieringBtn);
    });

    fetchLogsBtn.addEventListener('click', fetchLogs);
    
    // Initial log fetch on load
    fetchLogs();
});