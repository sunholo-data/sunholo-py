def main():
    from sunholo.chunker.loaders import read_file_to_documents

    result = read_file_to_documents("README.md")
    print(result)


if __name__ == "__main__":
    main()