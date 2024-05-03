import inspect
import os
import importlib.util

def list_functions(module):
    functions = inspect.getmembers(module, inspect.isfunction)
    return functions

def list_all_functions_in_package(package):
    functions = []
    for _, module in inspect.getmembers(package, inspect.ismodule):
        functions.extend(list_functions(module))
    return functions

def write_docstrings_to_md(module, output_file='../docs/docs/functions.md'):
    functions = list_all_functions_in_package(module)
    if not functions:
        print("No functions found in module.")
    else:
        print(f"Found functions: {[name for name, _ in functions]}")

    with open(output_file, 'w') as f:
        for name, func in functions:
            docstring = inspect.getdoc(func)
            if docstring:
                print(f"writing docstring for {name}")
                f.write(f"## {name}\n\n")
                f.write(f"{docstring}\n\n")
            else:
                print(f"No docstring for function: {name}")

if __name__ == "__main__":
    import sunholo
    write_docstrings_to_md(sunholo)
