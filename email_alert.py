from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
import smtplib
from smtplib import SMTPAuthenticationError
import os
import glob
import datetime
import random
import string
from alert_config import get_config

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ALERT_EMAIL = "jsaksham1473@gmail.com"


class Email:

    def __init__(self, source):
        self.source = source
        self.location = "Location not recieved yet"
        self.sender_email = get_config("VCD_EMAIL_ADDRESS", ALERT_EMAIL)
        self.sender_password = get_config("VCD_EMAIL_APP_PASSWORD", "").replace(" ", "").strip()
        self.hospital_email = get_config("VCD_HOSPITAL_EMAIL", ALERT_EMAIL)
        self.police_email = get_config("VCD_POLICE_EMAIL", ALERT_EMAIL)
        self.rto_email = get_config("VCD_RTO_EMAIL", ALERT_EMAIL)
        self.folder_path = os.path.join(_BASE_DIR, "outputs/frame_img/")
        self.files_path = os.path.join(self.folder_path, '*')
        self.files = sorted(glob.iglob(self.files_path), key=os.path.getctime, reverse=True)
        if self.files:
            self.last_file1 = self.files[0]
        else:
            self.last_file1 = None
        self.smtp = None

    def email_conn(self):
        if not self.sender_email:
            raise ValueError("VCD_EMAIL_ADDRESS is not configured.")
        if not self.sender_password:
            raise ValueError(
                "VCD_EMAIL_APP_PASSWORD is not configured. "
                "Create a Gmail App Password and set it in .env or as an environment variable."
            )
        self.smtp = smtplib.SMTP('smtp.gmail.com', 587, timeout=20)
        self.smtp.ehlo()
        self.smtp.starttls()
        self.smtp.ehlo()
        try:
            self.smtp.login(self.sender_email, self.sender_password)
        except SMTPAuthenticationError as exc:
            raise RuntimeError(
                "Gmail authentication failed (535). Use a valid App Password in "
                "VCD_EMAIL_APP_PASSWORD and ensure 2-Step Verification is enabled."
            ) from exc

    def message(self, subject="Python Notification", text="", img=None, attachment=None):
        msg = MIMEMultipart()
        msg['Subject'] = subject
        msg.attach(MIMEText(text))

        if img is not None:
            if type(img) is not list:
                img = [img]
            for one_img in img:
                img_data = open(one_img, 'rb').read()
                msg.attach(MIMEImage(img_data, name=os.path.basename(one_img)))

        if attachment is not None:
            if type(attachment) is not list:
                attachment = [attachment]

            for one_attachment in attachment:
                with open(one_attachment, 'rb') as f:
                    file = MIMEApplication(f.read(), name=os.path.basename(one_attachment))
                file['Content-Disposition'] = f'attachment;\n\t\t\tfilename="{os.path.basename(one_attachment)}"'
                msg.attach(file)

        return msg

    def send_email(self, send_message, location, mail, vcd_reference_code):
        if self.smtp is None:
            raise RuntimeError("SMTP connection is not initialized")
        if not mail:
            raise ValueError("Recipient email address is not configured")
        current_date = datetime.date.today()
        current_time = datetime.datetime.now().time()
        msg = self.message(
            " Attention !, Vehicle Crash Detected !",
            send_message
            + "\nVehicle Crash Detection Reference Number : " + vcd_reference_code
            + "\nDate : " + str(current_date)
            + "\nTime : " + str(current_time)
            + "\nLocation :" + location
            + "\nNOTE : This is an Automatically Generated Mail ,Please do not reply to it"
            + "\nThank you for your cooperation in this matter."
            + "\nSincerely,"
            + "\nRoad Safety Department",
            self.last_file1
        )
        to = [mail]
        self.smtp.sendmail(
            from_addr=self.sender_email,
            to_addrs=to,
            msg=msg.as_string()
        )
        print("Email Alert Successfully Sent")

    def quit_conn(self):
        if self.smtp is not None:
            try:
                self.smtp.quit()
            except Exception:
                pass
            finally:
                self.smtp = None

    def run_mail(self):
        try:
            with open(os.path.join(_BASE_DIR, 'messages/rto_message.txt'), encoding='utf-8') as rto_file:
                rto_message = rto_file.read().strip()
            with open(os.path.join(_BASE_DIR, 'messages/hospital_message.txt'), encoding='utf-8') as hospital_file:
                hospital_message = hospital_file.read().strip()
            with open(os.path.join(_BASE_DIR, 'messages/police_message.txt'), encoding='utf-8') as police_file:
                police_message = police_file.read().strip()
            code_length = 6
            vcd_reference_code = "VCD" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=code_length))

            if self.source == 0:
                self.location = "Hindustan College Of Science And Technology"
            else:
                self.location = "Hindustan College Of Science And Technology"

            print(self.location)
            self.email_conn()
            self.send_email(hospital_message, self.location, self.hospital_email, vcd_reference_code)
            self.send_email(police_message, self.location, self.police_email, vcd_reference_code)
            self.send_email(rto_message, self.location, self.rto_email, vcd_reference_code)
            return True
        except Exception as e:
            raise RuntimeError(f"Failed to send email alert: {e}") from e
        finally:
            self.quit_conn()
