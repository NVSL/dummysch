from lxml import etree as ET

import os
import ntpath as splitpath
import copy
import Swoop
import Swoop.tools

def make_empty_schematics (gcom_dir, catalog, sch_template):
    components = catalog.findall("component")
    
    for component in components:
        #print "Checking component:", component.get("keyname")
        home_dir = component.find("homedirectory").text
        home_dir = splitpath.basename(home_dir)
        home_dir = os.path.join(gcom_dir, home_dir)
        
        schematic_path = component.find("schematic")
        
        
        if schematic_path is None:
            # no schematic filename specified
            # so let's add one
            print "No schematic specified for", component.get("keyname")
            schematic_path = ET.Element("schematic")
            schematic_path.set("filename", "eagle/empty.auto.sch")
            component.append(schematic_path)
            
        schematic_path = os.path.join(home_dir, schematic_path.get("filename"))
        #print "Using:", schematic_path
        
        if os.path.exists(schematic_path):
            #print schematic_path, "exists"
            pass
        else:
            print "Making auto schematic:", schematic_path
            
            if not os.path.exists(os.path.dirname(schematic_path)):
                os.makedirs(os.path.dirname(schematic_path))
                
            sch_template.write(schematic_path)
            
    return catalog
        
def make_eagle_device_schematics (gcom_dir, catalog, sch_template, libraries):
    components = map(lambda x: x.et, catalog.get_list_of_components())
    
    base_template = copy.deepcopy(sch_template)
    
    for component in components:
        if component.find("schematic") is None and component.find("eagledevice") is None:
            continue;
            
        sch_template = copy.deepcopy(base_template)
        #print "Checking component:", component.get("keyname")
        home_dir = component.find("homedirectory").text
        home_dir = splitpath.basename(home_dir)
        home_dir = os.path.join(gcom_dir, home_dir)
        
        schematic_path = component.find("schematic")
        keyname = component.get("keyname")
            
        if schematic_path is None:
            # no schematic filename specified
            # so let's add one
            #print "No schematic specified for", component.get("keyname")
            schematic_path = ET.Element("schematic")
            schematic_path.set("filename", "eagle/"+keyname+".device.auto.sch")
            component.append(schematic_path)

        if schematic_path.get("filename") is None:
            raise Exception("Missing 'filename' attribute on <schematic>");
        schematic_path = os.path.join(home_dir, schematic_path.get("filename"))
        #print "Using:", schematic_path
        
        
        placedparts = component.find("placedparts")
        ref = None
        if placedparts is not None:
            placedparts = placedparts.findall("placedpart")
        
            if len(placedparts) > 1:
                print "Could not create schematic for component: "+component.get("keyname")+". More than one placed part."
            ref = placedparts[0].get("refdes")
            
        if ref is None:
            ref = "U1"
        
        has_auto = False
        if schematic_path.endswith(".auto.sch"): has_auto = True
        
        if os.path.exists(schematic_path) and not has_auto:
            #print schematic_path, "exists"
            pass
        else:
            #print "Making auto schematic:", schematic_path
            
            if not os.path.exists(os.path.dirname(schematic_path)):
                os.makedirs(os.path.dirname(schematic_path))
                
            # add device
            eagledevice = component.find("eagledevice")
            
            if eagledevice is None:
                print "Could not make auto schematic for:", component.get("keyname") + ". No eagledevice specified."
                #print
                continue
            
            device_name = eagledevice.get("device-name")
            if device_name is None:
                device_name = eagledevice.get("name")
            if device_name is None:
                print "Could not create schematic for component:", component.get("keyname") + ". No device name in eagledevice entry."
                
            library_name = eagledevice.get("library")
            
            variant = eagledevice.get("variant")
            if variant is None: variant = ""
            
            progname = component.get("progname")
            if progname is None:
                progname = ""
                
            if progname is not None:
                value = progname.upper()
            else:
                value = ""
                
            parts = sch_template.find("./drawing/schematic/parts")
            
            instances = sch_template.find("./drawing/schematic/sheets/sheet/instances")
            
            if (library_name == "None") or (library_name == "NONE") or (device_name == "None") or (device_name == "NONE"):
                print "Dummy part found:", ref, device_name, library_name, variant, value
            else:
                parts.append( ET.Element("part", name=ref, library=library_name, deviceset=device_name, device=variant, value=value) )
                instances.append( ET.Element("instance", part=ref, gate="G$1", x="0",y="0") )
            
            # add libraries
            for l in libraries:
                library = ET.parse(l)
                library.find("./drawing/library").set("name", l.split("/")[-1].replace(".lbr", ""))
                sch_template.find("./drawing/schematic/libraries").append(copy.deepcopy(library.find("./drawing/library")))

            make_pin_nets(sch_template)

            heSchematic = Swoop.SchematicFile.from_etree(sch_template)
            Swoop.tools.removeDeadEFPs(heSchematic)
            heSchematic.write(schematic_path)
            #sch_template.write(schematic_path)
            #print
            
    return catalog
            
def make_pin_nets (schematic):
    #print "Adding pin nets..."
    
    # find parts
    parts = schematic.find("./drawing/schematic/parts")
    
    if parts is None:
        return
    
    # to list
    parts = parts.findall("part")
    
    # map to names to find easier
    part_map = {}
    for part in parts:
        part_map[part.get("name")] = part
    
    # get all sheets
    sheets = schematic.find("./drawing/schematic/sheets")
    # to list
    sheets = sheets.findall("sheet")
    
    # for each sheet in the schematic
    for sheet in sheets:
        #print "In sheet..."
        instances = sheet.find("instances")
        instances = instances.findall("instance")
        
        for instance in instances:
            #print "In instance..."
            gate_name = instance.get("gate")
            ref = instance.get("part")
        
            library_name = part_map[ref].get("library")
            #print "Library:", library_name
            deviceset_name = part_map[ref].get("deviceset")
        
            library = schematic.find("./drawing/schematic/libraries/library/[@name='"+library_name+"']")
            
            deviceset = library.find("devicesets/deviceset/[@name='"+deviceset_name+"']")
            assert deviceset is not None, "Deviceset "+deviceset_name+" not found in library "+library_name+"."
            
            gates = deviceset.findall("./gates/gate")
            
            if len(gates) > 1:
                print "Part:", deviceset_name, "has more than one gate. Can only make auto schematics for devices with one gate. Make a schematic manually."
                exit(-1)
            elif len(gates) == 0:
                return
            
            available_gate_name = gates[0].get("name")
            
            # earlier we assumed that the gate_name is G$1, but this might not be the case. Here we fix that.
            if gate_name != available_gate_name:
                gate_name = available_gate_name
                instance.set("gate", gate_name)
            
            #print "Gate name:", gate_name
            gate = deviceset.find("gates/gate[@name='"+gate_name+"']")
        
            symbol = gate.get("symbol")
            symbol = library.find("symbols/symbol[@name='"+symbol+"']")
        
            pins = symbol.findall("pin")
        
            nets = sheet.find("nets")
        
            for pin in pins:
                #print "pin:", ref
                name = pin.get("name")
                net = ET.Element("net", {"name":name, "class":"0"})
                segment = ET.Element("segment")
                pinref = ET.Element("pinref", part=ref, gate=gate.get("name"), pin=name)
                
                segment.append(pinref)
                net.append(segment)
                nets.append(net)
        
        
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
