from lxml import etree as ET

import os
import ntpath as splitpath
import copy
import Swoop
import Swoop.tools
import logging as log

def make_empty_schematics (gcom_dir, catalog, sch_template):
    raise Exception("This function needs to be Swoopized")
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

    for l in libraries:
        Swoop.library_cache.register_library(l)
    
    for component in components:
        if component.find("schematic") is None and component.find("eagledevice") is None:
            continue;

        sch = Swoop.SchematicFile.from_etree(base_template)
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
            pass
        else:
            
            if not os.path.exists(os.path.dirname(schematic_path)):
                os.makedirs(os.path.dirname(schematic_path))

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
            # this is why this script is slow.  We copy the whole library, and
            # the clear out almost all of it a few lines later. If you want to
            # fix it, add a function to just what's need for an instance from
            # an .lbr to a .sch or .brd.  It'd be useful generally.
            library = Swoop.library_cache.load_library_by_name(library_name).get_library().clone().set_name(library_name)
            log.info("adding {}".format(library_name))
            sch.add_library(library)

            if (library_name == "None") or (library_name == "NONE") or (device_name == "None") or (device_name == "NONE"):
                print "Dummy part found:", ref, device_name, library_name, variant, value
            else:
                p = (Swoop.Part().
                     set_name(ref).
                     set_library(library_name).
                     set_deviceset(device_name).
                     set_device(variant))

                if library.get_deviceset(device_name).get_uservalue():
                    p.set_value(value)
                
                sch.add_part(p)
                sch.get_nth_sheet(0).add_instance(Swoop.Instance().
                                                  set_part(ref).
                                                  set_gate("G$1").
                                                  set_location(0,0))


            make_pin_nets(sch)

            Swoop.tools.removeDeadEFPs(sch)
            sch.write(schematic_path)
            
    return catalog
            
def make_pin_nets (schematic):

    for sheet in schematic.get_sheets():
        for instance in sheet.get_instances():
            gate_name = instance.get_gate()
            ref = instance.get_part()
        
            library = schematic.get_part(ref).find_library()
            deviceset = schematic.get_part(ref).find_deviceset()
            assert deviceset is not None, "Deviceset "+ schematic.get_part(ref).get_deviceset() +" not found in library "+schematic.get_part(ref).get_library()+"."
            gates = instance.find_part().find_deviceset().get_gates()
            
            if len(gates) > 1:
                print "Part:", deviceset_name, "has more than one gate. Can only make auto schematics for devices with one gate. Make a schematic manually."
                exit(-1)
            elif len(gates) == 0:
                return
            
            available_gate_name = gates[0].get_name()
            
            # earlier we assumed that the gate_name is G$1, but this might not be the case. Here we fix that.
            if gate_name != available_gate_name:
                gate_name = available_gate_name
                instance.set_gate(gate_name)
            
            for pin_name in (Swoop.From(deviceset).
                             get_gate(gate_name).
                             find_symbol().
                             get_pins().
                             get_name()):
                sheet.add_net(Swoop.Net().
                              set_name(pin_name).
                              set_class("0").
                              add_segment(Swoop.Segment().
                                          add_pinref(Swoop.Pinref().
                                                     set_part(ref).
                                                     set_gate(gate_name).
                                                     set_pin(pin_name))))
        
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
