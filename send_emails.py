from generate_txt import generate_text_tree

import smtplib
import MySQLdb
import copy
from getpass import getpass
import mimetypes
import pickle
import os
import argparse

from email.message import EmailMessage

def combine_texts(person_id, path=[]):
    text = "Hallo "
    db = MySQLdb.connect(passwd="", db="familiedb")
    c = db.cursor()
    c.execute("""select vorname from persons where person_id=%s""", (person_id,))
    name = c.fetchall()[0][0]
    text += name + ",\n"
    text += """da bald wieder das Seltmann-Familientreffen ansteht, möchte ich auch wieder die Familienmappe updaten. Das hier ist die aktuelle Information aus Deinem Zweig der Familie:\n
    """

    tree = generate_text_tree(path[0], path=path[1:])

    text += tree + "\n"

    text += """Könntest Du mir bitte bis zum 16. Oktober schreiben, ob sich da was geändert hat? Kannst Du mir auch die Geburtsdaten von neu dazugekommenen Familienmitgliedern schreiben?

Beim letzten Familientreffen wurde angeregt, Bilder in die Familienmappe einzufügen. Wenn Du magst, kannst Du mir ein Passbild oder Selfie schicken, das ich mit einbauen kann. Wenn Du beim Familientreffen mit dabei bist, kann ich auch dort ein Bild von Dir machen. Das ist natürlich nicht verpflichtend, wenn Du Dein Bild nicht mit einbauen willst.

Liebe Grüße,
Johann

P.S.: Ich hab diese Email mit einem selbst-geschriebenen Programm geschickt, das automatisch alle Email-Adressen aus der Familienmappe zieht. Wenn irgendwelche Fehler sind, sag mir bitte Bescheid, dann kann ich das Programm entsprechend anpassen."""

    return text

def send_email(msg_text, rec_addr, send_addr, pw, test_emails, send_list=False):
    try:
        msg = EmailMessage()
        msg.set_content(msg_text)

        msg['Subject'] = "Seltmann-Familientreffen"
        msg['From'] = send_addr
        msg['To'] = rec_addr
        msg['Bcc'] = ", ".join(test_emails)
        all_addr = [rec_addr] + test_emails

        if send_list:
            filename = "familienmappe.pdf"
            ctype, encoding = mimetypes.guess_type(filename)
            maintype, subtype = ctype.split('/', 1)
            with open(filename, 'rb') as fp:
                msg.add_attachment(fp.read(), maintype=maintype, subtype=subtype,
                        filename=filename)

        smtp_server = smtplib.SMTP("posteo.de", port=587)
        smtp_server.ehlo()
        smtp_server.starttls()
        smtp_server.ehlo()
        smtp_server.login(send_addr, pw)

        smtp_server.send_message(msg, from_addr=msg["From"], to_addrs=all_addr)
    except Exception as e:
        print(rec_addr)
        print(e)


def select_email_ids(start_id, path=[]):
    """
    Select email adresses to send to and from which person_id to start
    the sub-tree to be send to each address.

    Parameters
    ----------
    start_id : int
        person_id from which to start the search in the tree.
    path : [int]
        Path through family tree taken so far. Break off after two entries.

    Return
    ------
    addr_info : [(str,int,[int])]
        Tuples of (email,person_id, path to full tree).
        The third element is the path in the family tree to the start of the actual
        tree to be sent in the email. Other branches of the tree will not be shown.
    """

    db = MySQLdb.connect(passwd="", db="familiedb")
    c = db.cursor()

    c.execute("""select * from contact where person_id=%s""", (start_id,))
    contacts = c.fetchall()
    emails = [c[3] for c in contacts if c[1] == "email"]
    if len(path) < 2:
        path.append(start_id)
    if len(emails) > 0:
        curr_tup = (emails[0], start_id, path)
        addr_info = [curr_tup]
    else:
        addr_info = []

    c.execute("""select youngerid from below where olderid=%s""", (start_id,))
    child_ids = c.fetchall()
    for child_id in child_ids:
        addr_info += select_email_ids(child_id[0], copy.copy(path))

    c.execute("""select p2id from together where p1id=%s""", (start_id,))
    partner_ids = c.fetchall()
    if len(partner_ids) > 0:
        partner_id = partner_ids
        addr_info += select_email_ids(partner_id[0], copy.copy(path))

    return addr_info


def get_all_emails():
    """
    Just return all email addresses.
    """
    db = MySQLdb.connect(passwd="", db="familiedb")
    c = db.cursor()

    c.execute("""select * from contact where type='email'""")
    contacts = c.fetchall()
    emails = set([c[3] for c in contacts])

    return emails


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["questions", "list"], help="Whether to ask people for updates to their contact info or to send them the finished list.")
    args = parser.parse_args()

    sender_email = input("Enter sender email: ")
    pw = getpass()

    if args.action == "list":
        msg_text = """ """
        if msg_text.strip() == "":
            raise("You haven't set a message text.")
        emails = get_all_emails()
        emails = list(emails)
        send_email(msg_text, sender_email, sender_email, pw, emails)
    elif args.action == "questions":
        with open("already_sent.pkl", "rb") as als:
            already_sent = pickle.load(als)

        # person_ids from which to start family sub-trees to send to people
        starting_ids = [1,32,268,357]
        for gid in starting_ids:
            addr_info = select_email_ids(gid, path=[])
            emails = set([t[0] for t in addr_info])
            for (email, person_id, path) in addr_info:
                if email in already_sent:
                    continue
                emails.append(email)
                msg_text = combine_texts(person_id, path)
                send_email(msg_text, email, sender_email, pw)
        with open("already_sent.pkl", "wb") as als:
            pickle.dump(already_sent + emails, als)
