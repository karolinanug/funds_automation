@echo off
cd /d "C:\Users\vytik\OneDrive\Stalinis kompiuteris\Programavimas\funds_automation"
python run_daily_pipeline.py
python merge_data.py
python send_email.py
echo Automation completed at %date% %time% >> automation_log.txt