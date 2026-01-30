import modulefinder

def list_imported_modules(file_path):
    finder = modulefinder.ModuleFinder()
    finder.run_script(file_path)
    
    imported_modules = list(finder.modules.keys())
    return imported_modules

# Example usage
file_path = "main.py"  # Replace with the path to your script
modules = list_imported_modules(file_path)
print("Imported modules:")
for module in modules:
    print(module)