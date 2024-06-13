import armv8suite.testing.cli as cli
import armv8suite.routes as routes
import sys


def main_try():
    try:
        
        args = sys.argv[1:]
        cli.run_and_write_tests_with_args(args)
    except Exception as e:
        print("Python Error:")
        print(e)
        sys.exit(1)
    
def main():
    main_try()

if __name__ == '__main__':
    main()
