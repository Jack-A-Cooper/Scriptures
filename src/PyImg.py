#!/usr/bin/python3

# PyImg.py

from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, 
                             QHBoxLayout, QFileDialog,QDialogButtonBox, QLabel, QListWidget, 
                             QComboBox, QMessageBox, QListWidgetItem, QDialog, 
                             QGridLayout, QDesktopWidget, QProgressBar, QGroupBox,
                             QRadioButton, QTreeView)
from PyQt5.QtCore import QSize, QSettings, pyqtSignal, QObject
from PyQt5.QtGui import QPixmap
from PIL import Image
import os
import time
import sys
import threading

### CLASSES ======== CLASSES ======== CLASSES ###

# ||| Worker ||| #
#
class Worker(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(int)

    def __init__(self, filePaths, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filePaths = filePaths

    def run(self):
        total_files = len(self.filePaths)
        for i, file_path in enumerate(self.filePaths):
            # Perform processing...
            # Simulate processing with a sleep
            time.sleep(0.1)  # Adjust the sleep time as needed for testing
            progress_percent = ((i + 1) / total_files) * 100
            self.progress.emit(int(progress_percent))  # Emit progress as an integer percentage
        self.finished.emit()

# ||| ImageProcessor ||| #
#
class ImageProcessor(QMainWindow):
    def __init__(self):
        # Init GUI
        super().__init__()
        self.settings = QSettings("User", "ImageProcessor")
        self.filePaths = []  # List to store paths of selected images
        self.initUI()
        
        # Multithreading
        self.worker = Worker(self.filePaths)
        self.worker.finished.connect(self.processing_finished)
        self.worker.progress.connect(self.update_progress_bar)
        
        # Set starting window placement
        qtRectangle = self.frameGeometry()
        centerPoint = QDesktopWidget().availableGeometry().center()
        qtRectangle.moveCenter(centerPoint)
        self.move(qtRectangle.topLeft())

    def initUI(self):
        # Set window properties
        self.setWindowTitle("PyImg")
        self.setGeometry(0, 0, 1280, 720)
        self.resize(self.settings.value("size", QSize(1280, 720)))
        self.save_directory = None  # Initialize save_directory attribute
        
        # Main layout setup - horizontal box layout
        main_layout = QHBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Filesystem explorer panel (left side)
        filesystem_group = QGroupBox("Filesystem")
        filesystem_layout = QVBoxLayout()
        self.filesystem_view = QTreeView()  # Initialize with QFileSystemModel
        filesystem_layout.addWidget(self.filesystem_view)
        filesystem_group.setLayout(filesystem_layout)
        main_layout.addWidget(filesystem_group, 1)  # Add to main layout with stretch factor
        
        # Center layout for processing settings and queues (right side)
        center_layout = QVBoxLayout()
        
        # Add all the different UI sections created by helper functions
        center_layout.addLayout(self.create_process_settings_layout())
        center_layout.addLayout(self.create_scale_settings_layout())
        center_layout.addLayout(self.create_save_dir_settings_layout())
        center_layout.addWidget(self.create_type_processing_buttons_layout())
        center_layout.addLayout(self.create_eta_label())
        center_layout.addLayout(self.create_process_button())
        center_layout.addLayout(self.create_file_info_panel_layout())
        center_layout.addLayout(self.create_processing_queue_control_panel_layout())
        center_layout.addLayout(self.create_image_preview_section_layout())
        
        main_layout.addLayout(center_layout, 4)  # Add to main layout with stretch factor

        # Set the main layout to the central widget
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)
        
### FUNCTIONS ======== FUNCTIONS ======== FUNCTIONS ###

    ## ==== [ GUI ] ==== ##
    
    def create_process_settings_layout(self):
        p_layout = QHBoxLayout()
        
        # Create widgets for the processing settings
        self.process_option_combo = QComboBox(self)
        self.process_option_combo.addItems(["Single File", "Multiple Files", "Directory"])
        p_layout.addWidget(QLabel("Process Option:"))
        p_layout.addWidget(self.process_option_combo)
        
        # Processing type options - open save directory after processing options
        self.process_option_combo = QComboBox(self)
        self.process_option_combo.addItems(["Yes", "No"])
        p_layout.addWidget(QLabel("Open Save Directory After Processing?"))
        p_layout.addWidget(self.process_option_combo)
        
        processing_options_group = QGroupBox("Processing Options", self)
        processing_options_group.setLayout(p_layout)
        return processing_options_group

    def create_scale_settings_layout(self):
        # Scale factor and process options
        h_layout = QHBoxLayout()
        
        # Scale factor and process options - scaling options
        self.scale_factor_combo = QComboBox(self)
        self.scale_factor_combo.addItems(["1.5x", "2x", "4x", "6x", "8x"])
        h_layout.addWidget(QLabel("Scale Factor:"))
        h_layout.addWidget(self.scale_factor_combo)

        # Scale factor and process options - QGroupbox
        scale_selection_group = QGroupBox("Scale and Process Options")
        scale_selection_layout = QVBoxLayout()
        scale_selection_layout.addLayout(h_layout)
        h_layout.addWidget(scale_selection_group)
        
        scale_settings_group = QGroupBox("Processing Options", self)
        scale_settings_group.setLayout(h_layout)
        return scale_settings_group

    def create_save_dir_settings_layout(self):
        # Save directory options
        all_save_dir_group = QHBoxLayout()
        
        # Save directory options - change save dir options
        self.change_save_dir_btn = QPushButton('Change Save Directory', self)
        self.save_directory_label = QLabel("Save to: Not Set", self)
        all_save_dir_group.addWidget(self.change_save_dir_btn)
        all_save_dir_group.addWidget(self.save_directory_label)
        
        # Save directory options - QGroupbox
        save_dir_group = QGroupBox("Saving Options:")
        save_dir_layout = QHBoxLayout()
        save_dir_layout.addLayout(all_save_dir_group)
        all_save_dir_group.addWidget(save_dir_group)
        return all_save_dir_group.addWidget(save_dir_group)

    def create_type_processing_buttons_layout(self):
        # Control radio buttons
        control_process_group = QGroupBox("Processing Option Selection: ")
        process_selection_layout = QHBoxLayout()

        # Upscale
        self.upscale_btn = QRadioButton('Upscale', self)
        self.upscale_btn.clicked.connect(self.processing_logic)
        process_selection_layout.addWidget(self.upscale_btn)
        
        # Downscale
        self.downscale_btn = QRadioButton('Downscale', self)
        self.downscale_btn.clicked.connect(self.processing_logic)
        process_selection_layout.addWidget(self.downscale_btn)
        
        # Convert
        self.convert_btn = QRadioButton('Convert', self)
        self.convert_btn.clicked.connect(self.processing_logic)
        process_selection_layout.addWidget(self.convert_btn)
        
        # Convert from
        self.convert_from_combo = QComboBox(self)
        self.convert_from_combo.addItems(["png", "jpg/jpeg", "pdf", "tga", "bmp"])
        process_selection_layout.addWidget(QLabel("Convert From:"))
        process_selection_layout.addWidget(self.convert_from_combo)
        
        # Convert to
        self.convert_to_combo = QComboBox(self)
        self.convert_to_combo.addItems(["png", "jpg/jpeg", "pdf", "tga", "bmp"])
        process_selection_layout.addWidget(QLabel("Convert To:"))
        process_selection_layout.addWidget(self.convert_to_combo)
        
        control_process_group.setLayout(process_selection_layout)
        control_process_group.addWidget(self.convert_to_combo)
        return control_process_group

    def create_eta_label(self):
        # Process ETA label
        eta_button_layout = QHBoxLayout()
        self.eta_label = QLabel("Estimated Time: Not Calculated", self)
        eta_button_layout.addWidget(self.eta_label)
        return eta_button_layout.addWidget(control_process_group)

    def create_process_button(self):
        # Process button
        process_button_layout = QHBoxLayout()
        process_btn = QPushButton('Process', self)
        process_btn.clicked.connect(self.process_queue)
        process_button_layout.addWidget(process_btn)
        return process_button_layout

    def create_file_info_panel_layout(self):
        # File information panel
        file_info_control_group = 
        file_info_control_layout = QHBoxLayout()
        self.file_info_panel = QLabel("File Information:", self)
        file_info_control_layout.addWidget(self.file_info_panel)
        self.file_info_panel = QListWidget(self)
        self.file_info_panel.setSelectionMode(QListWidget.ExtendedSelection)
        file_info_control_layout.addWidget(self.file_info_panel)
        self.total_info_label = QLabel("Total Files: 0, Total Size: 0.00 MB", self)
        file_info_control_layout.addWidget(self.total_info_label)
        
        # Add/Remove images control panel
        add_btn = QPushButton('Add Images', self)
        add_btn.clicked.connect(self.add_images)
        file_info_control_layout.addWidget(add_btn)
        remove_btn = QPushButton('Remove Selected Image', self)
        remove_btn.clicked.connect(self.remove_selected_image)
        file_info_control_layout.addWidget(remove_btn)
        return file_info_control_layout
        
    def create_processing_queue_control_panel_layout(self):
        # Processing queue panel
        queue_control_group = QHBoxLayout()
        queue_panel_label = QLabel("Processing Queue:")
        queue_control_group.addWidget(queue_panel_label)
        
        self.queue_panel = QListWidget(self)
        self.queue_panel.setSelectionMode(QListWidget.ExtendedSelection)
        queue_control_group.addWidget(self.queue_panel)
        
        # Processing queue panel - information section
        self.total_processing_queue_label = QLabel("Total Files: 0, Total Size: 0.00 MB", self)
        queue_control_group.addWidget(self.total_processing_queue_label)
        
        # Processing queue panel - options section
        add_to_queue_btn = QPushButton('Add to Queue', self)
        add_to_queue_btn.clicked.connect(self.add_to_queue)
        queue_control_group.addWidget(add_to_queue_btn)

        remove_from_queue_btn = QPushButton('Remove from Queue', self)
        remove_from_queue_btn.clicked.connect(self.remove_from_queue)
        queue_control_group.addWidget(remove_from_queue_btn)
        #queue_control_group.setLayout(queue_control_layout)
        
        # Processing queue panel - progress bar section
        self.processing_queue_pbar = QProgressBar(self)
        self.processing_queue_pbar.setGeometry(30, 40, 200, 25)
        queue_control_group.addWidget(self.processing_queue_pbar)
        self.processing_queue_pbar.setHidden(True)
        return queue_control_group
        
    def create_image_preview_section_layout(self):
        # Image preview section
        preview_widget = QHBoxLayout()
        self.preview_widget = QWidget()
        self.preview_layout = QGridLayout()
        preview_widget.setLayout(preview_layout)
        preview_widget.addWidget(self.preview_widget)
        return preview_widget

    ## ==== [ CONTROL/LOGIC FLOW ] ==== ##
    
    # [ Control logic ] #
    def processing_logic(self):
        if not self.convert_btn.isChecked():
            # Determine upscale or downscale based on the radio buttons
            upscale = self.upscale_btn.isChecked()
            self.process_images(upscale)
        else:
            # Convert button is checked
            self.convert_images()

    # [ Upscale | Downscale ] #
    def scale_images_logic(self):
        scale_factor = self.scale_factor_combo.currentText()

    # [ Convert ] #
    def convert_images_logic(self):
        convert_from_format = self.convert_from_combo.currentText()
        convert_to_format = self.convert_to_combo.currentText()
        

    ## ==== HELPERS ==== ##

    def closeEvent(self, event):
        self.settings.setValue("size", self.size())
        super().closeEvent(event)

    ## ==== PATHING AND SAVING ==== ##

    def change_save_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Save Directory")
        if directory:
            self.save_directory = directory  # Set the save_directory attribute
            self.save_directory_label.setText(f"Save to: {directory}")
        else:
            # Handle the case where the user cancels the directory selection or it's invalid
            self.save_directory = None
            self.save_directory_label.setText("Save to: Not Set")
    
    def update_image_paths(self, old_path, new_path):
        # Safely remove old path and add new path to the list and the QListWidget
        self.file_info_panel.clear()  # Clear the QListWidget before repopulating it
        if old_path in self.filePaths:
            self.filePaths.remove(old_path)

        self.filePaths.append(new_path)  # Add new path to the list
        
        for path in self.filePaths:
            # Re-add all the items to the QListWidget
            self.file_info_panel.addItem(QListWidgetItem(os.path.basename(path)))
        self.update_preview()  # Update the preview to reflect the changes
        
    ## ==== FILE INFO PANEL ==== ##
    
    def add_images(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select Images", "", "Images (*.png *.jpg *.jpeg *.bmp *.gif)")
        self.filePaths.extend(files)
        self.update_file_info_panel()

    def remove_selected_image(self):
        selected_items = self.file_info_panel.selectedItems()
        if not selected_items:
            return
        for item in selected_items:
            # Extract the file name from the item text
            file_name = item.text().split(" - ")[0]
            # Find the full path in self.filePaths
            full_path = next((path for path in self.filePaths if os.path.basename(path) == file_name), None)
            if full_path:
                self.filePaths.remove(full_path)
                self.file_info_panel.takeItem(self.file_info_panel.row(item))
            else:
                print(f"Could not find the image path for {file_name} in the list of image paths.")
        self.update_file_info_panel()  # Update the panel to reflect the changes

    def update_file_info_panel(self):
        self.file_info_panel.clear()
        total_size = 0
        for path in self.filePaths:
            file_size = os.path.getsize(path) / (1024 * 1024)  # Size in MB
            total_size += file_size
            self.file_info_panel.addItem(f"{os.path.basename(path)} - {file_size:.2f} MB")

        # Update the total_info_label with total size and number of files
        total_files = len(self.filePaths)
        self.total_info_label.setText(f"Total Files: {total_files}, Total Size: {total_size:.2f} MB")
        
    def update_preview(self):
        # First, clear the existing previews
        while self.preview_layout.count():
            widget = self.preview_layout.takeAt(0).widget()
        if widget is not None:
            widget.deleteLater()

        # Add new previews for each image in the list
        for file_path in self.filePaths:
            label = QLabel()
            pixmap = QPixmap(file_path)
            label.setPixmap(pixmap.scaled(100, 100, Qt.KeepAspectRatio))
            self.preview_layout.addWidget(label)

        some_columns = 6  # For example, let's say you want 3 thumbnails per row.
        # Clear the current preview by removing widgets from the layout.
        while self.preview_layout.count():
            widget = self.preview_layout.takeAt(0).widget()
            if widget is not None:
                widget.deleteLater()

        # Add new previews for each image in the list.
        for idx, file_path in enumerate(self.filePaths):
            if os.path.exists(file_path):  # Check if the image file exists.
                label = QLabel()
                pixmap = QPixmap(file_path)
                if not pixmap.isNull():  # Check if the pixmap is valid.
                    scaled_pixmap = pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    label.setPixmap(scaled_pixmap)
                    row = idx // some_columns  # Calculate the row index.
                    col = idx % some_columns   # Calculate the column index.
                    self.preview_layout.addWidget(label, row, col)
                else:
                    print(f"Failed to load image: {file_path}")
    
    ## ==== PROCESSING QUEUE ==== ##
    
    def add_to_queue(self):
        # Allow users to select images to add to the queue
        files, _ = QFileDialog.getOpenFileNames(self, "Select Images", "", "Images (*.png *.jpg *.jpeg *.bmp *.gif)")
        for file in files:
            if file and file not in self.filePaths:  # Avoid duplicates
                self.filePaths.append(file)
                self.queue_panel.addItem(file)  # Add the file to the queue panel
                self.update_file_info_panel()  # Optional: Update the file info panel if necessary
    
    def remove_from_queue(self):
        # Remove selected images from the queue
        for item in self.queue_panel.selectedItems():
            self.queue_panel.takeItem(self.queue_panel.row(item))  # Remove from the queue panel

        # Remove the corresponding item from the file info panel and the filePaths list
        file_info_items_to_remove = [item.text() for item in self.file_info_panel.selectedItems()]
        for file_path in file_info_items_to_remove:
            if file_path in self.filePaths:
                self.filePaths.remove(file_path)  # Remove from the internal list
                # Find the QListWidgetItem by text and remove it from the file_info_panel
                list_items = self.file_info_panel.findItems(file_path, Qt.MatchExactly)
                if list_items:
                    for item in list_items:
                        self.file_info_panel.takeItem(self.file_info_panel.row(item))

        self.update_file_info_panel()  # Update the file info panel if necessary
    
    ## ==== PROCESSING QUEUE - HELPERS ==== ##
    
    def estimate_processing_time(self):
        if not self.filePaths:
            self.eta_label.setText("Estimated Time: Not Calculated")
            return

        # Sample process one image for timing
        start_time = time.time()
        # Here, call the function you would use to process the image. For example:
        # self.process_image(self.filePaths[0])
        end_time = time.time()

        elapsed_time = end_time - start_time
        total_time = elapsed_time * len(self.filePaths)
        self.eta_label.setText(f"Estimated Time: {total_time:.2f} seconds")

    ## ==== FILE PROCESSING - MULTITHREADING ==== ##
    
    def get_files_to_process(self):
        option = self.process_option_combo.currentText()
        if option == "Single File":
            file_path, _ = QFileDialog.getOpenFileName(self, "Select an Image", "", "Images (*.png *.jpg *.jpeg *.bmp *.gif)")
            return [file_path] if file_path else []
        elif option == "Multiple Files":
            return QFileDialog.getOpenFileNames(self, "Select Images", "", "Images (*.png *.jpg *.jpeg *.bmp *.gif)")[0]
        elif option == "Directory":
            directory = QFileDialog.getExistingDirectory(self, "Select Directory")
            return [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif'))] if directory else []
        return []
        
    def process_queue(self):
        # Update progress bar showing
        self.processing_queue_pbar.setHidden(False)
        
        # Create the worker with the list of image paths
        self.worker = Worker(self.filePaths)
        self.worker.finished.connect(self.processing_finished)
        self.worker.progress.connect(self.update_progress_bar)
        
        # Start processing in a thread
        processing_thread = threading.Thread(target=self.worker.run)
        processing_thread.start()

    def start_processing(self):
        # Perform the image processing tasks
        for file_path in self.filePaths:
            try:
                # Here, you would call the appropriate processing function
                # For example: self.upscale_image(file_path) or self.downscale_image(file_path)
                print(f"Processing {file_path}")  # Placeholder for actual processing logic
            except Exception as e:
                print(f"An error occurred while processing {file_path}: {e}")

        # Once processing is complete, update the UI accordingly
        # This should be done in a thread-safe way since PyQt doesn't allow
        # direct UI manipulation from a secondary thread
        # ...

    def processing_finished(self):
        self.update_progress_bar(100)
        QMessageBox.information(self, "Processing Complete", "All images have been processed.")
        self.processing_queue_pbar.setHidden(True)
    
    ## ==== FILE PROCESSING - MULTITHREADING - HELPERS ==== ##
        
    def progress_bar(self):
        for i in range(101):
            time.sleep(0.05)
            # Use signals or any thread-safe method to update the UI from a thread
            self.update_progress_bar(i)
    
    def update_progress_bar(self, value):
        # This method is to ensure thread-safe updates to the progress bar
        self.processing_queue_pbar.setValue(value)

    ## ==== FILE PROCESSING - SINGLE THREADING ==== ##

    def process_images(self, upscale):
        if not self.save_directory:
            QMessageBox.warning(self, "Save Directory Not Set", "Please set a save directory before processing images.")
            return
        
        scale_factor = float(self.scale_factor_combo.currentText().rstrip('x'))
        files = self.get_files_to_process()
        
        for file_path in files:
            new_file_path = self.scale_images(file_path, scale_factor, upscale)
            self.update_image_paths(file_path, new_file_path)
        self.update_preview()

    def scale_images(self, file_path, scale_factor, upscale):
        # Default to the same directory as the image if no save directory is set
        save_directory = self.save_directory or os.path.dirname(file_path)
        
        with Image.open(file_path) as img:
            w, h = img.size
            new_size = (int(w * scale), int(h * scale)) if upscale else (int(w / scale), int(h / scale))
            img = img.resize(new_size, Image.LANCZOS)
            
            # Create a new file name with a suffix to indicate upscaling or downscaling
            file_name = os.path.basename(file_path)
            name_part, extension_part = os.path.splitext(file_name)
            suffix = f"{'_upscaled' if upscale else '_downscaled'}_{scale}x"
            new_file_name = f"{name_part}{suffix}{extension_part}"
            target_path = os.path.join(save_directory, new_file_name)
            
            # Save the image to the new target path
            img.save(target_path)
            return target_path  # Return the new file path

        # Update self.filePaths and the QListWidget with the new file path
        self.update_image_paths(file_path, target_path)

    def convert_images(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select one or more files to convert", "", "Images (*.png *.jpg *.jpeg *.bmp *.gif)")
        if not files:
            return  # No files selected, exit the function
        
        convert_to_format = self.convert_to_combo.currentText().split('/')[0]  # Assuming 'jpg/jpeg' is a single option, take 'jpg'
        for file_path in files:
            new_file_path = self.convert_image(file_path, convert_to_format)
            self.update_image_paths(file_path, new_file_path)
        self.update_preview()

    def convert_image(self, file_path, target_format):
        # Default to the same directory as the image if no save directory is set
        save_directory = self.save_directory or os.path.dirname(file_path)
        base_name = os.path.basename(file_path)
        new_file_name = f"{base_name.rsplit('.', 1)[0]}.{target_format}"
        target_path = os.path.join(save_directory, new_file_name)
        
        with Image.open(file_path) as img:
            # Save the image to the new target path
            img.save(target_path)
            return target_path  # Return the new file path
        
        # Remove old file path from filePaths and QListWidget
        if file_path in self.filePaths:
            self.filePaths.remove(file_path)
            list_items = self.file_info_panel.findItems(base_name, Qt.MatchExactly)
            if list_items:
                for item in list_items:
                    self.file_info_panel.takeItem(self.file_info_panel.row(item))
        
        # Add new file path to filePaths and QListWidget
        self.filePaths.append(target_path)
        self.file_info_panel.addItem(target_path)

        self.update_file_info_panel()
        self.update_preview()

def main():
    app = QApplication(sys.argv)
    # Style setting
    style = 'Fusion'
    # style = 'Cleanlooks'
    # style = 'Windows'
    app.setStyle(style)
    ex = ImageProcessor()
    ex.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
