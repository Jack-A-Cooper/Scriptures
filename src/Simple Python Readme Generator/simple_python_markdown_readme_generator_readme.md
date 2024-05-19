# Simple Python Markdown Readme Generator

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
```