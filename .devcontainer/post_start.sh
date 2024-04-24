screen -dmS web
screen -S web -X stuff "cd /app/web^M" 
screen -S web -X stuff "npm run dev^M"
