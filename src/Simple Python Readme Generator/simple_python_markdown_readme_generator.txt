import os
import tkinter as tk
from tkinter import filedialog, messagebox

def generate_readme(script_file):
    script_name = os.path.basename(script_file)
    script_dir = os.path.dirname(script_file)
    readme_file = os.path.join(script_dir, f"{os.path.splitext(script_name)[0]}_readme.md")

    if os.path.exists(readme_file):
        overwrite = messagebox.askyesno("Overwrite Confirmation", f"{readme_file} already exists. Do you want to overwrite it?")
        if not overwrite:
            print("Operation cancelled.")
            return

    # Unless you want to change other script behaviors or you know what you are doing, then modify to your needs before this line.
    # Modify the following (the variable named 'content' below this line to whatever your readme's needs/conventions/etc. are:

    ###                                                         ###
    ###                                                         ###
    ###                                                         ###
    ###     BEGIN CONTENT TO GENERATE IN NEW MARKDOWN FILE      ###
    ###                                                         ###
    ###                                                         ###
    ###                                                         ###

    content = f"""```# Simple Python Markdown Readme Generator

### Note: I strongly recommend using Python's package manager 'pip' for installing the script's package requirements (as well as using an environmental variable!).

## To Run:
```
    python {script_name}
```

## Requirements:
```
    1. tkinter
    2. os
```

## Information:
    Generates a readme (in markdown format) following this file's convention. Extensible and modifiable for any particular needs and uses - simply modify the 'content' variable within the script (to clarify and avoid any confusion regarding which script I am remarking about here it is '{script_name}').
    
    For example, the current content variable for the current script is as follows:
    
    ```
    content = f"""# [FILE_NAME]

                    ## To Run:
                    ```
                        python [FILE_NAME].py
                    ```

                    ## Requirements:
                        1. [requirement 1...]
                        2. [requirement 2...]
                        3. [requirement 3...]
                        4. ...
                    
                    ## Information:
                        [Description of file/project/script/etc.]
    """
    ```

    so, you may add, remove, and/or modify all text/markdown between the format specifier (f""" on line 17 of this current file and the closing quotations (""") on line 30 of this current file.
    
    For example, I change what is in the content variable to now hold this instead [Note: replacing the contents within 'content' to the following actually generates this same exact readme file! - WOAH INCEPTION?!]:
    
    
    ```
   content = f"""# Simple Python Markdown Readme Generator

            ### Note: I strongly recommend using Python's package manager 'pip' for installing the script's package requirements (as well as using an environmental variable!).

            ## To Run:
                python {script_name}

            ## Requirements:
                1. tkinter
                2. os

            ## Information:
                Generates a readme (in markdown format) following this file's convention. Extensible and modifiable for any particular needs and uses - simply modify the 'content' variable within the script (to clarify and avoid any confusion regarding which script I am remarking about here it is '{script_name}').
                
                For example, the current content variable for the current script is as follows:
                
                content = f"""# [FILE_NAME]

                                ## To Run:
                                
                                    python [FILE_NAME].py
                                

                                ## Requirements:
                                    1. [requirement 1...]
                                    2. [requirement 2...]
                                    3. [requirement 3...]
                                    4. ...

                                ## Information:
                                    [Description of file/project/script/etc.]
                

                so, you may add, remove, and/or modify all text/markdown between the format specifier (f""" on line 17 of this current file and the closing quotations (""") on line 30 of this current file.

                For example, I change what is in the content variable to now hold this instead [Note: replacing the contents within 'content' to the following actually generates this same exact readme file! - WOAH INCEPTION?!]:
                

                    content = f"""# [FILE_NAME]

                                ## To Run:
                                
                                    python {script_name}
                                

                                ## Requirements:
                                    1. tkinter
                                    2. os

                                ## Information:
                                    [Description of file/project/script/etc.]
                                
                                Feel free to modify this to whatever suits your needs!

    """

    ###                                                         ###
    ###                                                         ###
    ###                                                         ###
    ###     END CONTENT TO GENERATE IN NEW MARKDOWN FILE        ###
    ###                                                         ###
    ###                                                         ###
    ###                                                         ###

    # Unless you want to change other script behaviors or you know what you are doing, then modify to your needs after this line.

    with open(readme_file, "w") as file:
        file.write(content)
    
    print(f"README file created at {readme_file}")

def main():
    root = tk.Tk()
    root.withdraw()  # Hide the main window

    script_file = filedialog.askopenfilename(
        title="Select Python Script",
        filetypes=[("Python files", "*.py"), ("All files", "*.*")]
    )

    if not script_file:
        messagebox.showerror("Error", "No file selected. Exiting.")
        return

    generate_readme(script_file)

if __name__ == "__main__":
    main()
