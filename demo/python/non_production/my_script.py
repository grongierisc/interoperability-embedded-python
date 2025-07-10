import os
import random

def main():
    # Get the value of the environment variable
    my_env_var = os.getenv('MY_ENV_VAR', 'default_value')
    
    # Print the value of the environment variable
    print(f'MY_ENV_VAR: {my_env_var}')

    if random.choice([True, False]):
        # Simulate a condition that raises an exception
        print("An error occurred!")
        # Raise an exception to demonstrate error handling
        raise Exception("This is a demo exception to illustrate error handling.")

    return "Script executed successfully!"


if __name__ == "__main__":
    main()
