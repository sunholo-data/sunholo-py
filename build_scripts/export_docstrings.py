import inspect
import sunholo
import os
import re

GITHUB_BASE_URL = "https://github.com/sunholo-data/sunholo-py/blob/main/"

def escape_mdx(text):
    """Escape special characters that cause MDX compilation errors."""
    if text is None:
        return ''
    # Escape angle brackets that aren't part of valid HTML tags
    text = re.sub(r'<(?![a-zA-Z/!])', '&lt;', text)
    text = re.sub(r'(?<![a-zA-Z"])>', '&gt;', text)
    # Escape curly braces that could be interpreted as JSX expressions
    text = text.replace('{', '&#123;')
    text = text.replace('}', '&#125;')
    return text

def list_functions(module):
    functions = inspect.getmembers(module, inspect.isfunction)
    result = []
    seen = set()
    for func_name, func in functions:
        # Skip if the function doesn't have a module or if it's not in the "sunholo" package
        if func.__module__ and func.__module__.startswith("sunholo") and func_name not in seen:
            seen.add(func_name)
            try:
                signature = inspect.signature(func)
                source_file = inspect.getfile(func)
                result.append((func_name, func, signature, source_file))
            except TypeError:
                continue
    return result

def list_classes(module):
    classes = inspect.getmembers(module, inspect.isclass)
    result = []
    seen = set()
    for cls_name, cls in classes:
        if cls.__module__ and cls.__module__.startswith("sunholo") and cls_name not in seen:
            seen.add(cls_name)
            try:
                source_file = inspect.getfile(cls)
                result.append((cls_name, cls, source_file))
            except (TypeError, OSError):
                continue
    return result

def list_all_functions_and_classes_in_package(package):
    functions = []
    classes = []
    visited_modules = set()

    def explore(module):
        if module in visited_modules:
            return
        visited_modules.add(module)
        functions.extend(list_functions(module))
        classes.extend(list_classes(module))
        for _, submodule in inspect.getmembers(module, inspect.ismodule):
            explore(submodule)

    explore(package)
    return functions, classes

def write_docstrings_to_md(package):
    functions, classes = list_all_functions_and_classes_in_package(package)

    if not functions and not classes:
        print("No functions or classes found in module.")
        return
    
    print(f"Found functions: {[name for name, _, _, _ in functions]}")
    print(f"Found classes: {[cls_name for cls_name, _, _ in classes]}")

    source_files = set([src for _, _, _, src in functions] + [src for _, _, src in classes])

    for source_file in source_files:
        relative_file_path = os.path.relpath(source_file)
        relative_md_path = os.path.splitext(relative_file_path)[0] + '.md'
        md_file_path = os.path.join('docs', 'docs', relative_md_path)
        os.makedirs(os.path.dirname(md_file_path), exist_ok=True)

        with open(md_file_path, 'w') as f:
            f.write(f"# {os.path.basename(source_file)}\n\n")
            f.write(f"*Source*: [{relative_file_path}]({GITHUB_BASE_URL + relative_file_path})\n\n")

            seen_functions = set()
            functions_written = False
            for func_name, func, signature, src in functions:
                if src == source_file and func_name not in seen_functions:
                    if not functions_written:
                        f.write("## Functions\n\n")
                        functions_written = True
                    seen_functions.add(func_name)
                    docstring = escape_mdx(inspect.getdoc(func))
                    f.write(f"### {func_name}{escape_mdx(str(signature))}\n")
                    f.write(f"\n{docstring or 'No docstring available.'}\n\n")

            seen_classes = set()
            classes_written = False
            for cls_name, cls, src in classes:
                if src == source_file and cls_name not in seen_classes:
                    if not classes_written:
                        f.write("## Classes\n\n")
                        classes_written = True
                    seen_classes.add(cls_name)
                    cls_docstring = escape_mdx(inspect.getdoc(cls))
                    f.write(f"### {cls_name}\n")
                    f.write(f"\n{cls_docstring or 'No docstring available.'}\n\n")
                    for method_name, method in inspect.getmembers(cls, inspect.isfunction):
                        signature = escape_mdx(str(inspect.signature(method)))
                        method_docstring = escape_mdx(inspect.getdoc(method))
                        f.write(f"* {method_name}{signature}\n")
                        f.write(f"   - {method_docstring or 'No docstring available.'}\n\n")
        
        with open(md_file_path, 'r') as f:  # Open in 'r' mode (read mode)
            contents = f.read()
            print(contents)   


if __name__ == "__main__":
    write_docstrings_to_md(sunholo)
