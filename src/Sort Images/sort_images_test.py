import unittest
import os
import shutil
import tempfile
import logging
import re
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
        self.image_file = "example.jpg"
        self.txt_files = [
            "example2_prompt.txt",
            "example_prompt.txt",
            "example_negative.txt",
            "example2_negative.txt",
            "example2_extra.txt",
            "example_extra.txt",
            "example_extra_extra.txt",
            "example2_extra_extra.txt",
            "example2.png"
        ]
        with open(self.image_file, 'w') as f:
            f.write("dummy image data")
        for txt_file in self.txt_files:
            with open(txt_file, 'w') as f:
                f.write(f"dummy data for {txt_file}")
        self.backup_dir = "backup"
        create_backup_dir(self.backup_dir)
        logging.info(f"Created test files in {self.test_dir}")

    def tearDown(self):
        for file in os.listdir(self.test_dir):
            file_path = os.path.join(self.test_dir, file)
            if os.path.isfile(file_path):
                os.remove(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        os.chdir(self.current_dir)

    def test_get_random_string(self):
        random_string = get_random_string(8)
        self.assertEqual(len(random_string), 8)
        self.assertTrue(all(c.islower() or c.isdigit() for c in random_string))

    def test_backup_file(self):
        backup_path = backup_file(self.image_file, self.backup_dir)
        self.assertIsNotNone(backup_path)
        self.assertTrue(os.path.exists(backup_path))

    def test_rename_file(self):
        new_name = "renamed_example.jpg"
        rename_file(self.image_file, new_name, dry_run=False, verbose=False)
        self.assertTrue(os.path.exists(new_name))
        self.assertFalse(os.path.exists(self.image_file))

    def test_process_txt_files(self):
        base_name = "example"
        unique_string = get_random_string(8)
        new_base_name = f"1_{unique_string}"
        process_txt_files(base_name, new_base_name, self.backup_dir, self.test_dir, dry_run=False, verbose=False)

        expected_files = [
            f"1_{unique_string}_prompt.txt",
            f"1_{unique_string}_negative.txt",
            f"1_{unique_string}_extra.txt",
            f"1_{unique_string}_extra_extra.txt"
        ]

        for file in expected_files:
            self.assertTrue(os.path.exists(os.path.join(self.test_dir, file)))

        original_files = [
            "example_prompt.txt",
            "example_negative.txt",
            "example_extra.txt",
            "example_extra_extra.txt"
        ]

        for file in original_files:
            self.assertFalse(os.path.exists(os.path.join(self.test_dir, file)))

    def test_process_image(self):
        unique_string = get_random_string(8)
        new_image_name = f"1_{unique_string}.jpg"
        process_image(self.image_file, new_image_name, self.test_dir, self.backup_dir, overwrite=True, dry_run=False, verbose=False)
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, new_image_name)))
        self.assertFalse(os.path.exists(os.path.join(self.test_dir, self.image_file)))

    def test_rename_images_dry_run(self):
        rename_images(self.test_dir, overwrite=True, backup_dir=self.backup_dir, dry_run=True, verbose=False, naming_convention="{index}_{random}", file_extensions=['.jpg', '.png'])

        self.assertTrue(os.path.exists(os.path.join(self.test_dir, self.image_file)))
        image_files = [f for f in os.listdir(self.test_dir) if re.match(r'\d+_[a-z0-9]{8}\.jpg', f)]
        self.assertFalse(image_files)

    def test_logging_levels(self):
        setup_logging(log_to_file=True, log_level=logging.DEBUG)
        logger = logging.getLogger()
        self.assertEqual(logger.level, logging.DEBUG)

    def test_custom_naming_convention(self):
        rename_images(self.test_dir, overwrite=True, backup_dir=self.backup_dir, dry_run=False, verbose=False, naming_convention="{index}_{random}", file_extensions=['.jpg'])

        image_files = [f for f in os.listdir(self.test_dir) if re.match(r'\d+_[a-z0-9]{8}\.jpg', f)]
        self.assertTrue(image_files)

        for img_file in image_files:
            prefix = img_file.split('_')[0]
            unique_string = img_file.split('_')[1].split('.')[0]
            associated_txt_files = [f for f in os.listdir(self.test_dir) if f.startswith(f"{prefix}_{unique_string}") and f.endswith('.txt')]
            self.assertTrue(associated_txt_files)
            for txt_file in associated_txt_files:
                self.assertTrue(txt_file.startswith(f"{prefix}_{unique_string}"))

    def test_file_filters(self):
        other_file = "other.txt"
        with open(other_file, 'w') as f:
            f.write("dummy other file")

        rename_images(self.test_dir, overwrite=True, backup_dir=self.backup_dir, dry_run=False, verbose=False, naming_convention="{index}_{random}", file_extensions=['.jpg'])

        image_files = [f for f in os.listdir(self.test_dir) if re.match(r'\d+_[a-z0-9]{8}\.jpg', f)]
        self.assertTrue(image_files)
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, other_file)))
        os.remove(other_file)

if __name__ == "__main__":
    unittest.main()
