# Project5-CPSC449-Asynchronous-Service-Orchestration

### Team Members:
- Cesar Martinez Melgoza
- Andy Cao
- Anitha Chockalingam
- Samuel Valls

### Database Initialization
Go to project directory /Project5-CPSC449-Asynchronous-Service-Orchestration-main/bin
run sh init.sh

#### Using Procfile:
Go to project directory /Project5-CPSC449-Asynchronous-Service-Orchestration-main
foreman start

#### Using Services
Go to the url: 'http://127.0.0.1:5400/docs'

### For the first endpoint...

Enter a username, Example: 'ProfAvery'

You should be presented with a JSON object that includes your username, unique_id, and game_id

Enter the same username and the JSON object will show the status of your current game 

### For the second endpoint...

Enter unique_id and game_id that corresponds to the username along with a guess (Copy these values from the response in the first endpoint)

The JSON object will display your results, indicating the result of your guess
