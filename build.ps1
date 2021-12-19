./venv/Scripts/activate
pyinstaller --add-data 'statMeter.ico;.' --icon=statMeter.ico  --onefile  statMeter.pyw 
sleep 5
# --clean 