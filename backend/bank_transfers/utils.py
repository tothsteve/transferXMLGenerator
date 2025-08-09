import xml.etree.ElementTree as ET
from xml.dom import minidom
from django.utils import timezone

def generate_xml(transfers):
    """Generate XML for bank transfers"""
    root = ET.Element("HUFTransactions")
    
    for transfer in transfers:
        transaction = ET.SubElement(root, "Transaction")
        
        # Originator
        originator = ET.SubElement(transaction, "Originator")
        orig_account = ET.SubElement(originator, "Account")
        orig_account_num = ET.SubElement(orig_account, "AccountNumber")
        orig_account_num.text = transfer.originator_account.clean_account_number()
        
        # Beneficiary
        beneficiary = ET.SubElement(transaction, "Beneficiary")
        name = ET.SubElement(beneficiary, "Name")
        name.text = transfer.beneficiary.name
        ben_account = ET.SubElement(beneficiary, "Account")
        ben_account_num = ET.SubElement(ben_account, "AccountNumber")
        ben_account_num.text = transfer.beneficiary.clean_account_number()
        
        # Amount
        amount = ET.SubElement(transaction, "Amount", Currency=transfer.currency)
        amount.text = f"{transfer.amount:.2f}"
        
        # Execution Date
        exec_date = ET.SubElement(transaction, "RequestedExecutionDate")
        exec_date.text = transfer.execution_date.strftime("%Y-%m-%d")
        
        # Remittance Info
        remittance = ET.SubElement(transaction, "RemittanceInfo")
        text = ET.SubElement(remittance, "Text")
        text.text = transfer.remittance_info
    
    # Pretty format
    rough_string = ET.tostring(root, 'unicode')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="    ", encoding=None).replace(
        '<?xml version="1.0" ?>\n', 
        '<?xml version="1.0" encoding="UTF-8"?>\n'
    )
