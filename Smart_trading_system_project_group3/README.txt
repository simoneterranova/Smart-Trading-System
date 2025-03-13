About the project
This program simulates energy transactions between prosumers and consumers over a 24-hour period. The simulation allows for manual assignment of energy from producers to consumers based on user input.


Requirements
Python installed on your system.


Usage
1. Open your terminal or command prompt.
2. Navigate to the directory containing `main.py`:
	```bash
	cd /path/to/directory
	```
3. Execute the program using the following command:
	```bash
	/usr/bin/python3 /path/to/directory/main.py
	```
	Replace `/path/to/directory` with the actual path to the `main.py` file.


Input Instructions
The program will prompt you for the following inputs:
1.Simulation Day
- Enter the day of the week for the simulation. Valid inputs are `Monday`, `Tuesday`,
	`Wednesday`, `Thursday`, `Friday`, `Saturday`, and `Sunday`. 
2.Number of Prosumers
- Enter the number of energy producers (prosumers). This must be a non-negative integer.
3.Number of Consumers
- Enter the number of energy consumers. This must be a non-negative integer.

Example Execution
```bash
/usr/bin/python3 /Users/username/smart_grids/main.py
Enter the day of the week for the simulation (e.g., 'Sunday'): Monday
Enter the number of prosumers (e.g., 3): 2
Enter the number of consumers (e.g., 3): 2
...
```


Troubleshooting
1. Invalid Day Input
- Error: "Invalid day of the week. Please enter a valid day."
- Ensure you input one of the seven days of the week (case-insensitive).
2. Invalid Number Input
- Error: "The number of prosumers/consumers must be a non-negative integer."
- Input a number greater than or equal to zero.
3. Unexpected Errors
- If you encounter unexpected errors, ensure your Python installation is correct and the file path is accurate.