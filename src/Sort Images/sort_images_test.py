import unittest
import os
import shutil
import tempfile
import logging
from sort_images import setup_logging, get_random_string, create_backup_dir, backup_file, rename_file, process_txt_files, process_image, rename_images

class TestImageRenaming(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.test_dir = tempfile.mkdtemp()
        
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.test_dir, ignore_errors=True)
    
    def setUp(self):
        self.current_dir = os.getcwd()
        os.chdir(self.test_dir)
        self.image_file = "image1.jpg"
        self.txt_file = "image1.txt"
        self.negative_txt_file = "image1_negative.txt"
        with open(self.image_file, 'w') as f:
            f.write("dummy image data")
        with open(self.txt_file, 'w') as f:
            f.write("dummy text data")
        with open(self.negative_txt_file, 'w') as f:
            f.write("dummy negative text data")
        self.backup_dir = "backup"
        create_backup_dir(self.backup_dir)

    def tearDown(self):
        for file in [self.image_file, self.txt_file, self.negative_txt_file, "renamed_image1.jpg", "renamed_image1.txt", "renamed_image1_negative.txt", "1_test.jpg"]:
            if os.path.exists(file):
                os.remove(file)
        if os.path.exists(self.backup_dir):
            shutil.rmtree(self.backup_dir, ignore_errors=True)
        os.chdir(self.current_dir)

    def test_get_random_string(self):
        random_string = get_random_string(8)
        self.assertEqual(len(random_string), 8)
        self.assertTrue(all(c.islower() or c.isdigit() for c in random_string))

    def test_backup_file(self):
        backup_path = backup_file(self.txt_file, self.backup_dir)
        self.assertTrue(os.path.exists(backup_path))

    def test_rename_file(self):
        new_name = "renamed_image.jpg"
        rename_file(self.image_file, new_name, dry_run=False, verbose=True)
        self.assertTrue(os.path.exists(new_name))
        os.remove(new_name)

    def test_process_txt_files(self):
        process_txt_files("image1", "renamed_image1", self.backup_dir, os.getcwd(), dry_run=False, verbose=True)
        self.assertTrue(os.path.exists("renamed_image1.txt"))
        self.assertTrue(os.path.exists("renamed_image1_negative.txt"))
        os.remove("renamed_image1.txt")
        os.remove("renamed_image1_negative.txt")

    def test_process_image(self):
        process_image(self.image_file, "renamed_image1.jpg", os.getcwd(), self.backup_dir, overwrite=True, dry_run=False, verbose=True)
        self.assertTrue(os.path.exists("renamed_image1.jpg"))
        self.assertTrue(os.path.exists("renamed_image1.txt"))
        self.assertTrue(os.path.exists("renamed_image1_negative.txt"))
        os.remove("renamed_image1.jpg")
        os.remove("renamed_image1.txt")
        os.remove("renamed_image1_negative.txt")

    def test_rename_images_dry_run(self):
        rename_images(current_dir=os.getcwd(), overwrite=False, backup_dir=self.backup_dir, dry_run=True, verbose=True)
        new_name_pattern = f"1_{get_random_string(8)}.jpg"
        self.assertFalse(os.path.exists(new_name_pattern))
        
    def test_validate_directory(self):
        with self.assertRaises(NotADirectoryError):
            rename_images(current_dir="invalid_directory", overwrite=False, backup_dir=self.backup_dir, dry_run=False, verbose=True)

    def test_logging_levels(self):
        setup_logging(log_to_file=False, log_level=logging.DEBUG)
        logger = logging.getLogger()
        self.assertEqual(logger.level, logging.DEBUG)
        setup_logging(log_to_file=False, log_level=logging.ERROR)
        logger = logging.getLogger()
        self.assertEqual(logger.level, logging.ERROR)

    def test_custom_naming_convention(self):
        rename_images(current_dir=os.getcwd(), overwrite=True, backup_dir=self.backup_dir, dry_run=False, verbose=True, naming_convention="{index}_test", file_extensions=['.jpg'])
        self.assertTrue(os.path.exists("1_test.jpg"))
        os.remove("1_test.jpg")

    def test_file_filters(self):
        image_file_png = "image2.png"
        with open(image_file_png, 'w') as f:
            f.write("dummy png data")
        rename_images(current_dir=os.getcwd(), overwrite=True, backup_dir=self.backup_dir, dry_run=False, verbose=True, file_extensions=['.jpg'])
        self.assertTrue(os.path.exists("1_test.jpg"))
        self.assertFalse(os.path.exists("1_test.png"))
        os.remove("1_test.jpg")
        os.remove(image_file_png)

if __name__ == "__main__":
    unittest.main()
