import csv
import os
from settings import SENDER_EMAIL, PASSWORD, DISPLAY_NAME, MAIL_COMPOSE, SUBJECT

from smtplib import SMTP
import smtplib
import markdown
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import ssl


def get_msg(csv_file_path, template):
    with open(csv_file_path, "r", encoding="utf-8-sig") as file:
        headers = [header.strip() for header in file.readline().strip().split(",")]
    print(f"Headers: {headers}")  # Debug statement
    
    with open(csv_file_path, "r", encoding="utf-8-sig") as file:
        data = csv.DictReader(file)
        for row in data:
            print(f"Row: {row}")  # Debug statement
            required_string = template
            for header in headers:
                value = row[header].strip()
                print(f"Replacing ${header} with {value}")  # Debug statement
                required_string = required_string.replace(f"${header}", value)
            print(f"Sending to {row['EMAIL']} with message: {required_string}")  # Debug statement
            yield row["EMAIL"], required_string


def confirm_attachments():
    file_contents = []
    file_names = []
    try:
        for filename in os.listdir("ATTACH"):
            entry = input(
                f"""TYPE IN 'Y' AND PRESS ENTER IF YOU CONFIRM TO ATTACH {filename}
                TO SKIP PRESS ENTER: """
            )
            confirmed = True if entry == "Y" else False
            if confirmed:
                file_names.append(filename)
                with open(f"{os.getcwd()}/ATTACH/{filename}", "rb") as f:
                    content = f.read()
                file_contents.append(content)

        return {"names": file_names, "contents": file_contents}
    except FileNotFoundError:
        print("No ATTACH directory found...")


def send_emails(server: SMTP, template, is_html):

    attachments = confirm_attachments()
    sent_count = 0

    for receiver, message in get_msg("data.csv", template):

        multipart_msg = MIMEMultipart("alternative")

        if SUBJECT:
            multipart_msg["Subject"] = SUBJECT
        else:
            multipart_msg["Subject"] = message.splitlines()[0]
        multipart_msg["From"] = DISPLAY_NAME + f" <{SENDER_EMAIL}>"
        multipart_msg["To"] = receiver

        text = message
        html = markdown.markdown(text)

        part1 = MIMEText(text, "plain")
        part2 = MIMEText(html, "html")

        multipart_msg.attach(part1)
        multipart_msg.attach(part2)

        if attachments:
            for content, name in zip(attachments["contents"], attachments["names"]):
                attach_part = MIMEBase("application", "octet-stream")
                attach_part.set_payload(content)
                encoders.encode_base64(attach_part)
                attach_part.add_header(
                    "Content-Disposition", f"attachment; filename={name}"
                )
                multipart_msg.attach(attach_part)

        try:
            server.sendmail(SENDER_EMAIL, receiver, multipart_msg.as_string())
        except Exception as err:
            print(f"Problem occurred while sending to {receiver}")
            print(err)
            input("PRESS ENTER TO CONTINUE")
        else:
            sent_count += 1

    print(f"Sent {sent_count} emails")


if __name__ == "__main__":
    host = "smtp.gmail.com"
    port = 587  # TLS

    is_html = MAIL_COMPOSE.endswith("html")

    with open(MAIL_COMPOSE, "r", encoding="utf-8") as f:
        template = f.read()

    context = ssl.create_default_context()

    server = SMTP(host=host, port=port)
    server.connect(host=host, port=port)
    server.ehlo()
    server.starttls(context=context)
    server.ehlo()
    server.login(user=SENDER_EMAIL, password=PASSWORD)
    print(SENDER_EMAIL, PASSWORD)

    send_emails(server, template, is_html)