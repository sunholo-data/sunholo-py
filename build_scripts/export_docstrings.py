import inspect
import sunholo

def list_functions(module):
    functions = inspect.getmembers(module, inspect.isfunction)
    return functions

def list_all_functions_in_package(package):
    functions = []
    for _, module in inspect.getmembers(package, inspect.ismodule):
        functions.extend(list_functions(module))
    return functions

def write_docstrings_to_md(package, output_file='docs/docs/functions.md'):
    functions = list_all_functions_in_package(package)
    if not functions:
        print("No functions found in module.")
    else:
        print(f"Found functions: {[name for name, _ in functions]}")

    with open(output_file, 'w') as f:
        # Write the header lines
        f.write("---\n")
        f.write("sidebar_position: 2\n")
        f.write("slug: /function-reference\n")
        f.write("---\n\n")
        f.write("# Function Reference\n\n")
        f.write("Below is a function reference generated from the docstrings of the functions within the sunholo module\n\n")

        # Write each function's documentation
        for name, func in functions:
            docstring = inspect.getdoc(func)
            if docstring:
                print(f"writing docstring for {name}")
                f.write(f"## {name}()\n")
                f.write(f"{docstring}\n\n")
            else:
                print(f"No docstring for function: {name}")

    with open(output_file, 'r') as f:
        print(f.read())

if __name__ == "__main__":
    write_docstrings_to_md(sunholo)
