from xml.dom import minidom
import pandas

def format_prop_df(j_series, var_series):
    combined_df = pandas.DataFrame(j_series)
    combined_df['var'] = var_series
    combined_list = combined_df.values.tolist()
    xml_string = ''
    for row in combined_list:
        row_string = ''
        for item in row:
            row_string = row_string + '\t' + "{:<4}".format(item)
        row_string = '\t' + row_string + '\n'
        xml_string = xml_string + row_string
    xml_string = '\n' + xml_string + '\t\t'
    return xml_string


def export_jsb_xml(prop_name, ixx, diameter, blades, pitch, ct, cp):
    root = minidom.Document()

    xml = root.createElement('propeller')
    xml.setAttribute('name', 'APC_' + prop_name)
    root.appendChild(xml)

    ixxElement = root.createElement('ixx')
    ixxContent = root.createTextNode(ixx)
    xml.appendChild(ixxElement)
    ixxElement.appendChild(ixxContent)

    diameterElement = root.createElement('diameter')
    diameterElement.setAttribute('unit', 'IN')
    diameterContent = root.createTextNode(diameter)
    xml.appendChild(diameterElement)
    diameterElement.appendChild(diameterContent)

    numbladesElement = root.createElement('numblades')
    numbladesContent = root.createTextNode(blades)
    xml.appendChild(numbladesElement)
    numbladesElement.appendChild(numbladesContent)

    minpitchElement = root.createElement('minpitch')
    minpitchContent = root.createTextNode(pitch)
    xml.appendChild(minpitchElement)
    minpitchElement.appendChild(minpitchContent)

    maxpitchElement = root.createElement('maxpitch')
    maxpitchContent = root.createTextNode(pitch)
    xml.appendChild(maxpitchElement)
    maxpitchElement.appendChild(maxpitchContent)

    thrustElement = root.createElement('table')
    thrustElement.setAttribute('name', 'C_THRUST')
    thrustElement.setAttribute('type', 'internal')
    xml.appendChild(thrustElement)

    thrustTableElement = root.createElement('tableData')
    thrustTableContent = root.createTextNode(ct)
    thrustElement.appendChild(thrustTableElement)
    thrustTableElement.appendChild(thrustTableContent)

    powerElement = root.createElement('table')
    powerElement.setAttribute('name', 'C_POWER')
    powerElement.setAttribute('type', 'internal')
    xml.appendChild(powerElement)

    powerTableElement = root.createElement('tableData')
    powerTableContent = root.createTextNode(cp)
    powerElement.appendChild(powerTableElement)
    powerTableElement.appendChild(powerTableContent)

    xml_text = root.toprettyxml(indent="\t")

    return xml_text