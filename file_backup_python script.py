import datetime as dt
import os
import shutil
import smtplib
import time
import zipfile
from tqdm import tqdm

days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
from_email = "email@domain.com"
from_email_password = "password"
emails = ["email@domain.com", "email2@domain.com"]

source_folder = "/Users/Documents/source_folder"
destination_folder = os.path.join("D:backup_folder")
temp_folder = "/Users/Documents/temp_folder"

root_path = os.getcwd()
file_paths = []
zipped_files_paths = []


def time_of_backup():
    # time of backup for the email notification
    current_date = dt.datetime.now()
    backup_date = current_date.date()
    hour = current_date.hour
    minute = current_date.minute
    # gets the day of the week based on the number of the day of the week
    day = days[current_date.weekday()]
    return f"on {day}, {backup_date}, at {hour}:{minute}."


backup_success_email_message = f"All files from '{source_folder}' have been successfully backed up " \
                               f"to '{destination_folder}' {time_of_backup()}\n" \
                               f"The original files have been moved to a temporary folder '{temp_folder}' " \
                               f"and will be deleted on"


missing_files_error_message = f"The '{source_folder}' is empty and no files have been backed up. " \
                              f"Please make sure the folder contains data and run the backup again."


def delete_zip_files():
    # delete residual archive in case any folder error occurs
    for root, directories, files in os.walk(root_path):
        for file in files:
            if file.endswith("zip"):
                os.remove(file)


def get_time_of_creation():
    # get the time of creation of the first file
    file_created = os.path.getctime(file_paths[-1])
    # convert the time in seconds to a timestamp
    file_creation = time.ctime(file_created)
    date = file_creation[:10] + file_creation[19:]
    return date


def create_archive(folder):
    # creates a zip archive from all files found in a source folder
    get_all_file_paths(folder)
    with zipfile.ZipFile(f'{create_backup_name()}.zip', 'w') as zipF:
        for file in tqdm(file_paths, unit=" Files", desc="Compressing"):
            time.sleep(0.1)
            zipF.write(file, compress_type=zipfile.ZIP_DEFLATED)


def get_all_file_paths(path):
    # crawling through directory and subdirectories the collect the file paths
    if not os.path.exists(source_folder):
        folder_not_found_email(source_folder)
        print(f"Folder '{path}' is unreachable, missing or was renamed. "
              f"Please check the folder path and run the backup again.")
        time.sleep(3)
        print("Script exiting in 5 seconds")
        time.sleep(5)
        exit()
    else:
        for root, directories, files in os.walk(path):
            for file in files:
                # join the two strings in order to form the full filepath.
                filepath = os.path.join(root, file)
                file_paths.append(filepath)


def create_backup_name():
    # create backup name based on folder name and a time of creation of the first file that was backed up
    filepath = os.path.dirname(source_folder)
    folder_name = os.path.basename(filepath)
    backup_file_time = get_time_of_creation()
    full_name = f"{folder_name}" + "_" + backup_file_time.replace(" ", "_")
    return full_name


def get_zipped_file_path(root):
    # get file path of the backed zip file
    for roots, directories, files in os.walk(root):
        for file in files:
            # join the two strings in order to form the full filepath.
            filepath = os.path.join(roots, file)
            if filepath.endswith("zip"):
                zipped_files_paths.append(filepath)


def copy_to_temp_folder(temp_path):
    # moves the original files that were already backed up to a temporary folder
    if not os.path.exists(temp_path):
        folder_not_found_email(temp_folder)
        print(f"Folder '{temp_folder}' is unreachable, missing or was renamed. "
              f"Please check the folder path and run the backup again. ")
        time.sleep(3)
        print("Script exiting in 5 seconds")
        time.sleep(5)
        exit()
    elif os.path.exists(temp_path):
        for file in tqdm(file_paths, unit=" Files", desc="Copying"):
            shutil.copy2(file, temp_folder)


def copy_zipped_files(destination):
    # copies the backed up files to a backup location (backup server)
    get_zipped_file_path(root_path)
    time.sleep(0.5)
    if os.path.exists(destination_folder):
        for file in tqdm(zipped_files_paths, unit=" Files", desc="Copying"):
            shutil.copy(file, destination)
            os.remove(file)
    else:
        folder_not_found_email(destination_folder)
        print(f"Folder '{destination_folder}' is unreachable, missing or was renamed. "
              f"Please check the folder path and run the backup again. ")
        time.sleep(1)
        delete_zip_files()
        print("Script exiting in 5 seconds")
        time.sleep(5)
        exit()


def delete_old_files():
    # deletes the original files that were already backed up, and copied to a temporary folder
    try:
        time.sleep(1)
        for file in tqdm(file_paths[::], unit=" Files", desc="Deleting"):
            time.sleep(0.05)
            os.remove(file)
    except FileNotFoundError:
        pass


def backup_success_email():
    # send an email notification when the backup script finishes successfully
    for email in emails:
        with smtplib.SMTP("smtp.gmail.com", port=587) as connect:
            connect.starttls()
            connect.login(user=from_email, password=from_email_password)
            connect.sendmail(from_addr=from_email, to_addrs=email,
                             msg=f"Subject:Database backup successful\n\n{backup_success_email_message} ")
            connect.close()


def missing_files_email():
    # send an email notification when there are no files in the source folder
    for email in emails:
        with smtplib.SMTP("smtp.gmail.com", port=587) as connect:
            connect.starttls()
            connect.login(user=from_email, password=from_email_password)
            connect.sendmail(from_addr=from_email, to_addrs=email,
                             msg=f"Subject:Database backup FAILED!\n\n{missing_files_error_message}")
            connect.close()


def folder_not_found_email(folder):
    # send an email notification when 'source folder', 'temp folder' or the 'destination folders are
    # unreachable, missing or have been renamed
    for email in emails:
        with smtplib.SMTP("smtp.gmail.com", port=587) as connect:
            connect.starttls()
            connect.login(user=from_email, password=from_email_password)
            connect.sendmail(from_addr=from_email, to_addrs=email,
                             msg=f"Subject:Database backup FAILED!\n\nThe '{folder}'"
                                 f" is unreachable, missing or was renamed. "
                                 f"Please check the folder path and run the backup again.")
            connect.close()


def run_backup():
    print("Starting Database files backup task.")
    time.sleep(1)
    try:
        print(f"Attempting to create an archive from files in '{source_folder}'.")
        time.sleep(1)
        create_archive(source_folder)
    except IndexError:
        missing_files_email()
        print("Source folder empty. No files will be backed up. Stopping the script in 5 seconds")
        time.sleep(5)
        exit()
    else:
        time.sleep(2)
        print(f"Copying archived files to '{destination_folder}'.")
        time.sleep(2)
        copy_zipped_files(destination_folder)
        time.sleep(2)
        print(f"Copying original files to a temporary folder '{temp_folder}'.")
        time.sleep(2)
        copy_to_temp_folder(temp_folder)
        time.sleep(2)
        print(f"Deleting original files from '{source_folder}'.")
        # delete_old_files()
        time.sleep(2)
        print(f"Sending notification email to '{emails}'.")
        backup_success_email()
        time.sleep(2)
        print("Task finished successfully.")
        time.sleep(5)
        exit()


run_backup()
