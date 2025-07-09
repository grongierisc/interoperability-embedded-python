import os

def main():
    # Get the value of the environment variable
    my_env_var = os.getenv('MY_ENV_VAR', 'default_value')
    
    # Print the value of the environment variable
    print(f'MY_ENV_VAR: {my_env_var}')


if __name__ == "__main__":
    main()
