## run_demo.ps1 – Quick demo for Kigali Rental Price Estimator
# ------------------------------------------------------------
# 1. Start the Flask development server (runs on http://127.0.0.1:5000)
#    This runs in a separate PowerShell job so the script can continue.
# ------------------------------------------------------------
Start-Job -ScriptBlock { python "c:\Users\calin\OneDrive\Desktop\Capstone assignment 1\app.py" } -Name "FlaskServer"
Write-Host "[Demo] Flask server started as background job. Waiting 5 seconds for it to be ready..."
Start-Sleep -Seconds 5

# ------------------------------------------------------------
# 2. Prepare JSON payload for prediction request
# ------------------------------------------------------------
$payload = @{
    bedrooms        = 2
    bathrooms       = 1
    amenities_count = 3
    location        = "Kacyiru"
    property_type   = "Apartment"
    furnished_status = "Unfurnished"
    parking         = "Yes"
    security        = "Yes"
    road_access     = "Good"
} | ConvertTo-Json

# ------------------------------------------------------------
# 3. Send POST request to the prediction endpoint
# ------------------------------------------------------------
$response = Invoke-RestMethod -Uri "http://127.0.0.1:5000/api/predict" `
                              -Method POST `
                              -Headers @{ "Content-Type" = "application/json" } `
                              -Body $payload
Write-Host "[Demo] Prediction response:`n$response"

# ------------------------------------------------------------
# 4. Clean up – stop the background Flask job
# ------------------------------------------------------------
Stop-Job -Name "FlaskServer" | Out-Null
Remove-Job -Name "FlaskServer" | Out-Null
Write-Host "[Demo] Flask server stopped. Demo complete."
