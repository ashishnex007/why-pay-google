import smtplib
from email.message import EmailMessage
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
        print(f"Error loading sent files: {e}")
    return sent_files

def send_photos_via_yahoo(sender_email, app_password, recipient_email, subject, body, folder_path):
    try:
        sent_files = load_sent_files()

        # Scan folder for PNG files
        print(f"Scanning folder: {folder_path}")
        photos = [file_name for file_name in os.listdir(folder_path)
                  if os.path.isfile(os.path.join(folder_path, file_name)) and file_name.lower().endswith('.png') and file_name not in sent_files]

        total_photos = len(photos)
        print(f"Total photos found: {total_photos}")
        
        current_batch = []  # Track files for the current email
        total_size = 0      # Track the total size of attachments
        email_count = 0     # Track the number of emails sent

        for i, file_name in enumerate(photos):
            file_path = os.path.join(folder_path, file_name)
            file_size = os.path.getsize(file_path)
            print(f"Processing file: {file_name}, Size: {file_size / (1024 * 1024):.2f} MB")

            # Check if adding this file would exceed the 24MB limit
            if total_size + file_size > MAX_EMAIL_SIZE_BYTES:
                # Send the current batch
                print(f"Batch size reached. Sending email with {len(current_batch)} files...")
                if email_count >= MAX_EMAILS_PER_HOUR:
                    print("Hourly email limit reached. Stopping execution.")
                    break

                isSent = send_email_batch(sender_email, app_password, recipient_email, subject, body, current_batch, folder_path)

                if(isSent):
                    # Write sent file names to output.txt
                    with open('output.txt', 'a') as output_file:
                        output_file.write("\n".join(current_batch) + "\n")
                        print(f"Batch sent. File names appended to output.txt.")
                else:
                    print("Failed to send email. ")

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
            print(f"Sending final batch with {len(current_batch)} files...")
            isSent = send_email_batch(sender_email, app_password, recipient_email, subject, body, current_batch, folder_path)

            if(isSent):
                # Write sent file names to output.txt
                with open('output.txt', 'a') as output_file:
                    output_file.write("\n".join(current_batch) + "\n")
                    print(f"Final batch sent. File names appended to output.txt.")
            else:
                print("Failed to send email. ")

            email_count += 1

        print(f"Total emails sent: {email_count}")

    except Exception as e:
        print(f"Error: {e}")

def send_email_batch(sender_email, app_password, recipient_email, subject, body, file_names, folder_path):
    try:
        # Create the email message
        msg = EmailMessage()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = subject
        msg.set_content(body)

        for file_name in file_names:
            file_path = os.path.join(folder_path, file_name)
            with open(file_path, 'rb') as photo:
                file_data = photo.read()
                msg.add_attachment(file_data, maintype='image', subtype='png', filename=file_name)

        # Connect to Yahoo's SMTP server and send the email
        print("Connecting to Yahoo SMTP server...")
        with smtplib.SMTP('smtp.mail.yahoo.com', 587) as smtp:
            # smtp.set_debuglevel(1)  # Enable debug output
            smtp.starttls()  # Secure the connection
            print("Logging in...")
            smtp.login(sender_email, app_password)
            print("Sending email...")
            smtp.send_message(msg)
            print("Email sent successfully!")
            return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

if __name__ == "__main__":
    sender_email = "<Your yahoo mail>"
    app_password = "<Your yahoo mail app password>"
    recipient_email = "<Your yahoo mail>"
    subject = "Check out these photos!"
    body = "Hi there, here are some photos I wanted to share with you."
    folder_path = "." # in case of "this" folder

    send_photos_via_yahoo(sender_email, app_password, recipient_email, subject, body, folder_path)
