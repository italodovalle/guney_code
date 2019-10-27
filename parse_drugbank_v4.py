##############################################################################
# DrugBank v4.3 XML parser
#
# eg 15/01/2016
##############################################################################

from xml.etree.ElementTree import iterparse
import os, cPickle

def main():
    base_dir = "../data/drugbank/"
    #file_name = base_dir + "drugbank.xml" 
    file_name = base_dir + "test.xml"
    parser = DrugBankXMLParser(file_name)
    parser.parse()
    drug = "DB00843"
    target = "BE0000426" #"BE0004796" #"P22303"
    for i in dir(parser):
	print i
	if i.startswith("drug"):
	    d = getattr(parser, i)
	    if drug in d: print d[drug]
	elif i.startswith("target"):
	    d = getattr(parser, i)
	    if target in d: print d[target]
    print parser.drug_to_target_to_values
    drug_to_uniprots = parser.get_targets(target_types = set(["target", "enzyme"]), only_paction=False)
    print drug_to_uniprots
    return


class DrugBankXMLParser(object):
    NS="{http://www.drugbank.ca}"

    def __init__(self, filename):
	self.file_name = filename
	self.drug_to_name = {}
	self.drug_to_description = {}
	self.drug_to_type = {}
	self.drug_to_groups = {}
	self.drug_to_indication = {}
	self.drug_to_pharmacodynamics = {}
	self.drug_to_moa = {}
	self.drug_to_toxicity = {}
	self.drug_to_synonyms = {}
	self.drug_to_products = {}
	self.drug_to_brands = {}
	self.drug_to_uniprot = {}
	self.drug_to_interactions = {} 
	self.drug_to_pubchem = {}
	self.drug_to_pubchem_substance = {}
	self.drug_to_kegg = {}
	self.drug_to_kegg_compound = {}
	self.drug_to_pharmgkb = {}
	self.drug_to_target_to_values = {} # drug - target - (type {target / enzyme / transporter / carrier}, known action, [action types])
        self.drug_to_categories = {}
        self.drug_to_atc_codes = {}
        self.drug_to_inchi_key = {}
        self.drug_to_smiles = {}
	self.target_to_name = {}
	self.target_to_gene = {}
	self.target_to_uniprot = {}
	return

    def parse(self):
	# get an iterable
	context = iterparse(self.file_name, ["start", "end"])
	# turn it into an iterator
	context = iter(context)
	# get the root element
	event, root = context.next()
	state_stack = [ root.tag ]
	drug_id = None
	drug_type = None
	drug_id_partner = None
	current_target = None
	resource = None
        current_property = None 
	target_types = set(map(lambda x: self.NS+x, ["target", "enzyme", "carrier", "transporter"]))
	target_types_plural = set(map(lambda x: x+"s", target_types))
	for (event, elem) in context:
	    if event == "start":
		state_stack.append(elem.tag)
		if len(state_stack) <= 2 and elem.tag == self.NS+"drug":
		    if "type" in elem.attrib:
			drug_type = elem.attrib["type"]
		    else:
			drug_type = None
		elif elem.tag == self.NS+"drugbank-id": 
		    if "primary" in elem.attrib and state_stack[-3] == self.NS+"drugbank" and state_stack[-2] == self.NS+"drug":
			drug_id = None
		    elif len(state_stack) > 3 and state_stack[-3] == self.NS+"drug-interactions" and state_stack[-2] == self.NS+"drug-interaction":
			drug_id_partner = None
		elif elem.tag == self.NS+"resource":
		    resource = None
		elif elem.tag == self.NS+"property":
                    current_property = None
		elif elem.tag in target_types: 
		    if state_stack[-2] in target_types_plural: 
			current_target = None 
	    if event == "end":
		if len(state_stack) <= 2 and elem.tag == self.NS+"drug":
		    if "type" in elem.attrib:
			drug_type = elem.attrib["type"]
		    else: 
			drug_type = None
		if elem.tag == self.NS+"drugbank-id":
		    if state_stack[-2] == self.NS+"drug":
			if "primary" in elem.attrib:
			    drug_id = elem.text
			    if drug_type is not None: 
			        self.drug_to_type[drug_id] = drug_type
			    #print drug_id, drug_type
		    elif len(state_stack) > 3 and state_stack[-3] == self.NS+"drug-interactions" and state_stack[-2] == self.NS+"drug-interaction":
			d = self.drug_to_interactions.setdefault(drug_id, {})
			drug_id_partner = elem.text
			d[drug_id_partner] = ""
		elif elem.tag == self.NS+"name":
		    if len(state_stack) <= 3 and state_stack[-2] == self.NS+"drug": 
			self.drug_to_name[drug_id] = elem.text.strip()
		    elif state_stack[-2] == self.NS+"product" and state_stack[-3] == self.NS+"products":
			product = elem.text
			product = product.strip().encode('ascii','ignore')
			if product != "":
			    self.drug_to_products.setdefault(drug_id, set()).add(product)
		    elif state_stack[-2] == self.NS+"international-brand" and state_stack[-3] == self.NS+"international-brands":
			brand = elem.text
			#idx = brand.find(" [")
			#if idx != -1:
			#    brand = brand[:idx]
			brand = brand.strip().encode('ascii','ignore')
			if brand != "":
			    self.drug_to_brands.setdefault(drug_id, set()).add(brand) 
		    #elif state_stack[-3] == self.NS+"targets" and state_stack[-2] == self.NS+"target":
		    elif state_stack[-3] in target_types_plural and state_stack[-2] in target_types:
			self.target_to_name[current_target] = elem.text 
		elif elem.tag == self.NS+"description":
		    if state_stack[-2] == self.NS+"drug":
			self.drug_to_description[drug_id] = elem.text
		    if len(state_stack) > 3 and state_stack[-3] == self.NS+"drug-interactions" and state_stack[-2] == self.NS+"drug-interaction":
			self.drug_to_interactions[drug_id][drug_id_partner] = elem.text
		elif elem.tag == self.NS+"group":
		    if state_stack[-2] == self.NS+"groups":
			self.drug_to_groups.setdefault(drug_id, set()).add(elem.text)
		elif elem.tag == self.NS+"indication":
		    if state_stack[-2] == self.NS+"drug":
			self.drug_to_indication[drug_id] = elem.text
		elif elem.tag == self.NS+"pharmacodynamics":
		    if state_stack[-2] == self.NS+"drug":
			self.drug_to_pharmacodynamics[drug_id] = elem.text
		elif elem.tag == self.NS+"mechanism-of-action":
		    if state_stack[-2] == self.NS+"drug":
			self.drug_to_moa[drug_id] = elem.text
		elif elem.tag == self.NS+"toxicity":
		    if state_stack[-2] == self.NS+"drug":
			self.drug_to_toxicity[drug_id] = elem.text
		elif elem.tag == self.NS+"synonym":
		    if state_stack[-2] == self.NS+"synonyms" and state_stack[-3] == self.NS+"drug":
			synonym = elem.text
			idx = synonym.find(" [")
			if idx != -1:
			    synonym = synonym[:idx]
			synonym = synonym.strip().encode('ascii','ignore')
			if synonym != "":
			    self.drug_to_synonyms.setdefault(drug_id, set()).add(synonym) 
		elif elem.tag == self.NS+"category":
		    if state_stack[-2] == self.NS+"categories":
			self.drug_to_categories.setdefault(drug_id, set()).add(elem.text)
		elif elem.tag == self.NS+"atc-code":
		    if state_stack[-2] == self.NS+"atc-codes":
			self.drug_to_atc_codes.setdefault(drug_id, set()).add(elem.attrib["code"])
		elif elem.tag == self.NS+"id":	
		    if state_stack[-3] in target_types_plural and state_stack[-2] in target_types:
			current_target = elem.text
			d = self.drug_to_target_to_values.setdefault(drug_id, {})
			d[current_target] = [state_stack[-2], False, []]
			#print current_target 
		elif elem.tag == self.NS+"action":	
		    if state_stack[-3] in target_types and state_stack[-2] == self.NS+"actions":
			self.drug_to_target_to_values[drug_id][current_target][2].append(elem.text)
		elif elem.tag == self.NS+"known-action":
		    if state_stack[-2] in target_types:
			if elem.text == "yes":
			    self.drug_to_target_to_values[drug_id][current_target][1] = True
			    if len(self.drug_to_target_to_values[drug_id][current_target][2]) == 0:
				#print "Inconsistency with target action: %s %s" % (drug_id, current_target)
				pass
		elif elem.tag == self.NS+"gene-name":
		    if state_stack[-3] in target_types and state_stack[-2] == self.NS+"polypeptide":
			self.target_to_gene[current_target] = elem.text 
		elif elem.tag == self.NS+"kind":
		    if state_stack[-3] == self.NS+"calculated-properties" and state_stack[-2] == self.NS+"property":
                        current_property = elem.text # InChIKey or SMILES
		elif elem.tag == self.NS+"value":
		    if state_stack[-3] == self.NS+"calculated-properties" and state_stack[-2] == self.NS+"property":
                        if current_property == "InChIKey":
                            inchi_key = elem.text # strip InChIKey=
                            if inchi_key.startswith("InChIKey="):
                                inchi_key = inchi_key[len("InChIKey="):]
                            self.drug_to_inchi_key[drug_id] = inchi_key
                        if current_property == "SMILES":
                            self.drug_to_smiles[drug_id] = elem.text 
		elif elem.tag == self.NS+"resource":
		    if state_stack[-3] == self.NS+"external-identifiers" and state_stack[-2] == self.NS+"external-identifier":
			resource = elem.text 
		elif elem.tag == self.NS+"identifier":
		    if state_stack[-3] == self.NS+"external-identifiers" and state_stack[-2] == self.NS+"external-identifier":
			if state_stack[-5] in target_types and state_stack[-4] == self.NS+"polypeptide":
			    if resource == "UniProtKB":
				self.target_to_uniprot[current_target] = elem.text
			elif state_stack[-4] == self.NS+"drug":
			    if resource == "PubChem Compound":
				self.drug_to_pubchem[drug_id] = elem.text
			    elif resource == "PubChem Substance":
				self.drug_to_pubchem_substance[drug_id] = elem.text
			    elif resource == "KEGG Drug":
				self.drug_to_kegg[drug_id] = elem.text
			    elif resource == "KEGG Compound":
				self.drug_to_kegg_compound[drug_id] = elem.text
			    elif resource == "UniProtKB":
				self.drug_to_uniprot[drug_id] = elem.text
			    elif resource == "PharmGKB":
				self.drug_to_pharmgkb[drug_id] = elem.text
		elem.clear()
		state_stack.pop()
	root.clear()
	return 

    
    def get_targets(self, target_types = set(["target"]), only_paction=False):
        # Map target ids to uniprot ids
	target_types = map(lambda x: self.NS + x, target_types)
	drug_to_uniprots = {}
        for drug, target_to_values in self.drug_to_target_to_values.iteritems():
            for target, values in target_to_values.iteritems():
		#print target, values
                try:
                    uniprot = self.target_to_uniprot[target]
                except:
                    # drug target has no uniprot
		    #print "No uniprot information for", target 
                    continue
		target_type, known, actions = values
		flag = False
		if only_paction:
		    if known:
			flag = True
		else:
		    if target_type in target_types:
			flag = True
		if flag:
		    drug_to_uniprots.setdefault(drug, set()).add(uniprot)
	return drug_to_uniprots


    def get_synonyms(self, selected_drugs=None, only_synonyms=False):
	name_to_drug = {}
	for drug, name in self.drug_to_name.iteritems():
	    if selected_drugs is not None and drug not in selected_drugs:
		continue
	    name_to_drug[name.lower()] = drug
	synonym_to_drug = {}
	for drug, synonyms in self.drug_to_synonyms.iteritems():
	    for synonym in synonyms:
		if selected_drugs is not None and drug not in selected_drugs:
		    continue
		synonym_to_drug[synonym.lower()] = drug
	if only_synonyms:
	    return name_to_drug, synonym_to_drug
	for drug, brands in self.drug_to_brands.iteritems():
	    for brand in brands:
		if selected_drugs is not None and drug not in selected_drugs:
		    continue
		synonym_to_drug[brand.lower()] = drug
	for drug, products in self.drug_to_products.iteritems():
	    for product in products:
		if selected_drugs is not None and drug not in selected_drugs:
		    continue
		synonym_to_drug[product.lower()] = drug
	return name_to_drug, synonym_to_drug


    def get_drugs_by_group(self, groups_to_include = set(["approved"]), groups_to_exclude=set(["withdrawn"])):
	selected_drugs = set()
	for drugbank_id, name in self.drug_to_name.iteritems():
	    # Consider only approved drugs
	    if drugbank_id not in self.drug_to_groups:
		continue
	    groups = self.drug_to_groups[drugbank_id]
	    #if "approved" not in groups or "withdrawn" in groups: 
	    if len(groups & groups_to_include) == 0:
		continue
	    if len(groups & groups_to_exclude) > 0:
		continue
	    selected_drugs.add(drugbank_id)
	return selected_drugs


def output_data(file_name, out_file):
    dump_file = file_name + ".pcl"
    if os.path.exists(dump_file):
	parser = cPickle.load(open(dump_file))
    else:
	parser = DrugBankXMLParser(file_name)
	parser.parse()
	cPickle.dump(parser, open(dump_file, 'w'))
    #target_type_list = ["target", "enzyme", "carrier", "transporter"]
    #for target_type in target_type_list:
    target_type_list = ["target"]
    drug_to_uniprots = parser.get_targets(target_types = set(target_type_list), only_paction=False)
    f = open(out_file, 'w')
    f.write("Drugbank id\tName\tGroup\tTargets\n") 
    #f.write("Drugbank id\tName\tGroup\tTarget uniprots\tEnzyme uniprots\tTransporter uniprots\tCarrier uniprots\tDescription\tIndication\tPubChem\tSMILES\tInchi\tAlternative names\t\n")
    #drug_to_description drug_to_indication drug_to_synonyms drug_to_products drug_to_brands 
    for drug, uniprots in drug_to_uniprots.iteritems():
	name = parser.drug_to_name[drug]
	groups = parser.drug_to_groups[drug]
	values = [ drug, name.encode("ascii", "replace") ]
	values.append(" | ".join(groups))
	values.append(" | ".join(uniprots))
	try:
	    f.write("%s\n" % "\t".join(values))
	except: 
	    print values
    f.close()
    return


if __name__ == "__main__":
    main()

