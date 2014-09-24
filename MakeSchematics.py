from lxml import etree as ET

import os
import ntpath as splitpath
import copy

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
    components = catalog.findall("component")
    
    base_template = copy.deepcopy(sch_template)
    
    for component in components:
        sch_template = copy.deepcopy(base_template)
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
            schematic_path.set("filename", "eagle/device.auto.sch")
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
                
            # add device
            eagledevice = component.find("eagledevice")
            
            if eagledevice is None:
                print "Could not make auto schematic for:", component.get("keyname"), "no eagledevice specified."
                continue
            
            device_name = eagledevice.get("device-name")
            if device_name is None:
                device_name = ""
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
            
            ref = "U1"
            
            parts.append( ET.Element("part", name=ref, library=library_name, deviceset=device_name, device=variant, value=value) )
            
            
            
            instances.append( ET.Element("instance", part=ref, gate="G$1", x="0",y="0") )
            
            # add libraries
            for l in libraries:
                library = ET.parse(l)
                library.find("./drawing/library").set("name", l.split("/")[-1].replace(".lbr", ""))
                sch_template.find("./drawing/schematic/libraries").append(copy.deepcopy(library.find("./drawing/library")))

            sch_template.write(schematic_path)
            
    return catalog
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            