# familienmappe
I maintain a list of contact information for my extended family. That information is saved in an SQL database. The code in this repo can generate a PDF file with the contact information and send it to the people, whose email addresses are listed in the database.

## Generation of PDF
Surprise: uses `generate_pdf.py`. Creates a PDF based on the contents of the database. It expects the database to be called `familiedb`. This database has the form:
```
+---------------------+
| Tables_in_familiedb |
+---------------------+
| below               |
| contact             |
| persons             |
| together            |
+---------------------+
```

Table `persons` contains the basic information for every person.
```describe persons;
+-----------+--------------+------+-----+---------+----------------+
| Field     | Type         | Null | Key | Default | Extra          |
+-----------+--------------+------+-----+---------+----------------+
| person_id | int(11)      | NO   | PRI | NULL    | auto_increment |
| vorname   | varchar(255) | NO   |     | NULL    |                |
| nachname  | varchar(255) | YES  |     | NULL    |                |
| spitzname | varchar(255) | YES  |     | NULL    |                |
| birthday  | date         | YES  |     | NULL    |                |
| img_path  | varchar(255) | YES  |     | NULL    |                |
+-----------+--------------+------+-----+---------+----------------+
```
The generation script expects all images of people to be in a subfolder named "bilder".

Table `contact`:
```describe contact;
+-----------+-----------------------------------------------------+------+-----+---------+-------+
| Field     | Type                                                | Null | Key | Default | Extra |
+-----------+-----------------------------------------------------+------+-----+---------+-------+
| person_id | int(11)                                             | NO   | MUL | NULL    |       |
| type      | enum('email','tel','handy','fax','adresse','other') | YES  |     | NULL    |       |
| name      | tinytext                                            | YES  |     | NULL    |       |
| info      | tinytext                                            | YES  |     | NULL    |       |
+-----------+-----------------------------------------------------+------+-----+---------+-------+
```

Table `below` describes vertical relationships in the family tree. In the case of multiple parents for each child, just give the relationship for one of the parents and describe the relationship between the parents in the table `together`.
```describe below;
+-----------+---------+------+-----+---------+-------+
| Field     | Type    | Null | Key | Default | Extra |
+-----------+---------+------+-----+---------+-------+
| olderid   | int(11) | YES  | MUL | NULL    |       |
| youngerid | int(11) | YES  | MUL | NULL    |       |
+-----------+---------+------+-----+---------+-------+
```

Table `together` contains marriages/other romantic relationships. Note that the script currently expects there to not be more than two people in one relationship.
```describe together;
+-------+---------+------+-----+---------+-------+
| Field | Type    | Null | Key | Default | Extra |
+-------+---------+------+-----+---------+-------+
| p1id  | int(11) | YES  | MUL | NULL    |       |
| p2id  | int(11) | YES  | MUL | NULL    |       |
+-------+---------+------+-----+---------+-------+
```

The script orders the persons in a family-tree-like fashion, beginning with the oldest person(s). Before running, change the script in lines 224-227, to call the generation function with the id of each of the starting persons. It generates a PDF called `familienmappe.pdf`.

## Sending the information
Call the script as either `send_emails.py list` or `send_emails.py questions`. The first one sends the generated PDF to everyone email in the database. The second one sends each person their part of the family tree and asks them, if any information has changed. Before running the script, change the server informaiton in the `send_email` function

### Questions
For requesting people's information, you may want to adapt the text in the `combine_texts` function. Also change the `starting_ids` in line 152 to those of the oldest people in the family tree. That way, each person will only be shown the tree of their branch of the family.

### List
For sending the completed list, update the message text in line 141.
