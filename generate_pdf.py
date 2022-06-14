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


def write_contact(document, contact_info, indent=0, img_path=None):
    base_indent = 15
    margin = 10

    prev_page = document.page_no()
    if img_path:
        prev_y = document.get_y()
        document.set_y(prev_y - 3)
        document.set_x(base_indent * (indent-1) + margin)
        document.image("bilder/"+img_path, w=15)
        img_y = document.get_y()
        #if img_y > prev_y:
        img_page = document.page_no()
        if img_page == prev_page:
            document.set_y(prev_y)
        else:
            document.set_y(12)

    contact_str = ""
    contact_info = sorted(contact_info, key=sortByType)
    for contact in contact_info:
        contact_str = ""#"    " * indent
        ctype = contact[1]
        cname = contact[2]
        cinfo = contact[3]
        if ctype == "email":
            contact_str += "@"
        elif ctype == "tel":
            contact_str += "☏"
        elif ctype == "handy":
            contact_str += "✆"#"📱"
        elif ctype == "fax":
            contact_str += "Fax"#"🖷"
        elif ctype == "adresse":
            contact_str += "✉"#"📮"

        if cname is not None:
            contact_str += " " + cname

        contact_str += ": " + cinfo
        document.set_x(base_indent * indent + margin)
        document.cell(w=0, h=0, txt=contact_str)
        document.ln(5)

    if img_path:# and (document.get_y() < img_y or document.page_no()>img_page):
        document.set_y(img_y)
        document.ln(2)


def generate_text_tree(document, start_person_id, path=[], indent=0):
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

    base_indent = 15
    margin = 10

    if len(partner_ids) > 0:
        # code currently assumes that everyone has at most one partner - need to rework if anyone ends up in a throuple
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
            tree = person[1]
            tree += " - " + partner[1] + " " + partner[2]
            document.set_x(base_indent * indent + margin)
            document.cell(w=0, h=0, txt=tree)
            document.ln(5)
        else:
            person_ln = person[2] if person[2] is not None else ""
            tree = person[1] + " " + person_ln
            partner_ln = partner[2] if partner[2] is not None else ""
            tree += " - " + partner[1] + " " + partner_ln
            document.set_x(base_indent * indent + margin)
            document.cell(w=0, h=0, txt=tree)
            document.ln(5)
        common_contact, person_only_contact, partner_only_contact = get_common_contact(contact_info, partner_contact)
        write_contact(document, common_contact, indent=indent+1)

        img_path = person[-1]
        if len(person_only_contact) != 0 or img_path is not None:
            tree = person[1]
            document.set_x(base_indent * (indent+1) + margin)
            document.cell(w=0, h=0, txt=tree)
            document.ln(5)
            write_contact(document, person_only_contact, indent=indent+2, img_path=img_path)

        img_path = partner[-1]
        if len(partner_only_contact) != 0 or img_path is not None:
            document.ln(5)
            tree = partner[1]
            document.set_x(base_indent * (indent+1) + margin)
            document.cell(w=0, h=0, txt=tree)
            document.ln(5)
            write_contact(document, partner_only_contact, indent=indent+2, img_path=img_path)
        document.ln(5)
    elif partner is None and (len(contact_info) > 0 or person[-1] is not None):
        person_ln = person[2] if person[2] is not None else ""
        tree = person[1] + " " + person_ln
        document.set_x(base_indent * indent + margin)
        document.cell(w=0, h=0, txt=tree)
        document.ln(5)
        img_path = person[-1]
        write_contact(document, contact_info, indent=indent+1, img_path=img_path)
        document.ln(5)
    else:
        img_path = person[-1]
        if img_path:
            prev_y = document.get_y()
            document.set_y(prev_y - 3)
            document.set_x(base_indent * (indent-1) + margin)
            document.image("bilder/"+img_path, w=15)
            img_y = document.get_y()
            document.set_y(prev_y)
        person_ln = person[2] if person[2] is not None else ""
        tree = person[1] + " " + person_ln
        document.set_x(base_indent * indent + margin)
        document.cell(w=0, h=0, txt=tree)
        document.ln(5)
        if img_path:
            document.set_y(img_y)

    c.execute("""select youngerid from below where olderid=%s""", (start_person_id,))
    child_ids = c.fetchall()
    if path != []:
        child_ids = [(ci[0],) for ci in child_ids if ci[0] in path+[270]]
        path = [ci for ci in path if ci in child_ids]

    for child_id in child_ids:
        document = generate_text_tree(document, child_id, path=path, indent=indent+1)
    if len(child_ids) > 0:
        c.execute("""select * from contact where person_id=%s""", (child_id,))
        contact_info = c.fetchall()
        if len(contact_info) == 0: # last child has no contact info
            document.ln(5)

    return document

if __name__ == "__main__":
    document = fpdf.FPDF()
    document.set_title("Seltmann-Familienmappe")
    document.add_font('DejaVuSans', fname='DejaVuSans.ttf', uni=True)
    document.add_font('DejaVuSansBold', fname='DejaVuSans-BoldOblique.ttf', uni=True)
    document.set_font("DejaVuSansBold", size=20)
    document.add_page()
    document.set_auto_page_break(True, margin=20)
    document.cell(w=0, h=0, align="C", txt="Seltmann-Familienmappe")
    document.ln(10)
    document.set_font("DejaVuSans", size=12)
    document.cell(w=0, h=0, align="C", txt="Stand: 26.11.2021")
    document.ln(10)
    generate_text_tree(document, 1)
    generate_text_tree(document, 32)
    generate_text_tree(document, 268)
    generate_text_tree(document, 357)
    document.output("familienmappe.pdf")
