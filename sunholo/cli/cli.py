# sunholo/cli/cli.py
import argparse

def main():
    parser = argparse.ArgumentParser(description="sunholo CLI tool.")
    parser.add_argument('--echo', help='Echo the string you use here')
    args = parser.parse_args()
    if args.echo:
        print(args.echo)

if __name__ == "__main__":
    main()
