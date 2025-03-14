import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os
import time

MAX_EMAIL_SIZE_MB = 24
MAX_EMAIL_SIZE_BYTES = MAX_EMAIL_SIZE_MB * 1024 * 1024  # Convert MB to bytes
MAX_EMAILS_PER_HOUR = 100  # Limit on the number of emails

def load_sent_files():
    """Load previously sent files from output.txt"""
    sent_files = set()
    try:
        if os.path.exists('output.txt'):
            with open('output.txt', 'r') as f:
                sent_files = set(line.strip() for line in f)
    except Exception as e:
        print("Error loading sent files: {}".format(e))
    return sent_files

def send_photos_via_yahoo(sender_email, app_password, recipient_email, subject, body, folder_path):
    try:
        sent_files = load_sent_files()

        # Scan folder for PNG files
        print("Scanning folder: {}".format(folder_path))
        photos = [file_name for file_name in os.listdir(folder_path)
                  if os.path.isfile(os.path.join(folder_path, file_name)) and file_name.lower().endswith('.jpg') and file_name not in sent_files]

        total_photos = len(photos)
        print("Total photos found: {}".format(total_photos))
       
        current_batch = []  # Track files for the current email
        total_size = 0      # Track the total size of attachments
        email_count = 0     # Track the number of emails sent

        for i, file_name in enumerate(photos):
            file_path = os.path.join(folder_path, file_name)
            file_size = os.path.getsize(file_path)
            print("Processing file: {}, Size: {:.2f} MB".format(file_name, file_size / (1024 * 1024)))

            # Check if adding this file would exceed the 24MB limit
            if total_size + file_size > MAX_EMAIL_SIZE_BYTES:
                # Send the current batch
                print("Batch size reached. Sending email with {} files...".format(len(current_batch)))
                if email_count >= MAX_EMAILS_PER_HOUR:
                    print("Hourly email limit reached. Stopping execution.")
                    break

                isSent = send_email_batch(sender_email, app_password, recipient_email, subject, body, current_batch, folder_path)

                if isSent:
                    # Write sent file names to output.txt
                    with open('output.txt', 'a') as output_file:
                        output_file.write("\n".join(current_batch) + "\n")
                        print("Batch sent. File names appended to output.txt.")
                else:
                    print("Failed to send email.")

                # Increment email count and reset for the next batch
                email_count += 1
                current_batch = []
                total_size = 0
                # time.sleep(COOLDOWN_SECONDS)  # Cooldown to avoid spamming

            # Add the file to the current batch
            current_batch.append(file_name)
            total_size += file_size

        # Send the final batch if it contains any files
        if current_batch and email_count < MAX_EMAILS_PER_HOUR:
            print("Sending final batch with {} files...".format(len(current_batch)))
            isSent = send_email_batch(sender_email, app_password, recipient_email, subject, body, current_batch, folder_path)

            if isSent:
                # Write sent file names to output.txt
                with open('output.txt', 'a') as output_file:
                    output_file.write("\n".join(current_batch) + "\n")
                    print("Final batch sent. File names appended to output.txt.")
            else:
                print("Failed to send email.")

            email_count += 1

        print("Total emails sent: {}".format(email_count))

    except Exception as e:
        print("Error: {}".format(e))

def send_email_batch(sender_email, app_password, recipient_email, subject, body, file_names, folder_path):
    try:
        # Create the email message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        for file_name in file_names:
            file_path = os.path.join(folder_path, file_name)
            with open(file_path, 'rb') as photo:
                mime_base = MIMEBase('image', 'jpg')
                mime_base.set_payload(photo.read())
                encoders.encode_base64(mime_base)
                mime_base.add_header('Content-Disposition', 'attachment', filename=file_name)
                msg.attach(mime_base)

        # Connect to Yahoo's SMTP server and send the email
        print("Connecting to Yahoo SMTP server...")
        smtp = smtplib.SMTP('smtp.mail.yahoo.com', 587)
        smtp.starttls()  # Secure the connection
        print("Logging in...")
        smtp.login(sender_email, app_password)
        print("Sending email...")
        smtp.sendmail(sender_email, recipient_email, msg.as_string())
        smtp.quit()
        print("Email sent successfully!")
        return True
    except Exception as e:
        print("Failed to send email: {}".format(e))
        return False

if __name__ == "__main__":
    sender_email = "<Your yahoo mail>"
    app_password = "<Your yahoo mail app password>"
    recipient_email = "<Your yahoo mail>"
    subject = "Check out these photos!"
    body = "Hi there, here are some photos I wanted to share with you."
    folder_path = "." # in case of "this" folder

    send_photos_via_yahoo(sender_email, app_password, recipient_email, subject, body, folder_path)
