schtasks /Create ^
 /SC MINUTE /MO 1 ^
 /TN "UpdatePowerJSON" ^
 /TR "\"%USERPROFILE%\Documents\Rainmeter\Skins\PowerWidget\.venv\Scripts\python.exe\" \"%USERPROFILE%\Documents\Rainmeter\Skins\PowerWidget\power.py\"" ^
 /F
schtasks /Query /TN "UpdatePowerJSON"
pause
