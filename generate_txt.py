import MySQLdb
import fpdf

def get_common_contact(contacts1, contacts2):
    """
    Between sets of contact information of two people,
    find which they share in common.
    """

    if contacts1 == () or contacts2 == ():
        return [], contacts1, contacts2

    c1id = contacts1[0][0]
    c2id = contacts2[0][0]

    contacts1 = [contact[1:] for contact in contacts1]
    contacts2 = [contact[1:] for contact in contacts2]
    common = [contact for contact in contacts1 if contact in contacts2]
    common_with_id = [[c1id] + list(contact) for contact in common]
    
    contacts1_only = [[c1id] + list(contact) for contact in contacts1 if contact not in contacts2]
    contacts2_only = [[c2id] + list(contact) for contact in contacts2 if contact not in contacts1]

    return common_with_id, contacts1_only, contacts2_only


def sortByType(contact):
    ctype = contact[1]
    if ctype == "adresse":
        return 0
    if ctype == "email":
        return 1
    if ctype == "tel":
        return 2
    if ctype == "fax":
        return 3
    if ctype == "handy":
        return 4
    return 5


def write_contact(contact_info, indent=0):
    contact_str = ""
    contact_info = sorted(contact_info, key=sortByType)
    for contact in contact_info:
        contact_str += "\t" * indent
        ctype = contact[1]
        cname = contact[2]
        cinfo = contact[3]
        if ctype == "email":
            contact_str += "📧"
        elif ctype == "tel":
            contact_str += "✆"
        elif ctype == "handy":
            contact_str += "📱"
        elif ctype == "fax":
            contact_str += "🖷"
        elif ctype == "adresse":
            contact_str += "📮"

        if cname is not None:
            contact_str += " " + cname

        contact_str += ": " + cinfo + "\n"

    return contact_str


def generate_text_tree(start_person_id, path=[], indent=0):
    """
    Recursively generate family tree with contact info in text form.

    Parameters
    ----------
    start_person_id : int
        person_id at root of tree.

    Return
    ------
    tree : str
        Family tree with contact info.
    indent : int
        Indent text further with each generation.
    """

    db = MySQLdb.connect(passwd="", db="familiedb")
    c = db.cursor()
    
    c.execute("""select * from persons where person_id=%s""", (start_person_id,))
    person = c.fetchall()[0]
    
    c.execute("""select * from contact where person_id=%s""", (start_person_id,))
    contact_info = c.fetchall()

    c.execute("""select * from together where p1id=%s""", (start_person_id,))
    partner_info = c.fetchall()
    partner_ids = [pair[1] for pair in partner_info]
    if len(partner_ids) > 0:
        # code currently assumes that everyone has at most one partner - need to rework if any ends up in a throuple
        partner_id = partner_ids[0]
        c.execute("""select * from persons where person_id=%s""", (partner_id,))
        partner = c.fetchall()[0]
        c.execute("""select * from contact where person_id=%s""", (partner_id,))
        partner_contact = c.fetchall()
    else:
        partner = None
        partner_contact = []

    if partner is not None:
        if person[2] == partner[2]: # don't write common surname twice
            tree = "\t" * indent + person[1]
            tree += " - " + partner[1] + " " + partner[2] + "\n"
        else:
            person_ln = person[2] if person[2] is not None else ""
            tree = "\t" * indent + person[1] + " " + person_ln
            partner_ln = partner[2] if partner[2] is not None else ""
            tree += " - " + partner[1] + " " + partner_ln + "\n"
        common_contact, person_only_contact, partner_only_contact = get_common_contact(contact_info, partner_contact)
        tree += write_contact(common_contact, indent=indent+1)
        tree += "\t" * (indent+1) + person[1] + "\n"
        tree += write_contact(person_only_contact, indent=indent+2)
        tree += "\t" * (indent+1) + partner[1] + "\n"
        tree += write_contact(partner_only_contact, indent=indent+2)
        tree += "\n"
    else:
        person_ln = person[2] if person[2] is not None else ""
        tree = "\t" * indent + person[1] + " " + person_ln
        tree += "\n" + write_contact(contact_info, indent=indent+1)

    c.execute("""select youngerid from below where olderid=%s""", (start_person_id,))
    child_ids = c.fetchall()
    if path != []:
        child_ids = [(ci[0],) for ci in child_ids if ci[0] in path+[270]]
        path = [ci for ci in path if ci in child_ids]
    for child_id in child_ids:
        tree += generate_text_tree(child_id, path=path, indent=indent+1)

    return tree


def generate_pdf():
    document = fpdf.FPDF()
    document.set_title("Seltmann-Familienmappe")
    document.set_font("helvetica")
    document.add_page()
    tree = generate_text_tree(1)
    document.multi_cell(w=0, h=None, txt=tree)
    document.output("familienmappe.pdf")

